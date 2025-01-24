import glob
import random
import nrrd

import pydicom

import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

import SimpleITK as sitk

import numpy as np
from matplotlib import pyplot as plt

from pydicom_generate.dcm.dcm_loaders import load_dicom_series_sitk, load_dicom_series_from_slices, \
    load_dicom_series_pydicom
from regrid_3d import volume_value


def get_sitk_index_grid(image):
    grid = np.zeros([image.GetSize()[0], image.GetSize()[1], image.GetSize()[2], 3])
    for x in range(0, image.GetSize()[0]):
        for y in range(0, image.GetSize()[1]):
            for z in range(0, image.GetSize()[2]):
                grid[x, y, z] = (x, y, z)

    return grid

def get_sitk_physical_grid(image):
    grid = np.zeros([image.GetSize()[0], image.GetSize()[1], image.GetSize()[2], 3])
    for z in range(0, image.GetSize()[2]):
        for y in range(0, image.GetSize()[1]):
            for x in range(0, image.GetSize()[0]):
                phys = image.TransformIndexToPhysicalPoint((x, y, z))
                ind = image.TransformPhysicalPointToIndex(phys)
                if x != ind[0] or y != ind[1] or z != ind[2]:
                    print("phys error!", x, y, z, phys, ind)
                grid[x ,y, z] = phys
        # if z < 5:
        # print(phys[2])
    return grid

def get_sitk_physical_grid_from_index_grid(image, index_grid):
    grid = np.zeros((index_grid.shape[0], index_grid.shape[1], index_grid.shape[2], 3))
    for x in range(0, index_grid.shape[0]):
        for y in range(0, index_grid.shape[1]):
            for z in range(0, index_grid.shape[2]):
                phys = image.TransformIndexToPhysicalPoint((x, y, z))
                ind = image.TransformPhysicalPointToIndex(phys)
                if x != ind[0] or y != ind[1] or z != ind[2]:
                    print("index to phys error!", x, y, z, phys, ind)

    return grid

def generate_regular_grid(image, xlen, ylen, zlen):

    print("generate_regular_grid", xlen, ylen, zlen, image.GetOrigin(), image.GetSpacing(), image.GetSpacing())
    grid = np.zeros((xlen, ylen, zlen, 3))
    for k in range(0, zlen):
        for j in range(0, ylen):
            for i in range(0, xlen):
                grid[i, j, k, 0] = image.GetOrigin()[0] + i * image.GetSpacing()[0]
                grid[i, j, k, 1] = image.GetOrigin()[1] + j * image.GetSpacing()[1]
                grid[i, j, k, 2] = image.GetOrigin()[2] + k * image.GetSpacing()[2]
        # if k < 5:
        # print(grid[i, j, k, 2])

    return grid

def get_minmax(grid, index):
    minn = np.min(grid[:, :, :, index])
    maxx = np.max(grid[:, :, :, index])
    delta = maxx - minn
    print("get_minmax", index, minn, maxx, delta)
    return minn, maxx, delta

def get_box(grid):
    xmin, xmax, xlen = get_minmax(grid, 0)
    ymin, ymax, ylen = get_minmax(grid, 1)
    zmin, zmax, zlen = get_minmax(grid, 2)

    box = np.array([
        [xmin, ymin, zmin],
        [xmax, ymin, zmin],
        [xmin, ymax, zmin],
        [xmax, ymax, zmin],
        [xmin, ymin, zmax],
        [xmax, ymin, zmax],
        [xmin, ymax, zmax],
        [xmax, ymax, zmax]
    ])

    return box

def get_sitk_index_grid_from_physical_grid(image, physical_grid):
    grid = np.zeros((physical_grid.shape[0], physical_grid.shape[1], physical_grid.shape[2], 3))
    for x in range(0, physical_grid.shape[0]):
        for y in range(0, physical_grid.shape[1]):
            for z in range(0, physical_grid.shape[2]):
                grid[x, y, z] = image.TransformPhysicalPointToIndex(physical_grid[x, y, z])
                if x != grid[x, y, z, 0] or y != grid[x, y, z, 1]  or z != grid[x, y, z, 2]:
                    print("phys to index Error!", x, y, z, physical_grid[x, y, z], grid[x, y, z])
    return grid

