import glob
import os
import tempfile
from zipfile import ZipFile
import SimpleITK as sitk
import numpy as np
import pydicom

from radlib.dcm.converters import pet_suv_factor
from radlib.projects.spore_17009_set import get_pathology_images


def load_image_from_flywheel(fw_client, fw_path, keep_slices=False):
    # given the "address" to an image, download the file to a temp dir and load it as an sitk Image

    image_name = fw_path.split('/')[-1]
    fw_path = fw_path.rsplit('/', 1)[0]

    # get acquisition
    ack = fw_client.resolve(f'{fw_path}').path[-1]

    # download image from fw to temp folder
    tmp_dir = tempfile.gettempdir()
    tmp_path = f'{tmp_dir}/{image_name}'

    ack.download_file(image_name, tmp_path)

    return load_image_from_local_path(tmp_path, tmp_dir, keep_slices)


def load_image_from_local_path(local_path, local_dir=None, separate_series=False, keep_slices=False):
    # given the path to a file, load it via sitk/pydicom
    series_ids = {}
    series_slices = {}
    if local_dir is None:
        local_dir = f'{tempfile.TemporaryDirectory().name}/{os.path.basename(local_path).replace(".zip", "")}'

    if local_path.endswith('.zip'):
        # save slices to a temp directory
        with ZipFile(local_path) as zip_file:
            zip_file.extractall(local_dir)
            dcm_paths = glob.glob(f'{local_dir}/*.dcm')

    # load slices
    # TODO: 202503 csk have to use pydicom/simpleitk mixture because simpleitk can't
    # read the radiopharmaceutical tags? revisit this someday
    for dcm_path in dcm_paths:
        dcm = pydicom.dcmread(dcm_path)

        # save indexed file names by series uid
        series_file_name = series_ids.get(dcm.SeriesInstanceUID)
        if series_file_name is None:
            index = 1
            while series_file_name is None or series_file_name in series_ids.values():
                series_file_name = f'{os.path.basename(local_path).split(".")[0]}_{index}'
                index += 1
            series_ids[dcm.SeriesInstanceUID] = series_file_name
        # add slice to current series uid
        slices = series_slices.get(series_file_name, [])
        slices.append(dcm)
        series_slices[series_file_name] = slices

    # for each series id in the folder
    series = {}
    series_slice_origins = {}
    for series_file_name, slices in series_slices.items():
        # sort slices
        slices = sorted(slices, key=lambda s: s.ImagePositionPatient[2])
        series_slices[series_file_name] = slices

        # create 3D array
        img_shape = list(slices[0].pixel_array.shape)
        img_shape.append(len(slices))
        img3d = np.zeros(img_shape)

        # fill 3D array with the images from the files
        # keep track of slice origins for later
        slice_origins = []
        for i, s in enumerate(slices):
            slice_origins.append(s.ImagePositionPatient)
            img2d = s.pixel_array

            # add slope/intercept handling
            if s.get('RescaleSlope') is not None:
                img2d = np.add(np.multiply(img2d, s.RescaleSlope), s.RescaleIntercept)

            # add SUV
            if s.Modality == 'PT':
                suv_factor = pet_suv_factor(s)
                img2d = np.multiply(img2d, suv_factor)

            # TODO: 202503 csk better way to handle this? color vs monochrome image data
            if len(img3d.shape)==4:
                img3d[:, :, :, i] = img2d
            else:
                img3d[:, :, i] = img2d

        # TODO: 202503 csk too much effort trying to keep mult-series dicom outputs, find a better way to deal with it!
        if keep_slices:
            if separate_series:
                return series_slices, series_slice_origins
            else:
                return list(series_slices.values())[0], series_slice_origins

        # cheat to ignore complex math to get sitk spacing and direction from dicoms!
        sitk0 = sitk.ReadImage([dcm_paths[0], dcm_paths[1]])

        # new sitk Image
        sitk_image = sitk.GetImageFromArray(img3d)
        sitk_image.SetOrigin(slice_origins[0])
        sitk_image.SetSpacing(sitk0.GetSpacing())
        sitk_image.SetDirection(sitk0.GetDirection())
        series[series_file_name] = sitk_image
        series_slice_origins[series_file_name] = slice_origins

    if separate_series:
        return series, series_slice_origins
    else:
        return list(series.values())[0], series_slice_origins