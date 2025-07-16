#!/usr/bin/env python
import json

from flywheel_gear_toolkit import GearToolkitContext

from fws_utils import uwhealthaz_client, get_project_specific_parameters

# Get the gear client
context = GearToolkitContext()
script_header = 'fws'
script_footer = '.ipynb'
rerun = False # TODO: 202503 csk make this configuration

fw_client = uwhealthaz_client()

group, project, subject = get_project_specific_parameters(fw_client)

# for each script file attached ot the project
# TODO: 202503 csk expand this to subject and/or session, or not very useful?
for code_file in [code_file for code_file in project.files if code_file.name.startswith(script_header) and
                  code_file.name.endswith('.ipynb')]:

    # check if it's been run before
    script_tag = code_file.name.replace(script_footer, '')
    print(script_tag)
    if script_tag not in group.tags:
        # add tag to the group
        group.add_tag(script_tag)

    elif script_tag in subject.tags:
        print(f"already ran script {script_tag}")
        continue

    # TODO: parse the notebook
    code_string = code_file.read().decode('utf-8', errors='ignore')
    code = json.loads(code_string)

    # cat the cells and run
    for cell in code['cells']:
        if cell['cell_type'] == 'code':
            if cell['source'].starts_with('# replace this with the generated data within the gear'):
                continue
            print(cell['source'])

    # tag the
    subject.add_tag(script_tag)
