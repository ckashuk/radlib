sitk_dicom_tags = {
    "PatientName": "0010|0010",
    "PatientID": "0010|0020",
    "StudyDate": "0008|0020",
    "StudyTime": "0008|0030",
    "Modality": "0008|0060",
    "AccessionNumber": "0008|0050",
    "StudyID": "0020|0010",
    "SeriesNumber": "0020|0011",
    "InstanceNumber": "0020|0013",
    "StudyInstanceUID": "0020|000d",
    "StudyDescription": "0008|1030",
    "SeriesInstanceUID": "0020|000e",
    "NominalScannedPixelSpacing": "0018|2010",
    "Laterality": "0020|0060",
    "PositionReferenceIndicator": "0020|1040",
    "PatientBirthDate": "0010|0030",
    "PatientSex": "0010|0040",
    "PatientAge": "0010|1010",
    "FrameOfReferenceUID": "0020|0052",
    "SliceThickness": "0018|0050",
    "ImagePositionPatient": "0020|0032",
    "ImageOrientationPatient": "0020|0037",
    "SliceLocation": "0020|1041",
    "PixelSpacing": "0028|0030",
    "SeriesDescription": "0008|103e",


}

def get_sitk_dicom_tag(image, tag_name):
    tag_id = sitk_dicom_tags[tag_name]
    try:
        return image.GetMetaData(tag_id)
    except Exception:
        return 'NA'

def set_sitk_dicom_tag(image, tag_name, value):
    # TODO: 202502 csk revisit this
    if value is None:
        value = ''
    tag_id = sitk_dicom_tags[tag_name]
    image.SetMetaData(tag_id, value)