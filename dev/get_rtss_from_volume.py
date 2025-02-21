import SimpleITK as sitk
import numpy as np
import glob
import nrrd
import pydicom
import os
from dcm.converters import nifti_to_nrrd_file, nrrd_to_dicomrt_file, nrrd_to_dicomrt

# seg_nii_path= 'H:/data/SPORE_P11_test/segmentations (5)/prostate.nii.gz'
seg_nii_path='//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Users/Carl/segmentations/P01_obl_regrid_seg/prostate.nii.gz'
pet_paths=glob.glob('//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Research/ProstateSPORE/DODDatasetComplete/CleanedProject/prosspore/DODProjectRead/17009_Pyl01/PET1/PET AC Prostate/dicom/*.dcm')
pet_data = [pydicom.dcmread(pet_path) for pet_path in pet_paths]
seg_nrrd_path = seg_nii_path.replace(".nii.gz", ".nrrd")
seg_rtss_path = f'c:/Users/CXK023/Documents/{os.path.basename(seg_nii_path.replace(".nii.gz", ".rtss.dcm"))}'

nifti_to_nrrd_file(seg_nii_path, seg_nrrd_path)
nrrd_data, nrrd_header = nrrd.read(seg_nrrd_path)

nrrd_to_dicomrt(nrrd_data, nrrd_header, pet_data, file_path=seg_rtss_path)

rtss = pydicom.dcmread(seg_rtss_path)
print(rtss)

