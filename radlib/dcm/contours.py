import numpy as np
import pydicom
from numpy import ma
from scipy import ndimage
from skimage import draw, measure


def parse_volume_parameters(origin: np.ndarray = None,
                            directions: np.ndarray = None,
                            sizes: np.ndarray = None,
                            nrrd_header: dict = None):
    """
    Get the 'big three': origin, directions, sizes from nrrd, dicom, or other metadata sources.

    Usually used in functions where initial values are passed in and/or a Nrrd-style header is included.
    Default to [0, 0, 0] origin and [[1, 0, 0], [0, 1, 0], [0, 0, 1]] direction if not found via the inputs.

    Parameters:
    -----------
    origin: array-like of float
        The initial origin in image space
    directions: array-like of float
        The initial directions (voxel dimensions) in image space (3x3)
    sizes: array-like of float
        The shape of the voxel matrix
    nrrd_header: Dictionary
        A dictionary of image metadata. 'space origin', 'space directions', and 'sizes' would be parsed
        from here

    Returns
    -------
    ndarray of float
        The origin in image space
    ndarray of float
        The directions (voxel dimensions) in image space
    ndarray of int
        The shape of the voxel matrix

    """
    # parse from Nrrd header if not passed in
    if nrrd_header is not None:
        if origin is None:
            origin = nrrd_header['space origin']
        if directions is None:
            directions = nrrd_header['space directions']
        if sizes is None:
            sizes = nrrd_header['sizes']

    # set defaults if still not found
    if origin is None:
        origin = [0.0, 0.0, 0.0]
    if directions is None:
        directions = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    if sizes is None:
        sizes = [100, 100, 100]  # hopefully you can get a better estimate later!

    # make sure directions is an array because python gets crabby about multidimensional lists
    directions = np.asarray(directions)


def voxel_to_image(voxel: np.ndarray,
                   origin: np.ndarray = None,
                   directions: np.ndarray = None,
                   sizes: np.ndarray = None,
                   nrrd_header: dict = None,
                   reverse_z: bool = False):
    """
    Convert from voxel (index) to image (physical) space coordinates

    Parameters
    ----------

    voxel : array-like of float
        The point to convert in voxel space, [x, y, z]
    origin : array-like of float, optional
        The origin of the matrix in image space [ox, oy, oz]
    directions : array-like of float, optional
        The directions of the matrix in image space, 3x3 (TODO: handle rotation)
    sizes : array-like of float
        The shape of the matrix
    nrrd_header : Dictionary
        Get origin, directions, and sizes from nrrd header dictionary
    reverse_z: bool
        Reverse the slices relative to the origin

    Returns
    -------
    array-like of float
        The converted point in image space [x, y, z]

    """

    # image parameters
    origin, directions, sizes = parse_volume_parameters(origin, directions, sizes, nrrd_header)

    # directions is 2D, make sure it is an array
    directions = np.asarray(directions)

    # transform
    xf = (origin[0] + directions[0, 0] * voxel[0])
    yf = (origin[1] + directions[1, 1] * voxel[1])
    z = (sizes[2] - voxel[2]) if reverse_z else voxel[2]
    zf = origin[2] + directions[2, 2] * z

    return [xf, yf, zf]


def image_to_voxel(point: np.ndarray,
                   origin: np.ndarray = None,
                   directions: np.ndarray = None,
                   sizes: np.ndarray = None,
                   nrrd_header: np.ndarray = None):
    """
    Convert from image (physical) space to voxel (index)

    Parameters
    ----------

    point : array-like of float
        The point to convert in image space, [x, y, z]
    origin : array-like of float, optional
        The origin of the matrix in image space [ox, oy, oz]
    directions : array-like of float, optional
        The directions of the matrix in image space, 3x3 (TODO: handle rotation)
    sizes : array-like of float
        The shape of the matrix
    nrrd_header : Dictionary
        Get origin, directions, and sizes from nrrd header dictionary

    Returns
    -------
    array-like of float
        The converted voxel in index space [x, y, z]

    Notes
    -----
    This function can return negative indexes to denote points that are not within a given matrix!

    """

    # image parameters
    origin, directions, sizes = parse_volume_parameters(origin, directions, sizes, nrrd_header=nrrd_header)

    # directions is 2D, make sure it is an array
    directions = np.asarray(directions)
    if len(directions.shape) == 1:
        directions3d = np.zeros((3, 3))
        directions3d[0][0] = directions[0]
        directions3d[1][1] = directions[1]
        directions3d[2][2] = directions[2]
        directions = directions3d

    # transform
    xf = int(round((point[0] - origin[0]) / directions[0, 0]))
    yf = int(round((point[1] - origin[1]) / directions[1, 1]))
    zf = int(round((point[2] - origin[2]) / directions[2, 2]))

    return [xf, yf, zf]


