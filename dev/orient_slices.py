import SimpleITK as sitk
import numpy as np
from scipy.ndimage import rotate
from dcm.dcm_loaders import load_dicom_series_pydicom
from regrid_3d import generate_slice_grid, generate_orthogonal_vectors, grid_resample_3d
import matplotlib.pyplot as plt



dcm_root1 = '/Users/carlkashuk/Downloads/flywheel/ProstateSPOREDemo/SUBJECTS/57/SESSIONS/03-19-05 9_59 AM/ACQUISITIONS/Recon 2_ WB CT SLICES/FILES/Recon 2_ WB CT SLICES'
dcm_root2 = '/Users/carlkashuk/Downloads/4 - TOP SAG SSFSE.dicom'

# slices1_pd, img1_pd, metadata1_pd = load_dicom_series_pydicom(dcm_root1)
slices2_pd, img2_pd, metadata2_pd = load_dicom_series_pydicom(dcm_root2)
img2_pd = np.rot90(img2_pd, 2, (0, 1))
img2_pd = np.rot90(img2_pd, 2, (1, 2))
# plt.imshow(img2_pd[:, :, 0])
# plt.show()
# exit()

iop = slices2_pd[0].ImageOrientationPatient
row_x = iop[0]
row_y = iop[1]
row_z = iop[2]
col_x = iop[3]
col_y = iop[4]
col_z = iop[5]

row_xa = np.arccos(row_x)
row_ya = np.arccos(row_y)
row_za = np.arccos(row_z)
col_xa = np.arccos(col_x)
col_ya = np.arccos(col_y)
col_za = np.arccos(col_z)

print(img2_pd.shape)
angle_x = np.rad2deg(row_xa)
angle_y = np.rad2deg(row_ya)
angle_z = np.rad2deg(row_za)
img2_pd_rot = rotate(img2_pd, angle=angle_x, axes = (1, 2), reshape=True)
img2_pd_rot = rotate(img2_pd_rot, angle=angle_y, axes = (0, 2), reshape=True)
img2_pd_rot = rotate(img2_pd_rot, angle=angle_z, axes = (0, 1), reshape=True)

sitk.WriteImage(sitk.GetImageFromArray(img2_pd), '/Users/carlkashuk/Documents/unrotated.nrrd')
sitk.WriteImage(sitk.GetImageFromArray(img2_pd_rot), '/Users/carlkashuk/Documents/rotated.nrrd')
print(img2_pd_rot.shape)
exit()

# origin1, axis1x, axis1y, axis1z = generate_slice_grid(slices1_pd)
# dist1x = np.diff(axis1x[:,0])
# dist1y = np.diff(axis1y[:,1])
# dist1z = np.diff(axis1z[:,2])
# spacing1 = [np.abs(np.mean(dist1x)), np.abs(np.mean(dist1y)), np.abs(np.mean(dist1z))]
# size1 = [len(axis1x), len(axis1y), len(axis1z)]

# origin1a, axis1xa, axis1ya, axis1za = generate_orthogonal_vectors(origin1, metadata1_pd['size'], metadata1_pd['spacing'])
origin2, axis2x, axis2y, axis2z = generate_slice_grid(slices2_pd)
size2 = [len(axis2x), len(axis2y), len(axis2z)]
# dist1x = np.diff(axis1x[:,0])
# dist1y = np.diff(axis1y[:,1])
# dist1z = np.diff(axis1z[:,2])
dist2x = np.diff(axis2x[:,0])
dist2y = np.diff(axis2y[:,1])
dist2z = np.diff(axis2z[:,2])

print(axis2x[:, 0])

spacing2 = [np.abs(np.mean(dist2x)), 0.06533213865664064, 0.06561899209960936]
origin2a, axis2xa, axis2ya, axis2za = generate_orthogonal_vectors(origin2, size2, spacing2)
exit()
dist1x = np.diff(axis1x[:,0])
dist1y = np.diff(axis1y[:,1])
dist1z = np.diff(axis1z[:,2])
print(np.min(dist1x), np.mean(dist1x), np.max(dist1x))
print(np.min(dist1y), np.mean(dist1y), np.max(dist1y))
print(np.min(dist1z), np.mean(dist1z), np.max(dist1z))
dist2x = np.diff(axis2x[:,0])
dist2y = np.diff(axis2y[:,1])
dist2z = np.diff(axis2z[:,2])
print(np.min(dist2x), np.mean(dist2x), np.max(dist2x))
print(np.min(dist2y), np.mean(dist2y), np.max(dist2y))
print(np.min(dist2z), np.mean(dist2z), np.max(dist2z))

