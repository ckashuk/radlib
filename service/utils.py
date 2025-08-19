import os
import shutil

import yaml


def parse_script(script_path):
    with open(script_path) as file:
        script = yaml.safe_load(file)

        return script

def generate_docker_call(script):
    return "run"

"""
def load_image(input_path, scratch_path):
    items = input_path.split("/")[-3]
    subject = items[-3]
    session = items[-2]
    acquisition = items[-1]
    file = items[0]

    os.makedirs(f'{scratch_path}/{subject}/{session}', exist_ok=True)

    if input_path.startswith('fw://'):
        fw_client = uwhealthaz_client()

        # flywheel address
        project = items[-4]
        group = items[-5]
        fw_client.resolve(f'/{group}/{project}/{subject}/{session}/{acquisition}/{file}')
        # find the flywheel location(s) of the file

        files = [file]
        if file == '*':


        # download it to the scratch space

    else:
        # local path
        self.logger.info("making more dirs")
        os.makedirs(f'{scratch_path}/nifti_raw/{subject}/{session}', exist_ok=True)
        input_path = f'/local/{input_path}'
        if input_path.endswith('*'):
            for input_path in glob.glob(input_path):
                print(f"copy {input_path} to {scratch_path}/nifti_raw/{subject}/{session}")
                shutil.copy(input_path, f'{scratch_path}/nifti_raw/{subject}/{session}')
        else:
            print(f"copy {input_path} to {scratch_path}")
            shutil.copy(input_path, scratch_path)

"""
