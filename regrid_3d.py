import numpy as np

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

    grida = np.zeros((slices[0].Rows, slices[0].Columns, len(slices), 3))
    for z, slice in enumerate(slices):
        m, z_projection = generate_position_matrix(slice)

        for x in range(0, grida.shape[0]):
            for y in range(0, grida.shape[1]):
                point = np.dot(m, [x, y, z, 1])  # projection, 1])
                grida[x, y, z] = point[0:3]

    for rotx in (0, 1, 2, 3):
        for roty in (0, 1, 2, 3):
            for rotz in (0, 1, 2, 3):
                grid = np.rot90(grida, rotx, (0, 1))
                grid = np.rot90(grid, roty, (0, 2))
                grid = np.rot90(grid, rotz, (1, 2))
                corners = [grid[0, 0, 0],
                           grid[grid.shape[0] - 1, 0, 0],
                           grid[grid.shape[0] - 1, grid.shape[1] - 1, 0],
                           grid[0, grid.shape[1] - 1, 0, 0],
                           grid[0, 0, grid.shape[2] - 1],
                           grid[grid.shape[0] - 1, 0, grid.shape[2] - 1],
                           grid[grid.shape[0] - 1, grid.shape[1] - 1, grid.shape[2] - 1],
                           grid[0, grid.shape[1] - 1, grid.shape[2] - 1],
                           ]

                print(f"corner orientations for {rotx}, {roty}, {rotz}:")

                print(min(np.min(corners[1]-corners[0]), np.min(corners[3] - corners[0]), np.min(corners[0] - corners[4])))
                print(min(np.min(corners[0]-corners[1]), np.min(corners[2] - corners[1]), np.min(corners[1] - corners[5])))
                print(min(np.min(corners[3]-corners[2]), np.min(corners[1] - corners[2]), np.min(corners[2] - corners[6])))
                print(min(np.min(corners[2]-corners[3]), np.min(corners[0] - corners[3]), np.min(corners[3] - corners[7])))
                print(min(np.min(corners[5]-corners[4]), np.min(corners[7] - corners[4]), np.min(corners[4] - corners[0])))
                print(min(np.min(corners[4]-corners[5]), np.min(corners[6] - corners[5]), np.min(corners[5] - corners[1])))
                print(min(np.min(corners[7]-corners[6]), np.min(corners[5] - corners[6]), np.min(corners[6] - corners[2])))
                print(min(np.min(corners[6]-corners[7]), np.min(corners[4] - corners[7]), np.min(corners[7] - corners[3])))

    exit()

    # minimum value in each axis
    minimum = [10000, 10000, 10000]
    for c, corner in enumerate(corners):
        # least value in each dimension
        for d in [0, 1, 2]:
            if corner[d] < minimum[d]:
                minimum[d] = corner[d]
    minimum = np.array(minimum)

    distances = []
    for c, corner in enumerate(corners):
        # distance from minimum
        dist_origin = distance_between(corner, minimum)
        # print(c, corner, minimum, dist_origin)

        distances.append({"corner": corner, "index": c, "dist_origin": dist_origin})

    # take origin as closest to minimums
    corner_origin = sorted(distances, key=lambda i: i['dist_origin'])[0]

    origin_point = corner_origin['corner']
    origin_index = corner_origin['index']

    # generate all axes
    gridyz0 = grid[:, 0, 0, :]
    gridxz0 = grid[0, :, 0, :]
    gridxy0 = grid[0, 0, :, :]
    gridyzt = grid[:, grid.shape[1] - 1, grid.shape[2] - 1, :]
    gridxzt = grid[grid.shape[0] - 1, :, grid.shape[2] - 1, :]
    gridxyt = grid[grid.shape[0] - 1, grid.shape[1] - 1, :, :]

    gridy0zt = grid[:, 0, grid.shape[2] - 1, :]
    gridx0zt = grid[0, :, grid.shape[2] - 1, :]
    gridx0yt = grid[0, grid.shape[0] - 1, :, :]
    gridytz0 = grid[:, grid.shape[1] - 1, 0, :]
    gridxtz0 = grid[grid.shape[0] - 1, :, 0, :]
    gridxty0 = grid[grid.shape[0] - 1, 0, :, :]

    orthogonal_corners = get_orthogonal_corners(origin_index)
    oa1 = corners[orthogonal_corners[0]]
    oa2 = corners[orthogonal_corners[1]]
    oa3 = corners[orthogonal_corners[2]]
    edge1 = None
    edge2 = None
    edge3 = None
    for e, edge in enumerate([gridyz0, gridxz0, gridxy0, gridyzt, gridxzt, gridxyt,
        gridy0zt, gridx0zt, gridx0yt, gridytz0, gridxtz0, gridxty0]):
        if origin_point in edge:
            if oa1 in edge and edge1 is None:
                edge1 = edge
                # print(e, "origin to oa1 edge found!")
            elif oa2 in edge and edge2 is None:
                edge2 = edge
                # print(e, "origin to oa2 edge found!")
            elif oa3 in edge and edge3 is None:
                edge3 = edge
                # print(e, "origin to oa3 edge found!")

    print("original axes lengths: ", edge1[-1]-edge1[0], edge2[-1]-edge2[0], edge3[-1]-edge3[0])
    edge1 = reverse_edge(edge1)
    edge2 = reverse_edge(edge2)
    edge3 = reverse_edge(edge3)
    print("reversed axes lengths: ", edge1[-1]-edge1[0], edge2[-1]-edge2[0], edge3[-1]-edge3[0])
    exit()
    return origin_point, edge1, edge2, edge3

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
    for x in range(0, size[0]):
        print(origin[0]+x*spacing[0], origin[1], origin[2])
    exit()
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


    print("original grid: ", x[0], x[-1], x[-1]-x[0], len(x), y[0], y[-1], y[-1]-y[0], len(y), z[0], z[-1], z[-1]-z[0], len(z))
    print("new grid: ", xp[0], xp[-1], xp[-1] - xp[0], len(xp), yp[0], yp[-1], yp[-1] - yp[0], len(yp), zp[0], zp[-1], zp[-1] - zp[0], len(zp))
    print("original grid: ", (x[-1]-x[0])/len(x), (y[-1]-y[0])/len(y), (z[-1]-z[0])/len(z))
    print("new grid: ", (xp[-1] - xp[0])/len(xp), (yp[-1] - yp[0])/len(yp), (zp[-1] - zp[0])/len(zp))
    exit()

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