fig = plt.figure()
ax = fig.add_subplot(projection='3d')

# ax.scatter3D(axis1x[:, 0], axis1x[:, 1], axis1x[:, 2], s=[5], marker='o', color=(1, 0.8, 0.8))
# ax.scatter3D(axis1y[:, 0], axis1y[:, 1], axis1y[:, 2], s=[10], marker='o', color=(1, 0.5, 0.5))
# ax.scatter3D(axis1z[:, 0], axis1z[:, 1], axis1z[:, 2], s=[15], marker='o', color=(1, 0.2, 0.2))
# ax.scatter3D(origin1[0], origin1[1], origin1[2], s=[15], marker='o', color=(0, 0, 0))

ax.scatter3D(axis2x[:, 0], axis2x[:, 1], axis2x[:, 2], s=[10], marker='o', color=(0.2, 0.7, 0.2))
ax.scatter3D(axis2y[:, 0], axis2y[:, 1], axis2y[:, 2], s=[10], marker='o', color=(0.5, 1, 0.5))
ax.scatter3D(axis2z[:, 0], axis2z[:, 1], axis2z[:, 2], s=[15], marker='o', color=(0.2, 1, 0.2))
ax.scatter3D(origin2[0], origin2[1], origin2[2], s=[15], marker='o', color=(0, 0, 0))

# ax.scatter3D(axis2xa[:, 0], axis2xa[:, 1], axis2xa[:, 2], s=[10], marker='o', color=(0.2, 0, 0.2))
# ax.scatter3D(axis2ya[:, 0], axis2ya[:, 1], axis2ya[:, 2], s=[10], marker='o', color=(0.5, 0, 0.5))
# ax.scatter3D(axis2za[:, 0], axis2za[:, 1], axis2za[:, 2], s=[15], marker='o', color=(0.2, 0, 0.2))

