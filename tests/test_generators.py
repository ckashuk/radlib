from radlib.dcm import DicomModalityException
import pydicom as pd
import unittest

from radlib.dcm import generate_valid_template_dcm

ct_reference_dcm_path = '../radlib/dcm/dicom_samples/1.2.826.0.1.3680043.2.629.20190306.10527514967919552016108815494.CT.dcm'
pt_reference_dcm_path = '../radlib/dcm/dicom_samples/1.2.826.0.1.3680043.2.629.20190306.10034577425707046841670623789.PT.dcm'
mr_reference_dcm_path = '../radlib/dcm/dicom_samples/01.dcm'
rtss_reference_dcm_path = '../radlib/dcm/dicom_samples/rtss.dcm'

class TestPydicomGenerate(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def gen_vs_ref(self, dcm_ref, dcm_gen, modality_name='DCM'):
        for tag in dcm_ref:
            tag_name = tag.keyword
            # TODO: 2024-12 csk pydicom utility does not populate PixelData, can this be tested?
            if tag_name == 'PixelData':
                continue

            # TODO: empty tag_name means private tag?
            if tag_name == '':
                continue
            value_ref = dcm_ref.get(tag_name, "NOT_FOUND_REF")
            value_gen = dcm_gen.get(tag_name, "NOT_FOUND_GEN")
            self.assertEqual(value_ref, value_gen, f"{modality_name} {tag_name} not equal. Ref value {value_ref}, gen value {value_gen}")

    def test_generate_ct(self):
        ct_ref = pd.dcmread(ct_reference_dcm_path)
        ct_gen = generate_valid_template_dcm("CT")

        self.gen_vs_ref(ct_ref, ct_gen, 'CT')

    def test_generate_pt(self):
        pt_ref = pd.dcmread(pt_reference_dcm_path)
        pt_gen = generate_valid_template_dcm("PT")

        self.gen_vs_ref(pt_ref, pt_gen, 'PT')

    def test_generate_mr(self):
        mr_ref = pd.dcmread(mr_reference_dcm_path)
        mr_gen = generate_valid_template_dcm("MR")

        self.gen_vs_ref(mr_ref, mr_gen, 'MR')

    def test_generate_rtss(self):
        rtss_ref = pd.dcmread(rtss_reference_dcm_path)
        rtss_gen = generate_valid_template_dcm("RTSS")

        self.gen_vs_ref(rtss_ref, rtss_gen, 'RTSS')

    def test_generate_bad_modality(self):
        with self.assertRaises(DicomModalityException):
            modality_gen = generate_valid_template_dcm("MOD")
