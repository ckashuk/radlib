import glob
import os
import tempfile
from enum import Enum
from zipfile import ZipFile
import SimpleITK as sitk
import pydicom
import dicom2nifti
from zipp.glob import separate


# from radlib.fw.flywheel_data import load_image_from_flywheel, load_image_from_local_path


class FWSImageFileLoadxception(Exception):
    pass

class FWSImageFileFlywheelException(Exception):
    pass

class FWSImageFileLocalException(Exception):
    pass

class FWSImageType(Enum):
    pydicom = 1
    nii = 2
    nrrd = 3
    sitk = 4


class FWSImageFile:

    # define valid image type file extensions
    dicom_file_types = ['.dcm', '.zip']
    image_file_types = ['.nii.gz', '.nrrd', '.jpg', '.jpeg', '.png', '.pdf']
    image_file_types.extend(dicom_file_types)


    def __init__(self, fw_client=None, fw_path=None, local_path=None):
        # TODO: 202503 csk find better way for load/save than "usable" flag
        self.fw_client = fw_client

        self.fw_path = fw_path
        self.local_path = local_path

        self.usable_paths = self.generate_usable_paths()

        self.image_store = None


    def file_name(self):
        if self.fw_client is not None:
            return self.fw_path.split('/')[-1]
        else:
            return self.local_path.split('/')[-1]

    @staticmethod
    def separate_flywheel_components(fw_path):
        components = fw_path.split('/')

        return components[0], components[1], components[2], components[3], components[4], components[5]


    @staticmethod
    def replace_flywheel_components(fw_path, project=None, subject=None, session=None, acquisition=None, file_name=None):
        components = FWSImageFile.separate_flywheel_components(fw_path)
        group = components[0]
        project = components[1] if project is None else project
        subject = components[2] if subject is None else subject
        session = components[3] if session is None else session
        acquisition = components[4] if acquisition is None else acquisition
        file_name = components[5] if file_name is None else file_name

        return f'{group}/{project}/{subject}/{session}/{acquisition}/{file_name}'


    def load_image(self, image_type: FWSImageType = FWSImageType.sitk, force_reload=False):
        image = None

        # print(f"load_image {image_type} {force_reload} {self.image_store is None} {len(self.usable_paths)}")
        if not force_reload and self.image_store is not None:
            return self.image_store

        if image_type == FWSImageType.sitk:
            # TODO: 202503 csk something better than hiding the warning when there are missing slices?
            sitk.ProcessObject_SetGlobalWarningDisplay(False)
            self.image_store = sitk.ReadImage(self.usable_paths)
            sitk.ProcessObject_SetGlobalWarningDisplay(True)

        elif image_type == FWSImageType.pydicom:
            image = []
            for path in self.usable_paths:
                image.append(pydicom.dcmread(path))
            self.image_store = image

        elif image_type == FWSImageType.nii:
            series_path = os.path.dirname(self.usable_paths[0])
            nifti_path = f'{tempfile.TemporaryDirectory.name}/file.nii.gz'
            self.image_store = dicom2nifti.dicom_series_to_nifti(series_path, nifti_path, reorient_nifti=True)

        if self.image_store is None:
            raise FWSImageFileLoadxception

        return self.image_store


    def save_image(self, type: FWSImageType = FWSImageType.nii, force_local_path = None ):
        # TODO: 202503 csk this code needs some work? add support for multiple series, easier handling for
        # flywheel vs local saving, add more options, clean up temp dirs!
        # make it easier and more intuitive for everyone to use!

        # make sure (local) usable paths is set
        if len(self.usable_paths) == 0:
            self.usable_paths = self.generate_usable_paths()

        # root output file path: use force_local_path, or find a temp place for it before pushing to flywheel
        local_path = force_local_path
        if local_path is None:
            tmp_dir = tempfile.mkdtemp()
            local_path = f'{tmp_dir}/{self.file_name()}'

        if type is FWSImageType.pydicom:
            # save to zip archive
            if not local_path.endswith('.zip'):
                local_path = f'{local_path}.zip'

            with ZipFile(local_path, mode='x') as zip_file:
                for usable_path in self.usable_paths:
                    zip_file.write(usable_path, arcname=os.path.basename(usable_path))

        if type is FWSImageType.nii:
            # save to nii file
            if not local_path.endswith('.nii.gz'):
                local_path = f'{local_path}.nii.gz'
            dicom2nifti.dicom_series_to_nifti(os.path.dirname(self.usable_paths[0]), local_path)

        # upload to flywheel
        if force_local_path is None and self.fw_client is not None:
            # file may not exist yet, so remove file designation from path to find acquisition
            fw_acquisition_path = self.fw_path.rsplit('/', 1)[0]
            fw = self.fw_client.resolve(fw_acquisition_path)
            ack = fw['path'][-1]
            ack.upload_file(local_path)


    def generate_usable_paths(self):
        usable_paths = []
        if self.fw_client is not None:
            usable_paths = FWSImageFile.get_paths_from_flywheel(self.fw_client, self.fw_path)
            print(len(usable_paths))

        else:
            if self.local_path is None:
                raise FWSImageFileLocalException
            usable_paths = FWSImageFile.get_paths_from_local(self.local_path)

        if len(usable_paths) == 0:
            raise FWSImageFileLocalException("usable_files path is empty!")

        for usable_path in usable_paths:
            if not FWSImageFile.fws_is_image_file(usable_path):
                raise FWSImageFileLocalException("usable_files path has no image file types!")

        return usable_paths

    @staticmethod
    def fws_is_file_type(path:str, file_types: list):
        for file_type in file_types:
            if path.endswith(file_type):
                return True
        return False

    @staticmethod
    def fws_is_image_file(path:str):
        # TODO: 202503 csk add more filetypes
        return FWSImageFile.fws_is_file_type(path, FWSImageFile.image_file_types)


    @staticmethod
    def fws_is_dcm_file(path:str):
        return FWSImageFile.fws_is_file_type(path, FWSImageFile.dicom_file_types)



    @staticmethod
    def get_paths_from_flywheel(fw_client, fw_path):
        # given the "address" to an image, download the file to a temp dir and get individual slice paths for later loading

        image_name = fw_path.split('/')[-1]
        fw_path = fw_path.rsplit('/', 1)[0]

        # get acquisition
        ack = fw_client.resolve(f'{fw_path}').path[-1]

        # download image from fw to temp folder
        tmp_dir = tempfile.mkdtemp()  #   TemporaryDirectory()
        tmp_path = f'{tmp_dir}/{image_name}'
        ack.download_file(image_name, tmp_path)
        paths = FWSImageFile.get_paths_from_local(tmp_path)
        return paths


    @staticmethod
    def get_paths_from_local(local_path):
        # given the path to a file, whether "real" or "temp", get the list of paths to slices included in it
        zip_dir = tempfile.mkdtemp()
        extract_name = os.path.basename(local_path).replace('.zip', '')
        # print("get_paths_from_local", local_path, zip_dir)
        if local_path.endswith('.zip'):
            # save slices to a temp directory
            with ZipFile(local_path) as zip_file:
                zip_file.extractall(zip_dir)
                # print(f"extracted {local_path} to {zip_dir}")

            paths = glob.glob(f'{zip_dir}/{extract_name}/*.dcm')
            return paths

        elif local_path.endswith('.dcm') or local_path.endswith('.nrrd') or local_path.endswith('.nii.gz'):
            return [local_path]
        else:
            return glob.glob(f'{local_path}/*')

