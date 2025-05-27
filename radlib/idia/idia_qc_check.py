import glob
import os
import json
import pandas as pd
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np


def detect_view_orientation(data, affine):
    """
    Automatically detect the view orientation based on image characteristics and affine matrix.

    Args:
        data (np.ndarray): The image data
        affine (np.ndarray): The affine transformation matrix from the NIfTI file

    Returns:
        str: Detected view ('axial', 'sagittal', or 'coronal')
    """
    # Get the absolute values of the affine matrix orientation components
    abs_affine = np.abs(affine[:3, :3])

    # Find the primary axis of each dimension
    primary_axes = np.argmax(abs_affine, axis=0)

    # In medical imaging conventions:
    # - X axis is typically Left-Right
    # - Y axis is typically Anterior-Posterior
    # - Z axis is typically Superior-Inferior

    # Check the orientation based on the third axis (slice direction)
    slice_axis = primary_axes[2]

    if slice_axis == 2:  # If Z axis is dominant in the third dimension
        return 'axial'
    elif slice_axis == 0:  # If X axis is dominant in the third dimension
        return 'sagittal'
    else:  # If Y axis is dominant in the third dimension
        return 'coronal'


def plot_mri_files(nifti_files, patient_id, timepoint, timepoint_path):
    """
    Plot MRI files with automatically detected view orientation.

    Args:
        nifti_files (list): List of NIFTI files to display
        patient_id (str): Patient identifier
        timepoint (str): Timepoint identifier
        timepoint_path (str): Path to the NIFTI files
    """
    nifti_files = sorted(nifti_files)
    n_files = len(nifti_files)
    n_cols = min(3, n_files)
    n_rows = (n_files + n_cols - 1) // n_cols

    fig = plt.figure(figsize=(5 * n_cols, 5 * n_rows))

    def get_slice_data(data, index, view):
        if view == 'axial':
            return data[:, :, index].T
        elif view == 'sagittal':
            return data[index, :, :].T
        elif view == 'coronal':
            return data[:, index, :].T

    def get_max_index(data, view):
        if view == 'axial':
            return data.shape[2]
        elif view == 'sagittal':
            return data.shape[0]
        elif view == 'coronal':
            return data.shape[1]

    for idx, nifti_file in enumerate(nifti_files):
        ax = fig.add_subplot(n_rows, n_cols, idx + 1)

        file_path = os.path.join(timepoint_path, nifti_file)
        img = nib.load(file_path)
        data = img.get_fdata()

        # Automatically detect view orientation
        view = detect_view_orientation(data, img.affine)

        # Get voxel dimensions
        voxel_dims = np.array(img.header.get_zooms())
        voxel_size_str = f"{voxel_dims[0]:.2f} x {voxel_dims[1]:.2f} x {voxel_dims[2]:.2f}"

        # Set initial slice index
        ax.index = get_max_index(data, view) // 2

        # Display initial slice
        ax.imshow(get_slice_data(data, ax.index, view), cmap='gray')
        max_index = get_max_index(data, view) - 1
        ax.set_title(f'{nifti_file}\n{view.capitalize()} Slice: {ax.index}/{max_index}\nVoxel size: {voxel_size_str}mm')

    plt.suptitle(f'Patient: {patient_id} - Timepoint: {timepoint}')
    plt.tight_layout()
    plt.show()
