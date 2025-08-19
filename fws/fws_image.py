import glob
import os
import tempfile
from enum import Enum
from zipfile import ZipFile
import SimpleITK as sitk
import flywheel
import pydicom
import dicom2nifti
from flywheel import ApiException
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
    tif = 5

class FWSLevel(Enum):
    group = 0
    project = 1
    subject = 2
    session = 3
    acquisition = 4
    file_name = 5

class FWSImageFile:
    levels = [FWSLevel.group, FWSLevel.project, FWSLevel.subject, FWSLevel.session, FWSLevel.acquisition, FWSLevel.file_name]
    # define valid image type file extensions
    dicom_file_types = ['.dcm', '.zip']
    image_file_types = ['.nii.gz', '.nrrd', '.jpg', '.jpeg', '.tif', '.png', '.pdf']
    image_file_types.extend(dicom_file_types)


    def __init__(self, fw_client=None, fw_path=None, local_path=None):
        self.fw_client = fw_client

        self.fw_path = fw_path
        self.local_path = local_path

        # 202503 csk make this on demand when we need it!
        # self.usable_paths = self.generate_usable_paths()
        self.usable_paths = None

        self.image_store = None


    def file_name(self):
        if self.fw_client is not None:
            return self.fw_path.split('/')[-1]
        else:
            return self.local_path.split('/')[-1]

    @staticmethod
    def separate_flywheel_components(fw_path):
        components = fw_path.split('/')
        group = components[0] if len(components) > 0 else None
        project = components[1] if len(components) > 1 else None
        subject = components[2] if len(components) > 2 else None
        session = components[3] if len(components) > 3 else None
        acquisition = components[4] if len(components) > 4 else None
        file_name = components[5] if len(components) > 5 else None
        return group, project, subject, session, acquisition, file_name


    @staticmethod
    def replace_flywheel_components(fw_path, project=None, subject=None, session=None, acquisition=None, file_name=None):
        components = FWSImageFile.separate_flywheel_components(fw_path)
        group = components[0]
        project = components[1] if project is None else project
        subject = components[2] if subject is None else subject
        session = components[3] if session is None else session
        acquisition = components[4] if acquisition is None else acquisition
        file_name = components[5] if file_name is None else file_name

        new_fw_path = f'{group}/{project}/{subject}/{session}/{acquisition}/{file_name}'.replace('//', '/')
        if new_fw_path.endswith('/'):
            new_fw_path = new_fw_path[:-1]

        return new_fw_path

    def resolve(self, level, label_if_not_found = None):
        # truncate path
        fw_path = self.fw_path
        for l in range(5, level.value, -1):
            fw_path = fw_path.rsplit('/', 1)[0]

        try:
            obj = self.fw_client.resolve(fw_path)['path'][level.value]
            return obj
        except (ApiException, flywheel.rest.ApiException, IndexError) as e:
            if label_if_not_found is None:
                return None
            # TODO: 202504 csk better way to handle this? recursion to add multiple levels??
            parent_path = fw_path.rsplit('/', 1)[0]
            parent_obj = self.fw_client.resolve(parent_path)['path'][-1]
            obj = None
            if level == FWSLevel.project:
                obj = parent_obj.add_project(label=label_if_not_found)
            if level == FWSLevel.subject:
                obj = parent_obj.add_subject(label=label_if_not_found)
            if level == FWSLevel.session:
                obj = parent_obj.add_session(label=label_if_not_found)
            if level == FWSLevel.acquisition:
                obj = parent_obj.add_acquisition(label=label_if_not_found)

            self.fw_path = f'{parent_path}/{label_if_not_found}'
            return obj

        return None

    def load_image(self, image_type: FWSImageType = FWSImageType.sitk, force_reload=False):
        image = None

        # 202503 csk made this on demand
        if self.usable_paths is None:
            self.usable_paths = self.generate_usable_paths()

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
            nifti_path = f'{tempfile.mkdtemp()}{os.path.sep}file.nii.gz'
            self.image_store = dicom2nifti.dicom_series_to_nifti(series_path, nifti_path, reorient_nifti=True)

        elif image_type == FWSImageType.tif:
            self.image_store = sitk.ReadImage(self.usable_paths[0])

        if self.image_store is None:
            raise FWSImageFileLoadxception

        return self.image_store


    def save_image(self, type: FWSImageType = FWSImageType.nii, force_local_path = None ):
        # TODO: 202503 csk this code needs some work? add support for multiple series, easier handling for
        # flywheel vs local saving, add more options, clean up temp dirs!
        # make it easier and more intuitive for everyone to use!

        # 202503 csk made this on demand
        if self.usable_paths is None:
            self.usable_paths = self.generate_usable_paths()

        # make sure (local) usable paths is set
        if len(self.usable_paths) == 0:
            self.usable_paths = self.generate_usable_paths()

        # root output file path: use force_local_path, or find a temp place for it before pushing to flywheel
        local_path = force_local_path
        if local_path is None:
            tmp_dir = tempfile.mkdtemp()
            local_path = f'{tmp_dir}{os.path.sep}{self.file_name()}'

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
            # make sure acquisition exists
            _, _, _, _, ack_label, _ = self.separate_flywheel_components(self.fw_path)
            ack = self.resolve(FWSLevel.acquisition, label_if_not_found=ack_label)

            # save file to it
            ack.upload_file(local_path)


    def generate_usable_paths(self):
        if self.fw_client is not None:
            usable_paths = FWSImageFile.get_paths_from_flywheel(self.fw_client, self.fw_path)
        else:
            if self.local_path is None:
                raise FWSImageFileLocalException
            usable_paths = FWSImageFile.get_paths_from_local(self.local_path)

        if len(usable_paths) == 0:
            raise FWSImageFileLocalException("usable_files path is empty!")

        for usable_path in usable_paths:
            if not FWSImageFile.fws_is_image_file(usable_path):
                raise FWSImageFileLocalException("usable_files path has no image file types!")

        if len(usable_paths) > 1 and usable_paths[0].endswith('.dcm'):
            # make sure these are sorted by z position fo correct reconstructuin!
            # do it now so we don't have to think about it later
            z_positions = []
            for usable_path in usable_paths:
                dcm = pydicom.dcmread(usable_path, stop_before_pixels=True)
                z_positions.append(dcm.ImagePositionPatient[2])
            usable_paths = [x for _, x in sorted(zip(z_positions, usable_paths), key=lambda pair: pair[0])]

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
        tmp_dir = tempfile.mkdtemp()
        tmp_path = f'{tmp_dir}{os.path.sep}{image_name}'
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

            # TODO 202503 csk look into this: sometimes unzips with extract name, sometimes does not.
            # does this come from the existing zip file archname???
            # paths = glob.glob(f'{zip_dir}/{extract_name}/*.dcm')
            paths = glob.glob(f'{zip_dir}{os.path.sep}*.dcm')
            return paths

        elif FWSImageFile.fws_is_image_file(local_path):
            return [local_path]
        else:
            return glob.glob(f'{local_path}{os.path.sep}*')

    def convert_image_to_dicom(self):
        if self.local_path is not None:
            self.local_path = f'{os.path.splitext(self.local_path)[0]}.dcm'
        else:
            self.local_path = f'{tempfile.mkdtemp()}{os.path.sep}{os.path.splitext(self.file_name())[0]}.dcm'
        sitk.WriteImage(self.image_store, self.local_path)
        self.image_store = sitk.ReadImage(self.local_path)

        return self.image_store

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
"""
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
                local_subject = file.local_path.split('/')[-3]

            fw_subject = ''
            if file.fw_path is not None:
                fw_subject = file.fw_path.split('/')[-4]
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

if __name__ == "__main__":
    pass
