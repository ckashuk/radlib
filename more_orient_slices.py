import numpy as np
import scipy
from matplotlib import pyplot as plt

from pydicom_generate.dcm.dcm_loaders import load_dicom_series_pydicom, load_dicom_series_sitk
from regrid_3d import generate_slice_grid, generate_orthogonal_vectors, grid_resample_3d_new
import SimpleITK as sitk
dcm_root1 = 'H:/data/A18GEProstate_00007_test/3 - Obl Ax T2.dicom'
# dcm_root2 = 'H:/data/A18GEProstate_00007_test/6 - Obl Cor T2.dicom'

def get_minmax(grid, axis=0):
    min = np.min(grid[:, :, :, axis])
    max = np.max(grid[:, :, :, axis])

    return min, max

def get_minmax_grid(grid, gridx=1, gridy=1, gridz=1):
    # minx, maxx = get_minmax(grid, 0)
    # miny, maxy = get_minmax(grid, 1)
    # minz, maxz = get_minmax(grid, 2)
    minx = np.mean(grid[0, :, :, 0])
    maxx = np.mean(grid[-1, :, :, 0])

    miny = np.mean(grid[:, 0, :, 1])
    maxy = np.mean(grid[:, -1, :, 1])

    minz = np.mean(grid[:, :, 0, 2])
    maxz = np.mean(grid[:, :, -1, 2])

    dx = (maxx-minx)/gridx
    if dx == 0:
        dx = 1
    dy = (maxy-miny)/grid
    
    dz = (maxz-minz)/gridz

    print(maxx-minx, maxy-miny, maxz-minz)

    points = []
    for x in np.arange(minx, maxx+dx, dx):
        for y in np.arange(miny, maxy+dy, dy):
            for z in np.arange(minz, maxz+dz, dz):
                points.append([x, y, z])
    points = np.array(points)

    return points

slices1_pd, img1_pd, metadata1_pd = load_dicom_series_pydicom(dcm_root1)
# slices2_pd, img2_pd, metadata2_pd = load_dicom_series_pydicom(dcm_root2)

grid1 = generate_slice_grid(slices1_pd)[100:101, 100:101, 0:1]
grid1_new = grid1
# grid2 = generate_slice_grid(slices2_pd)
img1_pd = img1_pd[100:101, 100:101, 0:1]

img1_pd = img1_pd[::2, ::2, ::2]
grid1 = grid1[::2, ::2, ::2, :]

x = grid1[:, :, :, 0]
y = grid1[:, :, :, 1]
z = grid1[:, :, :, 2]

minmax_box = get_minmax_grid(grid1)

minmax_x = minmax_box[:, 0]
minmax_y = minmax_box[:, 1]
minmax_z = minmax_box[:, 2]

fig = plt.figure()
ax = fig.add_subplot(projection='3d')

ax.scatter3D(x, y, z, s=[10], marker='o', color=(1, 0, 0))
ax.scatter3D(minmax_x, minmax_y, minmax_z, s=[10], marker='o', color=(0, 0, 1))

# ax.scatter3D(axis1y[:, 0], axis1y[:, 1], axis1y[:, 2], s=[10], marker='o', color=(1, 0.5, 0.5))
# ax.scatter3D(axis1z[:, 0], axis1z[:, 1], axis1z[:, 2], s=[15], marker='o', color=(1, 0.2, 0.2))
# ax.scatter3D(origin1[0], origin1[1], origin1[2], s=[15], marker='o', color=(0, 0, 0))

plt.show()
exit()

min_x, max_x = get_minmax(grid1, 0)
min_y, max_y = get_minmax(grid1, 1)
min_z, max_z = get_minmax(grid1, 2)

print(grid1.shape)
print(min_x, max_x)
print(min_y, max_y)
print(min_z, max_z)

img1_new = grid_resample_3d_new(grid1, img1_pd, grid1_new)

print(img1_pd.shape)
print(img1_new.shape)
print()

print(img1_pd)
print()
print(img1_new)

diff = img1_pd - img1_new

print(np.min(diff), np.mean(diff), np.max(diff))
