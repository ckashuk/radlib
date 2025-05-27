import os
import sys

from radlib.dcm.sorter import DicomSorter
from radlib.service.service_instance import ServiceInstance

dicom_input_path_env_name = 'DICOM_WATCH_FOLDER'
dicom_sorted_path_env_name = 'DICOM_SORTED_FOLDER'
dicom_converted_path_env_name = 'DICOM_CONVERTED_FOLDER'
dicom_single_script_path_env_name = 'DICOM_SORTER_SCRIPT_PATH'

def idia_ingest_processor(self, script_path):
    # always call setup first
    self.set_up(script_path)

    input_folder = self.scriptinfo.get('input_folder', '/mnt/RadServiceCache/idia_ingest_service/input')
    sorted_folder = self.scriptinfo.get('sorted_folder', '/mnt/RadServiceCache/idia_ingest_service/sorted')
    converted_folder = self.scriptinfo.get('converted_folder', '/mnt/RadServiceCache/idia_ingest_service/converted')

    if not os.path.exists(input_folder):
        print(f"must define {dicom_input_path_env_name} as an existing folder!")
        exit()

    sorter = DicomSorter(input_folder, sorted_folder, converted_folder, continuous=True)

    sorter.start()

    # always call cleanup just before writing output files
    self.clean_up(script_path)

if __name__ == "__main__":
    # instantiate the ServiceInstance, give it a processor function, and start it!
    # TODO: 202504 csk find better way(s) to stop!
    script_path = os.getenv(dicom_single_script_path_env_name)
    instance = ServiceInstance()
    instance.processor = idia_ingest_processor
    if script_path is not None:
        print("once!")
        instance.script_path = script_path
    else:
        print("server!")
    # instance.start()
