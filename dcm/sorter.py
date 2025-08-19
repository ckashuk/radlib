import os
import glob
import shutil
import tempfile
import time
from enum import Enum
from multiprocessing import Process
from zipfile import ZipFile

import flywheel
import pydicom
import re
import dicom2nifti
import subprocess

from dicom2nifti.exceptions import ConversionError

import sys
sys.path.append('/home/aa-cxk023/share/radlib')
from radlib.fw.flywheel_clients import uwhealthaz_client

class DicomSorter:
    # example "sort structure" uses pydicom tag names to produce a folder path to sort images
    # can also use raw text in these fields, each will become a subfolder
    default_radsurv_sort_structure = [
        '{PatientID}', # '{AccessionNumber}',
        '{StudyDate}',
        '{SeriesDescription}'
    ]

    # example filter to "clean" dicom names for filenames
    path_character_filter = [
        ['*', 'star'],
        [':', '_'],
        ['+', ''],
    ]

    # example filter to "clean" dicom names for filenames
    filename_character_filter = [
        ['*', 'star'],
        [':', '_'],
        ['+', ''],
        [os.path.sep, '_']
    ]

    # example filter for which dicoms are converted to nii. taken from RRS_RadSurv/preprocessing/Select4Modalities/copy_subject)_
    default_radsurv_filter = [
        ['t1', 'ax'], ['gd', 'axial'], ['t1', 'sag'], ['t1', 'mpr'],
        ['t1', 'tra'], ['t1', '3d'], ['+c', 'ax'], ['flair'], ['t2'],
        ['fse'], ['se'], ['bravo'], ['mprage'], ['fspgr']
    ]

    default_radsurv_sorted_folder_name = 'dicom_structuralMRI'
    default_radsurv_converted_folder_name = 'nifti_raw'

    def __init__(self, input_folder,
                 sorted_folder='None',
                 converted_folder='None',
                 sort_structure=None,
                 filename_filter=None,
                 service=False,
                 sorted_folder_name=None,
                 converted_folder_name=None,
                 send_to_flywheel=True,
                 flywheel_group=None,
                 flywheel_project=None,
                 preserve_input_files=False,
                 logger=None,
                 scratch_folder=None
                 ):

        self.logger = logger
        if self.logger is not None:
            self.logger.info(f'initializing dicom sorter')

        # these can be overridden
        self.sorted_folder_name =  DicomSorter.default_radsurv_sorted_folder_name if sorted_folder_name is None else sorted_folder_name
        self.converted_folder_name = DicomSorter.default_radsurv_converted_folder_name if converted_folder_name is None else converted_folder_name

        self.input_folder = input_folder
        self.scratch_folder = tempfile.TemporaryDirectory() if scratch_folder is None else scratch_folder

        if logger is not None:
            self.logger.info(f'input folder is {self.input_folder}')

        # make stage folders if not provided
        self.sorted_folder = f'{self.scratch_folder}/{self.sorted_folder_name}' if sorted_folder is None else sorted_folder
        self.converted_folder = f'{self.scratch_folder}/{self.converted_folder_name}' if converted_folder is None else converted_folder

        # define sort structure
        # TODO: 202505 csk add local variables or passed in parameters?
        self.sort_structure = DicomSorter.default_radsurv_sort_structure if sort_structure is None else sort_structure

        # defile filename filter
        # TODO: 202505 csk add local variables or passed in parameters?
        self.filename_filter = DicomSorter.default_radsurv_filter if filename_filter is None else filename_filter

        # lists of files so we know what's done and we don't leave extra copies around
        self.sorted_paths = []
        self.converted_paths = []
        self.moved_paths = []
        self.files_to_delete = []

        # pass in False to run once, or True for continuous use. Set to False for "manuaL" off
        self.service = service

        # other data
        self.send_to_flywheel = send_to_flywheel
        self.preserve_input_files = preserve_input_files
        self.flywheel_group = flywheel_group
        self.flywheel_project = flywheel_project

        # start process
        # self.run_process = Thread(target=self.run)
        # self.run_process.start()


    @staticmethod
    def clean_path(path):
        # clean up "bad" path characters
        for old, new in DicomSorter.path_character_filter:
            path = path.replace(old, new)
        return path

    @staticmethod
    def clean_filename(filename):
        # clean up "bad" path characters
        for old, new in DicomSorter.filename_character_filter:
            filename = filename.replace(old, new)
        return filename


    def get_sort_dir(self, meta):
        sort_dir = ''
        for item in self.sort_structure:
            while '{' in item:
                meta_item = re.search(r"{([A-Za-z0-9_]+)}", item).group(1)
                meta_item = '{' + meta_item + '}'
                value = meta.get(meta_item.replace('{', '').replace('}', ''))
                # 202505 csk have to clean the values from dicom metadata so they don't include bad characters or add path separators!
                value = self.clean_filename(value)
                item = item.replace(meta_item, value)
            sort_dir = f'{sort_dir}/{item}'

        return DicomSorter.clean_path(sort_dir)

    @staticmethod
    def get_unique_sorted_paths(sorted_folder):
        old_paths = [os.path.dirname(p) for p in DicomSorter.find_dcm_in_folder(sorted_folder)]
        new_paths = []

        for old_path in old_paths:
            if old_path not in new_paths:
                new_paths.append(old_path)

        return new_paths


    def sort_one_dcm(self, dcm_path, allow_duplicates=False):
        # TODO: 2025-06 csk temporary kludge for GBM data where two copies of each slice are
        # present, one with an integer name, one with a seriesinstanceuid (large filename)
        # print(os.path.basename(dcm_path))
        # if os.path.basename(dcm_path) > 20:
        #     print("return?")
        #     return
        # get metadata
        meta = pydicom.dcmread(dcm_path, stop_before_pixels=True)
        sort_dir = self.clean_path(self.get_sort_dir(meta))
        sort_filename = self.clean_filename(os.path.basename(dcm_path))
        sort_path = f'{self.sorted_folder}/{sort_dir}/{sort_filename}'
        if os.path.exists(sort_path) and not allow_duplicates:
            # TODO 202506 csk kludge to allow multiple images with same effective "name"
            sort_path = f'{os.path.dirname(sort_path)}A/{os.path.basename(sort_path)}'
        os.makedirs(os.path.dirname(sort_path), exist_ok=True)
        shutil.copy(dcm_path, sort_path)
        # print(f"copied {dcm_path} to {sort_path}")
        # TODO: 202506 csk fix this before enabling!
        # if self.preserve_input_files:
        #     shutil.copy(dcm_path, sort_path)
        # else:
        #     shutil.move(dcm_path, sort_path)

    def run(self):
        while True:
            if self.sort():
                # time.sleep(2)
                self.convert()
                if self.send_to_flywheel:
                    self.move(replace_dicoms=True, replace_niftis=True)
            time.sleep(2)
            # TODO: 202505 csk need to figure out difference between one-off and processor
            if not self.service:
                return

    def start(self):
        # start process
        self.run_process = Process(target=self.run)
        self.run_process.start()
        self.run_process.join()

    def stop(self):
        self.active = False

    def all_paths_done(self, path_type, path_list):
        unsorted_paths = True
        checked_paths = self.sorted_paths
        if path_type == 'converted':
            checked_paths = self.converted_paths
        if path_type == 'moved':
            checked_paths = self.moved_paths

        for path in path_list:
            if path not in checked_paths:
                unsorted_paths = False

        return unsorted_paths

    def sort(self):
        try:
            sort_paths = DicomSorter.find_dicom_in_folder(self.input_folder)
            if self.all_paths_done('sorted', sort_paths):
                if self.logger is not None:
                    self.logger.info(f'no files found to sort')
                return False

            # self.resolve_duplicate_names(sort_paths)

            for sort_path in sort_paths:
                if sort_path in self.sorted_paths:
                    continue

                if sort_path.endswith('dicom.zip'):
                    # path is a zip
                    temp_dir = tempfile.TemporaryDirectory()
                    with ZipFile(sort_path) as zip_file:
                        zip_file.extractall(temp_dir.name)
                        dcm_paths = DicomSorter.find_dcm_in_folder(temp_dir.name)
                        for tmp_path in dcm_paths:
                            self.sort_one_dcm(tmp_path)
                else:
                    # path is the file
                    self.sort_one_dcm(sort_path)

                # TODO: 202506 csk fix this before turning back on!
                # if not self.preserve_input_files:
                #    os.remove(sort_path)

                self.sorted_paths.append(sort_path)
                if self.logger is not None:
                    self.logger.info(f'sorted {sort_path}')

        except Exception as e:
            if self.logger is not None:
                self.logger.info(f'sort exception! {e}')

            time.sleep(2)
        return True

    def convert(self):
        # get sorted folders
        try:
            convert_paths = self.get_unique_sorted_paths(self.sorted_folder)
            if self.all_paths_done('converted', convert_paths):
                return

            for convert_path in convert_paths:
                if self.logger is not None:
                    self.logger.info(f'filter {self.filter(convert_path)} {convert_path}')

                if self.filter(convert_path):
                    nii_path = f'{convert_path.replace(" ", "_")}.nii.gz'
                    nii_path = nii_path.replace(self.sorted_folder, self.converted_folder)
                    os.makedirs(os.path.dirname(nii_path), exist_ok=True)

                    try:
                        dicom2nifti.dicom_series_to_nifti(convert_path, nii_path, reorient_nifti=True)
                        # print(f"converted {convert_path} to {nii_path}")
                    except ConversionError as e:
                        if self.logger is not None:
                            self.logger.error(f'dicom2nifti ConversionError {e}, check dicom {convert_path}')

                    self.converted_paths.append(convert_path)
                    if self.logger is not None:
                        self.logger.info(f'converted {convert_path}')

        except Exception as e:
            if self.logger is not None:
                self.logger.info(f'convert exception! {e}')
            time.sleep(2)

    def filter(self, file_path):
        file_name = os.path.basename(file_path)
        for filter_item in self.filename_filter:
            passed_filter = True
            for filter_string in filter_item:
                if filter_string.lower() not in file_name.lower():
                    passed_filter = False
            if passed_filter:
                return True

        return False


    def move(self, replace_dicoms=False, replace_niftis=False):
        fw_client = uwhealthaz_client()

        try:
            dicom_paths = DicomSorter.get_unique_sorted_paths(self.sorted_folder)
            nii_paths = DicomSorter.find_nii_in_folder(self.converted_folder)

            if len(dicom_paths) == 0 and len(nii_paths) == 0:
                return
            group = self.flywheel_group
            project = self.flywheel_project

            if group is None or project is None:
                if self.logger is not None:
                    self.logger.error(f'flywheel_group and flywheel project must be defined!')
                else:
                    print(f'flywheel_group and flywheel project must be defined!')
                exit()

            if len(dicom_paths) > 0:
                subject = dicom_paths[0].split(os.path.sep)[-3]
                session = dicom_paths[0].split(os.path.sep)[-2]
            else:
                subject = nii_paths[0].split(os.path.sep)[-3]
                session = nii_paths[0].split(os.path.sep)[-2]

            # dicoms
            for dicom_path in dicom_paths:
                acquisition = get_fw_acquisition(fw_client, group, project, subject, session, os.path.basename(dicom_path).replace('.dicom.zip', '').replace(" ", '_'))

                dicom_path = os.path.normpath(dicom_path)

                # make zip file
                zip_path = f'{dicom_path.replace(" ", "_")}.dicom.zip'
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                with ZipFile(zip_path, mode='x') as zip_file:
                    for usable_path in glob.glob(f'{dicom_path}/*.dcm'):
                        zip_file.write(usable_path, arcname=os.path.basename(usable_path))
                zip_file.close()
                if replace_dicoms:
                    acquisition.upload_file(zip_path)
                    # print("upload to ", acquisition.label, zip_path)
                # shutil.rmtree(dicom_path)
                # try:
                #     os.remove(zip_path)
                # except Exception as e:
                #     self.files_to_delete.append(zip_path)

            # niftis
            for nii_path in nii_paths:
                acquisition = get_fw_acquisition(fw_client, group, project, subject, session, os.path.basename(nii_path).replace(".nii.gz", '').replace(' ', '_'))

                if replace_niftis:
                    acquisition.upload_file(nii_path)
                    print("upload to ", acquisition.label, nii_path)
                # try:
                #     os.remove(nii_path)
                # except Exception as e:
                #     self.files_to_delete.append(nii_path)

        except Exception as e:
            if self.logger is not None:
                self.logger.info(f'move exception! {e}')
            time.sleep(2)


    @staticmethod
    def find_dcm_in_folder(folder):
        # use glob ** recursive
        return glob.glob(f'{folder}/**/*.dcm', recursive=True)

    @staticmethod
    def find_zip_in_folder(folder):
        # use glob ** recursive
        return glob.glob(f'{folder}/**/*.dicom.zip', recursive=True)

    @staticmethod
    def find_nii_in_folder(folder):
        # use glob ** recursive
        return glob.glob(f'{folder}/**/*.nii.gz', recursive=True)

    @staticmethod
    def find_dicom_in_folder(folder):
        files = DicomSorter.find_dcm_in_folder(folder)
        files.extend(DicomSorter.find_zip_in_folder(folder))
        return files


