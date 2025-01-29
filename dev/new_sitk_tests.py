import glob
import numpy as np
import SimpleITK as sitk
from matplotlib import pyplot as plt

from dcm.dcm_loaders import load_dicom_series_sitk
from dcm.dcm_regridder import generate_image_projection, generate_grid, generate_volume_projection

dcm_root = '//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Research/ProstateSPORE/DODDatasetComplete/CleanedProject/prosspore/DODProjectRead'
pet_dcm_root = f'{dcm_root}/17009_pyl17/PET1/PET AC Prostate/dicom'
mr_dcm_root = f'{dcm_root}/17009_pyl17/PET1/Obl Axial T2 Prostate/dicom'

pet, _, _ = load_dicom_series_sitk(pet_dcm_root)
mr, _, _ = load_dicom_series_sitk(mr_dcm_root)
print("loaded!")
pet_grid = generate_grid(mr)
print("gridded!")
proj0 = generate_volume_projection(mr, pet_grid)
print("projected0!", np.min(proj0), np.mean(proj0), np.max(proj0))
proj1 = generate_volume_projection(mr, pet_grid, mode=sitk.sitkLinear)
print("projected1!", np.min(proj1), np.mean(proj1), np.max(proj1))
proj2 = generate_volume_projection(mr, pet_grid, mode=sitk.sitkNearestNeighbor)
print("projected2!", np.min(proj2), np.mean(proj2), np.max(proj2))
proj3 = generate_volume_projection(mr, pet_grid, mode=sitk.sitkBSplineResampler)
print("projected3!", np.min(proj3), np.mean(proj3), np.max(proj3))

diff12 = proj1-proj2
diff13 = proj1-proj3
diff23 = proj2-proj3

for diff in [diff12, diff13, diff23]:
    print(np.min(diff), np.mean(diff), np.std(diff), np.max(diff))

plt.subplot(1, 3, 1)
plt.imshow(proj1[12, :, :])
plt.subplot(1, 3, 2)
plt.imshow(proj2[12, :, :])
plt.subplot(1, 3, 3)
plt.imshow(proj3[12, :, :])
plt.show()