def pydicom_to_contours(data_set: pydicom.Dataset):
    """
    Convert a pydicom sequence of contours (MultiValue) into a dictionary of lists of arrays (double)

    Parameters
    ----------
    data_set : Dataset
        Pydicom data structure containing a series of contours

    Returns
    -------
    Dictionary of ndarray of ndarray
        Dictionary indexed by ROI of contour lists, each contour list is a list of sets of contour points

    """

    # output
    contours = dict()

    # for each contour set
    for contourSequence in data_set.ROIContourSequence:
        roi = contourSequence.ReferencedROINumber
        if roi in contours:
            contour_list = contours.get(roi)
        else:
            contour_list = list()
            contours[roi] = contour_list

        # each ROI can have one or more contours, which each has one or more points associated with it
        for roiContour in contourSequence.ContourSequence:
            contour_data = roiContour.ContourData
            contour_array = []
            for value in contour_data:
                contour_array.append(float(value))
            contour_list.append(contour_array)

    return contours


def max_voxel_for_contours(contour_list,
                           origin: np.ndarray,
                           directions: np.ndarray):
    """
    Given a contour list in image space, and image parameters, find the largest 3D point in voxel space

    Parameters
    ----------
    contour_list : ndarray of ndarray of float
        Data for a set of contours, each ROI has a list, each list contains a 1-dimensional array of x, y, z points.
    origin : ndarray of float
        The origin of the contour list in image space
    directions : ndarray of float
        The directions (dimensions) of voxels in image space

    Returns
    -------
    ndarray of floats
        1x3 dimensional array of the maximum voxel index for all three dimensions

    """
    # return value
    voxel_max = [0, 0, 0]

    # for each ROI
    for roi in contour_list:
        contours = contour_list.get(roi)
        for contour in contours:
            # get max point for this contour
            xm = np.max(contour[0::3])
            ym = np.max(contour[1::3])
            zm = np.max(contour[2::3])

            # store current max for the whole set
            contour_voxel_max = image_to_voxel(np.asarray((xm, ym, zm)), origin, directions)
            if contour_voxel_max[0] >= voxel_max[0]:
                voxel_max[0] = contour_voxel_max[0] + 1
            if contour_voxel_max[1] >= voxel_max[1]:
                voxel_max[1] = contour_voxel_max[1] + 1
            if contour_voxel_max[2] >= voxel_max[2]:
                voxel_max[2] = contour_voxel_max[2] + 1

    return voxel_max


def parameters_for_contours(contour_list):
    """
    Given a contour list in image space, find parameters for the enclosing volume

    Parameters
    ----------
    contour_list : ndarray of ndarray of float
        Data for a set of contours, each ROI has a list, each list contains a 1-dimensional array of x, y, z points.

    Returns
    -------
    ndarrays of floats
        origin (minimum point), spacing (voxel size), sizes (array size), maximum point

    """
    # min and max points
    min_point = [10000, 10000, 10000]
    max_point = [0, 0, 0]
    spacing = [10000, 10000, 10000]
    min_z = 10000
    z_last = 0

    # for each ROI
    for roi in contour_list:
        contours = contour_list.get(roi)
        for contour in contours:
            # get min and max point for this contour
            x_points = contour[0::3]
            y_points = contour[1::3]
            z_points = contour[2::3]
            x_min = np.min(x_points)
            y_min = np.min(y_points)
            z_min = np.min(z_points)
            x_max = np.max(x_points)
            y_max = np.max(y_points)
            z_max = np.max(z_points)
            x_diff = np.abs(np.diff(x_points))
            x_diff = np.ma.MaskedArray(x_diff, x_diff == 0)
            y_diff = np.abs(np.diff(y_points))
            y_diff = np.ma.MaskedArray(y_diff, y_diff == 0)
            z_diff = np.abs(z_points[0]-z_last)
            z_last = z_points[0]
            if 0 < z_diff < min_z:
                min_z = z_diff

            # store current max for the whole set
            min_point = np.minimum(min_point, np.asarray((x_min, y_min, z_min)))
            max_point = np.maximum(max_point, np.asarray((x_max, y_max, z_max)))
            spacing = np.asarray(np.minimum(spacing, np.asarray((np.min(x_diff), np.min(y_diff), min_z))))

    # size of the voxel array
    extents = np.asarray(np.subtract(max_point, min_point))
    sizes = np.add(np.divide(extents, spacing), 1)
    sizes = np.asarray(sizes, dtype=int)
    spacing3d = np.zeros((3, 3))
    spacing3d[0][0] = spacing[0]
    spacing3d[1][1] = spacing[1]
    spacing3d[2][2] = spacing[2]
    return min_point, spacing, sizes, max_point


