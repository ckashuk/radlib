#!/usr/bin/env python
import glob
import json
import logging
import os
import subprocess
import shutil
import zipfile

from flywheel_gear_toolkit import GearToolkitContext

# This is the run.py code to run and parse an OSCAR analysis from a Flywheel gear.
# This gear will be run on an acquisition that contains at least one dicom series.
# Outputs will go to that acquisition, and to an analysis connected to the gear run.

# change log:
# 2026-07 csk    gear 0.9.0 initial version
# 2026-07 csk    gear 0.9.1 update "gear output files" (cannot use upload_file on flywheel gear analysis container!)
# 2026-08 csk    gear 0.9.10 add input file chooser, file filters and override
log = logging.getLogger(__name__)

def get_metadata_for_flywheel_file(dicom_file, metadata_path:list[str]):
    """
    Get the value of a "metadata path" from a flywheel file object.
    Assumes metadata were added by the file_metadata_importer gear or some other
    method that mimics it

    Parameters
    ----------
    dicom_file:
        The flywheel File object to find the tag in
    metadata_path: list[str]
        The metadata path to look for the info. A series of dict keys

    Returns
    -------
    The value of the dicom tag if it exists in the File, or None
    """

    # traverse the set of keys

    value = dicom_file
    for key in metadata_path:
        value = None if value is None else value.get(key)
    return value


def run_oscar_tools(context: GearToolkitContext) -> None:
    """
    run the OSCAR toolkit and update the results to flywheel

    TODO: 202508 csk someday we can break flywheel-specific stuff out of here
    and build a primary python endpoint for RUN_OSCAR_TOOLS.sh!

    Parameters
    ----------
    context: GearToolkitContext
        A flywheel gear toolkit object containing environment information for the gear
    """

    # get the analysis container object from the gear context
    fw_client = context.client
    analysis_from = fw_client.get(context.destination["id"])

    # get the gear parameters
    image_file_name = context.get_input_filename('image_file')
    override = context.config.get('override')

    # get the parents of this analysis to build the script
    group_id = analysis_from.parents["group"]
    project = fw_client.get_project(analysis_from.parents["project"])
    subject = fw_client.get(analysis_from.parents["subject"])
    session = fw_client.get(analysis_from.parents["session"])
    acquisition = fw_client.resolve(f'{group_id}/{project.label}/{subject.label}/{session.label}/{os.path.basename(image_file_name).replace(".dicom.zip", "")}')['path'][-1]
    image_file = fw_client.resolve(f'{group_id}/{project.label}/{subject.label}/{session.label}/{acquisition.label}/{os.path.basename(image_file_name)}')['path'][-1]

    # 202508 csk  debugging info, could get rid of
    log.debug("file_name is ", image_file_name)
    log.debug("acquisition is ", acquisition.label)
    log.debug("file is ", image_file.name)
    log.debug("override is ", type(override), f'[{override}]')
    log.debug("modality is ", get_metadata_for_flywheel_file(image_file, ['modality']))
    log.debug("orientation is ", get_metadata_for_flywheel_file(image_file, ['classification', 'Scan Orientation']))
    log.debug("slice thickness is ", get_metadata_for_flywheel_file(image_file, ['info', 'header', 'dicom', 'SliceThickness']))
    log.debug("slice count is ", get_metadata_for_flywheel_file(image_file, ['zip_member_count']))

    # check image filter
    # TODO: 202508 csk if this changes a lot, consider looping through a dict of criteria instead
    if not override:
        if get_metadata_for_flywheel_file(image_file, ['modality']) != 'CT':
            log.error(f'File {image_file_name} is not "CT"!')
            exit()
        if get_metadata_for_flywheel_file(image_file, ['classification', 'Scan Orientation']) != 'Axial':
            log.error(f'File {image_file_name} is not Axial"!')
            exit()
        if get_metadata_for_flywheel_file(image_file, ['info', 'header', 'dicom', 'SliceThickness']) > 10:
            log.error(f'File {image_file_name} slice_thickness is > 10 (mm)!')
            exit()
        if len(get_metadata_for_flywheel_file(image_file, ['zip_member_count'])) < 10:
            log.error(f'File {image_file_name} has less than 10 slices!')
            exit()

    else:
        log.info("The following image filers were ignored:")
        log.info("   - Modality is CT")
        log.info("   - Orientation is Axial")
        log.info("   - Slice thickness < 10 (mm)")
        log.info("   - SliceCount is > 10")

    # make DICOMIn folder and fill with dcm slices from the file
    os.mkdir('/DICOMIn')
    zip_path = f'/DICOMIn/{image_file_name}'
    acquisition.download_file(image_file_name, zip_path)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall('/DICOMIn')
    os.remove(zip_path)

    # add environment variable for base filename to use
    base_filename = f"{project.label}_{subject.label}_{session.label}".replace(' ', '_')
    os.environ["FILENAME"] = base_filename
    base_output_path = f'/OutputResults/{base_filename}/output'

    # run the command and wait for it to finish
    command_text = "/RUN_OSCAR_TOOLS.sh"
    p = subprocess.Popen(command_text, text=True, close_fds=True)
    exit_code = p.wait()

    if exit_code != 0:
        log.error(f"run_oscar_tools exited with code {exit_code}")

    # save Results.json as custom info to the acquisition
    # 2025-07 csk have to do this silly reload when using info
    acquisition = acquisition.reload()
    info = acquisition.info
    results_json_path = glob.glob(f'{base_output_path}/{base_filename}Results.json')[0]
    with open(results_json_path) as j:
        oscar_toolkit = json.load(j)
    info['oscar_toolkit'] = oscar_toolkit
    acquisition.update_info(info)

    # save resampled dicoms to acquisition file
    resampled_dicom_zip_path = f'{context.output_dir}/{image_file_name.replace(" ", "_")}_resampled.dicom.zip'
    with zipfile.ZipFile(resampled_dicom_zip_path, 'w') as zipf:
        for resampled_dicom_path in glob.glob(f'{base_output_path}/dicomoriginal/*'):
            zipf.write(resampled_dicom_path, f'/{os.path.basename(resampled_dicom_path)}')

    # save other dcm files to acquisition
    # TODO: 2025-07 csk make new acquisition here if necessary
    for segment_dcm_path in glob.glob(f'/{base_output_path}/*.dcm'):
        acquisition.upload_file(segment_dcm_path)

    # save other nii and jpg files to the gear's analysis (via copy to output_dir)
    for output_nii_path in glob.glob(f'{base_output_path}/*.nii.gz'):
        shutil.copy(output_nii_path, f'{context.output_dir}/{os.path.basename(output_nii_path)}')

    for output_jpg_path in glob.glob(f'{base_output_path}/*.jpg'):
        shutil.copy(output_jpg_path, f'{context.output_dir}/{os.path.basename(output_jpg_path)}')

    log.info("run_oscar_gear ran successfully!")


if __name__ == "__main__":
    run_oscar_tools(GearToolkitContext())
