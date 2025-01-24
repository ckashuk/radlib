import glob

import SimpleITK as sitk
from win32con import DMDITHER_RESERVED7

from pydicom_generate.dcm.dcm_generators import generate_dcm_from_volume, generate_projection, generate_grid
from pydicom_generate.dcm.dcm_loaders import load_dicom_series_sitk


pet = sitk.GetArrayFromImage(sitk.ReadImage('H:/data/SPORE_P11_test/pet7.nrrd'))
regrid_img = sitk.ReadImage('H:/data/SPORE_P11_test/test7.nrrd')
sitk.WriteImage(regrid_img,'H:/data/SPORE_P11_test/test7.nii.gz' )
regrid = sitk.GetArrayFromImage(regrid_img)

regrid[pet < 5000] = 0

rere = sitk.GetImageFromArray(regrid)
rere.SetOrigin(regrid_img.GetOrigin())
rere.SetSpacing(regrid_img.GetSpacing())
sitk.WriteImage(rere, 'H:/data/SPORE_P11_test/rere7.nrrd')
exit()

dcm_root = '//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Research/ProstateSPORE/DODDatasetComplete/CleanedProject/prosspore/DODProjectRead'
# image_files = glob.glob(f'{dcm_root}/17009_pyl17/PET1/Obl Axial T2 Prostate/dicom/*.dcm')
# img = sitk.ReadImage(image_files)

ortho_dcm_root = f'h:/data/SPORE_P11_test/SPORE_P11_mr_ortho'
"""
generate_dcm_from_volume(generate_projection(img), ortho_dcm_root, ref_image=img,
                         origin = [-298.4375, -298.4375, -114.89500427246],
                         spacing= [3.125, 3.125, 2.77999999306417],
                         direction=[1, 0, 0, 0, 1, 0, 0, 0, 1])
"""

pet7, _, _ = load_dicom_series_sitk(f'{dcm_root}/17009_Pyl11/PET1/PET AC Prostate/dicom')
mr7, _, _ = load_dicom_series_sitk(f'{dcm_root}/17009_Pyl11/PET1/Obl Axial T2 Prostate/dicom')
ortho7, _, _ = load_dicom_series_sitk(ortho_dcm_root)

generate_dcm_from_volume(generate_projection(mr7, generate_grid(pet7)), f'h:/data/SPORE_P11_test/SPORE_P11_mr_projection', pet7)
test7, _, _ = load_dicom_series_sitk(f'h:/data/SPORE_P11_test/SPORE_P11_mr_projection')

print(pet7.GetOrigin(), pet7.GetSize(), pet7.GetSpacing(), pet7.GetDirection())
print(mr7.GetOrigin(), mr7.GetSize(), mr7.GetSpacing(), mr7.GetDirection())
print(ortho7.GetOrigin(), ortho7.GetSize(), ortho7.GetSpacing(), ortho7.GetDirection())
print(test7.GetOrigin(), test7.GetSize(), test7.GetSpacing(), test7.GetDirection())

sitk.WriteImage(pet7, f'h:/data/SPORE_P11_test/pet7.nrrd')
sitk.WriteImage(mr7, f'h:/data/SPORE_P11_test/mr7.nrrd')
sitk.WriteImage(ortho7, f'h:/data/SPORE_P11_test/ortho7.nrrd')
sitk.WriteImage(test7, f'h:/data/SPORE_P11_test/test7.nrrd')
