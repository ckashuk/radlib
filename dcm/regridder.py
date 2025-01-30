from typing import Union

import numpy as np
import SimpleITK as sitk

def generate_grid(img: sitk.Image)-> np.ndarray:
    """
    given an sitk Image, generate a grid of physical points based on the size/indices of the image

    Parameters
    ----------
    img: sitk.Image
        the image to grid

    Returns
    -------
    a numpy array with x, y, z, 3 dimensions, for every x, y, z in the image's index space (GetSize()), there
    is a 3-d point in the image's physical space

    """

    # use the image's GetSize() to initialize the output grid
    grid = np.zeros((img.GetSize()[0], img.GetSize()[1],  img.GetSize()[2], 3))

    for kk in range(0, grid.shape[2]):
        for jj in range(0, grid.shape[1]):
            for ii in range(0, grid.shape[0]):
                # for each indexed point in the image, generate the physical point
                grid[ii, jj, kk] = img.TransformIndexToPhysicalPoint((ii, jj, kk))

    return grid


def evaluate_at_continuous_index_wrapper(img:sitk.Image,
                                         new_point: np.ndarray,
                                         default_value:float=0,
                                         interp=sitk.sitkLinear)-> Union[int, float]:
    """
    wrapper for sitk EvaluateAtContinuousIndex IndexError to zero out out any values that fall outside the grid

    Parameters
    ----------
    img: sitk.Image
        the image to get the volume value from
    new_point: np.ndarray
        an i, j, k point in index space to get the value from. If EvaluateAtContinuousIndex throws and IndexError,
        return the default value
    default_value: float=0
        the value to use if the index point is outside the index grid of the image. defaults to 0
    interp:
        the interpolation mode to use, from sitk constants. Possible values are sitk.sitkNearest, sitk.sitkLinear.
        detaults to sitk.sitkLinear
    Returns
    -------
    the value from the image's volume, or default_value
    """
    # evaluate the volume value at the new grid poisition
    # catch index outside of grid and zero out those values
    # TODO: 202501 csk better exception to catch here?? it's from sitk so we can't use IndexError
    try:
        new_value = img.EvaluateAtContinuousIndex(new_point, interp=interp)
    except RuntimeError as e:
        new_value = default_value

    return new_value


def generate_regridded_volume(img:sitk.Image,
                              grid:np.ndarray=None,
                              default_value:float=0,
                              mode=sitk.sitkLinear) -> np.ndarray:
    """
    given a sitk Image, generate a volume projection onto a new grid.

    Parameters
    ----------
    img: sitk.Image
        The image to take volume information from
    grid: np.ndarray, optional, default None
        The grid of physical points to take volume information from,
        must be in the form [i, j, k, (x, y, z)] where i, j, and k are image index values, and x, y, z are
        corresponding image physical values
        if not provided, will regrid as an "orthographic projection" on the size of the image data,
        attempting to pad for oblique images
    default_value: float=0
        the value to use if the index point is outside the index grid of the image. defaults to 0
    mode:
        the interpolation mode to use, from sitk constants. Possible values are sitk.sitkNearest, sitk.sitkLinear.
        detaults to sitk.sitkLinear


    Returns
    -------
       a np.ndarray of "regridded" image volume data,


    """

    # "force" origin + index * spacing when making orthogonal grid,
    index_to_physical = lambda index, origin, spacing: origin + index * spacing

    if grid is None:
        # generate an orthogonal projection overlaying the space of the image's grid
        # TODO: 202502 csk do we need an option for a reference image with it's origin/spacing/direction??

        # find padded k index length to account for oblique images in 3d space
        # TODO: 202502 csk can we/ do we need to do this for x and y too??
        extent_z = img.TransformIndexToPhysicalPoint((0, 0, img.GetSize()[2]-1))[2] - img.TransformIndexToPhysicalPoint((0, 0, 0))[2]
        index_z = int((extent_z-img.GetOrigin()[2])/img.GetSpacing()[2])

        # use the image's GetSize() to initialize the output volume
        new_volume = np.zeros((img.GetSize()[0], img.GetSize()[1], index_z), dtype=np.int16)

        # traverse the orthogonal indices of the projected grid
        for kk in range(0, new_volume.shape[2]):
            zz = index_to_physical(kk, img.GetOrigin()[2], img.GetSpacing()[2])
            for jj in range(0, new_volume.shape[1]):
                yy = index_to_physical(jj, img.GetOrigin()[1], img.GetSpacing()[1])
                for ii in range(0, new_volume.shape[0]):
                    xx = index_to_physical(ii, img.GetOrigin()[0], img.GetSpacing()[0])

                    # convert physical point of grid to index point in new image space
                    # use continuous index to allow interpolation
                    new_point = img.TransformPhysicalPointToContinuousIndex((xx, yy, zz))
                    # evaluate the volume value at the new grid position
                    # catch index outside of grid and zero out those values
                    # TODO: csk 202601 break this out into separate function? seemed to be performance hit
                    try:
                        new_value = evaluate_at_continuous_index_wrapper(img, new_point, interp=mode)
                    except IndexError as e:
                        new_value = default_value

                    new_volume[ii, jj, kk] = new_value

    else:
        new_volume = np.zeros(grid.shape[0:3], dtype=np.int16)

        # traverse the included grid
        for kk in range(0, grid.shape[2]):
            for jj in range(0, grid.shape[1]):
                for ii in range(0, grid.shape[0]):
                    new_point = img.TransformPhysicalPointToContinuousIndex(grid[ii, jj, kk])
                    try:
                        new_value = evaluate_at_continuous_index_wrapper(img, new_point, interp=mode)
                    except Exception as e:
                        new_value = default_value
                    new_volume[ii, jj, kk] = new_value

    # 202501 csk swapaxes needs to be done because of simpleitk's wierd indexing
    new_volume = np.swapaxes(new_volume, 0, 2)
    return new_volume


def generate_regridded_image(img:sitk.Image,
                             grid:np.ndarray=None,
                             mode=sitk.sitkLinear,
                             copy_tags=True) -> sitk.Image:
    """
    wrapper to get an sitk Image rather than an ndarray for a projection

    Parameters
    ----------
   img: sitk.Image
        The image to take volume information from
    grid: np.ndarray, optional, default None
        The grid of physical points to take volume information from,
        must be in the form [i, j, k, (x, y, z)] where i, j, and k are image index values, and x, y, z are
        corresponding image physical values
        if not provided, will regrid on the size of the image data, attempting to pad for oblique images
    default_value: float=0
        the value to use if the index point is outside the index grid of the image. defaults to 0
    mode:
        the interpolation mode to use, from sitk constants. Possible values are sitk.sitkNearest, sitk.sitkLinear.
        detaults to sitk.sitkLinear

    Returns
    -------
    a new sitk.Image with parameters of img but containing "regridded" image volume data
    """

    new_volume = generate_regridded_volume(img, grid, mode)

    # TODO: csk 202501 do we need to reverse the swapaxes in this case??
    new_volume = np.swapaxes(new_volume, 0, 2)
    new_img = sitk.GetImageFromArray(new_volume)

    # copy information from the original image
    new_img.CopyInformation(img)
    if copy_tags:
        for key in img.GetMetaDataKeys():
            new_img.SetMetaData(key, img.GetMetaData(key))

    return new_img