img_root = 'h://data/fivebyfive'
img_files = [f'{img_root}/slice10.dcm', f'{img_root}/slice11.dcm',
             f'{img_root}/slice12.dcm', f'{img_root}/slice13.dcm', f'{img_root}/slice14.dcm']
img1_files = glob.glob('H:/data/SPORE_P11_test/SPORE_P11_images/PET1/Obl Axial T2 Prostate/dicom/*.dcm')
img2_files = glob.glob('H:/data/SPORE_P11_test/SPORE_P11_images/PET1/PET AC Prostate/dicom/*.dcm')
img1 = sitk.ReadImage(img1_files)
img2 = sitk.ReadImage(img2_files)
img3 = sitk.ReadImage(img_files)
img4 = sitk.ReadImage(img_files)
dir = img1.GetDirection()
img4.SetDirection(img1.GetDirection())

print(img3.GetOrigin(), img3.GetSpacing(), img3.GetSize())
print(img3.GetDirection())
print(img4.GetOrigin(), img4.GetSpacing(), img4.GetSize())
print(img4.GetDirection())

points1 = np.zeros((5, 5, 5, 4))
points2 = np.zeros((5, 5, 5, 4))
for x in [0, 1, 2, 3, 4]:
    for y in [0, 1, 2, 3, 4]:
        for z in [0, 1, 2, 3, 4]:
            phys1 = img3.TransformIndexToPhysicalPoint((x, y, z))
            phys2 = img4.TransformIndexToPhysicalPoint((x, y, z))
            points1[x, y, z, 0] = phys1[0]
            points1[x, y, z, 1] = phys1[1]
            points1[x, y, z, 2] = phys1[2]
            points1[x, y, z, 3] = img3.GetPixel((x, y, z))
            points2[x, y, z, 0] = phys2[0]
            points2[x, y, z, 1] = phys2[1]
            points2[x, y, z, 2] = phys2[2]
            points2[x, y, z, 3] = img4.GetPixel((x, y, z))

            ind1 = img3.TransformPhysicalPointToIndex(phys1)
            ind2 = img4.TransformPhysicalPointToIndex(phys2)


fig = plt.figure()
ax = fig.add_subplot(projection='3d')

rval = 1
for z in range(0, points1.shape[2]-1):
    for y in range(0, points1.shape[1] - 1):
        for x in range(0, points1.shape[0] - 1):
            point = img3.TransformIndexToPhysicalPoint((x, y, z))
            point1 = points1[x, y, z, 0:3]
            point2 = img3.TransformPhysicalPointToIndex(point)
            val1 = points1[x, y, z, 3]
            val = img3.GetPixel((x, y, z))
            # print(x, y, z, point2, point, point1, val, val1)
            ax.scatter3D(point[0], point[1], point[2], s=[1000], marker='o', color=(z/5, 0, 0))

"""
for z in range(0, points2.shape[2]-1):
    for y in range(0, points2.shape[1] - 1):
        for x in range(0, points2.shape[0] - 1):
            point = img4.TransformIndexToPhysicalPoint((x, y, z))
            point1 = points1[x, y, z, 0:3]
            point2 = img4.TransformPhysicalPointToIndex(point)
            val1 = points1[x, y, z, 3]
            val = img4.GetPixel((x, y, z))
            # print(x, y, z, point2, point, point1, val, val1)
            ax.scatter3D(point[0], point[1], point[2], s=[1000], marker='o', color=(0, 0, z/5))

plt.show()
exit()
"""



rval = 1
for z in range(0, len(z2)-1):
    ax.scatter3D(x2, y2, z2, s=[10], marker='o', color=(0, 0, rval))
    rval -= 0.1
    if rval < 0:
        rval = 1

plt.show()
exit()
# img1_root = 'H:/data/4 - TOP SAG SSFSE.dicom/*.dcm'
img1_root = 'H:/data/SPORE_P11_test/SPORE_P11_images/PET1/Obl Axial T2 Prostate/dicom/*.dcm'
# img1_root = 'H:/data/dcm_qa_ct-master/dcm_qa_ct-master/In/GE/*.dcm'
img2_root = 'H:/data/SPORE_P11_test/SPORE_P11_images/PET1/PET AC Prostate/dicom/*.dcm'

