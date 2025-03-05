import shutil

import pandas as pd
import SimpleITK as sitk
import glob
import tempfile
import pydicom
import os

from radlib.dcm.loaders import load_dicom_series_sitk
from radlib.dcm.utilities import set_sitk_dicom_tag, get_sitk_dicom_tag
from radlib.flywheel.flywheel_clients import uwhealth_client

# Ignore all warnings for now
sitk.ProcessObject_SetGlobalWarningDisplay(False)

# TODO: 2-25-03 csk generalize this to a class? or decide if that's too much work

# spore_17009_excel_path = '//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Research/ProstateSPORE/Pathology Data/Working Post-Surg Imaging Review/FINAL.2022.12.24.post surgery review data.xlsx'
spore_17009_excel_path = 'H://data/FINAL.2022.12.24.post surgery review data.xlsx'
spore_17009_pathology_converter = pd.ExcelFile(spore_17009_excel_path)

spore_17009_subject_list_path = 'H:/source/SPORE/SPORE_subject_list.csv'
spore_17009_subject_list = pd.read_csv(spore_17009_subject_list_path)

spore_17009_image_root = '//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Research/ProstateSPORE/DODDatasetComplete/CleanedProject/prosspore/DODProjectRead'
spore_17009_pathology_root = '//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Research/ProstateSPORE/Pathology Data'


spore_fw_client = uwhealth_client()

def get_subject_data_for_excel_id(excel_id):
    return spore_17009_subject_list[spore_17009_subject_list['excel_id'] == excel_id]

def get_image_id_for_excel_id(excel_id):
    return get_subject_data_for_excel_id(excel_id)['image_id'].values[0]

def get_pathology_id_for_excel_id(excel_id):
    return get_subject_data_for_excel_id(excel_id)['pathology_id'].values[0]

def get_pathology_index_for_excel_id(excel_id):
    return get_subject_data_for_excel_id(excel_id)['pathology_index'].values[0]

def get_pathology_path(excel_id):
    pathology_id = get_pathology_id_for_excel_id(excel_id)
    path = f'{spore_17009_pathology_root}/{pathology_id}/Beebe Data/H_E Slices/Edited Scans/'
    return path

def get_pet_path(excel_id, pet_index=1):
    image_id = get_image_id_for_excel_id(excel_id)
    path = f'{spore_17009_image_root}/{image_id}/PET{pet_index}'
    return path

def get_pathology_images(excel_id):
    image_paths = glob.glob(f'{get_pathology_path(excel_id)}/*.tif')

    # filter "extra" images
    image_paths = [image_path for image_path in image_paths if '_punch' not in image_path and 'hard' not in image_path]

    for image_path in image_paths:
        print(os.path.basename(image_path))
    exit()

    slice_numbers = [int(os.path.basename(image_path).replace('.tif', '').replace('_', ' ').split('lice ')[1].split(' ')[0].split('_')[0]) for image_path in image_paths]
    images = [sitk.ReadImage(image_path) for image_path in image_paths]

    # TODO: csk 01/2025 more pythonic way to do this??
    for image, slice_number in zip(images, slice_numbers):
        image.SetMetaData('0020|0013', str(slice_number))

    return images

def use_pathology_slice_image(image_name):
    # kludgy way to focus only on the "good" slice names that make sense
    if not image_name.upper().startswith('U'):
        return False
    if 'rot' in image_name:
        return False
    if 'unch' in image_name:
        return False
    if 'hard to orient' in image_name:
        return False
    if 'SLICE_' in image_name.upper():
        return False
    if '_.TIF' in image_name.upper():
        return False
    if not image_name.upper().endswith('TIF') and not image_name.upper().endswith('JPG'):
        return False
    if not "SLICE" in image_name.upper():
        return False
    return True

def convert_sitk_to_pydicom(sitk_image):
    # Create a named temporary file with dcm suffix
    temp = tempfile.NamedTemporaryFile(delete=False)
    dcm_file_name = f'{temp.name}.dcm'

    # save sitk_image as dcm
    sitk.WriteImage(sitk_image, dcm_file_name)

    # load with pydicom for ease of metadata editing
    pydicom_image = pydicom.dcmread(dcm_file_name)

    return pydicom_image

def convert_pathology_images_to_dcm(excel_id):
    images = [convert_sitk_to_pydicom(image) for image in get_pathology_images(excel_id)]
    images = sorted(images, key=lambda s: s.InstanceNumber)
    return images

def get_pet_images(excel_id, pet_index=1):
    image_paths = glob.glob(f'{get_pet_path(excel_id, pet_index)}/PET AC Prostate/dicom/*.dcm')
    images = [pydicom.dcmread(image_path) for image_path in image_paths]
    images = sorted(images, key=lambda s: s.SliceLocation)
    return images

def get_pet_images_from_flywheel(excel_id, pet_index=1):
    image_paths = glob.glob(f'{get_pet_path(excel_id, pet_index)}/PET AC Prostate/dicom/*.dcm')
    images = [pydicom.dcmread(image_path) for image_path in image_paths]
    images = sorted(images, key=lambda s: s.SliceLocation)
    return images

