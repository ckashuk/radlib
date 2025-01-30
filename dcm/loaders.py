import pydicom
import numpy as np
import matplotlib.pyplot as plt
import glob
import SimpleITK as sitk

# load the DICOM files
# from https://pydicom.github.io/pydicom/stable/auto_examples/image_processing/reslice.html#sphx-glr-auto-examples-image-processing-reslice-py
def debug_print(message, debug_flag):
    # TODO: csk add code to print to file, html, etc to make it more useful
    if debug_flag:
        print(message)

def load_dicom_series_pydicom(dicom_root, debug=False):
    # TODO: csk add support for multiple series in one folder
    files = []
    if not '*' in dicom_root:
        dicom_root = f'{dicom_root}/*'
    debug_print(f"glob: {dicom_root}", debug)
    for fname in glob.glob(dicom_root, recursive=False):
        debug_print(f"loading: {fname}", debug)
        files.append(pydicom.dcmread(fname))

    debug_print(f"file count: {len(files)}", debug)

    # skip files with no SliceLocation (eg scout views)
    slices = []
    skipcount = 0
    for f in files:
        if hasattr(f, "SliceLocation"):
            slices.append(f)
        else:
            skipcount = skipcount + 1

    debug_print(f"skipped, no SliceLocation: {skipcount}", debug)
    return load_dicom_series_from_slices(slices)


def load_dicom_series_from_slices(slices):
    # ensure they are in the correct order
    slices = sorted(slices, key=lambda s: s.SliceLocation)

    # pixel aspects, assuming all slices are the same
    # TODO: csk add "real" slice thickness from z positions, also add ImageOrientationPatient
    ps = slices[0].PixelSpacing
    ss = slices[0].SliceThickness

    # create 3D array
    img_shape = list(slices[0].pixel_array.shape)
    img_shape.append(len(slices))
    img3d = np.zeros(img_shape)

    # fill 3D array with the images from the files
    for i, s in enumerate(slices):
        img2d = s.pixel_array
        # csk add slope/intercept handling
        if s.get('RescaleSlope') is not None:
            img2d = np.add(np.multiply(img2d, s.RescaleSlope), s.RescaleIntercept)
        img3d[:, :, i] = img2d

    img3d = np.array(img3d)

    metadata={'spacing': np.array([ps[0], ps[1], ss]),
              'origin': np.array(slices[0].ImagePositionPatient),
              'direction': np.array(slices[0].ImageOrientationPatient),
              'size': np.array(img_shape)}
    return img3d, metadata, slices

def load_dicom_series_sitk(dicom_root, debug=False):
    reader = sitk.ImageSeriesReader()
    dicom_paths = reader.GetGDCMSeriesFileNames(dicom_root)
    reader.SetFileNames(dicom_paths)
    image_sitk = reader.Execute()

    # TODO: this is mainly for comparisons
    img3d = sitk.GetArrayFromImage(image_sitk)
    img3d = np.transpose(img3d, (1, 2, 0))
    metadata={'spacing': image_sitk.GetSpacing(),
              'origin': image_sitk.GetOrigin(),
              'direction': image_sitk.GetDirection(),
              'size': image_sitk.GetSize()}

    return image_sitk, img3d, metadata


def plot_orthagonal_slices(img3d, metadata):
    # plot 3 orthogonal slices
    ps = metadata['spacing'][0:2]
    ss = metadata['spacing'][2]
    img_shape = metadata['size']
    ax_aspect = ps[1] / ps[0]
    sag_aspect = ps[1] / ss
    cor_aspect = ss / ps[0]

    a1 = plt.subplot(1, 3, 1)
    img2d_axial = img3d[:, :, img_shape[2] // 2]
    plt.imshow(img2d_axial)
    a1.set_aspect(ax_aspect)

    a2 = plt.subplot(1, 3, 2)
    img2d_sagittal = np.rot90(img3d[:, img_shape[1] // 2, :].T, 2)
    plt.imshow(img2d_sagittal)
    a2.set_aspect(1/sag_aspect)

    a3 = plt.subplot(1, 3, 3)
    img2d_coronal = np.rot90(img3d[img_shape[0] // 2, :, :].T, 2)
    plt.imshow(img2d_coronal)
    a3.set_aspect(cor_aspect)

    plt.show()