def get_fw_acquisition(fw_client, group, project_label, subject_label, session_label, acquisition_label):
    try:
        project = fw_client.resolve(f'{group}/{project_label}')['path'][-1]
        subject = fw_client.resolve(f'{group}/{project_label}/{subject_label}')['path'][-1]

    except flywheel.rest.ApiException as e:
        subject = project.add_subject(label=subject_label)

    try:
        session = fw_client.resolve(f'{group}/{project_label}/{subject_label}/{session_label}')['path'][-1]

    except flywheel.rest.ApiException as e:
        session = subject.add_session(label=session_label)

    try:
        acquisition = fw_client.resolve(f'{group}/{project_label}/{subject_label}/{session_label}/{acquisition_label}')['path'][-1]

    except flywheel.rest.ApiException as e:
        acquisition = session.add_acquisition(label=acquisition_label)

    return acquisition


"""
if __name__ == "__main__":
    input_folder = 'z:/temp/temp_in'
    sorted_folder = 'z:/temp/temp_sorted'
    converted_folder = 'z:/temp/temp_converted'

    # dicoms
    sorter = DicomSorter(input_folder, sorted_folder, converted_folder,
                         preserve_input_files=True,
                         flywheel_group='idia_group',
                         flywheel_project='UPenn Cohort')
    sorter.active = True
    sorter.run()
"""