ax.scatter3D(axis2x[:, 0][::-1], axis2x[:, 1], axis2x[:, 2], s=[10], marker='o', color=(0.2, 0.2, 0.7))
# plt.show()
"""
# draw axes
ax.scatter3D(grid1yz0[:, 0], grid1yz0[:, 1], grid1yz0[:, 2], s=[5], marker='o', color=(1, 0.8, 0.8))
ax.scatter3D(grid1xz0[:, 0], grid1xz0[:, 1], grid1xz0[:, 2], s=[10], marker='o', color=(1, 0.5, 0.5))
ax.scatter3D(grid1xy0[:, 0], grid1xy0[:, 1], grid1xy0[:, 2], s=[15], marker='o', color=(1, 0.2, 0.2))

ax.scatter3D(grid1yzt[:, 0], grid1yzt[:, 1], grid1yzt[:, 2], s=[5], marker='o', color=(1, 0.8, 0.8))
ax.scatter3D(grid1xzt[:, 0], grid1xzt[:, 1], grid1xzt[:, 2], s=[10], marker='o', color=(1, 0.5, 0.5))
ax.scatter3D(grid1xyt[:, 0], grid1xyt[:, 1], grid1xyt[:, 2], s=[15], marker='o', color=(1, 0.2, 0.2))

ax.scatter3D(grid1y0zt[:, 0], grid1y0zt[:, 1], grid1y0zt[:, 2], s=[5], marker='o', color=(1, 0.8, 0.8))
ax.scatter3D(grid1x0zt[:, 0], grid1x0zt[:, 1], grid1x0zt[:, 2], s=[10], marker='o', color=(1, 0.5, 0.5))
ax.scatter3D(grid1x0yt[:, 0], grid1x0yt[:, 1], grid1x0yt[:, 2], s=[15], marker='o', color=(1, 0.2, 0.2))

ax.scatter3D(grid1ytz0[:, 0], grid1ytz0[:, 1], grid1ytz0[:, 2], s=[5], marker='o', color=(1, 0.8, 0.8))
ax.scatter3D(grid1xtz0[:, 0], grid1xtz0[:, 1], grid1xtz0[:, 2], s=[10], marker='o', color=(1, 0.5, 0.5))
ax.scatter3D(grid1xty0[:, 0], grid1xty0[:, 1], grid1xty0[:, 2], s=[15], marker='o', color=(1, 0.2, 0.2))

ax.scatter3D(origin1[0], origin1[1], origin1[2], s=[20], marker='X', color=(0, 0, 0))


ax.scatter3D(grid2yz0[:, 0], grid2yz0[:, 1], grid2yz0[:, 2], s=[5], marker='o', color=(1, 0.8, 0.8))
ax.scatter3D(grid2xz0[:, 0], grid2xz0[:, 1], grid2xz0[:, 2], s=[10], marker='o', color=(1, 0.5, 0.5))
ax.scatter3D(grid2xy0[:, 0], grid2xy0[:, 1], grid2xy0[:, 2], s=[15], marker='o', color=(1, 0.2, 0.2))

ax.scatter3D(grid2yzt[:, 0], grid2yzt[:, 1], grid2yzt[:, 2], s=[5], marker='o', color=(1, 0.8, 0.8))
ax.scatter3D(grid2xzt[:, 0], grid2xzt[:, 1], grid2xzt[:, 2], s=[10], marker='o', color=(1, 0.5, 0.5))
ax.scatter3D(grid2xyt[:, 0], grid2xyt[:, 1], grid2xyt[:, 2], s=[15], marker='o', color=(1, 0.2, 0.2))

ax.scatter3D(grid2y0zt[:, 0], grid2y0zt[:, 1], grid2y0zt[:, 2], s=[5], marker='o', color=(1, 0.8, 0.8))
ax.scatter3D(grid2x0zt[:, 0], grid2x0zt[:, 1], grid2x0zt[:, 2], s=[10], marker='o', color=(1, 0.5, 0.5))
ax.scatter3D(grid2x0yt[:, 0], grid2x0yt[:, 1], grid2x0yt[:, 2], s=[15], marker='o', color=(1, 0.2, 0.2))

ax.scatter3D(grid2ytz0[:, 0], grid2ytz0[:, 1], grid2ytz0[:, 2], s=[5], marker='o', color=(1, 0.8, 0.8))
ax.scatter3D(grid2xtz0[:, 0], grid2xtz0[:, 1], grid2xtz0[:, 2], s=[10], marker='o', color=(1, 0.5, 0.5))
ax.scatter3D(grid2xty0[:, 0], grid2xty0[:, 1], grid2xty0[:, 2], s=[15], marker='o', color=(1, 0.2, 0.2))

ax.scatter3D(origin2[0], origin2[1], origin2[2], s=[20], marker='X', color=(0, 0, 0))
"""

"""
print(len(axis1x), len(axis1y), len(axis1z), len(img1_pd), len(axis1xa), len(axis1ya), len(axis1za))
grid1_resampled = grid_resample_3d(axis1x[:, 0], axis1y[:,1], axis1z[:, 2], img1_pd, axis1xa[:, 0], axis1ya[:, 1], axis1za[:, 2])
grid1 = sitk.GetImageFromArray(img1_pd)
grid1.SetOrigin(origin1)
grid1.SetSpacing(spacing1)
sitk.WriteImage(grid1, '/Users/carlkashuk/Documents/grid1.nrrd')

grid1a = sitk.GetImageFromArray(grid1_resampled)
grid1a.SetOrigin(origin1a)
grid1a.SetSpacing(spacing1)
sitk.WriteImage(grid1a, '/Users/carlkashuk/Documents/grid1_resampled.nrrd')
"""

print("before", np.min(img2_pd), np.mean(img2_pd), np.max(img2_pd) )
img2_pd = np.swapaxes(img2_pd, 0, 2)
print("during", np.min(img2_pd), np.mean(img2_pd), np.max(img2_pd) )

grid2_resampled = grid_resample_3d(axis2x[:, 0][::-1], axis2y[:, 1], axis2z[:, 2], img2_pd, axis2xa[:, 0], axis2ya[:, 1], axis2za[:, 2])
print("after", np.min(grid2_resampled), np.mean(grid2_resampled), np.max(grid2_resampled) )
grid2 = sitk.GetImageFromArray(img2_pd)
grid2.SetOrigin(origin2)
grid2.SetSpacing(spacing2)
sitk.WriteImage(grid2, '/Users/carlkashuk/Documents/grid2.nrrd')
grid2a = sitk.GetImageFromArray(grid2_resampled)
grid2a.SetOrigin(origin2a)
grid2a.SetSpacing(spacing2)
sitk.WriteImage(grid2a, '/Users/carlkashuk/Documents/grid2_resampled.nrrd')


