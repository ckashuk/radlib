#!/usr/bin/env python
import time

import yaml
from flywheel_gear_toolkit import GearToolkitContext
import os

base_image = 'rrs_radsurv'
scripts_label = 'scripts'
active_fw_name = f'{base_image}_{time.time()}'
active_label = 'active'
active_script_label = 'active_script_name'

def fws_add_script(container, script_info):
    container = container.reload()
    info = container.info
    scripts = info.get(scripts_label, [])
    scripts.append(script_info)
    info[scripts_label] = scripts
    container.update_info(info)


# Get the gear client
gear_context = GearToolkitContext()

# Grab client from gear context
fw_client = gear_context.client

# Get the analysis container object from Flywheel where this gear was started (session)
analysis_from = fw_client.get(gear_context.destination["id"])
analysis_from = analysis_from.reload()
# if analysis_from.get('active') is None:
#    raise Exception(f'Processor is not active for {os.path.basename(os.path.dirname(__file__))}!')
# get the parents of this analysis to build the script
group_id = analysis_from.parents["group"]
project = fw_client.get_project(analysis_from.parents["project"])
subject = fw_client.get(analysis_from.parents["subject"])
session = fw_client.get(analysis_from.parents["session"])

# create the script
# TODO: 202507 csk add function to build for specific processor
script_info = {
    'base_image': base_image,
    'active_fw_name': active_fw_name,
    'filesets': {
        'dicom_raw': f'fw://{group_id}/{project.label}/{subject.label}/{session.label}/*/*.dicom.zip',
        'nifti_raw': f'fw://{group_id}/{project.label}/{subject.label}/{session.label}/*/*.nii.gz',
        'preprocessed': f'fw://{group_id}/{project.label}/{subject.label}/{session.label}/preprocessed/*',
        # 'nifti_raw_modalities_niiQuery.csv': '/home/aa-cxk023/share/files/nifti_raw_modalities_niiQuery.csv'
        }
    }

try:
    # Get the analysis container object from Flywheel where the processor will look for scripts:
    analysis = fw_client.resolve(f'{group_id}/{project.label}/analyses/{script_info["base_image"]}')['path'][-1]

    # submit the script
    fws_add_script(analysis, script_info)

    # wait for the cript to run
    analysis = analysis.reload()
    active = analysis.info.get(active_label)
    if active:
        active_script = analysis.info.get(active_script_label)
        while active_script != active_fw_name:
            time.sleep(3)
            analysis = analysis.reload()
            active_script = analysis.info.get(active_script_label)

        while active_script == active_fw_name:
            time.sleep(3)
            analysis = analysis.reload()
            active_script = analysis.info.get(active_script_label)


except Exception as e:
    print("exception", e)
    raise Exception(f'Not connected to a processor for {script_info["base_image"]}!')
