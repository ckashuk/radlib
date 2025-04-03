import unittest
from unittest.mock import MagicMock, patch

import SimpleITK as sitk
import numpy as np
import os
import glob

from flywheel import flywheel, ApiException

from radlib.fw.flywheel_clients import uwhealthaz_client
from radlib.fws.fws_image import FWSImageFile, FWSImageFileLocalException, FWSImageType, FWSLevel

"""
tests for FWSImageFile object, a class to hold information on an image file which could come
from a local file share or from a Flywheel instance. BIG ASSUMPTION is that the file name in 
both cases is the same
"""
class TestFWSImageFile(unittest.TestCase):
    def setUp(self):
        # flywheel client
        self.fw_client = uwhealthaz_client()

        # flywheel paths
        self.flywheel_jpg_path = 'prostatespore/fws_test_project/fws_test_subject/fws_test_session/jpg/UW17009-1 Slice 1.tif'
        self.flywheel_MR_path = 'prostatespore/fws_test_project/fws_test_subject/fws_test_session/MR/Obl Axial T2 Prostate.zip'
        self.flywheel_multi_path = 'prostatespore/fws_test_project/fws_test_subject/fws_test_session/multi'
        self.flywheel_nifti_path = 'prostatespore/fws_test_project/fws_test_subject/fws_test_session/nifti/P01_obl.nii.gz'
        self.flywheel_PET_path = 'prostatespore/fws_test_project/fws_test_subject/fws_test_session/PET/PET AC Prostate.zip'
        self.flywheel_spreadsheet_path = 'prostatespore/fws_test_project/fws_test_subject/fws_test_session/spreadsheet/FINAL.2022.12.24.oost surgery review data.xlsx'
        self.flywheel_svs_path = 'prostatespore/fws_test_project/fws_test_subject/fws_test_session/svs/17009-1-Slice 1-001.svs'

        self.good_fw_path = 'prostatespore/fws_test_project/fws_test_subject/fws_test_session/MR/Obl Axial T2 Prostate.zip'
        self.bad_session_fw_path = FWSImageFile.replace_flywheel_components(self.good_fw_path, session='bad_session')
        self.bad_acquisition_fw_path = FWSImageFile.replace_flywheel_components(self.good_fw_path, acquisition='bad_acquisition')


        # local paths
        self.local_root = '//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Research/test_data/flywheelscripts'
        self.output_root = f'{self.local_root}/output'
        self.local_jpg_path = f'{self.local_root}/local/jpg/UW17009-1 Slice 1.tif'
        self.local_MR_path = f'{self.local_root}/local/MR/Obl Axial T2 Prostate.zip'
        self.local_multi_path = f'{self.local_root}/local/multi'
        self.local_nifti_path = f'{self.local_root}/local/nifti/P01_obl.nii.gz'
        self.local_PET_path = f'{self.local_root}/local/PET/PET AC Prostate.zip'
        self.local_spreadsheet_path = f'{self.local_root}/local/spreadsheet/FINAL.2022.12.24.oost surgery review data.xlsx'
        self.local_svs_path = f'{self.local_root}/local/svs/17009-1-Slice 1-001.svs'

        self.local_PET_save_path = f'{self.local_root}/output/PET AC Prostate.zip'

        # local unzips for comparison
        self.local_unzipped_jpg_path = f'{self.local_root}/local_unzipped/jpg/UW17009-1 Slice 1.tif'
        self.local_unzipped_MR_path = f'{self.local_root}/local_unzipped/MR/'
        self.local_unzipped_multi_path = f'{self.local_root}/local_unzipped/multi'
        self.local_unzipped_nifti_path = f'{self.local_root}/local_unzipped/nifti/P01_obl.nii.gz'
        self.local_unzipped_PET_path = f'{self.local_root}/local_unzipped/PET/'
        self.local_unzipped_spreadsheet_path = f'{self.local_root}/local_unzipped/spreadsheet/FINAL.2022.12.24.oost surgery review data.xlsx'
        self.local_unzipped_svs_path = f'{self.local_root}/local_unzipped/svs/17009-1-Slice 1-001.svs'

        # 'bad' paths
        self.flywheel_bad_path = 'prostatespore/fws_test_project/fws_test_subject/fws_test_session/empty/not_a_file.zip'
        self.local_empty_path = self.local_root
        self.local_bad_path = '/path1/path2/path3'

    def test_create_image(self):
        file_fw = FWSImageFile(fw_client=self.fw_client, fw_path=self.flywheel_PET_path)
        file_local = FWSImageFile(local_path=self.local_PET_path)
        file_local_unzipped = FWSImageFile(local_path=self.local_unzipped_PET_path)
        self.assertEqual(len(file_fw.usable_paths), len(file_local_unzipped.usable_paths))
        self.assertEqual(len(file_local.usable_paths), len(file_local_unzipped.usable_paths))
        for file1, file2, file3 in zip(file_fw.usable_paths, file_local.usable_paths, file_local_unzipped.usable_paths):
            self.assertEqual(os.path.basename(file1), os.path.basename(file2))
            self.assertEqual(os.path.basename(file1), os.path.basename(file2))

    def test_create_image_exceptions(self):

        with self.assertRaises(ApiException):
            file_fw_empty = FWSImageFile(fw_client=self.fw_client, fw_path=self.flywheel_bad_path)

        with self.assertRaises(ApiException):
            file_fw_bad = FWSImageFile(fw_client=self.fw_client, fw_path=self.local_bad_path)

        with self.assertRaises(FWSImageFileLocalException):
            file_fw_disconnected = FWSImageFile(fw_path=self.flywheel_PET_path)

        with self.assertRaises(FWSImageFileLocalException):
            file_local_empty = FWSImageFile(local_path=self.local_empty_path)

        with self.assertRaises(FWSImageFileLocalException):
            file_local_bad = FWSImageFile(local_path=self.local_bad_path)


    def test_load_image(self):
        # create
        fws_file_fw = FWSImageFile(fw_client=self.fw_client, fw_path=self.flywheel_PET_path)
        fws_file_local = FWSImageFile(local_path=self.local_PET_path)

        # load
        file_fw1 = fws_file_fw.load_image(image_type=FWSImageType.pydicom)
        file_fw2 = fws_file_local.load_image(image_type=FWSImageType.sitk)

        # assert
        self.assertEqual(list(file_fw1[0].ImagePositionPatient), list(file_fw2.GetOrigin()), "test_load_from_flywheel data issue")
        self.assertEqual(len(file_fw1), file_fw2.GetSize()[2], "test_load_from_flywheel image data issue")

        # test no reload
        file_fw1 = fws_file_fw.load_image(image_type=FWSImageType.sitk)
        self.assertEqual(list(file_fw1[0].ImagePositionPatient), list(file_fw2.GetOrigin()), "test_load_from_flywheel do not reload failed")

        # test reload
        file_fw1 = fws_file_fw.load_image(image_type=FWSImageType.sitk, force_reload=True)
        self.assertEqual(list(file_fw1.GetOrigin()), list(file_fw2.GetOrigin()), "test_load_from_flywheel reload failed")

    def test_save_image(self):
        # clear
        local_files = glob.glob(f'{self.output_root}/*')
        for local_file in local_files:
            os.remove(local_file)

        # create
        fws_file_fw = FWSImageFile(fw_client=self.fw_client, fw_path=self.flywheel_PET_path)
        fws_file_local = FWSImageFile(local_path=self.local_PET_path)

        # load
        file_fw = fws_file_fw.load_image(image_type=FWSImageType.pydicom)
        file_local_zip = fws_file_local.load_image(image_type=FWSImageType.pydicom)
        file_local_nii = fws_file_local.load_image(image_type=FWSImageType.nii)

        # change
        new_ack_path = FWSImageFile.replace_flywheel_components(fws_file_fw.fw_path, acquisition='fws_test')
        fws_file_new = fws_file_fw
        fws_file_new.fw_path=new_ack_path

        local_save_root = os.path.splitext(self.local_PET_save_path)[0]
        local_zip_save_path = f'{local_save_root}.zip'
        local_nii_save_path = f'{local_save_root}.nii.gz'

        # save
        fws_file_new.save_image(FWSImageType.pydicom)
        fws_file_new.save_image(FWSImageType.nii)
        fws_file_local.save_image(type=FWSImageType.pydicom, force_local_path=local_zip_save_path)
        fws_file_local.save_image(type=FWSImageType.nii, force_local_path=local_nii_save_path)

        self.assertTrue(os.path.isfile(local_zip_save_path), 'fws save local zip failed')
        self.assertTrue(os.path.isfile(local_nii_save_path), 'fws save local nii failed')

        # TODO: 202503 csk reload files and perform more comparisons
        # reload
        # file_fw_saved = fws_file_new.load_image(image_type=FWSImageType.pydicom)
        # file_local_zip_saved =
        # self.assertEqual(len(file_fw), len(file_fw1a))

    def test_separate_flywheel_components(self):
        fw_named_path = 'group/project/subject/session/acquisition/file_name'
        fw_path_names = [name for name in FWSImageFile.separate_flywheel_components(fw_named_path)]

        for level in FWSImageFile.levels:
            self.assertEqual(fw_path_names[level.value], level.name, f'separate_flywheel_components failed for {level.name}')


    def test_resolve(self):

        # good image has all levels, so we can get the comparisons:
        good_objs = self.fw_client.resolve(self.good_fw_path)['path']

        # test good cases
        good_fw_image = FWSImageFile(fw_client=self.fw_client, fw_path = self.good_fw_path)
        for level in FWSImageFile.levels:
            obj_good = good_fw_image.resolve(level)
            obj_ref = good_objs[level.value]
            if level == FWSLevel.file_name:
                self.assertEqual(obj_good.name, obj_ref.name, f"resolve found failed at {level.name}")
            else:
                self.assertEqual(obj_good.label, obj_ref.label, f"resolve found failed at {level.name}")

        # test None cases (level does not exist)
        bad_fw_image = FWSImageFile(fw_client=self.fw_client, fw_path=self.bad_session_fw_path)

        for level in FWSImageFile.levels:
            obj_bad = bad_fw_image.resolve(level)
            obj_ref = good_objs[level.value]
            if level in [FWSLevel.file_name, FWSLevel.acquisition, FWSLevel.session]:
                self.assertEqual(obj_bad, None, f"resolve not found failed at {level.name}")
            else:
                self.assertEqual(obj_bad.label, obj_ref.label, f"resolve partial found failed at {level.name}")

        # test add if not exist: requires removal from flywheel test project for now!
        # TODO: 202504 csk need acquisition for now, improve this when we need other levels!
        add_fw_image = FWSImageFile(fw_client=self.fw_client, fw_path=self.bad_acquisition_fw_path)
        level = FWSLevel.acquisition
        obj_added = add_fw_image.resolve(level, label_if_not_found='added_acquisition')
        self.assertEqual(obj_added.label, 'added_acquisition', f'resolve add if not found failed for {level.name}')


if __name__ == "__main__":
    unittest.main()