# img1_root = '//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Research/TCIA/manifest-xxn3N2Qq630907925598003437/PREVSRCTStruct/Allen^Ezra/20151123/null/CT/*.dcm'

img1_slice_files = glob.glob(img1_root)
img2_slice_files = glob.glob(img2_root)

for f, file in enumerate(img1_slice_files):
    img = sitk.ReadImage(file)
    img1a = img[300:305, 300:305]
    # for key in img.GetMetaDataKeys():
    #     val = img.GetMetaData(key)
    #     img1a.SetMetaData(key, val)
    sitk.WriteImage(img1a, f'H://data/fivebyfive/slice{f}.dcm')
exit()

img1, vox1, meta1 = load_dicom_series_sitk(img1_root.replace("*.dcm", ""), debug=False)
vox1a, meta1a, slices1a = load_dicom_series_pydicom(img1_root.replace("*.dcm", ""), debug=False)

for s, slice in enumerate(slices1a):
    slice.pixel_array = slice.pixel_array[5, 5]
    pydicom.dcmwrite(f'H://data/fivebyfive/slice{s}.dcm', slice)
exit()

# img1a, _, _ = load_dicom_series_from_slices(load_dicom_series_pydicom())
img2, _, _ = load_dicom_series_sitk(img2_root.replace("*.dcm", ""), debug=False)
print(img1.GetOrigin(), img1.GetSpacing(), img1.GetSize(), img1.GetDirection())
phys_grid = get_sitk_physical_grid(img1)


img1_old = sitk.GetImageFromArray(vox1)
img1_old.SetOrigin(img1.GetOrigin())
img1_old.SetSpacing(img1.GetSpacing())
img1_old.SetDirection(img1.GetDirection())
sitk.WriteImage(img1_old, 'h://data/img1_old.nrrd')

zmin, zmax, zlen = get_minmax(phys_grid, 2)

zd = int(zlen/img1.GetSpacing()[2])


print("phys", phys_grid.shape)
new_grid = generate_regular_grid(img1, phys_grid.shape[0], phys_grid.shape[1], zd)  #phys_grid.shape[2])
print("new", new_grid.shape)

physx = phys_grid[::20, ::20, ::2, 0]
physy = phys_grid[::20, ::20, ::2, 1]
physz = phys_grid[::20, ::20, ::2, 2]

newx = new_grid[::20, ::20, ::2, 0]
newy = new_grid[::20, ::20, ::2, 1]
newz = new_grid[::20, ::20, ::2, 2]


fig = plt.figure()
ax = fig.add_subplot(projection='3d')
rval = 1
for z in range(0, physz.shape[2]-1):
    print(z, rval, physz.shape)
    ax.scatter3D(physx[:, :, z], physy[:, :, z], physz[:, :, z], s=[10], marker='o', color=(rval, 0, 0))
    ax.scatter3D(newx[:, :, z], newy[:, :, z], newz[:, :, z], s=[10], marker='o', color=(0, 0, rval))
    rval -= 0.1
    if rval < 0:
        rval = 1

plt.show()

"""
print(vox1.shape)
print(new_grid.shape)
# print(">>>", volume1[51, 51, 12])
new_volume1 = np.zeros((new_grid.shape[0], new_grid.shape[1], new_grid.shape[2]))
for z in range(0, new_grid.shape[2]):
    for y in range(0, new_grid.shape[1]):
        for x in range(0, new_grid.shape[0]):
            res = img1.TransformPhysicalPointToContinuousIndex(new_grid[x, y, z])
            val = volume_value(vox1, np.array(res))
            new_volume1[x, y, z] = val

img1_new = sitk.GetImageFromArray(new_volume1)
img1_new.SetOrigin(img1.GetOrigin())
img1_new.SetSpacing(img1.GetSpacing())
sitk.WriteImage(img1_new, 'h://data/img1_new.nrrd')
exit()
"""
