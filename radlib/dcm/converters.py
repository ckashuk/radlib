import glob
from collections import OrderedDict
import datetime
import nrrd
import numpy as np
import numpy.ma as ma
import os
import pydicom
import pydicom.uid
import skimage
from pydicom.sequence import Sequence
from pydicom.dataset import Dataset
import scipy.ndimage
from scipy import ndimage
import SimpleITK as SimpleITK
from skimage import measure

from radlib.dcm import contours


class InvalidDicomDateFormatException(Exception):
    pass


class InvalidDicomKeyException(Exception):
    pass


def strptime_formats(date_string: str):
    """
    Run strptime for dates coming from DICOM: with and without .milliseconds and UTC offset

    Parameters
    ----------
    date_string: str
        date stamp from DICOM: YYYYMMDDHHMMSS or YYYYMMDDHHMMSS.mm or YYYYMMDDHHMMSS&HHMM or YYYYMMDDHHMMSS.mm&HHMM

    Returns
    -------
    datetime object from the string
    Raises AiqInvalidDicomDateFormat error if none of these work
    """

    for fmt in ('%Y%m%d%H%M%S', '%Y%m%d%H%M%S.%f', '%Y%m%d%H%M%S%z', '%Y%m%d%H%M%S.%f%z'):
        try:
            return datetime.datetime.strptime(date_string, fmt)
        except ValueError:
            pass
    raise InvalidDicomDateFormatException(date_string)


def pet_suv_factor(pet_slice: pydicom.FileDataset):
    """
    Calculate the factor to normalize PET data to SUV

    Describe the algorithm here

    Parameters
    ----------
    pet_slice : FileDataset
        PET data slice (assume loaded by pydicom with metadata included)

    Returns
    -------
    float
        A factor to be applied to voxels in that PET to take weight and scan dose into account

    """

    try:  # csk 11/23 catch missing weight/startdatetime or other expected dicom tags
        weight = pet_slice.PatientWeight  # in kg
        half_life = pet_slice.RadiopharmaceuticalInformationSequence[0].RadionuclideHalfLife  # in s
        inj_dose = pet_slice.RadiopharmaceuticalInformationSequence[0].RadionuclideTotalDose  # in Bq

        # Delay time between injection and start of scan( in s)
        # csk 2021-04 RadiopharmaceuticalStartDateTime should have replaced RadiopharmaceuticalStartTime in DICOM spec,
        # but some older scans still use it, so make sure we can handle both
        inj_datetime = pet_slice.RadiopharmaceuticalInformationSequence[0].get('RadiopharmaceuticalStartDateTime')
        if inj_datetime is None:
            inj_datetime = pet_slice.SeriesDate + \
                           pet_slice.RadiopharmaceuticalInformationSequence[0].get('RadiopharmaceuticalStartTime')

        scan_datetime = pet_slice.SeriesDate + pet_slice.SeriesTime
        inj_datetime = strptime_formats(inj_datetime)
        scan_datetime = strptime_formats(scan_datetime)

        print(scan_datetime, inj_datetime)
        t = (scan_datetime - inj_datetime).total_seconds()
        print(t)

        scan_dose = inj_dose * np.exp(-(np.log(2) * t) / half_life)  # in Bq

        # Calculate SUV factor
        return 1 / ((scan_dose / weight) * 0.001)
    except Exception as e:
        raise InvalidDicomKeyException(e)


def load_dicom(path: str,
               resample: np.ndarray = None):
    """
    load a directory of DICOM slices into an array

    Parameters
    ----------

    path : str
        A path containing one or more DICOM files
    resample : np.ndarray of float, optional
        A three-dimensional array of the shape that the slices should be reshaped to
        TODO: currently we assume a square slice with x and y equal

    Returns
    --------
    array-like of FileDataset
        An array of slices, sorted by SliceLocation, each containing a 2 dimensional matrix of image data

    """
    files = []
    slice_zoom = -1

    for fname in glob.glob(path+"\\*", recursive=False):
        file = pydicom.dcmread(fname)
        # figure out orientation
        # TODO: Remove if not needed. Uncomment if needed.
        # if file.PatientPosition == "HFS":  # head first supine, need to transpose
        #    tmp = np.transpose(file.pixel_array)
        #    file.PixelData = tmp.tobytes()

        # resample if needed
        if resample is not None:
            slice_array = file.pixel_array
            if slice_zoom == -1:
                slice_zoom = resample[0] / slice_array.shape[0]
            slice_array = ndimage.zoom(slice_array, slice_zoom, order=3)
            file.PixelData = slice_array.tobytes()
            file.Rows, file.Columns = file.PixelArray.shape

        files.append(file)

    # ensure they are in the correct order
    # csk 2021-04 ImagePositionPatient is required (SliceLocation is not) and appears to be more reliable
    slices = sorted(files, key=lambda s: s.ImagePositionPatient[2])

    return slices


