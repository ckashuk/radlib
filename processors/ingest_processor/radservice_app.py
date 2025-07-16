import sys

sys.path.append('/home/aa-cxk023/share/radlib')

from radlib.dcm.sorter import DicomSorter
from radlib.processor.processor import Processor


class IngestProcessor(Processor):

    def processor_script(self):
        print("IngestProcessor processor_script!")
        dicom_raw = self.get_fileset('dicom_raw')
        dicom_sorted = self.get_fileset('dicom_sorted')
        nifti_raw = self.get_fileset('nifti_raw')

        sorter = DicomSorter('/dicom_raw',
                             f'{self.scratch_path}/dicom_sorted',
                             converted_folder='/nifti_raw',
                             preserve_input_files=False,
                             send_to_flywheel=True,
                             service=False,
                             flywheel_group=self.script_info.get('flywheel_group'),
                             flywheel_project=self.script_info.get('flywheel_project'),
                             logger=self.logger)
        sorter.start()
        # clean up
        # if not self.script_info.get('preserve_input_files', True):
        #     shutil.rmtree('/dicom_raw')
        # shutil.rmtree(sorted_folder)
        # shutil.rmtree('/nifti_raw')


if __name__ == "__main__":
    IngestProcessor.run_processor()