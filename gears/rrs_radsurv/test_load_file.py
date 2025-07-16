from zipfile import ZipFile
import os
import tempfile
import shutil
import glob
import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
import pydicom

from sample_files.fws_utils import pet_suv_factor, load_image_from_local_path

# path0 = 'H:/data/1.2.840.113619.2.363.218786664.1531252487.973562.dcm'
# path1 = 'H:/data/1.2.840.113619.2.363.218786664.1531252488.24888.dcm'

path0 = 'H:/data/1.2.840.113619.2.363.10499743.3637188.17917.1531224814.29.dcm'
path1 = 'H:/data/1.2.840.113619.2.363.10499743.3637188.17917.1531224814.30.dcm'

img0 = sitk.ReadImage(path0)
img1 = sitk.ReadImage(path1)
img2 = sitk.ReadImage([path0, path1])

print(img0.GetOrigin(), img0.GetSpacing(), img0.GetDirection(), img0.GetSize())
print(img1.GetOrigin(), img1.GetSpacing(), img1.GetDirection(), img1.GetSize())
print(img2.GetOrigin(), img2.GetSpacing(), img2.GetDirection(), img2.GetSize())
exit()

tmp = load_image_from_local_path('C:/Users/CXK023/Downloads/prostatespore/csk test project/17009_Pyl11/pathology linkage test/PET1/PET AC Prostate.zip')
print(tmp.GetSize())

img = sitk.GetArrayFromImage(tmp)
for i in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
    plt.subplot(3, 3, i)
    print(np.min(img), np.max(img))
    plt.imshow(img[:, :, 10*i-10], vmin=0, vmax=5)  # np.min(img), vmax=np.max(img))

plt.show()

tmp = load_image_from_local_path('//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Users/Carl/regrid_tests/P01_obl_regrid.nii.gz')
print(tmp.GetSize())

img = sitk.GetArrayFromImage(tmp)
for i in range(1, 89):
    plt.subplot(10, 10, i)
    print(np.min(img), np.max(img))
    plt.imshow(img[:, :, i], vmin=np.min(img), vmax=np.max(img))

plt.show()