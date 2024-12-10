from pydicom_generate.dcm.dicom_validator.validate_iods import validate
from pydicom_generate.dcm.pydicom_generate_rtss_master import generate_rtss_dcm
from pydicom_generate.dcm.pydicom_generated_ct_master import generate_ct_dcm
from pydicom_generate.dcm.pydicom_generated_pt_master import generate_pt_dcm
from pydicom_generate.dcm.pydicom_generated_mr_master import generate_mr_dcm


# valid modalities that this code knows about
dicom_modalities = {
    'CT': {'ciod': '1.2.840.10008.5.1.4.1.1.2', 'creator_function': generate_ct_dcm},
    'PT': {'ciod': '1.2.840.10008.5.1.4.1.1.128', 'creator_function': generate_pt_dcm},
    'MR': {'ciod': '1.2.840.10008.5.1.4.1.1.4', 'creator_function': generate_mr_dcm},
    'RTSS': {'ciod': '1.2.840.10008.5.1.4.1.1.481.3', 'creator_function': generate_rtss_dcm}
}

# unique exception class to know when dicom modality issues arise
class DicomModalityException(Exception):
    pass

def check_for_valid_modality(modality):
    # exception if code cannot handle the modality
    if not modality in dicom_modalities.keys():
        raise DicomModalityException(f"generate_dcm dcm_type {modality} not reecognized; should be one of {dicom_modalities.keys()}")


