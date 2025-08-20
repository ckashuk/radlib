import glob
import os
import shutil
import sys
import tempfile
import time
import logging
import zipfile
import pydicom

import yaml

import flywheel
from nibabel.dft import pydicom

sys.path.append('/home/aa-cxk023/share/radlib')
from radlib.dcm.sorter import DicomSorter

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)
from radlib.fw.flywheel_clients import uwhealthaz_client
from radlib.processor.processor import Processor
from radlib.fws.fws_utils import fws_is_flywheel_path, fws_has_more_scripts, fws_get_next_script, fws_resolve_object, \
    fws_expand_path, fws_add_script

from radlib.processors.rrs_radsurv_processor.processor_app import RrsRadsurvProcessor


class DicomlWatcherException(Exception):
    pass

# TODO: 202507 csk add
class DicomWatcher():
    def __init__(self, config_path, scratch_path=None):
        self.config = DicomWatcher.load_config(config_path)
        self.scratch_path = tempfile.mkdtemp() if scratch_path is None else scratch_path
        self.watch_log_path = f'{self.scratch_path}/{self.watch_name()}.log'
        self.active = True
        self.fw_client = uwhealthaz_client()

    @staticmethod
    def load_config(config_path):
        with open(config_path, 'r') as yaml_path:
            script_info = yaml.safe_load(yaml_path)
        return script_info

    def watch_name(self):
        if self.config.get('watch_name') is not None:
            return self.config.get('watch_name')
        return 'unnamed_watcher'

    def expand_dicom_paths(self, dicom_paths):
        new_paths = []
        for dicom_path in dicom_paths:
            new_paths.extend(fws_expand_path(dicom_path))
        return new_paths

    def watch(self):
        # csk need to get the logger again when run in a separate process!
        self.logger = logging.getLogger(self.watch_name())
        print(">>>>>dicom watcher logger! named ", self.watch_name(), "path", self.watch_log_path)
        logging.basicConfig(
            filename=self.watch_log_path,
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')

        base_image = 'rrs_radsurv'
        scripts_label = 'scripts'
        active_fw_name = f'{base_image}_{time.time()}'
        active_label = 'active'
        active_script_label = 'active_script_name'

        while self.active:
            # for each path being watched
            for path_def in self.config.get('paths', []):
                watch_path = f'{path_def}/*'
                print(f"watch path {watch_path}")
                new_folders = glob.glob(watch_path)

                group_id = 'idia_group'
                project_label = 'idia_brain_segmentation'

                if len(new_folders) > 0:
                    new_folder = new_folders[0]
                    print("new_folder!", new_folder)
                    time.sleep(30)
                    # get first actual dcm file
                    print("folder:", new_folders[0])
                    files = glob.glob(f'{new_folders[0]}/**/*.dcm', recursive=True)
                    if len(files) == 0:
                        files = glob.glob(f'{new_folders[0]}/**/*.dicom.zip', recursive=True)
                    dicom_path = files[0]
                    if dicom_path.endswith('.zip'):
                        with tempfile.TemporaryDirectory() as temp_path:
                            with zipfile.ZipFile(dicom_path) as zip:
                                zip.extractall(temp_path)
                                dicom_path = glob.glob(f'{temp_path}/*')[0]
                                dcm = pydicom.dcmread(dicom_path)
                    else:
                        dcm = pydicom.dcmread(dicom_path)

                    subject_label = dcm.PatientID  # '<SUBJECT>'
                    session_label = dcm.StudyDate.replace(' ', '_')  # '<SESSION>'
                    print(f'>>>>>found [{subject_label}] [{session_label}]')

                    script_info = {
                        'base_image': base_image,
                        'active_fw_name': active_fw_name,
                        'filesets': {
                            'dicom_raw': f'{new_folder}/*',
                            'dicom_sorted': f'fw://{group_id}/{project_label}/{subject_label}/{session_label}/*/*.dicom.zip',
                            'nifti_raw': f'fw://{group_id}/{project_label}/{subject_label}/{session_label}/*/*.nii.gz',
                            'preprocessed': f'fw://{group_id}/{project_label}/{subject_label}/{session_label}/preprocessed/*',
                            'nifti_raw_modalities_niiQuery.csv': '/home/aa-cxk023/share/files/nifti_raw_modalities_niiQuery.csv'
                        }
                    }

                    try:
                        # Get the analysis container object from Flywheel where the processor will look for scripts:
                        analysis = \
                        self.fw_client.resolve(f'{group_id}/{project_label}/analyses/{script_info["base_image"]}')['path'][-1]

                        # submit the script
                        print("add script!")
                        print(analysis.label)
                        print(script_info)
                        fws_add_script(analysis, script_info)

                        # wait for the cript to run
                        analysis = analysis.reload()
                        active = analysis.info.get(active_label)
                        if active:
                            active_script = analysis.info.get(active_script_label)
                            while active_script != active_fw_name:
                                time.sleep(3)
                                analysis = analysis.reload()
                                active_script = analysis.info.get(active_script_label)

                            while active_script == active_fw_name:
                                time.sleep(3)
                                analysis = analysis.reload()
                                active_script = analysis.info.get(active_script_label)


                    except Exception as e:
                        print("exception", e)
                        raise Exception(f'Not connected to a processor for {script_info["base_image"]}!')

                    shutil.rmtree(new_folder)

            # pause for a breath
            time.sleep(3)

if __name__ == "__main__":
    # watcher = DicomWatcher("dicom_watcher_config.yaml", "z:/scratch")
    watcher = DicomWatcher("dicom_watcher_config.yaml", "/home/aa-cxk023/share/scratch")
    watcher.watch()