import SimpleITK as sitk
import numpy as np

from pydicom_generate.dcm.dcm_loaders import load_dicom_series_pydicom
from regrid_3d import generate_slice_grid, grid_resample_3d_new

dcm_root1 = 'H:/data/A18GEProstate_00007_test/3 - Obl Ax T2.dicom'

slices1_pd, img1_pd, metadata1_pd = load_dicom_series_pydicom(dcm_root1)
grid1 = generate_slice_grid(slices1_pd)
img1_pd = img1_pd[100:109, 100:109, 0:5]
grid1 = grid1[100:109, 100:109, 0:5, :]
img1_new = grid_resample_3d_new(grid1, img1_pd, grid1, mode='nearest')
grid1a = generate_slice_grid(img1_new)
diff = img1_new - img1_pd
print(np.min(diff), np.mean(diff), np.max(diff))
diff2 = grid1 - grid1a
print(np.min(diff2), np.mean(diff2), np.max(diff2))
exit()

tmp_points = grid1[100:109, 100:109, 100:109]
tmp_volume = img1_pd[100:109, 100:109, 100:109]

exit()

grid1_new = grid1
img1_pd = img1_pd

img1_new = grid_resample_3d_new(grid1, img1_pd, grid1, mode='nearest')

print(img1_new.shape)

diff = img1_pd - img1_new
print(np.min(diff), np.mean(diff), np.max(diff))

img1_old = sitk.GetImageFromArray(img1_pd)
sitk.WriteImage(img1_old, 'h://data/img1_old.nrrd')
img1_new = sitk.GetImageFromArray(img1_new)
sitk.WriteImage(img1_new, 'h://data/img1_new.nrrd')
