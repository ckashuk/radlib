from extras.dicom_standard_validation.spec_reader.edition_reader import EditionReader
from pathlib import Path

from radlib.dcm import check_for_valid_modality, dicom_modalities

def get_tag_id_key(tag_id):
    tag_id_pair = tag_id.replace('(', '0x').replace(',', ',0x').replace(')', '').split(',')
    tag_id_key = (int(tag_id_pair[0], 16), int(tag_id_pair[1], 16))
    return tag_id_key

def load_dicom_standard(modality):
    check_for_valid_modality(modality)

    standard_tags = []

    # code "borrowed" from dicom-valiidator, part of pydicom github. TODO: reference
    standard_path = str(Path.home() / "dicom-validator")
    revision = "current"
    recreate_json=False
    edition_reader = EditionReader(standard_path)
    base_path = edition_reader.get_revision(revision, recreate_json)
    json_path = Path(base_path, "json")
    dicom_info = EditionReader.load_dicom_info(json_path)

    # wwe know modality is valid, so find dicom standard ciod
    ciod = dicom_modalities[modality]['ciod']

    # modules for this modality's standard tags
    module = dicom_info.iods[ciod][('modules')]

    # traverse the module dict for tags
    for module_name, module_info in module.items():
        # print(">>>", module_name, module_info)
        module_use = module_info['use']
        module_tags = dicom_info.modules[module_info['ref']]
        for tag_id, values in module_tags.items():
            # TODO: figure this out?
            if tag_id=='include':
                continue
            tag_name = values['name']
            tag_type = values['type']
            # TODO: figure out how to deal with xx?
            if 'xx' in tag_id:
                # print(f"tag_id={tag_id} {tag_name}??")
                continue
            # if tag_name == 'Focal Spot(s)':
            #     print(module_name, tag_name, tag_type)

            # are there items under this one?
            items = values.get('items', [])
            if len(items)>0:
                for subid, subvalues in items.items():
                    if subid=='include':
                        continue

                    # if subvalues['name'] == 'Focal Spot(s)':
                    #     print(module_name, tag_id, tag_name, tag_type, subid, subvalues)
                    # TODO: kludge: force subtags to type of parent tag
                    subvalues['tagid'] = subid
                    subvalues['type'] = tag_type
                    subvalues['module_name'] = module_name
                    subvalues['module_use'] = module_use
                    if 'xx' in subid:
                        # print(f"tag_id={subid} {subvalues}??")
                        continue

                    standard_tags.append(subvalues)
            else:
                values['tagid'] = tag_id
                values['module_name'] = module_name
                values['module_use'] = module_use
                standard_tags.append(values)

    return standard_tags

