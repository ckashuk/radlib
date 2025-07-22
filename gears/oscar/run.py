#!/usr/bin/env python
import yaml
import glob
from flywheel_gear_toolkit import GearToolkitContext

from radlib.fws.fws_fileset import FWSFileSet

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

fs_renal = FWSFileSet('renal', 'fw://oscargroup/oscar_test_project/TCGA-B0-5702/CT ABDOMEN/2-ABD W_O/2 - ABD W_O.dicom.zip')
print(fs_renal.get_local_paths())