def generate_array_from_dicom(slices: pydicom.FileDataset,
                              resample: np.ndarray = None):
    """
    Given an array of "slices" usually from DICOM files, convert to an image volume matrix

    Parameters
    ----------
    slices : array-like of FileDataset
        An ordered array of pydicom slices each coresponding to a 2D slice of image information
    resample : array-like of float, optional
        A three-dimensional array of the shape that the slices should be reshaped to
        TODO: currently this is not working

    Returns
    -------
    ndarray of float
        A three dimensional matrix of image data from all of the slices

    """
    # create 3D array
    slice_shape = slices[0].pixel_array.shape
    img_shape = [slice_shape[0], slice_shape[1], len(slices)]

    if resample is not None:
        img3d = np.zeros(resample)
    else:
        img3d = np.zeros(img_shape)

    rescale_suv = 1.0
    if slices[0].Modality == 'PT':
        rescale_suv = pet_suv_factor(slices[0])

    # fill 3D array with the images from the files
    for i, s in enumerate(slices):
        img2d = s.pixel_array

        # rescale values from metadata
        rescale_slope = s.RescaleSlope
        rescale_intercept = s.RescaleIntercept
        img2d = img2d * rescale_slope + rescale_intercept

        # if PET, convert to SUV
        if s.Modality == 'PT':
            img2d = img2d * rescale_suv

        # resample to another shape
        if resample is not None:
            img2d = skimage.transform.resize(img2d, (resample[0], resample[1]))

        img3d[:, :, i] = img2d

    return img3d


def new_dicom_dataset(source_data_set: Dataset = None,
                      modality: str = None,
                      pixel_array: np.ndarray = None):
    """
    Generate minimum amount of metadata for a valid dicom file

    Parameters
    ----------
    source_data_set : Dataset, optional
        Get required metadata from this (pydicom formatted) dicom's metadata (default: None)
    modality : str, optional
        Generate file of this type.
        Valid values: RTSTRUCT, CT
        If None, take from copy_from. If copy_from also None, default to RTSTRUCT
        if CT, need to include pixel_array
    pixel_array: np.ndarray, optional
        if requires image data, a 2-d array to be used

    Returns
    -------
    Dataset
        A new pydicom Dataset with required metadata for a new Dicom file

    Notes
    -----
    Minimum set was taken from SlicerRT export -> pydicom codify script -> dicom standard browser
    (dicom.innolitics.com) type

      """
    data_set = Dataset()

    # Patient elements
    # 2-required, empty if unknown
    data_set.PatientName = source_data_set.PatientName if source_data_set is not None else ''
    data_set.PatientID = source_data_set.PatientID if source_data_set is not None else ''
    data_set.PatientBirthDate = source_data_set.PatientBirthDate if source_data_set is not None else ''
    data_set.PatientSex = source_data_set.PatientSex if source_data_set is not None else ''

    # General Study elements
    # 1-required
    data_set.StudyInstanceUID = pydicom.uid.generate_uid()

    # 2-required, empty if unknown
    data_set.StudyDate = source_data_set.StudyDate if source_data_set is not None else ''
    data_set.StudyTime = source_data_set.StudyTime if source_data_set is not None else ''
    data_set.ReferringPhysicianName = source_data_set.ReferringPhysicianName if source_data_set is not None else ''
    data_set.StudyID = source_data_set.StudyID if source_data_set is not None else ''
    data_set.AccessionNumber = source_data_set.AccessionNumber if source_data_set is not None else ''
    data_set.StudyDescription = source_data_set.StudyDescription if source_data_set is not None else ''

    # RT Series elements
    # 1-required
    data_set.SeriesInstanceUID = pydicom.uid.generate_uid()

    # 2-required, empty if unknown
    data_set.SeriesNumber = source_data_set.SeriesNumber if source_data_set is not None else ''

    # General Equipment elements
    # 2-required, empty if unknown
    data_set.Manufacturer = source_data_set.Manufacturer if source_data_set is not None else ''

    # SOP common elements
    # 1-required
    data_set.SOPInstanceUID = pydicom.uid.generate_uid()

    # IOD specific elements
    if modality is None:
        modality = "RTSTRUCT"

    if modality == "RTSTRUCT":
        # RTSS or structure set
        data_set.Modality = modality
        data_set.SOPClassUID = '1.2.840.10008.5.1.4.1.1.481.3'

    if modality == "CT":
        # CT file
        data_set.Modality = modality
        data_set.SOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
        data_set.ImagePositionPatient = ['-350.000', '-350.000', '-1690.000']
        data_set.ImageOrientationPatient = ['1.000000', '0.000000', '0.000000', '0.000000', '1.000000', '0.000000']
        data_set.PixelData = pixel_array.tobytes()
        data_set.Rows, data_set.Columns = pixel_array.shape
        data_set.BitsAllocated = 16
        data_set.BitsStored = 16
        data_set.HighBit = 15
        data_set.PixelRepresentation = 1
        data_set.SamplesPerPixel = 1
        data_set.PixelSpacing = ['1.367188', '1.367188']
        data_set.RescaleIntercept = "-1024"
        data_set.RescaleSlope = "1"
        data_set.RescaleType = 'HU'
        data_set.is_little_endian = True
        data_set.is_implicit_VR = False

        # File meta info data elements
        file_meta = Dataset()
        file_meta.FileMetaInformationGroupLength = 208
        file_meta.FileMetaInformationVersion = b'\x00\x01'
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1'
        file_meta.ImplementationClassUID = '1.2.840.113619.6.290'
        file_meta.ImplementationVersionName = 'pet_coreload.44'
        file_meta.SourceApplicationEntityTitle = 'wimrpct2'
        data_set.file_meta = file_meta

    return data_set


