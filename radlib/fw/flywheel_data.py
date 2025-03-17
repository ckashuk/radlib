import glob
import os
import tempfile
from zipfile import ZipFile
import SimpleITK as sitk
import numpy as np
import pydicom

from dcm.converters import pet_suv_factor


# TODO: 2025-03 csk cache labels so we don't need to pass all of them for each of these functions
def load_image_from_flywheel(fw_client, group_label, project_label, subject_label, series_label, ack_label, image_name):
    # given the "address" to an image, download the file to a temp dir and load it as an sitk Image

    # get acquisition
    ack = fw_client.resolve(f'{group_label}/{project_label}/{subject_label}/{series_label}/{ack_label}').path[-1]

    # download image from fw to temp folder
    tmp_dir = tempfile.gettempdir()
    tmp_path = f'{tmp_dir}/{image_name}'
    ack.download_file(image_name, tmp_path)

    return load_image_from_local_path(tmp_path, tmp_dir)


def load_image_from_local_path(local_path, local_dir=None):
    # given the path to a file, load it via sitk/pydicom

    if local_dir is None:
        local_dir = tempfile.TemporaryDirectory().name

    if local_path.endswith('.zip'):
        # save slices to a temp directory
        with ZipFile(local_path) as zip_file:
            zip_file.extractall(local_dir)
            local_unzipped_path = f'{local_dir}/{os.path.basename(local_path).replace(".zip", "")}'
            dcm_paths = glob.glob(f'{local_unzipped_path}/*.dcm')

            # load slices
            # TODO: 202503 csk have to use pydicom/simpleitk mixture because simpleitk can't
            # read the radiopharmaceutical tags? revisit this someday
            slices = []
            for dcm_path in dcm_paths:
                slices.append(pydicom.dcmread(dcm_path))

            # sort slices
            slices = sorted(slices, key=lambda s: s.ImagePositionPatient[2])

            # create 3D array
            img_shape = list(slices[0].pixel_array.shape)
            img_shape.append(len(slices))
            img3d = np.zeros(img_shape)

            # fill 3D array with the images from the files
            for i, s in enumerate(slices):
                img2d = s.pixel_array

                # add slope/intercept handling
                if s.get('RescaleSlope') is not None:
                    img2d = np.add(np.multiply(img2d, s.RescaleSlope), s.RescaleIntercept)

                # add SUV
                if s.Modality == 'PT':
                    suv_factor = pet_suv_factor(s)
                    img2d = np.multiply(img2d, suv_factor)

                img3d[:, :, i] = img2d

        # pixel spacing, assuming all slices are the same
        ps = slices[0].PixelSpacing
        ss = slices[1].ImagePositionPatient[2] - slices[0].ImagePositionPatient[2]
        pixel_spacing = [ps[0], ps[1], ss]

        # cheat to ignore complex math to get sitk spacing and direction from dicoms!
        sitk0 = sitk.ReadImage([dcm_paths[0], dcm_paths[1]])

        # new sitk Image
        sitk_image = sitk.GetImageFromArray(img3d)
        sitk_image.SetOrigin(slices[0].ImagePositionPatient)
        sitk_image.SetSpacing(sitk0.GetSpacing())
        sitk_image.SetDirection(sitk0.GetDirection())

        return sitk_image
    else:
        return sitk.ReadImage(local_path)
