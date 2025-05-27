
"""
tests for fws_utils
"""
import unittest

from radlib.fw.flywheel_clients import uwhealthaz_client
from radlib.fws.fws_utils import fw_types, fw_type_objects, fws_in_jupyter_notebook, fws_separate_flywheel_labels, fws_resolve_object


class TestFwsUtils(unittest.TestCase):
    def setUp(self):
        self.fw_client = uwhealthaz_client()

        self.test_flywheel_path_1 = 'fw://prostatespore/fws_test_project/fws_test_subject/fws_test_session/PET/PET AC Prostate.zip'
        self.test_flywheel_path_2 = 'fw://prostatespore/fws_test_project/fws_test_subject/fws_test_session/MR/Obl Axial t2 Prostate.zip'
        self.test_flywheel_path_bad = 'fw://prostatespore/fws_test_project/fws_tset_subject/fws_test_session/PET/PET AC Prostate.zip'

        # function under test
        # def fws_create_new_cell(contents: str = ''):


    def test_fws_in_jupyter_notebook(self):
        # function under test
        # def fws_in_jupyter_notebook():

        res = fws_in_jupyter_notebook()
        self.assertFalse(res, "fws_in_jupyter_notebook failed check")


    def test_fws_separate_flywheel_labels(self):
        # function under test
        # def fws_separate_flywheel_labels(fw_path: str)-> list[str]:
        labels0 = fws_separate_flywheel_labels(self.test_flywheel_path_1)
        labels1 = self.test_flywheel_path_1.replace('fw://', '').split('/')

        for fw_type, label0, label1 in zip(fw_types, labels0, labels1):
            self.assertEqual(label0, label1, f"fws_separate_flywheel_labels failed at {fw_type}")

        labels2 = self.test_flywheel_path_1.replace('fw://', '').split('/')

        for fw_type, label0, label2 in zip(fw_types, labels0, labels2):
            self.assertEqual(label0, label2, f"fws_separate_flywheel_labels failed at {fw_type}")


    def test_fws_resolve_object(self):
        # function under test
        # def fws_resolve_object(fw_client, fw_path:str, fw_type:str='project'):
        for fw_type, fw_type_object in zip(fw_types, fw_type_objects):
            obj = fws_resolve_object(self.fw_client, self.test_flywheel_path_1, fw_type)
            self.assertEqual(type(obj), fw_type_object, f"fws_resolve_object failed at {fw_type}")


    def test_fws_download_files_from_flywheel(self):
        # function under test
        # def fws_download_files_from_flywheel(fw_client, fw_path, local_path, logger=None):
        pass

    def test_fws_create_paths(self):
        # function under test
        # def fws_create_paths(paths: list[str]):
        pass

    def test_fws_copy_file(self):
        # function under test
        # def fws_copy_file(path_from: str, path_to:str, logger=None):
        pass

    def fws_load_image(self):
        # function under test
        # def fws_load_image(fw_client, fw_path, file_name, local_root, local_path):
        pass

        # function under test
        # def fws_input_file_list(fw_client, project_label,
        #                                 subject_labels=None,
        #                                 session_labels=None,
        #                                 acquisition_labels=None,
        #                                 generate_code=False,
        #                                local_root=None):
        pass
