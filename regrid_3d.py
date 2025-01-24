import time

import numpy as np
from math import sqrt

from torch.backends.cuda import cuFFTPlanCache


#region code to use ImageOrientationPatient to regrid "oblique" mr images, etc, to a "common" orthogonal grid for comparison
def generate_position_matrix(slice):
    iop = np.array(slice.ImageOrientationPatient)
    ipp = np.array(slice.ImagePositionPatient)
    spacing = np.array(slice.PixelSpacing)

    normal = np.cross(iop[0:3], iop[3:])
    z_projection = np.dot(ipp, normal)

    # 4x4 matrix defined in the calculation
    m = np.array([[iop[0] * spacing[0], iop[3] * spacing[1], 0, ipp[0]],
                  [iop[1] * spacing[0], iop[4] * spacing[1], 0, ipp[1]],
                  [iop[2] * spacing[0], iop[5] * spacing[1], 0, ipp[2]],
                  [0, 0, 0, 1]
                  ])
    return m, z_projection

def generate_slice_grid(slices):

    grid = np.zeros((slices[0].Rows, slices[0].Columns, len(slices), 3))
    for z, slice in enumerate(slices):
        m, z_projection = generate_position_matrix(slice)

        for x in range(0, grid.shape[0]):
            for y in range(0, grid.shape[1]):
                point = np.dot(m, [x, y, z, 1])  # projection, 1])
                grid[x, y, z] = point[0:3]

    return grid

def reverse_edge(edge):
    print("reverse_edge", edge.shape)
    for c in [0, 1, 2]:
        if edge[-1, c] - edge[0, c] < 0:
            edge = np.flip(edge, c)
    return edge

def distance_between(point1, point2):
    # TODO: check that points have same dimensions
    squared_dist = np.array([(point1[d]-point2[d])**2 for d in range(len(point1))])
    return np.sqrt(np.sum(squared_dist))


orthogonal_corners = {0: np.array([1, 3, 4]),
                      1: np.array([0, 2, 5]),
                      2: np.array([1, 3, 6]),
                      3: np.array([0, 2, 7]),
                      4: np.array([0, 5, 7]),
                      5: np.array([1, 4, 6]),
                      6: np.array([3, 5, 7]),
                      7: np.array([3, 4, 6]),
                      }
def get_orthogonal_corners(origin_index):
    return orthogonal_corners.get(origin_index, np.array([0, 0, 0]))

def equals(q1, q2, digits):
    q1 = round(q1, digits)
    q2 = round(q2, digits)
    return q1 == q2