def image_to_contour(volume: np.ndarray,
                     origin: np.ndarray,
                     directions: np.ndarray):
    """
    Given a volume matrix, generate a dictionary of contours grouped by "roi" (value that is used in the matrix)

    Parameters
    ----------
    volume : ndarray of float
        The matrix of ndarray volume data
    origin : ndarray of float
        A three dimensional point of the orgin of the volume in image space
    directions : ndarray of float
        A three dimensional array of the voxel dimensions in each direction
        TODO: handle rotations

    Returns
    -------
    Dictionary of ndarray of ndarray
        A dictionary of contour lists by ROI name

    """

    # return value
    contours = dict()

    # for each slice, get all ROIs present (ignore 0)
    for slice_index in range(volume.shape[2]):
        image_slice = volume[:, :, slice_index]
        rois = np.unique(image_slice)
        rois = np.delete(rois, 0).astype(int)

        # for each ROI in the slice, generate contour(s)
        for roi in rois:
            if roi in contours:
                contour_list = contours.get(roi)
            else:
                contour_list = list()
                contours[roi] = contour_list

            # find the contour(s) for this roi
            roi_slice = (image_slice == roi)

            generated_contours = measure.find_contours(roi_slice, 0.8)

            for arr in generated_contours:
                contour_array = []
                for point in range(0, arr.shape[0]):
                    v = np.append(arr[point], slice_index)
                    contour_point = voxel_to_image(v, origin, directions)
                    contour_array.append(contour_point[0])
                    contour_array.append(contour_point[1])
                    contour_array.append(contour_point[2])
                contour_list.append(contour_array)

    return contours


def contours_to_image(contour_list,
                      origin: np.ndarray = None,
                      spacing: np.ndarray = None,
                      sizes: np.ndarray = None):
    """
    Generate a voxel volume from a set of contours

    Parameters
    ----------
    contour_list: ndarray of ndarry of float
        A list of arrays of contour points[x1, y1, z1, x2, y2, z2 ...]
    origin : ndarray of float
        Origin of the grid [px, py, pz]
    spacing : ndarray of float
        Voxel volume size [vx, vy, vz] or [[vxx, vxy, vxz], [vyx, vyy, vzy], [vzx, vzy, vzz]]
    sizes : ndarray of int, optional
        If provided, use as the maximum size of the matrix, otherwise calculate
    """

    # figure out parameters for the volume
    originp, spacingp, sizesp, max_point = parameters_for_contours(contour_list)
    if origin is None:
        origin = originp
    if spacing is None:
        spacing = spacingp
    if sizes is None:
        sizes = sizesp

    img = np.zeros(sizes)

    # force to 3D:
    if spacing.ndim == 1:
        spacing3d = np.zeros((3, 3))
        spacing3d[0, 0] = spacing[0]
        spacing3d[1, 1] = spacing[1]
        spacing3d[2, 2] = spacing[2]
        spacing = spacing3d

    # now place each contour on the matrix
    for roi in contour_list:
        contours = contour_list.get(roi)
        for contour in contours:
            x = contour[0::3]
            y = contour[1::3]

            # TODO: assume z is the same for the contour, because this is what we have seen so far
            z = contour[2::3]
            zv = image_to_voxel(contour[0:3], origin, spacing)[2]
            if zv > img.shape[2]:
                print(zv, '>', img.shape[2])
                continue

            # area to determine if this is a 'fill' or a 'hole'
            area = 0.5 * (np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

            coords_x = []
            coords_y = []

            for index in range(0, len(x)):
                voxel_point = image_to_voxel(np.asarray((x[index], y[index], z[index])), origin, spacing)
                # add the point
                coords_x.append(voxel_point[1])
                coords_y.append(voxel_point[0])

            fill_coords_x, fill_coords_y = draw.polygon(coords_x, coords_y, img.shape[0:2])
            contour_outline = np.zeros(img.shape[0:2], dtype=np.bool)
            contour_outline[fill_coords_y, fill_coords_x] = True  # sitk is xyz, numpy is zyx

            contour_filled = ndimage.binary_fill_holes(contour_outline)
            contour_masked = ma.masked_array(data=img[:, :, zv], mask=False)

            index = 9
            if area > 0:
                index = roi

            contour_masked.mask = contour_filled
            img[:, :, zv] = ma.filled(contour_masked, index)

    return img, origin, spacing