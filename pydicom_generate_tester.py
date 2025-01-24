from pydicom import FileDataset
import numpy as np
import pydicom

from pydicom_generate.dcm.dcm_generators import generate_dcm_pydicom, generate_dcm_dcmtk
from pydicom_generate.dcm.dcm_loaders import load_dicom_series_from_slices


ref_jpg_path = 'H:/source/PediatricBoneAgeCollaborationAidoc/standards/M10.jpg'
output_dcm_path = 'H:/source/PediatricBoneAgeCollaborationAidoc/work_csk/M10.dcm'

dcm = generate_dcm_dcmtk(ref_jpg_path, output_dcm_path)
exit()


def save_dicom_series_to_nrrd(slices, path):
    dcm = generate_dcm_pydicom('CT', pixel_data, origin=[100, 100, 0], spacing=[10, 10, 10])
    slices2_pd, img2_pd, metadata2_pd = load_dicom_series_from_slices(dcm)
    print(len(slices2_pd))


pixel_data = np.random.randint(-3000, 3000, (100, 100, 50))

slices1 = generate_dcm_pydicom('SC', pixel_data, origin=[100.0000, 100.0000, 0.0], spacing=[10.0, 10.0, 10.0])
# dcm2 = generate_dcm_pydicom('CT', pixel_data, origin=(-125, -125, 25), spacing=(1, 1, 5))
# dcm3 = generate_dcm_pydicom('CT', pixel_data, origin=(-125, -125, 25), spacing=(1, 1, 5))
# dcm4 = generate_dcm_pydicom('CT', pixel_data, origin=(-300, -300, -150), spacing=(0.5, 0.5, 2))
save_dicom_series_to_nrrd(slices1, '/Users/carlkashuk/Documents/dcm1.nrrd')
exit()

def add_list_to_set(l, s=None):
    if s is None:
        s = set()
    for item in l:
        s.add(item)
    return s

def compare_dicoms(dcm1, dcm2):
    all_tags = add_list_to_set(dcm2, add_list_to_set(dcm1))
    for item in dcm2:
        all_tags.add(item)
    print(len(list(all_tags)), len(dcm1), len(dcm2))


ct_reference_dcm_path = '../pydicom_generate/dcm/1.2.826.0.1.3680043.2.629.20190306.10527514967919552016108815494.CT.dcm'
ct_dicom_reference: FileDataset = pydicom.dcmread(ct_reference_dcm_path)

ct_std = load_dicom_standard('CT')
ct_std_all_tags = [tag['tagid'] for tag in ct_std]
ct_std_required_tags = [tag['tagid'] for tag in  ct_std if tag['type'] == '1']

ct_dicom_template = generate_valid_template_dcm('CT')
ct_dicom_dcm = pydicom.dcmread(ct_reference_dcm_path)

ct_template_used_tags = list(ct_dicom_template.keys())
ct_reference_used_tags = list(ct_dicom_reference.keys())

# compare_dicoms(ct_std_all_tags, ct_template_used_tags)
# compare_dicoms(ct_std_all_tags, ct_reference_used_tags)
# compare_dicoms(ct_template_used_tags, ct_reference_used_tags)
for tag in ct_dicom_reference.keys():
    if tag == (0x7FE0,0x0010):
        continue
    print(tag, ct_dicom_reference.get(tag))
exit()


for tag in ct_required_tags:
    tag_id = tag['tagid']
    tag_name = tag['name']
    tag_type = tag['type']
    module_name = tag['module_name']
    module_use = tag['module_use']
    value = ct_dicom_template.get(get_tag_id_key(tag_id))
    value2 = ct_dicom_dcm.get(get_tag_id_key(tag_id))
    # if value is None and module_use =='M':
    if value is not None:
        print(module_name, module_use, tag_id, tag_name, tag_type, (value == value2), value, value2)