def generate_position_vectors_slices(slices: list):
    x_vector = []
    y_vector = []
    z_vector = []

    slice_projections = []

    # TODO: have to assume slices sorted and equal slice sizes?
    rows = np.array(slices[0].Rows)
    columns = np.array(slices[0].Columns)
    spacing = np.array(slices[0].PixelSpacing)

    spacings = np.array([np.subtract(slice2.ImagePositionPatient, slice1.ImagePositionPatient) for slice1, slice2 in zip(slices, slices[1:])])
    delta_spacings = np.array([np.max(spacings[:, i]) - np.min(spacings[:, i]) for i in [0, 1, 2]])
    mean_spacings = np.array([np.mean(spacings[:, i]) for i in [0, 1, 2]])
    positions = np.array([slice.PatientPosition for slice in slices])

    # first pass to get slice positions and matrices
    for s, slice in enumerate(slices):
        m, z_projection = generate_position_matrix(slice)

        slice_corners = [np.dot(m, [0, 0, z_projection, 1])[0:3], np.dot(m, [columns, 0, z_projection, 1])[0:3],
                         np.dot(m, [columns, rows, z_projection, 1])[0:3], np.dot(m, [0, rows, z_projection, 1])[0:3]]
        slice_center = np.dot(m, [int(rows/2), int(columns/2), z_projection, 1])
        slice_projections += [{"z": z_projection, "m": m, 'corners': slice_corners,
                               'center': slice_center[0:3] }]

    slice_projections = sorted(slice_projections, key = lambda i: i['z'])

    # second pass to get sorted slice positions
    for p in slice_projections:
        z_vector.append(p['corners'][0])

    m0 = slice_projections[0]
    mn = slice_projections[-1]

    print("mean_spacings", mean_spacings)

    # x/i positions
    for i in range(0, rows):
        xp = np.dot(m0['m'], [i, columns, 0, 1])
        x_vector.append(xp[0:3])

    # y/j positions
    for j in range(0, columns):
        yp = np.dot(m0['m'], [rows, j, 0, 1])
        y_vector.append(yp[0:3])

    mhalf = slice_projections[len(slice_projections) // 2]

    return np.array(x_vector), np.array(y_vector), np.array(z_vector), m0['corners'], mn['corners'], mhalf['center']

def get_longest_axis(vector_3d):
    # TODO: can the list be written better??
    lengths = [np.abs(v[-1] - v[0] + (v[1] - v[0])) for v in [vector_3d[:, 0], vector_3d[:, 1], vector_3d[:, 2]]]
    i = np.argmax(lengths)
    max = lengths[i]
    return i, max

def generate_axis_vectors(vector_x, vector_y, vector_z, center):
    # get "actual" x, y, z direction for each "calculated" x, y, z vector
    axis_vectors = []
    axes = {}

    for v in [vector_x, vector_y, vector_z]:
        i, max = get_longest_axis(v)
        axes[i] = {'length': max, 'center': center[i],
                   'counts': [len(v[:, 0]), len(v[:, 1]), len(v[:, 2])]}
    origin = []
    for i in [0, 1, 2]:
        print(i, len(axes))
        origin.append(axes[i]['center'] - 0.5 * axes[i]['length'])

    for i in [0, 1, 2]:
        counts = axes[i]['counts']
        v = [np.full(counts[0], origin[0]),
             np.full(counts[1], origin[1]),
             np.full(counts[2], origin[2])
             ]

        # replace axis in question
        center = axes[i]['center']
        length = axes[i]['length']
        count = axes[i]['counts'][i]
        start = center - 0.5*length
        step = length/count

        # print("length, count", length, count, step, step-0.976562)

        # start = -250  # center - 0.5*length
        # step = 0.976562  #
        # print("start, step", start, step)
        # exit()

        v_axis = np.array([start + step * i for i in range(0, count)])
        v[i] = v_axis
        axis_vectors.append(np.swapaxes(np.array(v), 0, 1))

    return axis_vectors[0], axis_vectors[1], axis_vectors[2]

def generate_orthogonal_vectors(origin, size, spacing):
    print(origin, size, spacing)
    # for x in range(0, size[0]):
    #     print(origin[0]+x*spacing[0], origin[1], origin[2])
    # exit()
    x_vector = [np.array([origin[0]+x*spacing[0], origin[1], origin[2]]) for x in range(0, size[0])]
    y_vector = [np.array([origin[0], origin[1]+y*spacing[1], origin[2]]) for y in range(0, size[1])]
    z_vector = [np.array([origin[0], origin[1], origin[2]+z*spacing[2]]) for z in range(0, size[2])]

    print("new grid ortho: ", x_vector[0], x_vector[-1], x_vector[-1] - x_vector[0], len(x_vector),
          y_vector[0], y_vector[-1], y_vector[-1] - y_vector[0], len(y_vector),
          z_vector[0], z_vector[-1], z_vector[-1] - z_vector[0], len(z_vector))
    print("new grid ortho: ", (x_vector[-1] -x_vector[0]) / len(x_vector),
          (y_vector[-1] - y_vector[0]) / len(y_vector),
          (z_vector[-1] - z_vector[0]) / len(z_vector))

    return origin, np.array(x_vector), np.array(y_vector), np.array(z_vector)


def print_error(msg: str):
    print(msg)
    exit()
#endregion

# region original image regridding algorithm translated from UW med physics matlab code requires regular grids
def has_uniform_spacing(x: np.ndarray):
    # check to see if this axis is uniformly-spaced
    dx = x[1] - x[0]
    for index in range(1, x.shape[0] - 1):
        if np.abs(np.abs(x[index] - x[index - 1]) - np.abs(dx)) / np.abs(dx) > 1e-4:
            return False
    return True


def is_increasing(x: np.array):
    # ensure that the original coordinate system vector is monotonically increasing
    for index in range(1, x.shape[0] - 1):
        if x[index] - x[index - 1] <= 0.0:
            return False
    return True


def bin_searched(arr: np.ndarray, searchnum: float):
    # Accepts a float array of data of length M ordered lowest to highest and a number
    # called searchnum.  Returns the index of the first element of the array, a, that is
    # less than or equal to the searchnum.  If the searchnum is less than a[0], then -1
    # is returned, and if the searchnum is greater than a[M-1], then M is returned.
    bottom = 0
    top = arr.shape[0]-1
    print(arr[bottom], arr[top], searchnum)
    # Ensure that the search parameter lies inside boundaries
    if searchnum > arr[top]:
        return arr.shape[0]
    if searchnum < arr[bottom]:
        return -1

    while True:
        mid = int((top + bottom) / 2)
        if searchnum == arr[bottom]:
            return bottom
        elif searchnum == arr[mid]:
            return mid
        elif searchnum == arr[top]:
            return top
        elif searchnum < arr[mid]:
            top = mid - 1
        elif searchnum > arr[mid + 1]:
            bottom = mid + 1
        else:
            return mid


def grid_resample_3d(x: np.ndarray,
                     y: np.ndarray,
                     z: np.ndarray,
                     volume: np.ndarray,
                     xp: np.ndarray,
                     yp: np.ndarray,
                     zp: np.ndarray,
                     mode='linear',
                     sliced=False):
    """
    #GRIDRESAMPLE3D 3-D interpolation
    #  fp = gridResample3D(x,y,z,f,xp,yp,zp) resamples the values of the
    #  function fp at points on a 3-D rectilinear grid specified by the vectors
    #  xp, yp, zp, based on the original function, f, which has points
    #  specified by the vectors x, y, z.  The x, y, z vectors must be
    #  monotonically increasing, but the vectors xp, yp, and zp do not.

    #  fp = gridResample3D(...,mode) specifies an interpolation mode.  The
    #  'mode' argument can be either 'linear' or 'nearest', which corresponds
    #  to 3-D linear interpolation and nearest neighbor interpolation,
    #  respectively.  The default interpolation mode is 'linear'.
    #
    #  For data defined on a simple Cartesian grid, this function is much
    #  faster and more effective than interp3, which requires the user to input
    #  a set of three 3D coordinate grids (one for each dimension), along with
    #  the original data.  This wastes time and memory.
    #
    #  Ryan T Flynn, 6-27-07
    """

    if x.ndim != 1 or y.ndim != 1 or z.ndim != 1 or \
            volume.ndim != 3 or xp.ndim != 1 or yp.ndim != 1 or zp.ndim != 1:
        print_error('x, y, z, volume, zp, yp, zp must have proper dimensions.')

    # check the size of the original data array against the original coordinate system
    if x.shape[0] != volume.shape[0] or y.shape[0] != volume.shape[1] or z.shape[0] != volume.shape[2]:
        print_error('x, y, and z must have same dimensions as f')

    if not isinstance(mode, str):
        print_error('mode must be a character array')

    # ensure that the original coordinate system vectors are monotonically increasing
    if not is_increasing(x):
        print_error('x must be a monotonically increasing vector.')

    if not is_increasing(y):
        print_error('y must be a monotonically increasing vector.')

    if not is_increasing(z):
        print_error('z must be a monotonically increasing vector.')


    # centers of first elements in each axis
    x0 = x[0]
    y0 = y[0]
    z0 = z[0]

    # change between points
    dx = x[1] - x[0]
    dy = y[1] - y[0]
    dz = z[1] - z[0]

    # check to see if any axes are uniformly-spaced
    x_uniform_spacing = has_uniform_spacing(x)
    y_uniform_spacing = has_uniform_spacing(y)
    z_uniform_spacing = has_uniform_spacing(z)

    # determine the interpolation mode
    nearest_neighbor_flag = mode == 'nearest'
    linear_flag = mode == 'linear'

    # minimum value from the input volume (rather than 0)
    min_value = np.min(volume)

    # set up the output grid
    volume_new = np.zeros((xp.shape[0], yp.shape[0], zp.shape[0]))
    val = 0

    # interpolate the old grid onto the new one
    tol = 1e-3
    for k_new in range(0, zp.shape[0]):
        k_old = np.where(np.abs(z - zp[k_new]) < tol)[0]
        foundz = len(k_old) > 0
        if foundz and sliced:
            # keep the original slice
            volume_new[:, :, k_new] = volume[:, :, k_old[0]]
            continue

        foundy = False
        for j_new in range(0, yp.shape[0]):
            j_old = 0
            if foundz:
                j_old = np.where(np.abs(y - yp[j_new]) < tol)[0]
                foundy = len(j_old) > 0

            for i_new in range(0, xp.shape[0]):
                if foundy:
                    i_old = np.where(np.abs(x - xp[i_new]) < tol)[0]
                    if len(i_old) > 0:
                        # same voxel position in both volumes, so no interpolation needed
                        volume_new[i_new, j_new, k_new] = volume[i_old[0], j_old[0], k_old[0]]
                        print("found?", i_old, j_old, k_old, i_new, j_new, k_new)
                        continue

                # see if the point exists in both grids
                # find the bordering indices in the old grid that contain the current point
                # in the new grid
                print("not found:", i_old, j_old, k_old, i_new, j_new, k_new)
                if not x_uniform_spacing:
                    i = np.searchsorted(x, xp[i_new])  # bin_search(x, xp[i_new])
                else:
                    i = int((xp[i_new] - x0) / dx)

                if not y_uniform_spacing:
                    j = np.searchsorted(y, yp[j_new])  # bin_search(y, yp[j_new])
                else:
                    j = int((yp[j_new] - y0) / dy)

                if not z_uniform_spacing:
                    k = np.searchsorted(z, zp[k_new])  # bin_search(z, zp[k_new])
                else:
                    k = int((zp[k_new] - z0) / dz)

                # if the current point falls outside of the original grid, use minimum value
                # csk 2020-02-17 code was zeroing out the last cell in each row/column
                if (i < 0) or (i > x.shape[0]-2) or \
                        (j < 0) or (j > y.shape[0]-2) or \
                        (k < 0) or (k > z.shape[0]-2):
                    print(i, j, k, i_new, j_new, k_new, "outside grid", min_value)
                    volume_new[i_new, j_new, k_new] = min_value

                else:
                    # the divisions here are safe, since x, y, and z are monotonically increasing
                    t = (xp[i_new] - x[i]) / (x[i + 1] - x[i])
                    u = (yp[j_new] - y[j]) / (y[j + 1] - y[j])
                    v = (zp[k_new] - z[k]) / (z[k + 1] - z[k])

                    if linear_flag:
                        # linear interpolation
                        val = volume[i, j, k]*(1-t)*(1-u)*(1-v) + \
                            volume[i, j, k+1]*(1-t)*(1-u)*v + \
                            volume[i, j+1, k+1]*(1-t)*u*v + \
                            volume[i+1, j+1, k+1]*t*u*v + \
                            volume[i, j+1, k]*(1-t)*u*(1-v) + \
                            volume[i+1, j+1, k]*t*u*(1-v) + \
                            volume[i+1, j, k+1]*t*(1-u)*v + \
                            volume[i+1, j, k]*t*(1-u)*(1-v)

                    elif nearest_neighbor_flag:
                        # nearest neighbor interpolation
                        if t >= 0.5:
                            i = i + 1
                        if u >= 0.5:
                            j = j + 1
                        if v >= 0.5:
                            k = k + 1

                        val = volume[i, j, k]
                        print(f"{i}, {j}, {k}, {i_new}, {j_new}, {k_new}, val={val}")

                    else:
                        print_error('Unknown interpolation mode.  Must be either "linear" or "nearest".')

                    volume_new[i_new, j_new, k_new] = val

    return volume_new

# endregion, requires

# region new image regridding algorithm for radiology "oblique" mr scans, etc, does not require regular grids
# 202501 csk begin new grid interpolation algorithm for radiology "oblique" mr scans, etc


def volume_value(volume: np.ndarray, point: np.ndarray, outside_value:float=0, use_minimum:bool=False)-> float:
    """
    Given a volume array and a point of indices into the array, return the volume value while catching
    indices that are outside the array bounds

    Parameters
    ----------
    volume: np.array
        Values that make up the volume, must have same dimensions as point
    point: np.array
        Array indices for the value to get from volume, must have same dimensions as volume
    outside_value: float, default 0
        Value to use if point falls outside of the volume array
    use_minimum: boolean, default False
        Instead of given outside_value, use the minimum value of volume

    Returns
        A float value of the volume at the point
    -------
    """

    # TODO: best way to extrapolate outside the volume?
    if use_minimum:
        outside_value = np.min(volume)

    # allow passing possibly negative indices
    if np.sum(np.where(point < 0, 1, 0)) > 0:
        return outside_value

    try:
        value = volume
        for p in point:
             value = value[int(p)]
        # if round(point[0]) == 51 and round(point[1]) == 51 and round(point[2]) == 12:
        #     print(point, value, volume[round(point[0]), round(point[1]), round(point[2])])
        #     exit()
        ##print(volume.shape, point)
        ##exit()
        return value

    except IndexError:
        return outside_value

def distance_from(point1, point2, include_direction=False):
    """
    Get the distance between two points, must both have same dimensions
    # TODO: is this already done somewhere??

    Parameters
    ----------
    point1: np.ndarray
        A point of image coordinates
    point2
        A point of image coordinates
    Returns
        The image coordinate distance between the two points, with direction indicated by +/-
    -------

    """
    dist = 0
    mult = 1
    for d1, d2 in zip(point1, point2):
        dist += (d2 - d1)**2
        if include_direction and d2 < d1:
            mult = -1

    return mult * sqrt(dist)

def find_closest_point(points_volume, point2):
    best_distance = 100000
    best_point = np.array([-1, -1, -1])
    for xx in range(points_volume.shape[0]):
        for yy in range(points_volume.shape[1]):
            for zz in range(points_volume.shape[2]):
                point1 = points_volume[xx, yy, zz]
                dist = distance_from(point1, point2)
                if 0 < dist < best_distance:
                    best_distance = dist
                    best_point = np.array([xx, yy, zz])
    print("find_closest_point", best_distance, best_point)
    return best_point

# axis that forms box around the new point
def get_axis_points(points, i, j, k):
    return np.array([
        [[points[i, j, k], points[i+1, j, k], points[i, j+1, k], points[i, j, k+1]]]
    ])


def interpolate_point(new_point, closest_i, closest_j, closest_k, dx, dy, dz, points_volume, volume, mode='linear'):
    t = (new_point[0] - points_volume[closest_i, closest_j, closest_k, 0])/dx
    u = (new_point[1] - points_volume[closest_i, closest_j, closest_k, 1])/dy
    v = (new_point[2] - points_volume[closest_i, closest_j, closest_k, 2])/dz

    if mode == 'linear':
        # linear interpolation
        val = volume_value(volume, np.array([closest_i, closest_j, closest_k])) * (1 - t) * (1 - u) * (1 - v) + \
              volume_value(volume, np.array([closest_i, closest_j, closest_k + 1])) * (1 - t) * (1 - u) * v + \
              volume_value(volume, np.array([closest_i, closest_j + 1, closest_k + 1])) * (1 - t) * u * v + \
              volume_value(volume, np.array([closest_i + 1, closest_j + 1, closest_k + 1])) * t * u * v + \
              volume_value(volume, np.array([closest_i, closest_j + 1, closest_k])) * (1 - t) * u * (1 - v) + \
              volume_value(volume, np.array([closest_i + 1, closest_j + 1, closest_k])) * t * u * (1 - v) + \
              volume_value(volume, np.array([closest_i + 1, closest_j, closest_k + 1])) * t * (1 - u) * v + \
              volume_value(volume, np.array([closest_i + 1, closest_j, closest_k])) * t * (1 - u) * (1 - v)

    elif mode == 'nearest':
        # nearest neighbor interpolation
        if t >= 0.5:
            closest_i = closest_i + 1
        if u >= 0.5:
            closest_j = closest_j + 1
        if v >= 0.5:
            closest_k = closest_k + 1

        val = volume_value(volume, np.array([closest_i, closest_j, closest_k]))

    else:
        print_error('Unknown interpolation mode.  Must be either "linear" or "nearest".')

    return val


def find_local_delta(points, xi, yi, zi):
    # if +1 does not exist in some dimension, use -1
    # other index
    xi2 = xi + 1
    if xi2 >= points.shape[0]-1:
        xi2 = xi - 1
    yi2 = yi + 1
    if yi2 >= points.shape[1]-1:
        yi2 = yi - 1
    zi2 = zi + 1
    if zi2 >= points.shape[2]-1:
        zi2 = zi - 1

    point1 = points[xi, yi, zi]
    point2 = points[xi2, yi, zi]
    dx = np.abs(point2[0] - point1[0])

    point1 = points[xi, yi, zi]
    point2 = points[xi, yi2, zi]
    dy = np.abs(point2[1] - point1[1])

    point1 = points[xi, yi, zi]
    point2 = points[xi, yi, zi2]
    dz = np.abs(point2[2] - point1[2])

    return dx, dy, dz


def find_closest_index_for_point(volume, x, y, z, dx, dy, dz, ox, oy, oz):
    # print("find_closest_index_for_point")
    # print(x, y, z, dx, dy, dz, ox, oy, oz)
    x = np.abs(x - ox)/dx
    if x > volume.shape[0]-1:
        x = volume.shape[0]-1
    y = np.abs(y - oy)/dy
    if y > volume.shape[1]-1:
        y = volume.shape[1]-1
    z = np.abs(z - oz)/dz
    if z > volume.shape[2]-1:
        z = volume.shape[2]-1

    # if 19 < x < 20:
    #     print(x, y, z)
    return x, y, z


def grid_resample_3d_new(points_volume: np.ndarray,
                     volume: np.ndarray,
                     points_new: np.ndarray,
                     mode='linear'):
    """
    #GRIDRESAMPLE3D 3-D interpolation
    #  fp = gridResample3D(x,y,z,f,xp,yp,zp) resamples the values of the
    #  function fp at points on a 3-D rectilinear grid specified by the vectors
    #  xp, yp, zp, based on the original function, f, which has points
    #  specified by the vectors x, y, z.  The x, y, z vectors must be
    #  monotonically increasing, but the vectors xp, yp, and zp do not.

    #  fp = gridResample3D(...,mode) specifies an interpolation mode.  The
    #  'mode' argument can be either 'linear' or 'nearest', which corresponds
    #  to 3-D linear interpolation and nearest neighbor interpolation,
    #  respectively.  The default interpolation mode is 'linear'.
    #
    #  For data defined on a simple Cartesian grid, this function is much
    #  faster and more effective than interp3, which requires the user to input
    #  a set of three 3D coordinate grids (one for each dimension), along with
    #  the original data.  This wastes time and memory.
    #
    #  Ryan T Flynn, 6-27-07
    """
    if points_volume.ndim != 4 or volume.ndim != 3 or points_new.ndim != 4:
        print_error(f'points_original {points_volume.ndim}, volume {volume.ndim}, points_new {points_new.ndim} must have proper dimensions.')

    # check the size of the original data array against the original coordinate system
    if (points_volume.shape[0] != volume.shape[0] or
            points_volume.shape[1] != volume.shape[1] or
            points_volume.shape[2] != volume.shape[2]):
        print_error('points_original must have same dimensions as f')

    if not isinstance(mode, str):
        print_error('mode must be a character array')

    # centers of first elements in each axis
    x0 = points_volume[0, 0, 0, 0]
    y0 = points_volume[0, 0, 0, 1]
    z0 = points_volume[0, 0, 0, 2]

    # change between points
    dx = points_volume[1, 0, 0, 0] - points_volume[0, 0, 0, 0]
    dy = points_volume[0, 1, 0, 1] - points_volume[0, 0, 0, 1]
    dz = points_volume[0, 0, 1, 2] - points_volume[0, 0, 0, 2]

    dx_new = points_new[1, 0, 0, 0] - points_new[0, 0, 0, 0]
    dy_new = points_new[0, 1, 0, 1] - points_new[0, 0, 0, 1]
    dz_new = points_new[0, 0, 1, 2] - points_new[0, 0, 0, 2]

    minx = np.min(points_volume[0, 0, 0, 0])
    miny = np.min(points_volume[0, 0, 0, 1])
    minz = np.min(points_volume[0, 0, 0, 2])

    minx_new = np.min(points_new[0, 0, 0, 0])
    miny_new = np.min(points_new[0, 0, 0, 1])
    minz_new = np.min(points_new[0, 0, 0, 2])

    diff = points_volume - points_new

    # set up the output grid
    volume_new = np.zeros((points_new.shape[0:3]))

    # iterate through all new points z, y, x, check if interpolation is not needed, else interpolate
    tol = 1e-3
    interpolated_count = 0
    not_interpolated_count = 0
    for k_new in range(0, points_new.shape[2]):
        current_origin = points_new[0, 0, k_new]
        print(points_volume[0, 0, k_new], current_origin)
        print("pct done", k_new/points_new.shape[2], points_volume[0, 0, k_new], points_new[0, 0, k_new], current_origin[0], current_origin[1], current_origin[2])
        for j_new in range(0, points_new.shape[1]):
            for i_new in range(0, points_new.shape[0]):
                point = points_volume[i_new, j_new, k_new]
                i_new2, j_new2, k_new2 = find_closest_index_for_point(volume, point[0], point[1], point[2], dx, dy, dz, current_origin[0], current_origin[1], current_origin[2])
                if i_new != i_new2 or j_new != j_new2 or k_new != k_new2:
                    print("diff", i_new, i_new2, j_new, j_new, k_new, k_new2)
                continue
                # t1 = time.time()
                # print(i_new, j_new, k_new)
                point_new = points_new[i_new, j_new, k_new]
                dxn, dyn, dzn = find_local_delta(points_new, i_new, j_new, k_new)
                i_old, j_old, k_old = find_closest_index_for_point(volume, point_new[0], point_new[1], point_new[2], dxn, dyn, dzn, current_origin[0], current_origin[1], current_origin[2])
                i_old = round(i_old)
                j_old = round(j_old)
                k_old = round(k_old)


                # t2 = time.time()
                if i_new == i_old and j_new == j_old and k_new == k_old:
                    # same voxel position in both volumes, so no interpolation needed
                    volume_new[i_new, j_new, k_new] = volume_value(volume, np.array([i_old, j_old, k_old]))
                    # print(i_new, j_new, k_new, "no interpolation!", t2-t1)
                    not_interpolated_count += 1
                else:
                    # interpolate the new point onto the old grid
                    # t3 = time.time()
                    best_point = [i_old, j_old, k_old]
                    # print(i_old, j_old, k_old, int(i_old), int(j_old), int(k_old))
                    # t4 = time.time()
                    val = interpolate_point(points_new[i_new, j_new, k_new], best_point[0], best_point[1], best_point[2], dxn, dyn, dzn, points_volume, volume, mode)
                    volume_new[i_new, j_new, k_new] = val
                    interpolated_count += 1
                    # t5 = time.time()
                    # print(i_new, j_new, k_new, "interpolated", t2-t1, t3-t2, t4-t3, t5-t4)
    print(f"interpolated_count={interpolated_count}, not_interpolated_count={not_interpolated_count}. total_count={volume_new.shape[0]*volume_new.shape[1]*volume_new.shape[2]}")
    return volume_new
# endregion