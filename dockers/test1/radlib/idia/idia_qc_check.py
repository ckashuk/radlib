import os

import flywheel

from dockers.rrs_radsurv_service.radlib.fw.flywheel_clients import uwhealthaz_client
from dockers.rrs_radsurv_service.radlib.fws.fws_image import FWSImageFileList, FWSImageFile, FWSImageType

root_path="z:/radiology/Groups/IDIAGroup/Data/_Brain/Radiology/_Adult/_Glioma/GBM_Cohort_brucegroup/"
mri_data="TCGA-GBM"
indir="DICOM_structuralMRI_fws"
outdir="nifti_raw"

input_path=os.path.join(root_path,mri_data,indir)
output_path=os.path.join(root_path,mri_data,outdir)

fw_client = uwhealthaz_client()
group_id = ''
project_label = "GBM Cohort"
subject_label = "RAD-AI-CNS-TUMOR-0001"

fw_subject_path = 'brucegroup/GBM Cohort/RAD-AI-CNS-TUMOR-0001'

def get_fw_files(fw_client, fw_path):
    list = FWSImageFileList()

    subject = fw_client.resolve(fw_path)['path'][-1]  # ['path'][-1]
    for session in subject.sessions():
        acquisition_path = f'{fw_path}/{session.label}/nifti_raw'
        try:
            ack = fw_client.resolve(acquisition_path)['path'][-1]
        except flywheel.rest.ApiException:
            continue

        for file in ack.files:
            file_path = f'{acquisition_path}/{file.name}'
            file_data = FWSImageFile(fw_client, fw_path=file_path)
            list[file.name] = file_data

    return list


def mri_data_check(file_list):
    for file_name, file_data in file_list.items():
        print(file_name)
        file = file_data.load_image(FWSImageType.nii)
        print(file)

selected_files = get_fw_files(fw_client, fw_subject_path)

mri_data_check(selected_files)

"""
for timepoint in timepoint_dirs:
    timepoint_path = os.path.join(patient_path, timepoint)
    nifti_files = [f for f in os.listdir(timepoint_path) if f.endswith('.nii.gz')]

    if not nifti_files:
        continue
    nifti_files = sorted(nifti_files)
    n_files = len(nifti_files)
    n_cols = min(3, n_files)
    n_rows = (n_files + n_cols - 1) // n_cols

    fig = plt.figure(figsize=(5 * n_cols, 5 * n_rows))


    def on_key(event, ax, img_data, title, voxel_dims):
        if event.key == 'up':
            ax.index = min(ax.index + 1, img_data.shape[2] - 1)
        elif event.key == 'down':
            ax.index = max(ax.index - 1, 0)

        ax.images[0].set_array(img_data[:, :, ax.index].T)
        ax.set_title(f'{title}\nSlice: {ax.index}/{img_data.shape[2] - 1}\nVoxel size: {voxel_dims:.2f}mm')
        fig.canvas.draw_idle()


    for idx, nifti_file in enumerate(nifti_files):
        ax = fig.add_subplot(n_rows, n_cols, idx + 1)

        file_path = os.path.join(timepoint_path, nifti_file)
        img = nib.load(file_path)
        data = img.get_fdata()

        # Get voxel dimensions
        voxel_dims = np.array(img.header.get_zooms())
        voxel_size_str = f"{voxel_dims[0]:.2f} x {voxel_dims[1]:.2f} x {voxel_dims[2]:.2f}"

        try:
            ax.index = data.shape[2] // 2
            ax.imshow(data[:, :, ax.index].T, cmap='gray')
            ax.set_title(f'{nifti_file}\nSlice: {ax.index}/{data.shape[2] - 1}\nVoxel size: {voxel_size_str}mm')

            fig.canvas.mpl_connect('key_press_event',
                                   lambda event, ax=ax, data=data, title=nifti_file, voxel_dims=voxel_size_str:
                                   on_key(event, ax, data, title, voxel_dims))
        except:
            continue

    plt.suptitle(f'Patient: {patient_id} - Timepoint: {timepoint}')
    plt.tight_layout()
    plt.show()
"""