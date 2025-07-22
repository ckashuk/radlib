#!/usr/bin/env python
import yaml
from flywheel_gear_toolkit import GearToolkitContext

def fws_add_script(container, script_info):
    container = container.reload()
    info = container.info
    scripts = info.get('scripts', [])
    scripts.append(script_info)
    info['scripts'] = scripts
    container.update_info(info)


# Get the gear client
gear_context = GearToolkitContext()

# Grab client from gear context
fw_client = gear_context.client

# Get the analysis container object from Flywheel where this gear was started (session)
analysis_from = fw_client.get(gear_context.destination["id"])

# get the parents of this analysis to build the script
group_id = analysis_from.parents["group"]
project = fw_client.get_project(analysis_from.parents["project"])
subject = fw_client.get(analysis_from.parents["subject"])
session = fw_client.get(analysis_from.parents["session"])

# create the script
# TODO: 202507 csk add function to build for specific processor
script_info = {
    'base_image': 'rrs_radsurv',
    'filesets': {
        'dicom_raw': f'fw://{group_id}/{project.label}/{subject.label}/{session.label}/dicom_raw/*',
        'nifti_raw': f'fw://{group_id}/{project.label}/{subject.label}/{session.label}/nifti_raw/*',
        'preprocessed': f'fw://{group_id}/{project.label}/{subject.label}/{session.label}/preprocessed/*',
        # 'nifti_raw_modalities_niiQuery.csv': '/home/aa-cxk023/share/files/nifti_raw_modalities_niiQuery.csv'
        }
    }

try:
    # Get the analysis container object from Flywheel where the processor will look for scripts:
    analysis_to = fw_client.resolve(f'{group_id}/{project.label}/analyses/{script_info["base_image"]}')['path'][-1]

    # submit the script
    fws_add_script(analysis_to, script_info)

except Exception as e:
    print("exception", e)
    print(f"Not connected to a processor for {script_info['base_image']}!")
