# -*- coding: utf-8 -*-
# Coded version of DICOM file '01.dcm'
# Produced by pydicom codify utility script
# 2024-12 csk added None to PixelData assignment, remove save_as, wrap in function

import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.sequence import Sequence

def generate_mr_dcm():
    # File meta info data elements
    file_meta = FileMetaDataset()
    file_meta.FileMetaInformationGroupLength = 196
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.4'
    file_meta.MediaStorageSOPInstanceUID = '1.2.826.0.1.3680043.2.629.20190306.16934440677809323137760939299'
    file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1'
    file_meta.ImplementationClassUID = '1.2.40.0.13.1.1.1'
    file_meta.ImplementationVersionName = 'dcm4che-1.4-JP'

    # Main data elements
    ds = Dataset()
    ds.SpecificCharacterSet = 'ISO_IR 100'
    ds.ImageType = ['ORIGINAL', 'PRIMARY', 'OTHER']
    ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.4'
    ds.SOPInstanceUID = '1.2.826.0.1.3680043.2.629.20190306.16934440677809323137760939299'
    ds.StudyDate = '20171115'
    ds.SeriesDate = '20171115'
    ds.AcquisitionDate = '20171115'
    ds.ContentDate = '20171115'
    ds.StudyTime = '070504'
    ds.SeriesTime = '070846'
    ds.AcquisitionTime = '070846'
    ds.ContentTime = '070846'
    ds.AccessionNumber = 'ACC00016S001'
    ds.Modality = 'MR'
    ds.Manufacturer = 'GE MEDICAL SYSTEMS'
    ds.ReferringPhysicianName = ''
    ds.StudyDescription = 'MRI PEDIATRIC QUICK SPINE W/ O CONTRAST'
    ds.SeriesDescription = 'TOP SAG SSFSE'
    ds.ManufacturerModelName = 'DISCOVERY MR750w'

    # Anatomic Region Sequence
    anatomic_region_sequence = Sequence()
    ds.AnatomicRegionSequence = anatomic_region_sequence

    # Anatomic Region Sequence: Anatomic Region 1
    anatomic_region1 = Dataset()
    anatomic_region_sequence.append(anatomic_region1)
    anatomic_region1.CodeValue = 'T-D0146'
    anatomic_region1.CodingSchemeDesignator = 'SRT'
    anatomic_region1.CodeMeaning = 'Spine'

    ds.PatientName = 'PatAge25_50,00016'
    ds.PatientID = '00016'
    ds.PatientBirthDate = '20130516'
    ds.PatientSex = 'F'
    ds.PatientAge = '004Y'
    ds.PatientSize = '0.832'
    ds.PatientWeight = '14.97'
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

    ds.BodyPartExamined = 'SPINE'
    ds.ScanningSequence = 'SE'
    ds.SequenceVariant = 'SK'
    ds.ScanOptions = ['FAST_GEMS', 'EDR_GEMS', 'SS_GEMS', 'ACC_GEMS', 'PFP']
    ds.MRAcquisitionType = '2D'
    ds.AngioFlag = 'N'
    ds.SliceThickness = '5'
    ds.RepetitionTime = '1698.63'
    ds.EchoTime = '89.6'
    ds.NumberOfAverages = '0.632353'
    ds.ImagingFrequency = '127.770972'
    ds.ImagedNucleus = '1H'
    ds.EchoNumbers = '1'
    ds.MagneticFieldStrength = '3'
    ds.SpacingBetweenSlices = '5'
    ds.EchoTrainLength = '1'
    ds.PercentSampling = '63.2353'
    ds.PercentPhaseFieldOfView = '70'
    ds.PixelBandwidth = '325.508'
    ds.DeviceSerialNumber = '00000608CHILDMR1'
    ds.SoftwareVersions = ['27', 'LX', 'MR Software release:DV25.1_R02_1649.a']
    ds.ProtocolName = 'Pediatric Quick Spine 1-'
    ds.HeartRate = '0'
    ds.CardiacNumberOfImages = '0'
    ds.TriggerWindow = '0'
    ds.ReconstructionDiameter = '260'
    ds.ReceiveCoilName = 'C Spine+Neck 36'
    ds.AcquisitionMatrix = [0, 320, 192, 0]
    ds.InPlanePhaseEncodingDirection = 'ROW'
    ds.FlipAngle = '90'
    ds.VariableFlipAngleFlag = 'N'
    ds.SAR = '3.49935'
    ds.PatientPosition = 'HFS'
    ds.StudyInstanceUID = '1.2.826.0.1.3680043.2.629.20190306.26892463439694541730260328393'
    ds.SeriesInstanceUID = '1.2.826.0.1.3680043.2.629.20190306.42955119484454791999499672144'
    ds.StudyID = ''
    ds.SeriesNumber = '4'
    ds.AcquisitionNumber = '1'
    ds.InstanceNumber = '1'
    ds.ImagePositionPatient = [29.2071, -97.4175, 62.2212]
    ds.ImageOrientationPatient = [-0.0189953, 0.991401, 0.129475, -0.0284853, 0.128909, -0.991247]
    ds.FrameOfReferenceUID = '1.2.826.0.1.3680043.2.629.20190306.23407408132402237932380821620'
    ds.Laterality = ''
    ds.ImagesInAcquisition = '13'
    ds.PositionReferenceIndicator = ''
    ds.SliceLocation = '-23.0466938'
    ds.StackID = '1'
    ds.InStackPositionNumber = 1
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = 'MONOCHROME2'
    ds.Rows = 512
    ds.Columns = 512
    ds.PixelSpacing = [0.5078, 0.5078]
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.SmallestImagePixelValue = 0
    ds.LargestImagePixelValue = 4666
    ds.LongitudinalTemporalInformationModified = 'MODIFIED'
    ds.WindowCenter = '2333'
    ds.WindowWidth = '4666'
    ds.LossyImageCompression = '00'
    ds.PerformedProcedureStepStartDate = '20171115'
    ds.PerformedProcedureStepStartTime = '065644'
    ds.PixelData = None # 2024-12 csk Array of 524288 bytes excluded

    ds.file_meta = file_meta
    ds.set_original_encoding(False, True)
    # ds.save_as(r'01_from_codify.dcm', enforce_file_format=True)

    return ds