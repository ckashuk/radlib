import os
import glob
import shutil
import tempfile
import time
from enum import Enum
from threading import Thread
from zipfile import ZipFile

import flywheel
import pydicom
import re
import dicom2nifti
import subprocess

from radlib.fw.flywheel_clients import uwhealthaz_client

class DicomSorter:
    # example "sort structure" uses pydicom tag names to produce a folder path to sort images
    # can also use raw text in these fields, each will become a subfolder
    default_radsurv_sort_structure = [
        '{AccessionNumber}',
        '{StudyDate}',
        '{SeriesDescription}'
    ]

    # example filter to "clean" dicom names for filenames
    path_character_filter = [
        ['*', 'star'],
        ['+', '']
    ]

    # example filter for which dicoms are converted to nii. taken from RRS_RadSurv/preprocessing/Select4Modalities/copy_subject)_
    default_radsurv_filter = [
        ['t1', 'ax'], ['gd', 'axial'], ['t1', 'sag'], ['t1', 'mpr'],
        ['t1', 'tra'], ['t1', '3d'], ['+c', 'ax'], ['flair'], ['t2'],
        ['fse'], ['se'], ['bravo'], ['mprage'], ['fspgr']
    ]

    default_radsurv_sorted_folder_name = 'dicom_structuralMRI'
    default_radsurv_converted_folder_name = 'nifti_raw'

    def __init__(self, input_folder, sorted_folder='None', converted_folder='None', sort_structure=None,
                 filename_filter=None, continuous=False,
                 sorted_folder_name=None, converted_folder_name=None,
                 send_to_flywheel=True,
                 delete_input_files=True
                 ):

        # these can be overridden
        self.sorted_folder_name =  DicomSorter.default_radsurv_sorted_folder_name if sorted_folder_name is None else sorted_folder_name
        self.converted_folder_name = DicomSorter.default_radsurv_converted_folder_name if converted_folder_name is None else converted_folder_name

        self.input_folder = input_folder
        self.scratch_folder = tempfile.TemporaryDirectory()

        # make stage folders if not provided
        self.sorted_folder = f'{self.scratch_folder}/{self.sorted_folder_name}' if sorted_folder is None else sorted_folder
        self.converted_folder = f'{self.scratch_folder}/{self.converted_folder_name}' if converted_folder is None else converted_folder

        # define sort structure
        # TODO: 202505 csk add local variables or passed in parameters?
        self.sort_structure = DicomSorter.default_radsurv_sort_structure if sort_structure is None else sort_structure

        # defile filename filter
        # TODO: 202505 csk add local variables or passed in parameters?
        self.filename_filter = DicomSorter.default_radsurv_filter if filename_filter is None else filename_filter

        # list of intermediate files that have not be able to be deleted yet
        files_to_delete = []

        # pass in False to run once, or True for continuous use. Set to False for "manuaL" off
        self.active = continuous

        # other flags
        self.send_to_flywheel = send_to_flywheel
        self.delete_input_files = delete_input_files

        # start process
        # self.run_process = Thread(target=self.run)
        # self.run_process.start()


    @staticmethod
    def clean_dir(path):
        # clean up "bad" path characters
        for old, new in DicomSorter.path_character_filter:
            path = path.replace(old, new)
        return path

    def get_sort_dir(self, meta):
        sort_dir = ''
        for item in self.sort_structure:
            while '{' in item:
                meta_item = re.search(r"{([A-Za-z0-9_]+)}", item).group(1)
                meta_item = '{' + meta_item + '}'
                value = meta.get(meta_item.replace('{', '').replace('}', ''))
                item = item.replace(meta_item, value)
            sort_dir = f'{sort_dir}/{item}'
        return DicomSorter.clean_dir(sort_dir)

    @staticmethod
    def get_unique_sorted_paths(sorted_folder):
        old_paths = [os.path.dirname(p) for p in DicomSorter.find_dcm_in_folder(sorted_folder)]
        new_paths = []

        for old_path in old_paths:
            if old_path not in new_paths:
                new_paths.append(old_path)

        return new_paths

    def get_sorted_dir(self):
        # get every .dcm in the output dir
        dcm_output_list = DicomSorter.find_dcm_in_folder(self.output_folder)

    def sort_one_dcm(self, dcm_path, allow_duplicates=False):
        # get metadata
        meta = pydicom.dcmread(dcm_path, stop_before_pixels=True)
        sort_dir =self.get_sort_dir(meta)
        sort_path = f'{self.sorted_folder}/{sort_dir}/{os.path.basename(dcm_path)}'
        if os.path.exists(sort_path) and not allow_duplicates:
            return
        os.makedirs(os.path.dirname(sort_path), exist_ok=True)

        if self.delete_input_files:
            shutil.move(dcm_path, sort_path)
        else:
            shutil.copy(dcm_path, sort_path)


    def run(self):
        while True:
            self.sort()
            self.convert()
            if self.send_to_flywheel:
                self.move()
            time.sleep(2)
            for file_to_delete in self.files_to_delete:
                try:
                    os.remove(file_to_delete)
                    self.files_to_delete.remove(file_to_delete)

                except Exception as e:
                    time.sleep(2)

            if not self.active:
                self.run_process.stop()

    def start(self):
        # start process
        self.run_process = Thread(target=self.run)
        self.run_process.start()

    def stop(self):
        self.active = False

    def sort(self):
        try:
            sort_paths = DicomSorter.find_dicom_in_folder(self.input_folder)
            if len(sort_paths) == 0:
                return
            for sort_path in sort_paths:
                print("sorting", sort_path)
                if sort_path.endswith('dicom.zip'):
                    # path is a zip
                    temp_dir = tempfile.TemporaryDirectory()
                    with ZipFile(sort_path) as zip_file:
                        zip_file.extractall(temp_dir.name)
                        dcm_paths = DicomSorter.find_dcm_in_folder(temp_dir.name)
                        for tmp_path in dcm_paths:
                            self.sort_one_dcm(tmp_path)
                    os.remove(sort_path)
                else:
                    # path is the file
                    self.sort_one_dcm(sort_path)

        except Exception as e:
            print("sort", e)
            time.sleep(2)


    def convert(self):
        # get sorted folders
        try:
            convert_paths = self.get_unique_sorted_paths(self.sorted_folder)
            if len(convert_paths) == 0:
                return

            for convert_path in convert_paths:
                print("filter", self.filter(convert_path), convert_path)
                if self.filter(convert_path):
                    print("converting", convert_path)
                    nii_path = f'{convert_path.replace(" ", "_")}.nii.gz'
                    nii_path = nii_path.replace(self.sorted_folder, self.converted_folder)
                    os.makedirs(os.path.dirname(nii_path), exist_ok=True)
                    dicom2nifti.dicom_series_to_nifti(convert_path, nii_path, reorient_nifti=True)

        except Exception as e:
            print("convert", e)
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

    def move(self):
        fw_client = uwhealthaz_client()

        try:
            dicom_paths = DicomSorter.get_unique_sorted_paths(self.sorted_folder)
            nii_paths = DicomSorter.find_nii_in_folder(self.converted_folder)
            if len(dicom_paths) == 0 and len(nii_paths) == 0:
                return
            group = 'brucegroup'
            project = 'GBM Cohort new'
            if len(dicom_paths) > 0:
                subject = dicom_paths[0].split(os.path.sep)[-3]
                session = dicom_paths[0].split(os.path.sep)[-2]
            else:
                subject = nii_paths[0].split(os.path.sep)[-3]
                session = nii_paths[0].split(os.path.sep)[-2]

            # dicoms
            acquisition = get_fw_acquisition(fw_client, group, project, subject, session, 'dicom_raw')
            for dicom_path in dicom_paths:
                print("moving", dicom_path)
                # make zip file
                zip_path = f'{dicom_path.replace(" ", "_")}.dicom.zip'
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                with ZipFile(zip_path, mode='x') as zip_file:
                    for usable_path in glob.glob(f'{dicom_path}/*.dcm'):
                        zip_file.write(usable_path, arcname=os.path.basename(usable_path))
                zip_file.close()
                acquisition.upload_file(zip_path)
                shutil.rmtree(dicom_path)
                try:
                    os.remove(zip_path)
                except Exception as e:
                    self.files_to_delete.append(zip_path)

            # niftis
            acquisition = get_fw_acquisition(fw_client, group, project, subject, session, 'nifti_raw')
            for nii_path in nii_paths:
                print("moving", nii_path)
                acquisition.upload_file(nii_path)
                try:
                    os.remove(nii_path)
                except Exception as e:
                    self.files_to_delete.append(nii_path)

        except Exception as e:
            print("move", e)
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


if __name__ == "__main__":
    input_folder = 'z:/temp/temp_in'
    sorted_folder = 'z:/temp/temp_sorted'
    converted_folder = 'z:/temp/temp_converted'

    # dicoms
    sorter = DicomSorter(input_folder, sorted_folder, converted_folder)
    sorter.active = True

    # sorter.sort()
    # sorter.convert()
    # sorter.move()

    while True:
        # print("outside")
        time.sleep(2)



