import SimpleITK as sitk
import numpy as np
import glob
import sys
import os

root_folder = sys.argv[1]

for file_path in glob.glob(f'{root_folder}/*.nii.gz'):
    img = sitk.ReadImage(file_path)
    arr = sitk.GetArrayFromImage(img)
    print(os.path.basename(file_path), img.GetOrigin(), img.GetSpacing(), img.GetSize(), np.min(arr), np.mean(arr), np.max(arr))