def get_axial_images(excel_id, pet_index=1):
    image_paths = glob.glob(f'{get_pet_path(excel_id, pet_index)}/Obl Axial T2 Prostate/dicom/*.dcm')
    images = [pydicom.dcmread(image_path) for image_path in image_paths]
    images = sorted(images, key=lambda s: s.SliceLocation)
    return images

def parse_index(val):
    if type(val) is str:
        for de in [' ', '-', ',']:
            if de in val:
                val = val.split(de)[0]

    return int(val)

def get_slice_conversion(excel_id):
    # data from excel workbook for sheet_name
    xls = spore_17009_pathology_converter.parse(excel_id)
    path_slice = xls['Path Slice #']
    i = xls[xls['Path Slice #'].isnull()].index[0]
    path_indices = [parse_index(i) for i in list(path_slice[:i])]
    pre_indices = [parse_index(i) for i in list(xls['Pre imaging slices'][:i])]
    post_indices = [parse_index(i) for i in list(xls['Post imaging slices'][:i])]

    return path_indices, pre_indices, post_indices


def update_pathology_positions(pathology_dicoms, reference_dicoms, pathology_indices, reference_indices):

    for image in pathology_dicoms:
        # 202501 csk minus one because excel sheet pathology slice indices start with "apex"
        image_index = image.InstanceNumber - 1
        print(">>>", image_index, pathology_indices, image_index in pathology_indices)
        if image_index in pathology_indices:
            conversion_index = pathology_indices.index(image_index)
            reference_index = reference_indices[conversion_index]
            reference_ipp = reference_dicoms[reference_index].ImagePositionPatient
            print("+++", image_index, conversion_index, reference_index, reference_ipp, pathology_indices, reference_indices)
            image.ImagePositionPatient = reference_ipp
            image.SliceLocation = reference_ipp[2]


def update_dicom_tags(excel_id, dicoms, reference_dicom):
    uid = pydicom.uid.generate_uid()
    for d, dicom in enumerate(dicoms):
        update_dicom_tags_for_pathology_instance(excel_id, dicom, d, reference_dicom, uid)


def save_dicoms(excel_id, dicoms, dicom_root, modality):
    dicom_id_root = f'{dicom_root}/{excel_id}'

    if not os.path.exists(dicom_id_root):
        os.mkdir(dicom_id_root)

    dicom_id_root = f'{dicom_id_root}/{modality}'
    if not os.path.exists(dicom_id_root):
        os.mkdir(dicom_id_root)

    for d, dicom in enumerate(dicoms):
        file_path = f'{dicom_id_root}/{excel_id}_{dicom.InstanceNumber}.dcm'
        pydicom.dcmwrite(file_path, dicom)

def copy_dicoms(excel_id, modality, pet_index, new_root):
    new_id_root = f'{new_root}/{modality}'
    if not os.path.exists(new_id_root):
        os.mkdir(new_id_root)

    old_root = f'{get_pet_path(excel_id, pet_index)}/{modality}/dicom/'

    shutil.copytree(old_root, new_id_root, dirs_exist_ok=True)


def generate_volume(excel_id, modality, pet_index, new_root):
    old_root = f'{get_pet_path(excel_id, pet_index)}/{modality}/dicom/'
    sitk_image = load_dicom_series_sitk(old_root)
    new_path = f'{new_root}/{excel_id}_{modality}{pet_index}.nii'
    sitk.WriteImage(sitk_image[0], new_path)


