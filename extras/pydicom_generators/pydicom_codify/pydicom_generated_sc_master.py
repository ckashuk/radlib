# -*- coding: utf-8 -*-
# Coded version of DICOM file './M10.dcm'
# Produced by pydicom codify utility script
# 2024-12 csk added None to PixelData assignment, remove save_as, wrap in function
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.sequence import Sequence

def generate_sc_dcm():
    # File meta info data elements
    file_meta = FileMetaDataset()
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.7'
    file_meta.MediaStorageSOPInstanceUID = '1.2.276.0.7230010.3.1.4.165240133.21536.1734112512.319'
    # file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.4.70'
    file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.4.50'
    # file_meta.ImplementationClassUID = '1.2.276.0.7230010.3.0.3.6.8'
    # file_meta.ImplementationClassUID = '1.2.40.0.13.1.1.1'
    file_meta.ImplementationClassUID = '1.2.276.0.7230010.3.0.3.6.8'
    # file_meta.ImplementationVersionName = 'OFFIS_DCMTK_368'
    # file_meta.ImplementationClassUID = '1.2.40.0.13.1.1.1'
    file_meta.ImplementationVersionName = 'dcm4che-1.4.37'

    # Main data elements
    ds = Dataset()
    ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.7'
    ds.SOPInstanceUID = '1.2.276.0.7230010.3.1.4.165240133.21536.1734112512.319'
    ds.StudyDate = ''
    ds.StudyTime = ''
    ds.AccessionNumber = ''
    ds.ConversionType = 'WSD'
    ds.ReferringPhysicianName = ''
    ds.PatientName = ''
    ds.PatientID = ''
    ds.PatientBirthDate = ''
    ds.PatientSex = ''
    ds.StudyInstanceUID = '1.2.276.0.7230010.3.1.2.165240133.21536.1734112512.318'
    ds.SeriesInstanceUID = '1.2.276.0.7230010.3.1.3.165240133.21536.1734112512.317'
    ds.StudyID = ''
    ds.SeriesNumber = None
    ds.InstanceNumber = None
    ds.PatientOrientation = ''
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = 'MONOCHROME2'
    ds.Rows = 1670
    ds.Columns = 1287
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.LossyImageCompression = '00'
    # ds.LossyImageCompressionRatio = '4.03637'
    # ds.LossyImageCompressionMethod = 'ISO_10918_1'
    ds.PixelData = None # 2024-12 csk Array of 532502 bytes excluded

    ds.file_meta = file_meta
    ds.set_original_encoding(False, True)
    # ds.save_as(r'./M10_from_codify.dcm', enforce_file_format=True)

    return ds