import pandas as pd

from fw.flywheel_clients import uwhealthaz_client

gbm_niiquery_path = '//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/IDIAGroup/Data/_Brain/Radiology/_Adult/_Glioma/GBM_Cohort_brucegroup/UW-GBM/logs/GBM_Cohort_brucegroup_nifti_raw_modalities_niiQuery.csv'
gbm_converter = pd.read_csv(gbm_niiquery_path)

def get_image_name(id, modality):
    if 'RAD-' not in id:
        id = f'RAD-AI-CNS-TUMOR-{id}'
    found_row = gbm_converter[(gbm_converter['ID'] == id) & (gbm_converter['mri_tag'] == modality)]
    return found_row['mri_modalities (original nifti)'].values[0].replace(" ", "_")

def get_t1_name(id):
    return get_image_name(id, 'T1')

def get_t1c_name(id):
    return get_image_name(id, 'T1c')

def get_t2_name(id):
    return get_image_name(id, 'T2')

def get_flair_name(id):
    return get_image_name(id, 'FLAIR')


if __name__ == "__main__":
    id = '0001'
    t1_file_name = get_t1_name(id)
    t1c_file_name = get_t1c_name(id)
    t2_file_name = get_t2_name(id)
    flair_file_name = get_flair_name(id)

    fw_client = uwhealthaz_client()
    t1_file = fw_client.resolve(f'brucegroup/GBM Cohort new/RADAICNS-0001-01/20191210/nifti_raw/{t1_file_name}')['path'][-1]
    print(t1_file_name, t1_file.name)

    print(t1c_file_name)
    t1c_file = fw_client.resolve(f'brucegroup/GBM Cohort new/RADAICNS-0001-01/20191210/nifti_raw/{t1c_file_name}')['path'][-1]
    print(t1c_file_name, t1c_file.name)

    t2_file = fw_client.resolve(f'brucegroup/GBM Cohort new/RADAICNS-0001-01/20191210/nifti_raw/{t2_file_name}')['path'][-1]

    flair_file = fw_client.resolve(f'brucegroup/GBM Cohort new/RADAICNS-0001-01/20191210/nifti_raw/{flair_file_name}')['path'][-1]
    print(flair_file_name, flair_file.name)