def update_dicom_tags_for_pathology_instance(pathology_id, pathology_dicom, instance_index, reference_dicom,
                                   new_series_instance_uid = pydicom.uid.generate_uid() ):

    # for tag in pathology_dicom.GetMetaDataKeys():
    #     print("path", tag, pathology_dicom.GetMetaData(tag))
    # for tag in reference_dicom.GetMetaDataKeys():
    #     print("ref", tag, reference_dicom.GetMetaData(tag))
    # exit()

    # tags
    set_sitk_dicom_tag(pathology_dicom, "PatientID", get_sitk_dicom_tag(reference_dicom, "PatientID"))
    set_sitk_dicom_tag(pathology_dicom, "PatientName", get_sitk_dicom_tag(reference_dicom, "PatientName"))
    set_sitk_dicom_tag(pathology_dicom, "PatientBirthDate", get_sitk_dicom_tag(reference_dicom, "PatientBirthDate"))
    set_sitk_dicom_tag(pathology_dicom, "PatientSex", get_sitk_dicom_tag(reference_dicom, "PatientSex"))
    set_sitk_dicom_tag(pathology_dicom, "PatientAge", get_sitk_dicom_tag(reference_dicom, "PatientAge"))

    set_sitk_dicom_tag(pathology_dicom, "AccessionNumber", get_sitk_dicom_tag(reference_dicom, "AccessionNumber"))
    set_sitk_dicom_tag(pathology_dicom, "StudyTime", get_sitk_dicom_tag(reference_dicom, "StudyTime"))
    set_sitk_dicom_tag(pathology_dicom, "Modality", get_sitk_dicom_tag(reference_dicom, "Modality"))
    set_sitk_dicom_tag(pathology_dicom, "StudyInstanceUID", get_sitk_dicom_tag(reference_dicom, "StudyInstanceUID"))
    set_sitk_dicom_tag(pathology_dicom, "StudyDescription",get_sitk_dicom_tag(reference_dicom, "StudyDescription") + '-pathology')
    set_sitk_dicom_tag(pathology_dicom, "SeriesNumber",str(int(get_sitk_dicom_tag(reference_dicom, "SeriesNumber")) + 1))
    # pathology_dicom.InstanceNumber = str(instance_index)
    set_sitk_dicom_tag(pathology_dicom, "SeriesInstanceUID",get_sitk_dicom_tag(reference_dicom, "SeriesInstanceUID") + '.1') # , new_series_instance_uid)
    set_sitk_dicom_tag(pathology_dicom, "NominalScannedPixelSpacing",None)
    set_sitk_dicom_tag(pathology_dicom, "Laterality",None)
    set_sitk_dicom_tag(pathology_dicom, "PositionReferenceIndicator",None)

    set_sitk_dicom_tag(pathology_dicom, "FrameOfReferenceUID", get_sitk_dicom_tag(reference_dicom, "FrameOfReferenceUID"))

    set_sitk_dicom_tag(pathology_dicom, "SliceThickness", get_sitk_dicom_tag(reference_dicom, "SliceThickness"))
    set_sitk_dicom_tag(pathology_dicom, "ImagePositionPatient", get_sitk_dicom_tag(reference_dicom, "ImagePositionPatient"))
    set_sitk_dicom_tag(pathology_dicom, "ImageOrientationPatient", get_sitk_dicom_tag(reference_dicom, "ImageOrientationPatient"))
    set_sitk_dicom_tag(pathology_dicom, "SliceLocation", get_sitk_dicom_tag(reference_dicom, "ImagePositionPatient")[2])
    set_sitk_dicom_tag(pathology_dicom, "PixelSpacing", get_sitk_dicom_tag(reference_dicom, "PixelSpacing"))

    set_sitk_dicom_tag(pathology_dicom, "SeriesDescription",f"{pathology_id} pathology series")

    pathology_dicom.SetOrigin(reference_dicom.GetOrigin())
    pathology_dicom.SetSpacing(reference_dicom.GetSpacing())

    # print(pathology_dicom.GetOrigin(), pathology_dicom.GetSpacing(), pathology_dicom.GetSize())
    # print(pathology_dicom.GetDirection())
    # print(reference_dicom.GetOrigin(), reference_dicom.GetSpacing(), reference_dicom.GetSize())
    # print(reference_dicom.GetDirection())

    return pathology_dicom

def update_dicom_tags_for_mr(mr_dicom_root, reference_dicom):
    for file_path in glob.glob(f'{mr_dicom_root}/*.dcm'):
        mr_dicom = pydicom.dcmread(file_path)
        update_dicom_tags_for_mr_instance(mr_dicom, reference_dicom)
        pydicom.dcmwrite(file_path, mr_dicom)

def update_dicom_tags_for_mr_instance(mr_dicom, reference_dicom, series_id=pydicom.uid.generate_uid()):
    # tags

    set_sitk_dicom_tag(mr_dicom, "PatientID", get_sitk_dicom_tag(reference_dicom, "PatientID"))
    set_sitk_dicom_tag(mr_dicom, "PatientName", get_sitk_dicom_tag(reference_dicom, "PatientName"))
    set_sitk_dicom_tag(mr_dicom, "PatientBirthDate", get_sitk_dicom_tag(reference_dicom, "PatientBirthDate"))
    set_sitk_dicom_tag(mr_dicom, "PatientSex", get_sitk_dicom_tag(reference_dicom, "PatientSex"))
    set_sitk_dicom_tag(mr_dicom, "PatientAge", get_sitk_dicom_tag(reference_dicom, "PatientAge"))

    set_sitk_dicom_tag(mr_dicom, "FrameOfReferenceUID", get_sitk_dicom_tag(reference_dicom, "FrameOfReferenceUID"))

    set_sitk_dicom_tag(mr_dicom, "AccessionNumber", get_sitk_dicom_tag(reference_dicom, "AccessionNumber"))
    set_sitk_dicom_tag(mr_dicom, "SeriesInstanceUID", series_id)
    set_sitk_dicom_tag(mr_dicom, "StudyInstanceUID", get_sitk_dicom_tag(reference_dicom, "StudyInstanceUID"))
    set_sitk_dicom_tag(mr_dicom, "StudyID", get_sitk_dicom_tag(reference_dicom, 'StudyID'))
    set_sitk_dicom_tag(mr_dicom, "SliceLocation", str(reference_dicom.GetOrigin()[2]))

    set_sitk_dicom_tag(mr_dicom, "SeriesDescription", f'{get_sitk_dicom_tag(reference_dicom, "PatientID")} regridded Obl series')

    # test
    set_sitk_dicom_tag(mr_dicom, "ImageOrientationPatient", get_sitk_dicom_tag(reference_dicom, "ImageOrientationPatient"))
    return mr_dicom
