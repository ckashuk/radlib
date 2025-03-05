import glob
import tempfile
from zipfile import ZipFile
import SimpleITK as sitk

# TODO: 2025-03 csk cache labels so we don't need to pass all of them for each of these functions

def load_dicom_zip_from_flywheel(fw_client, group_label, project_label, subject_label, series_label, ack_label, file_name):
    # given an acquisition, take the first file (zip) and turn it into a list of sitk.Image slices
    # TODO: update for multi-file acquisitions

    # get acquisition
    ack = fw_client.resolve(f'{group_label}/{project_label}/{subject_label}/{series_label}/{ack_label}').path[-1]

    # download the zip file
    zipdir = tempfile.gettempdir()
    zip_path = f'{zipdir}/{file_name}'
    ack.download_file(file_name, zip_path)

    # pull slice files from the zip and save them
    slices = []
    with ZipFile(zip_path) as zip_file:
        zipdir = tempfile.TemporaryDirectory()
        with zipdir as tempdir:
            zip_file.extractall(tempdir)
            dcm_paths = glob.glob(f'{tempdir}/*.dcm')
            for dcm_path in dcm_paths:
                slices.append(sitk.ReadImage(dcm_path))
    return slices


def load_image_from_flywheel(fw_client, group_label, project_label, subject_label, series_label, ack_label, image_name):
    # given an acquisition, take the first file (non-zip) and turn it into a list of sitk.Image slices
    # TODO: update for multi-file acquisitions
    # TODO: combine zip and non-zip forms!

    # get acquisition
    ack = fw_client.resolve(f'{group_label}/{project_label}/{subject_label}/{series_label}/{ack_label}').path[-1]

    # download image from flywheel to temp folder
    imgdir = tempfile.gettempdir()
    img_path = f'{imgdir}/{image_name}'
    ack.download_file(image_name, img_path)

    # use simpleitk to convert to dicom
    # TODO: is there a better way?
    tmp = sitk.ReadImage(img_path)
    img_path = f"{img_path}.dcm"
    sitk.WriteImage(tmp, img_path)

    return sitk.ReadImage(img_path)
