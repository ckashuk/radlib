import glob
import pydicom
import matplotlib.pyplot as plt
import numpy as np

for file_path in glob.glob('C:/Users/CXK023/Downloads/1199 - Perfusion ROIs.dicom/*'):
    slice = pydicom.dcmread(file_path)
    print(slice.SeriesInstanceUID, slice.pixel_array.shape)

    plt.subplot(1, 3, 1)
    plt.imshow(slice.pixel_array[:, :, 0])

    plt.subplot(1, 3, 2)
    plt.imshow(slice.pixel_array[:, :, 1])

    plt.subplot(1, 3, 3)
    plt.imshow(slice.pixel_array[:, :, 1])

    diff12 = slice.pixel_array[:, :, 1] - slice.pixel_array[:, :, 0]
    diff23 = slice.pixel_array[:, :, 2] - slice.pixel_array[:, :, 1]
    diff13 = slice.pixel_array[:, :, 2] - slice.pixel_array[:, :, 0]

    for diff in diff12, diff23, diff13:
        print(np.min(diff), np.mean(diff), np.max(diff))
    plt.show()
