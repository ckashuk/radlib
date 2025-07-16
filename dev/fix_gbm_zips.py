import tempfile
import zipfile
import glob
import shutil
import os

root_path = '//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/IDIAGroup'
if not os.path.exists(root_path):
    root_path = '/home/aa-cxk023/idia'

subject_root_path = f'{root_path}/Data/_Brain/Radiology/_Adult/_Glioma/GBM_Cohort_brucegroup/UW-GBM/dicom_raw'

for subject_path in glob.glob(f'{subject_root_path}/*'):
    session_paths = glob.glob(f'{subject_path}/*')
    session_paths.sort()
    dicom_paths = glob.glob(f'{session_paths[0]}/*')
    for dicom_path in dicom_paths:
        if not dicom_path.endswith('.dicom.zip'):
            with tempfile.TemporaryDirectory() as temp_path:
                if dicom_path.endswith('.zip'):
                    with zipfile.ZipFile(dicom_path) as zip:
                        zip.extractall(temp_path)
                        files = glob.glob(f'{temp_path}/*')
                        if len(files) == 1:
                            for file in glob.glob(f'{files[0]}/*'):
                                shutil.move(file, f'{temp_path}/{os.path.basename(file)}')
                            shutil.rmtree(files[0])
                else:
                    for file in glob.glob(f'{dicom_path}/*'):
                        shutil.copy(file, f'{temp_path}/{os.path.basename(file)}')

                copied_files = glob.glob(f'{temp_path}/*')
                print(os.path.basename(session_paths[0]), len(copied_files))