def nrrd_to_dicomrt_file(nrrd_path, dicomrt_path):
    """
    Wrap the Nrrd to DICOM-RT in a function that does the conversion and then converts back

    Parameters
    ----------
    nrrd_path : str
        The path to read the Nrrd format data from
    dicomrt_path : str
        The path to write the DICOM-RT format data to

    Returns
    -------
    float
        The mean squared error when the file is converted and then converted back
        TODO: check some small holes are being filled in?

    """
    nrrd_data, nrrd_header = nrrd.read(nrrd_path)
    nrrd_to_dicomrt(nrrd_data, nrrd_header, file_path=dicomrt_path)

    # validate
    dicom_slice = pydicom.dcmread(dicomrt_path)
    nrrd_comp, nrrd_comp_header = dicomrt_to_nrrd(dicom_slice)
    return (np.square(nrrd_comp - nrrd_data)).mean(axis=None)


def nrrd_to_dicomrt(nrrd_data, nrrd_header: dict, ref_dicom_data: list = None, reverse_z: bool = False,
                    resampled: bool = False, file_path: str = ""):
    """
    Given a set of one or more dicom files and an NRRD file of segmentations, generate a dicom-RT
       structure set file

    Parameters
    ----------
    nrrd_data : Dictionary
        A 3-d matrix of image data
    nrrd_header : Dictionary
        Nrrd tags that go along with nrrd_data
    dicom_data: list, optional
        A reference list of DICOM slice data to model this dataset on
    reverse_z : bool, optional
        Reverse the direction of the z axis (default false)
    resampled : bool, optional
        Resample nrrd data to match dimensions of the dicom data before contouring (default False)
    file_path : str, optional
        Path to write the resulting structure set file

    Returns
    -------
    Dataset
        A dicom dataset containing the structure set data

    Notes
    -----
    Adapted from codify.py output (a script which is part of pydicom, that creates Python code to replicate
    a dicom file using pydicom)

    """
    dicom_ref = None

    if ref_dicom_data is not None:
        dicom_ref = ref_dicom_data[0]

    # get coordinate change information from the original data
    slice_count = nrrd_data.shape[2]
    slice_zoom = 1
    if resampled:
        slice_zoom = dicom_ref.pixel_array.shape[0] / nrrd_data.shape[0]
    nrrd_origin = nrrd_header['space origin']
    nrrd_directions = nrrd_header['space directions']

    if resampled:
        nrrd_directions[0] /= slice_zoom
        nrrd_directions[1] /= slice_zoom

    # list of image UIDs for ROIs to connect images to ROIs
    image_uids = []

    # list of ROIs that have already been seen
    image_rois = []

    # Main data elements
    ds = new_dicom_dataset(dicom_ref, "RTSTRUCT")

    # coordinate values
    # ds.ImagePosition = []
    # ds.ImagePosition.append(nrrd_origin[0])
    # ds.ImagePosition.append(nrrd_origin[1])
    # ds.ImagePosition.append(nrrd_origin[2])

    # ds.PixelSpacing = []
    # ds.PixelSpacing.append(nrrd_directions[0, 0])
    # ds.PixelSpacing.append(nrrd_directions[1, 1])
    # ds.SpacingBetweenSlices = nrrd_directions[2, 2]

    # ds.Rows = nrrd_data.shape[0]
    # ds.Columns = nrrd_data.shape[1]
    # ds.NumberOfSlices = nrrd_data.shape[2]

    ds.OperatorsName = "Carl^Kashuk"
    ds.FrameOfReferenceUID = dicom_ref.FrameOfReferenceUID  # pydicom.uid.generate_uid()
    ds.PositionReferenceIndicator = ''
    # Structure Set elements
    ds.InstanceNumber = "1"
    ds.StructureSetLabel = "UW"
    ds.StructureSetName = "ROI"
    ds.StructureSetDate = datetime.date.today().strftime("%Y%m%d")  # '20160630' TODO should this be nrrd or dicom date?
    ds.StructureSetTime = datetime.date.today().strftime("%H%M%S")  # '143113'

    # these are elements that code the images from the dicom and relates them to
    # contours

    # Referenced Frame of Reference Sequence
    refd_frame_of_ref_sequence = Sequence()
    ds.ReferencedFrameOfReferenceSequence = refd_frame_of_ref_sequence

    # Referenced Frame of Reference Sequence: Referenced Frame of Reference 1
    refd_frame_of_ref1 = Dataset()
    refd_frame_of_ref1.FrameOfReferenceUID = dicom_ref.FrameOfReferenceUID

    # RT Referenced Study Sequence
    rt_refd_study_sequence = Sequence()
    refd_frame_of_ref1.RTReferencedStudySequence = rt_refd_study_sequence

    # RT Referenced Study Sequence: RT Referenced Study 1
    rt_refd_study1 = Dataset()
    rt_refd_study1.ReferencedSOPClassUID = '1.2.840.10008.3.1.2.3.2'
    rt_refd_study1.ReferencedSOPInstanceUID = ds.StudyInstanceUID

    # RT Referenced Series Sequence
    rt_refd_series_sequence = Sequence()
    rt_refd_study1.RTReferencedSeriesSequence = rt_refd_series_sequence

    # RT Referenced Series Sequence: RT Referenced Series 1
    rt_refd_series1 = Dataset()
    rt_refd_series1.SeriesInstanceUID = pydicom.uid.generate_uid()

    # Contour Image Sequence
    contour_image_sequence = Sequence()
    rt_refd_series1.ContourImageSequence = contour_image_sequence

    for z in range(slice_count):
        # Contour Image Sequence for slice
        contour_image1 = Dataset()
        contour_image1.ReferencedSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
        image_uids.insert(z, pydicom.uid.generate_uid())
        contour_image1.ReferencedSOPInstanceUID = image_uids[z]
        contour_image_sequence.append(contour_image1)

    rt_refd_series_sequence.append(rt_refd_series1)
    rt_refd_study_sequence.append(rt_refd_study1)
    refd_frame_of_ref_sequence.append(refd_frame_of_ref1)

    # Structure Set ROI Sequence
    structure_set_roi_sequence = Sequence()
    ds.StructureSetROISequence = structure_set_roi_sequence

    # ROI Contour Sequence
    roi_contour_sequence = Sequence()
    ds.ROIContourSequence = roi_contour_sequence

    for slice_index in range(slice_count):
        # for each slice, get all ROIs present (ignore 0)
        image_slice = nrrd_data[:, :, slice_index]
        rois = np.unique(image_slice)
        rois = np.delete(rois, 0).astype(int)

        # for each ROI in the slice, generate contour(s)
        for roi in rois:

            # find the ROI for this contour and create it if it wasn't already seen
            if roi not in image_rois:
                # Structure Set ROI Sequence: Structure Set ROI
                structure_set_roi = Dataset()
                structure_set_roi.ROINumber = str(roi)
                structure_set_roi.ReferencedFrameOfReferenceUID = dicom_ref.FrameOfReferenceUID # pydicom.uid.generate_uid()
                structure_set_roi.ROIName = 'ROI ' + str(roi)
                structure_set_roi.ROIGenerationAlgorithm = "AUTOMATIC"
                structure_set_roi_sequence.append(structure_set_roi)
                image_rois.append(roi)

            # ROI Contour Sequence
            roi_contour = Dataset()
            roi_contour.ROIDisplayColor = ['128', '174', '128']

            # Contour Sequence
            contour_sequence = Sequence()
            roi_contour.ContourSequence = contour_sequence

            # find the contour(s) for this roi
            roi_slice = (image_slice == roi)

            if resampled:
                roi_slice = scipy.ndimage.zoom(roi_slice, slice_zoom, order=0)

            contours = measure.find_contours(roi_slice, 0.8)

            for arr in contours:

                # Contour Sequence
                contour = Dataset()

                # Contour Image Sequence
                contour_image_sequence = Sequence()
                contour.ContourImageSequence = contour_image_sequence
                # Contour Image
                contour_image = Dataset()
                contour_image.ReferencedSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
                contour_image.ReferencedSOPInstanceUID = image_uids[slice_index]
                contour_image_sequence.append(contour_image)

                contour.ContourGeometricType = 'CLOSED_PLANAR'
                contour_point_count = 0
                points_string = []
                for point in range(0, arr.shape[0]):
                    xf = (nrrd_origin[0] + nrrd_directions[0, 0] * arr[point, 0])
                    yf = (nrrd_origin[1] + nrrd_directions[1, 1] * arr[point, 1])
                    z = (slice_count - slice_index) if reverse_z else slice_index
                    zf = nrrd_origin[2] + nrrd_directions[2, 2] * z
                    xf = int(xf)
                    yf = int(yf)
                    zf = int(zf)
                    points_string.append(xf)
                    points_string.append(yf)
                    points_string.append(zf)
                    contour_point_count += 1

                contour.NumberOfContourPoints = contour_point_count
                contour.ContourData = points_string
                contour_sequence.append(contour)

            roi_contour.ReferencedROINumber = str(roi)
            roi_contour_sequence.append(roi_contour)

    # RT ROI Observations Sequence
    rtroi_observations_sequence = Sequence()
    ds.RTROIObservationsSequence = rtroi_observations_sequence

    # RT ROI Observations Sequence: RT ROI Observations 1
    rtroi_observations = Dataset()
    rtroi_observations.ObservationNumber = "1"
    rtroi_observations.ReferencedROINumber = "1"
    rtroi_observations.ROIObservationLabel = 'Segment'
    rtroi_observations.RTROIInterpretedType = ''
    rtroi_observations.ROIInterpreter = ''
    rtroi_observations_sequence.append(rtroi_observations)

    if len(file_path) > 0:
        # File meta info data elements
        file_meta = Dataset()
        file_meta.FileMetaInformationVersion = b'\x00\x01'
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.481.3'
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1'
        file_meta.ImplementationClassUID = '1.2.276.0.7230010.3.0.3.6.3'
        file_meta.ImplementationVersionName = 'OFFIS_DCMTK_363'
        file_meta_length = 2 + 29 + 19 + 27 + 15 + len(file_meta.MediaStorageSOPInstanceUID)
        file_meta.FileMetaInformationGroupLength = file_meta_length
        ds.file_meta = file_meta
        ds.is_implicit_VR = False
        ds.is_little_endian = True
        ds.save_as(file_path, write_like_original=False)
    return ds


