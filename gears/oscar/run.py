#!/usr/bin/env python
import shutil

from flywheel_gear_toolkit import GearToolkitContext

import glob
import json
import subprocess
import os
import zipfile

# This is the run.py code to run and parse an OSCAR analysis from a Flywheel gear.
# This gear will be run on an acquisition that contains at least one dicom series.
# Outputs will go to that acquisition, and to an analysis connected to the gear run.

# change log:
# 2026-07 csk    initial gear 0.9.0
# 2026-07 csk    update "gear output files" (cannot use upload_file on flywheel gear analysis container!)

# get the analysis container object from the gear context
gear_context = GearToolkitContext()
fw_client = gear_context.client
analysis_from = fw_client.get(gear_context.destination["id"])

# get the parents of this analysis to build the script
# group_id = analysis_from.parents["group"]
project = fw_client.get_project(analysis_from.parents["project"])
subject = fw_client.get(analysis_from.parents["subject"])
session = fw_client.get(analysis_from.parents["session"])
acquisition = session.acquisitions()[0]
file = acquisition.files[0]

# make DICOMIn folder and fill with dcm slices from the file
os.mkdir('/DICOMIn')
zip_path = f'/DICOMIn/{file.name}'
acquisition.download_file(file.name, zip_path)

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
resampled_dicom_zip_path = f'{gear_context.output_dir}/{file.name.replace(" ", "_")}_resampled.dicom.zip'
with zipfile.ZipFile(resampled_dicom_zip_path, 'w') as zip:
    for resampled_dicom_path in glob.glob(f'{base_output_path}/dicomoriginal/*'):
        zip.write(resampled_dicom_path, f'/{os.path.basename(resampled_dicom_path)}')

# save other dcm files to acquisition
# TODO: 2025-07 csk make new acquisition here if necessary
for segment_dcm_path in glob.glob(f'/{base_output_path}/*.dcm'):
    acquisition.upload_file(segment_dcm_path)

# save other nii and jpg files to the gear's analysis (via copy to output_dir)
for output_nii_path in glob.glob(f'{base_output_path}/*.nii.gz'):
    shutil.copy(output_nii_path, f'{gear_context.output_dir}/{os.path.basename(output_nii_path)}')

for output_jpg_path in glob.glob(f'{base_output_path}/*.jpg'):
    shutil.copy(output_jpg_path, f'{gear_context.output_dir}/{os.path.basename(output_jpg_path)}')