"""
def load_image_from_flywheel(self):
    # given the "address" to an image, download the file to a temp dir and load it as an sitk Image

    image_name = self.fw_path.split('/')[-1]
    fw_path = fw_path.rsplit('/', 1)[0]

    # get acquisition
    ack = fw_client.resolve(f'{fw_path}').path[-1]

    # download image from fw to temp folder
    tmp_dir = tempfile.gettempdir()
    tmp_path = f'{tmp_dir}/{image_name}'

    ack.download_file(image_name, tmp_path)

    return load_image_from_local_path(tmp_path, tmp_dir)


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

class FWSImageFileList(dict):
    def __init__(self, files = None):
        super().__init__()
        if files is not None:
            for file_name, file_data in files.items():
                self[file_name] = file_data

    def get_subject_list(self):
        subject_list = []

        for file in self.values():
            local_subject = ''
            if file.local_path is not None:
                local_subject = file.local_path.split('/')[-3]

            fw_subject = ''
            if file.fw_path is not None:
                fw_subject = file.fw_path.split('/')[-3]
            subject = local_subject
            if len(subject)==0:
                subject = fw_subject
            elif subject != fw_subject:
                subject = f'{subject}|{fw_subject}'

            if subject not in subject_list:
                subject_list.append(subject)
        return subject_list

    def get_session_list(self, sorted=False):
        session_list = []

        for file in self.values():
            local_subject = ''
            if file.local_path is not None:
                local_subject = file.local_path.split('/')[-1]

            fw_subject = ''
            if file.fw_path is not None:
                fw_subject = file.fw_path.split('/')[-2]
            subject = local_subject
            if len(subject) == 0:
                subject = fw_subject
            elif subject != fw_subject:
                subject = f'{subject}|{fw_subject}'

            if subject not in session_list:
                session_list.append(subject)

        if sorted:
            session_list.sort()

        return session_list

    def get_list_for_session(self, session_label):
        new_list = FWSImageFileList()
        for file_name, file_data in self.items():
            if session_label in file_data.fw_path:
                new_list[file_name] = file_data
        return new_list
"""

if __name__ == "__main__":
    pass
