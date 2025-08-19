# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 11:37:52 2024

@author: axs291

Extra Info
https://stackoverflow.com/questions/34782409/understanding-dicom-image-attributes-to-get-axial-coronal-sagittal-cuts
"""
# %%


# import OS module
import os
import tempfile

import dicom2nifti
import numpy as np
import pandas as pd
import zipfile
import shutil
import pydicom
import logging
from zipfile import BadZipfile
from datetime import datetime
import SimpleITK as sitk

from radlib.fw.flywheel_data import load_image_from_local_path
from radlib.fws.fws_image import FWSImageFileList, FWSImageType, FWSImageFile, FWSLevel
from radlib.fws.fws_utils import fws_input_file_list

logger = logging.getLogger(__name__)


# %%
def get_planes_mri(dataset):
    imgorientation = dataset.ImageOrientationPatient
    codification = np.int16(np.round(np.array(imgorientation[:])))
    # codification_list =[]
    # for position,binary_value in enumerate(codification):
    #     if abs(binary_value)!=0:
    #         codification_list.append(position)

    plane = ''

    if codification[0] == 1 and codification[4] == 1:
        # print('axial') # E.g: ['1', '0', '0', '0', '1', '0']
        plane = 'Axial'

    if codification[0] == 1 and codification[5] == -1:  # E.g: ['1', '0', '0', '0', '0', '-1']
        # print('Coronal')
        plane = 'Coronal'

    if codification[1] == 1 and codification[5] == -1:
        plane = 'Sagital'
        # print('Sagittal') # E.g: ['0', '1', '0', '0', '0', '-1']

    if plane == '':
        plane = 'Axial'

    a = 0

    return plane


def extractdcminfo(dotdcm, folder, dicomfile):
    # Load the DICOM file
    dataset = pydicom.dcmread(dotdcm)
    try:
        # Access metadata elements
        patient_name = str(dataset.PatientName)
        patient_id = dataset.PatientID
        modality = dataset.Modality
        datadescription = dataset.SeriesDescription
        # acquisitiondate = int(dataset.AcquisitionDate)

        dictionary = {
            "Patient ID": patient_id,
            "Patient Name": str(patient_name),
            # "Acquisition Date": int(acquisitiondate),
            "Modality": modality,
            "SeriesDescription": datadescription,
            "Plane": get_planes_mri(dataset)
        }

        return dictionary

    except Exception as e:
        logging.error(f"dicom properties error: {e} in {folder}>>> {dicomfile}")
        return None

    # Extract image orientation


# %%

def find_modality_str(series_description):
    my_dict = {
        "T1": "t1" in series_description,
        "T2": "t2" in series_description,
        "FLAIR": "flair" in series_description,
        "+C": "+c" in series_description,
        "sag": "sag" in series_description,
        "ax": "ax" in series_description,
        "cor": "cor" in series_description
    }

    # Create a DataFrame with the specified column order
    df_modality = pd.DataFrame([my_dict], columns=['T1', 'T2', 'FLAIR', '+C', 'sag', 'ax', 'cor'])
    return df_modality


# %%

def copy_subject(input_dir, folder, time_point_folder, out_root, uncompress=False):
    dest_folder = os.path.join(out_root, folder, time_point_folder + '/')

    # print(time_point_folder)
    output_df = pd.DataFrame()

    dcm_list = os.listdir(input_dir)
    # print(len(os.listdir(input_dir)))

    if (len(os.listdir(input_dir)) > 0) & (len(os.listdir(input_dir)) > 3):

        for dicomfile in dcm_list:
            dcm_path = input_dir + dicomfile
            zip_path = dest_folder + '/' + dicomfile

            if os.path.exists(zip_path):
                print(f"{dicomfile}, >>>> already exists. Skip it")
                continue

            try:
                with zipfile.ZipFile(dcm_path, 'r') as zip_ref:

                    try:
                        file_list = zip_ref.namelist()
                        file_to_extract = file_list[0]

                        dotdcm = zip_ref.extract(file_to_extract)
                        info_dcm = extractdcminfo(dotdcm, folder, dicomfile)
                        if info_dcm == None:
                            continue

                        series_description = info_dcm['SeriesDescription'].lower()
                        # print(series_description)
                        df_dictionary = pd.DataFrame([info_dcm])

                        # Convert to lower case
                        df_dictionary["SeriesDescription"] = df_dictionary["SeriesDescription"][0].lower()

                        df_dictionary.insert(1, "path", dcm_path, True)
                        df_dictionary.insert(3, "time point", time_point_folder.split(' ')[0], True)

                        # Insert time point information

                        find_mod = find_modality_str(df_dictionary["SeriesDescription"][0])

                        result = pd.concat([df_dictionary, find_mod], axis=1)

                        # time_point_folder[:time_point_folder.index(' ')]

                        target_dcm = None

                        if series_description.find('t1') >= 0 and series_description.find('ax') >= 0:
                            # print('t1')
                            target_dcm = dcm_path
                        elif series_description.find('t1') >= 0 and series_description.find('sag') >= 0:
                            # print('t1')
                            target_dcm = dcm_path

                        elif series_description.find('t1') >= 0 and series_description.find('mpr') >= 0:
                            # print('t1')
                            target_dcm = dcm_path
                        elif series_description.find('t1') >= 0 and series_description.find('tra') >= 0:
                            # print('t1')
                            target_dcm = dcm_path

                        elif series_description.find('t1') >= 0 and series_description.find('3d') >= 0:
                            # print('t1')
                            target_dcm = dcm_path

                        elif series_description.find('+c') >= 0 and series_description.find('ax') >= 0:
                            # print('t1c')

                            target_dcm = dcm_path

                        elif series_description.find('flair') >= 0 or series_description.find(
                                't2') >= 0 or series_description.find('fse') >= 0:
                            target_dcm = dcm_path


                        elif series_description.find('bravo') >= 0 or series_description.find(
                                'mprage') >= 0 or series_description.find('fspgr') >= 0:
                            target_dcm = dcm_path
                            # (3D Ax BRAVO, MPRAGE,FSPGR  )

                        # else:
                        #     print("no matching series description [t1+c T1 t2 flair Bravo, MPRAGE, FSPGR]  in",dicomfile )

                        if target_dcm != None:
                            os.makedirs(dest_folder, exist_ok=True)
                            shutil.copy(target_dcm, zip_path)

                            if uncompress:
                                extract_folder = zip_path.replace('.zip', '')
                                # Extract the zip file
                                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                    zip_ref.extractall(extract_folder)

                                # Remove the zip file after extraction
                                os.remove(zip_path)
                    except Exception as e:
                        logging.error(f"Dicom copy error: {e} in case {folder}")

                    output_df = pd.concat([output_df, result], ignore_index=True)
                    output_df['Patient Name'] = 'Patient-' + output_df['Patient Name'][0][-4:]
                    # output_df = pd.concat([output_df, df_dictionary], ignore_index=True)

            except(BadZipfile):
                print("An exception occurred")
                print(dcm_path)
    else:
        print("not enought scans in", time_point_folder)

    return output_df


def get_dicom_date(dicom_data):
    """
    Try to get the date from various DICOM tags in order of preference.
    """
    date_attributes = [
        'AcquisitionDate',
        'SeriesDate',
        'StudyDate'
    ]
    # dicom_data = pydicom.dcmread(dicom_file)
    for attr in date_attributes:
        try:
            date_value = getattr(dicom_data, attr)
            if date_value:
                return datetime.strptime(date_value, '%Y%m%d').strftime('%Y%m%d')
        except (AttributeError, ValueError):
            continue

    return None


def ordering_studies(input_dir, parent):
    dcm_list = input_dir
    # print(len(os.listdir(input_dir)))

    dcm_dates = []
    for dicomfolder in list(dcm_list[:]):
        dcm_files = os.listdir(parent + '/' + dicomfolder)
        if (len(dcm_files) > 0) & (len(dcm_files) > 3):
            dcm_path = parent + '/' + dicomfolder + '/' + dcm_files[0]

            try:
                with zipfile.ZipFile(dcm_path, 'r') as zip_ref:
                    # Specify the file you want to extract
                    try:
                        file_list = zip_ref.namelist()
                        # print(file_list)
                        dicom_file = zip_ref.extract(file_list[0])
                        dicom_date = get_dicom_date(dicom_file)
                        # print(f" dicom_date, dcm_file {dicom_date} {dcm_files[0]}")

                    except Exception as e:
                        print("an exception")

            except  Exception as e:
                print("an exception")

            dcm_dates.append(dicom_date)

    return dcm_dates


# %%
ListModalities = []

def select_dicom(dcm):

    series_description = dcm.SeriesDescription.lower()
    if series_description.find('t1') >= 0 and series_description.find('ax') >= 0:
        return True
    elif series_description.find('t1') >= 0 and series_description.find('sag') >= 0:
        return True
    elif series_description.find('t1') >= 0 and series_description.find('mpr') >= 0:
        return True
    elif series_description.find('t1') >= 0 and series_description.find('tra') >= 0:
        return True
    elif series_description.find('t1') >= 0 and series_description.find('3d') >= 0:
        return True
    elif series_description.find('+c') >= 0 and series_description.find('ax') >= 0:
        return True
    elif series_description.find('flair') >= 0 or series_description.find('t2') >= 0 or series_description.find('fse')>=0:
        return True
    elif series_description.find('bravo') >= 0 or series_description.find('mprage') >= 0 or series_description.find('fspgr')>=0 :
        return True

    return False

# 202503 csk broke out individual subject to be used by flywheel
def DicomSelectionSingle(fws_input_files):
    sessions = fws_input_files.get_session_list(sorted=True)
    selected_dicoms = FWSImageFileList()
    if len(sessions) > 0:
        for time_point in sessions:
            print("time_point>>>>", time_point)
            session_files = fws_input_files.get_list_for_session(time_point)
            for file_name, file_data in session_files.items():
                image_slices = file_data.load_image(FWSImageType.pydicom, force_reload = True)
                dicom_slice = image_slices[0]
                if select_dicom(dicom_slice):
                    selected_dicoms[file_name] = file_data
            """
            try:
                PatientDataFrame = copy_subject(time_point_path, folder, time_point_folder, out_root,
                                                uncompress=True)
                mult_folder_list = [time_point_path for i in range(len(PatientDataFrame))]
                # PatientDataFrame.insert(1, "path", mult_folder_list, True)
                final_df = pd.concat([final_df, PatientDataFrame], ignore_index=True)

                if len(PatientDataFrame) != 0:
                    ListModalities.append(PatientDataFrame.SeriesDescription.to_list())

            except():
                print("An exception occurred")
                print(folder)
            """
    else:
        logging.debug(f"no valid time acquistion data (None) in folder")

    return selected_dicoms

def convert_dataset_to_nifti(fws_selected_files, local_output_folder=None, fw_acquisition_label=None):
    for file_name, file_data in fws_selected_files.items():
        if local_output_folder is None:
            local_output_folder  = tempfile.mkdtemp()
        nifti_name = file_data.file_name().split(' - ')[1].replace('+', '').replace(".dicom.zip", ".nii.gz")
        dicom2nifti.dicom_series_to_nifti(os.path.dirname(file_data.usable_paths[0]), f'{local_output_folder}/{nifti_name}')
        if fw_acquisition_label is not None and file_data.fw_client is not None:
            # check for valid acquisition
            file_data.fw_path = FWSImageFile.replace_flywheel_components(file_data.fw_path, acquisition=fw_acquisition_label, file_name=nifti_name)
            ack = file_data.resolve(FWSLevel.acquisition)

            file_data.save_image(FWSImageType.nii)

def mri_data_check(fws_selected_files):
    for file in fws_selected_files:
        print(file.file_name())
