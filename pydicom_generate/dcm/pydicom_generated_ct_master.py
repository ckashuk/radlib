# -*- coding: utf-8 -*-
# Coded version of DICOM file '1.2.826.0.1.3680043.2.629.20190306.10527514967919552016108815494.CT.dcm'
# Produced by pydicom codify utility script
# 2024-12 csk added None to PixelData assignment, remove save_as, wrap in function
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.sequence import Sequence

def generate_ct_dcm():

    # File meta info data elements
    file_meta = FileMetaDataset()
    file_meta.FileMetaInformationGroupLength = 198
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
    file_meta.MediaStorageSOPInstanceUID = '1.2.826.0.1.3680043.2.629.20190306.10527514967919552016108815494'
    file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.4.70'
    file_meta.ImplementationClassUID = '1.2.40.0.13.1.1.1'
    file_meta.ImplementationVersionName = 'dcm4che-1.4.37'

    # Main data elements
    ds = Dataset()
    ds.SpecificCharacterSet = 'ISO_IR 100'
    ds.ImageType = ['ORIGINAL', 'PRIMARY', 'AXIAL']
    ds.InstanceCreationDate = '20050319'
    ds.InstanceCreationTime = '100740'
    ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
    ds.SOPInstanceUID = '1.2.826.0.1.3680043.2.629.20190306.10527514967919552016108815494'
    ds.StudyDate = '20050319'
    ds.SeriesDate = '20050319'
    ds.AcquisitionDate = '20050319'
    ds.ContentDate = '20050319'
    ds.StudyTime = '095904'
    ds.SeriesTime = '100105'
    ds.AcquisitionTime = '100239'
    ds.ContentTime = '100740'
    ds.AccessionNumber = '57-01'
    ds.Modality = 'CT'
    ds.Manufacturer = 'GE MEDICAL SYSTEMS'
    ds.ReferringPhysicianName = ''
    ds.StudyDescription = 'BODY ONC'
    ds.SeriesDescription = 'WB CT SLICES'
    ds.ManufacturerModelName = 'Discovery LS'
    ds.PatientName = '57'
    ds.PatientID = '57'
    ds.PatientBirthDate = '19250501'
    ds.PatientSex = 'M'
    ds.PatientAge = '079Y'
    ds.PatientWeight = '76.0'
    ds.PatientIdentityRemoved = 'YES'
    ds.DeidentificationMethod = 'CTP Default: based on DICOM PS3.15 AnnexE.'

    # De-identification Method Code Sequence
    deidentification_method_code_sequence = Sequence()
    ds.DeidentificationMethodCodeSequence = deidentification_method_code_sequence

    # De-identification Method Code Sequence: De-identification Method Code 1
    deidentification_method_code1 = Dataset()
    deidentification_method_code_sequence.append(deidentification_method_code1)
    deidentification_method_code1.CodeValue = '113100'
    deidentification_method_code1.CodingSchemeDesignator = 'DCM'
    deidentification_method_code1.CodeMeaning = 'Basic Application Confidentiality Profile'

    # De-identification Method Code Sequence: De-identification Method Code 2
    deidentification_method_code2 = Dataset()
    deidentification_method_code_sequence.append(deidentification_method_code2)
    deidentification_method_code2.CodeValue = '113105'
    deidentification_method_code2.CodingSchemeDesignator = 'DCM'
    deidentification_method_code2.CodeMeaning = 'Clean Descriptors Option'

    # De-identification Method Code Sequence: De-identification Method Code 3
    deidentification_method_code3 = Dataset()
    deidentification_method_code_sequence.append(deidentification_method_code3)
    deidentification_method_code3.CodeValue = '113107'
    deidentification_method_code3.CodingSchemeDesignator = 'DCM'
    deidentification_method_code3.CodeMeaning = 'Retain Longitudinal Temporal Information Modified Dates Option'

    # De-identification Method Code Sequence: De-identification Method Code 4
    deidentification_method_code4 = Dataset()
    deidentification_method_code_sequence.append(deidentification_method_code4)
    deidentification_method_code4.CodeValue = '113108'
    deidentification_method_code4.CodingSchemeDesignator = 'DCM'
    deidentification_method_code4.CodeMeaning = 'Retain Patient Characteristics Option'

    # De-identification Method Code Sequence: De-identification Method Code 5
    deidentification_method_code5 = Dataset()
    deidentification_method_code_sequence.append(deidentification_method_code5)
    deidentification_method_code5.CodeValue = '113109'
    deidentification_method_code5.CodingSchemeDesignator = 'DCM'
    deidentification_method_code5.CodeMeaning = 'Retain Device Identity Option'

    ds.ScanOptions = 'HELICAL MODE'
    ds.SliceThickness = '5.000000'
    ds.KVP = '140'
    ds.DataCollectionDiameter = '500.000000'
    ds.SoftwareVersions = 'LightSpeedAppsct_dst_dls_1.7_R2.9N.IRIX646.5'
    ds.ReconstructionDiameter = '500.000000'
    ds.DistanceSourceToDetector = '949.075012'
    ds.DistanceSourceToPatient = '541.000000'
    ds.GantryDetectorTilt = '0.000000'
    ds.TableHeight = '164.800003'
    ds.RotationDirection = 'CW'
    ds.ExposureTime = '1121'
    ds.XRayTubeCurrent = '120'
    ds.Exposure = '5684'
    ds.FilterType = 'BODY FILTER'
    ds.GeneratorPower = '16800'
    ds.FocalSpots = '0.700000'
    ds.ConvolutionKernel = 'STANDARD'
    ds.PatientPosition = 'HFS'
    ds.StudyInstanceUID = '1.2.826.0.1.3680043.2.629.20190306.17914024151380783659612095864'
    ds.SeriesInstanceUID = '1.2.826.0.1.3680043.2.629.20190306.24383137657561136748847147075'
    ds.StudyID = ''
    ds.SeriesNumber = '2'
    ds.AcquisitionNumber = '1'
    ds.InstanceNumber = '190'
    ds.ImagePositionPatient = [-250.000000, -250.000000, -801.750000]
    ds.ImageOrientationPatient = [1.000000, 0.000000, 0.000000, 0.000000, 1.000000, 0.000000]
    ds.FrameOfReferenceUID = '1.2.826.0.1.3680043.2.629.20190306.19273506363705523454111579391'
    ds.PositionReferenceIndicator = 'OM'
    ds.SliceLocation = '-801.750000'
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = 'MONOCHROME2'
    ds.Rows = 512
    ds.Columns = 512
    ds.PixelSpacing = [0.976562, 0.976562]
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.PixelPaddingValue = -2000
    ds.LongitudinalTemporalInformationModified = 'MODIFIED'
    ds.WindowCenter = '40'
    ds.WindowWidth = '400'
    ds.RescaleIntercept = '-1024'
    ds.RescaleSlope = '1'
    ds.WindowCenterWidthExplanation = ''
    ds.LossyImageCompression = '00'
    ds.PerformedProcedureStepStartDate = '20050319'
    ds.PerformedProcedureStepStartTime = '095904'
    ds.PixelData = None # 2024-12 csk Array of 191680 bytes excluded

    ds.file_meta = file_meta
    ds.set_original_encoding(False, True)
    # ds.save_as(r'1.2.826.0.1.3680043.2.629.20190306.10527514967919552016108815494.CT_from_codify.dcm', enforce_file_format=True)

    return ds
