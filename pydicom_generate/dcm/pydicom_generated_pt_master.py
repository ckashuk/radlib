# -*- coding: utf-8 -*-
# Coded version of DICOM file '1.2.826.0.1.3680043.2.629.20190306.10034577425707046841670623789.PT.dcm'
# Produced by pydicom codify utility script
# 2024-12 csk added None to PixelData assignment, remove save_as, wrap in function
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.sequence import Sequence

def generate_pt_dcm():
    # File meta info data elements
    file_meta = FileMetaDataset()
    file_meta.FileMetaInformationGroupLength = 200
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.128'
    file_meta.MediaStorageSOPInstanceUID = '1.2.826.0.1.3680043.2.629.20190306.10034577425707046841670623789'
    file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.4.70'
    file_meta.ImplementationClassUID = '1.2.40.0.13.1.1.1'
    file_meta.ImplementationVersionName = 'dcm4che-1.4.37'

    # Main data elements
    ds = Dataset()
    ds.SpecificCharacterSet = 'ISO_IR 100'
    ds.ImageType = ['ORIGINAL', 'PRIMARY']
    ds.InstanceCreationDate = '20050319'
    ds.InstanceCreationTime = '104102.000'
    ds.InstanceCreatorUID = '1.2.826.0.1.3680043.2.629.20190306.11445658067479641639626656989'
    ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.128'
    ds.SOPInstanceUID = '1.2.826.0.1.3680043.2.629.20190306.10034577425707046841670623789'
    ds.StudyDate = '20050319'
    ds.SeriesDate = '20050319'
    ds.AcquisitionDate = '20050319'
    ds.ContentDate = '20050319'
    ds.StudyTime = '095904.00'
    ds.SeriesTime = '100520.00'
    ds.AcquisitionTime = '100520.00'
    ds.ContentTime = '103559.00'
    ds.AccessionNumber = '57-01'
    ds.Modality = 'PT'
    ds.Manufacturer = 'GE MEDICAL SYSTEMS'
    ds.ReferringPhysicianName = ''
    ds.StudyDescription = 'BODY ONC'
    ds.SeriesDescription = 'WB IRCTAC'
    ds.ManufacturerModelName = 'Discovery LS'
    ds.PatientName = '57'
    ds.PatientID = '57'
    ds.PatientBirthDate = '19250501'
    ds.PatientSex = 'M'
    ds.PatientAge = '079Y'
    ds.PatientSize = '1.6000000238419'
    ds.PatientWeight = '76'
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

    ds.SliceThickness = '4.25'
    ds.AcquisitionTerminationCondition = 'TIME'
    ds.AcquisitionStartCondition = 'MANU'
    ds.AcquisitionStartConditionData = '0'
    ds.AcquisitionTerminationConditionData = '0'
    ds.SoftwareVersions = '16.01'
    ds.ContrastBolusRoute = ''
    ds.IntervalsAcquired = '0'
    ds.IntervalsRejected = '0'
    ds.ReconstructionDiameter = '500'
    ds.GantryDetectorTilt = '0'
    ds.TableHeight = '165'
    ds.FieldOfViewShape = 'CYLINDRICAL RING'
    ds.FieldOfViewDimensions = [550, 153]
    ds.CollimatorType = 'RING'
    ds.ActualFrameDuration = '300000'
    ds.PatientPosition = 'HFS'
    ds.StudyInstanceUID = '1.2.826.0.1.3680043.2.629.20190306.17914024151380783659612095864'
    ds.SeriesInstanceUID = '1.2.826.0.1.3680043.2.629.20190306.13479168241210250116412212951'
    ds.StudyID = ''
    ds.SeriesNumber = None
    ds.InstanceNumber = '176'
    ds.ImagePositionPatient = [-250.00000000000, -250.00000000000, -121.75000000000]
    ds.ImageOrientationPatient = [1.00000000000000, 0.00000000000000, 0, 0, 1, -0]
    ds.FrameOfReferenceUID = '1.2.826.0.1.3680043.2.629.20190306.19273506363705523454111579391'
    ds.PositionReferenceIndicator = 'Orbital Meatal Line'
    ds.SliceLocation = '-121.75000000000'
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = 'MONOCHROME2'
    ds.Rows = 128
    ds.Columns = 128
    ds.PixelSpacing = [3.90625, 3.90625]
    ds.CorrectedImage = ['DECY', 'ATTN', 'SCAT', 'DTIM', 'RAN', 'RADL', 'DCAL', 'SLSENS', 'NORM']
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.LongitudinalTemporalInformationModified = 'MODIFIED'
    ds.RescaleIntercept = '0'
    ds.RescaleSlope = '0.401448'
    ds.LossyImageCompression = '00'

    # Energy Window Range Sequence
    energy_window_range_sequence = Sequence()
    ds.EnergyWindowRangeSequence = energy_window_range_sequence

    # Energy Window Range Sequence: Energy Window Range 1
    energy_window_range1 = Dataset()
    energy_window_range_sequence.append(energy_window_range1)
    energy_window_range1.EnergyWindowLowerLimit = '000000000000300'
    energy_window_range1.EnergyWindowUpperLimit = '000000000000650'


    # Radiopharmaceutical Information Sequence
    radiopharmaceutical_information_sequence = Sequence()
    ds.RadiopharmaceuticalInformationSequence = radiopharmaceutical_information_sequence

    # Radiopharmaceutical Information Sequence: Radiopharmaceutical Information 1
    radiopharmaceutical_information1 = Dataset()
    radiopharmaceutical_information_sequence.append(radiopharmaceutical_information1)
    radiopharmaceutical_information1.Radiopharmaceutical = 'FDG -- fluorodeoxyglucose'
    radiopharmaceutical_information1.RadiopharmaceuticalVolume = '0'
    radiopharmaceutical_information1.RadiopharmaceuticalStartTime = '084800.00'
    radiopharmaceutical_information1.RadionuclideTotalDose = '447350464'
    radiopharmaceutical_information1.RadionuclideHalfLife = '6588'
    radiopharmaceutical_information1.RadionuclidePositronFraction = '0.97000002861023'

    # Radionuclide Code Sequence
    radionuclide_code_sequence = Sequence()
    radiopharmaceutical_information1.RadionuclideCodeSequence = radionuclide_code_sequence

    # Radionuclide Code Sequence: Radionuclide Code 1
    radionuclide_code1 = Dataset()
    radionuclide_code_sequence.append(radionuclide_code1)
    radionuclide_code1.CodeValue = 'C-111A1'
    radionuclide_code1.CodingSchemeDesignator = '99SDM'
    radionuclide_code1.CodeMeaning = '18F'


    # Radiopharmaceutical Code Sequence
    radiopharmaceutical_code_sequence = Sequence()
    radiopharmaceutical_information1.RadiopharmaceuticalCodeSequence = radiopharmaceutical_code_sequence

    # Radiopharmaceutical Code Sequence: Radiopharmaceutical Code 1
    radiopharmaceutical_code1 = Dataset()
    radiopharmaceutical_code_sequence.append(radiopharmaceutical_code1)
    radiopharmaceutical_code1.CodeValue = 'Y-X1743'
    radiopharmaceutical_code1.CodingSchemeDesignator = '99SDM'
    radiopharmaceutical_code1.CodeMeaning = 'FDG -- fluorodeoxyglucose'

    ds.NumberOfSlices = 205
    ds.NumberOfTimeSlices = 6
    ds.TypeOfDetectorMotion = 'NONE'

    # Patient Orientation Code Sequence
    patient_orientation_code_sequence = Sequence()
    ds.PatientOrientationCodeSequence = patient_orientation_code_sequence

    # Patient Orientation Code Sequence: Patient Orientation Code 1
    patient_orientation_code1 = Dataset()
    patient_orientation_code_sequence.append(patient_orientation_code1)
    patient_orientation_code1.CodeValue = 'F-10450'
    patient_orientation_code1.CodingSchemeDesignator = '99SDM'
    patient_orientation_code1.CodeMeaning = 'recumbent'

    # Patient Orientation Modifier Code Sequence
    patient_orientation_modifier_code_sequence = Sequence()
    patient_orientation_code1.PatientOrientationModifierCodeSequence = patient_orientation_modifier_code_sequence

    # Patient Orientation Modifier Code Sequence: Patient Orientation Modifier Code 1
    patient_orientation_modifier_code1 = Dataset()
    patient_orientation_modifier_code_sequence.append(patient_orientation_modifier_code1)
    patient_orientation_modifier_code1.CodeValue = 'F-10340'
    patient_orientation_modifier_code1.CodingSchemeDesignator = '99SDM'
    patient_orientation_modifier_code1.CodeMeaning = 'supine'


    # Patient Gantry Relationship Code Sequence
    patient_gantry_relationship_code_sequence = Sequence()
    ds.PatientGantryRelationshipCodeSequence = patient_gantry_relationship_code_sequence

    # Patient Gantry Relationship Code Sequence: Patient Gantry Relationship Code 1
    patient_gantry_relationship_code1 = Dataset()
    patient_gantry_relationship_code_sequence.append(patient_gantry_relationship_code1)
    patient_gantry_relationship_code1.CodeValue = 'F-10470'
    patient_gantry_relationship_code1.CodingSchemeDesignator = '99SDM'
    patient_gantry_relationship_code1.CodeMeaning = 'headfirst'

    ds.SeriesType = ['STATIC', 'IMAGE']
    ds.Units = 'BQML'
    ds.CountsSource = 'EMISSION'
    ds.RandomsCorrectionMethod = 'RTSUB'
    ds.AttenuationCorrectionMethod = 'measured,, 0.096000 cm-1,'
    ds.DecayCorrection = 'START'
    ds.ReconstructionMethod = 'OSEM'
    ds.ScatterCorrectionMethod = 'Convolution subtraction'
    ds.AxialMash = [3, 2]
    ds.TransverseMash = '1'
    ds.CoincidenceWindowWidth = '12'
    ds.FrameReferenceTime = '1516000'
    ds.SliceSensitivityFactor = '0.826479'
    ds.DecayFactor = '1.19154'
    ds.DoseCalibrationFactor = '205'
    ds.ScatterFractionFactor = '0.116847'
    ds.ImageIndex = 176
    ds.PixelData = None # 2024-12 csk Array of 524288 bytes excluded

    ds.file_meta = file_meta
    ds.set_original_encoding(False, True)
    # ds.save_as(r'1.2.826.0.1.3680043.2.629.20190306.10034577425707046841670623789.PT_from_codify.dcm', enforce_file_format=True)

    return ds