def dicomrt_to_nrrd_file(dicom_path, nrrd_path):
    """
    Convert a DICOM-RT file to a Nrrd file including header (assume one slice)

    Parameters
    ----------
    dicom_path : str
        The path of the DICOM-RT file to read from
    nrrd_path : str
        The path of the Nrrd file to write to
    Returns
    -------
    None

    """
    dicom_slice = pydicom.dcmread(dicom_path)
    nrrd_data, nrrd_header = dicomrt_to_nrrd(dicom_slice, file_path=nrrd_path)
    nrrd.write(nrrd_path, nrrd_data, nrrd_header)


def dicomrt_to_nrrd(dicom_data, file_path=None):
    """
    Given a dicomrt file, generate a nrrd structure from it

    Parameters
    ----------
    dicom_data : Dataset
        A python list of pydicom-read images
    file_path : str, optional
        Path to write the resulting structure set file

    Returns
    -------
    nrrd_data : ndarray
        A nrrd dataset containing a matrix of image data
    nrrd_header : Dictionary
        A Nrrd header dictionary

      """
    # dimensions of the resulting matrix
    dimensions = (dicom_data.Rows, dicom_data.Columns, dicom_data.NumberOfSlices)

    ds = dicom_data

    ds_origin = ds.ImagePosition
    ds_directions = ds.PixelSpacing
    ds_directions.append(ds.SpacingBetweenSlices)
    directions = np.array((ds_directions[0], ds_directions[1], ds_directions[2]))  # convert from pydicom multivalue

    # add contours
    contour_list = contours.pydicom_to_contours(ds)
    nrrd_data = contours.contours_to_image(contour_list, ds_origin, directions, sizes=dimensions)

    for contourSequence in ds.ROIContourSequence:
        roi = contourSequence.ReferencedROINumber
        for roiContour in contourSequence.ContourSequence:
            contour = roiContour.ContourData

            contour_slice = np.zeros((dimensions[0], dimensions[1]))
            x = contour[0::3]
            y = contour[1::3]

            # area to figure out if it is a shape contour (positive) or a hole contour (negative)
            area = 0.5 * (np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            zf = int(round((contour[2] - ds_origin[2]) / ds_directions[2]))  # z always same

            # convert each point
            for index in range(0, len(x)):
                xf = int(round((x[index] + 0.5 - ds_origin[0]) / ds_directions[0]))
                yf = int(round((y[index] + 0.5 - ds_origin[1]) / ds_directions[1]))
                contour_slice[xf, yf] = 1

            # mask it
            contour_filled = ndimage.binary_fill_holes(contour_slice)
            contour_masked = ma.masked_array(data=nrrd_data[:, :, zf], mask=False)

            if area > 0:
                contour_masked.mask = contour_filled
                nrrd_data[:, :, zf] = ma.filled(contour_masked, roi)

            else:
                contour_masked.mask = (contour_filled - contour_slice)
                nrrd_data[:, :, zf] = ma.filled(contour_masked, 0)

    # build the Nrrd header
    nrrd_header = OrderedDict()
    nrrd_header['type'] = 'double'
    nrrd_header['dimension'] = 3
    nrrd_header['space'] = 'left-posterior-superior'

    nrrd_header['sizes'] = np.array(dimensions)
    nrrd_header['space directions'] = np.array(((float(dicom_data.PixelSpacing[0]), 0., 0.),
                                                (0., float(dicom_data.PixelSpacing[1]), 0.),
                                                (0., 0., float(dicom_data.SpacingBetweenSlices)))
                                               )
    nrrd_header['encoding'] = 'gzip'
    nrrd_header['endian'] = 'little'
    nrrd_header['kinds'] = ('domain', 'domain', 'domain')
    nrrd_header['space origin'] = np.array((float(dicom_data.ImagePosition[0]),
                                            float(dicom_data.ImagePosition[1]),
                                            float(dicom_data.ImagePosition[2])))

    # write to file(s)
    if file_path is not None:
        nrrd.write(file_path, nrrd_data, nrrd_header)

    return nrrd_data, nrrd_header


def dicom_to_nrrd(dicom_data, file_path=None):
    """
    Given a dicom file, generate a nrrd structure from it

    Parameters
    ----------
    dicom_data : Dataset
        A python list of pydicom-read images
    file_path : str, optional
        Path to write the resulting structure set file

    Returns
    -------
    nrrd_data : ndarray
        A nrrd dataset containing a matrix of image data
    nrrd_header : Dictionary
        A Nrrd header dictionary

      """
    # dimensions of the resulting matrix
    # We should add a try catch if the number of slices is not in the DICOM
    dimensions = (dicom_data[0].Rows, dicom_data[0].Columns, len(dicom_data))

    ds = dicom_data[0]

    # ds_origin = ds.ImagePosition
    ds_directions = ds.PixelSpacing
    ds_directions.append(ds.SliceThickness)

    # add contours
    nrrd_data = contours.generate_array_from_dicom(dicom_data)

    # build the Nrrd header
    nrrd_header = OrderedDict()
    nrrd_header['type'] = 'double'
    nrrd_header['dimension'] = 3
    nrrd_header['space'] = 'left-posterior-superior'

    nrrd_header['sizes'] = np.array(dimensions)
    nrrd_header['space directions'] = np.array(((float(ds.PixelSpacing[0]), 0., 0.),
                                               (0., float(ds.PixelSpacing[1]), 0.),
                                               (0., 0., float(ds.SliceThickness)))
                                               )
    nrrd_header['encoding'] = 'gzip'
    nrrd_header['endian'] = 'little'
    nrrd_header['kinds'] = ('domain', 'domain', 'domain')
    nrrd_header['space origin'] = np.array((float(ds.ImagePositionPatient[0]),
                                            float(ds.ImagePositionPatient[1]),
                                            float(ds.ImagePositionPatient[2])))

    # write to file(s)
    if file_path is not None:
        nrrd.write(file_path, nrrd_data, nrrd_header)

    return nrrd_data, nrrd_header


def image_file_type(image_path):
    """
    Get the type extension from an image file path.
    If the path ends in .gz, grab the prior one as well

    Parameters
    ----------
    image_path : str
        The pathname of the image file

    Returns
    -------
    file_type : str
        The extension of the file name, pluz .gz if it is included
    """
    (path, file_type) = os.path.splitext(image_path)
    if file_type == '.gz':
        (_, file_type) = os.path.splitext(path)
        file_type = file_type + '.gz'
    return file_type


def sitk_converter(reader_type, reader_path, writer_type, writer_path):
    """
    SimpleITX reader/writer stub to be used ina number of file converters

    Parameters
    ----------
    reader_type : str
        The simpleITK type for the input
        TODO check simpleITK for valid values
    reader_path : str
        the file path for the input reader
    writer_type
        The simpleITK type for the output
        TODO check simpleITK for valid values
    writer_path
       the file path for the output reader

    Returns
    -------
    None

    """
    # reader
    input_reader = SimpleITK.ImageFileReader()
    input_reader.SetImageIO(reader_type)
    input_reader.SetFileName(reader_path)
    img_ref = input_reader.Execute()

    # writer
    output_writer = SimpleITK.ImageFileWriter()
    output_writer.SetImageIO(writer_type)
    output_writer.SetFileName(writer_path)
    output_writer.Execute(img_ref)


def nrrd_to_nifti_file(nrrd_path, nifti_path):
    """
    SimpleITX Nrd to Nifti file converter

    Parameters
    ----------
    nrrd_path : str
        the file path for the input reader in Nrrd format
    nifti_path
       the file path for the output reader in Nifti format

    Returns
    -------
    None

    """
    sitk_converter('NrrdImageIO', nrrd_path, 'NiftiImageIO', nifti_path)


def nifti_to_nrrd_file(nifti_path, nrrd_path):
    """
    SimpleITX Nrd to Nifti file converter

    Parameters
    ----------
    nifti_path : str
        the file path for the input reader in Nifti format
    nrrd_path
       the file path for the output reader in Nrrd format

    Returns
    -------
    None

    """
    sitk_converter('NiftiImageIO', nifti_path, 'NrrdImageIO', nrrd_path)


def convert_file(from_path, from_type, to_path, to_type, logger):
    if from_type == '.nrrd':
        if to_type == '.nii':
            nrrd_to_nifti_file(from_path, to_path)
        if to_type == '.dcm':
            nrrd_to_dicomrt_file(from_path, to_path)

    elif from_type == '.nii':
        if to_type == '.nrrd':
            nrrd_to_nifti_file(from_path, to_path)
        if to_type == '.dcm':
            if logger is not None:
                logger.log_info("still working on this")
            else:
                print("still working on this")

    elif from_type == '.dcm':
        if to_type == '.nrrd':
            dicomrt_to_nrrd_file(from_path, to_path)
        if to_type == '.nii':
            if logger is not None:
                logger.log_info("still working on this")
            else:
                print("still working on this")

    else:
        if logger is not None:
            logger.log_info("cannot convert " + from_type + " to " + to_type + "(yet)")
        else:
            print("cannot convert " + from_type + " to " + to_type + "(yet)")

        logger.log_info("cannot convert " + from_type + " to " + to_type + "(yet)")
