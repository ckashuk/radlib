import glob
import subprocess
import yaml
import os

from radlib.fw.flywheel_clients import uwhealthaz_client
from radlib.fws.fws_utils import fws_create_paths, fws_copy_file, \
    fws_separate_flywheel_labels, fws_download_files_from_flywheel, fws_upload_files_to_flywheel
from radlib.service.service_instance import ServiceInstance


def total_segmentator_processor(self, script_path):
    # always call setup first
    self.set_up(script_path)

    # unique name for the processor
    self.processor_name = 'Total Segmentator processor'
    self.logger.info(self.processor_name)

    # total segmentator preprocessing

    try:
        # get scratch space
        unique_name = self.get_unique_name()
        scratch_path = f'/scratch/{unique_name}'
        log_path = f'/logs/{unique_name}.log'
        fws_create_paths([f'{scratch_path}/logs'])

        # get parameters
        input_path = self.script_info['input_path']
        output_path = self.script_info['output_path']

        local_input_path = f'{scratch_path}/{os.path.basename(input_path)}'
        local_output_path = f'{scratch_path}/{os.path.basename(output_path)}'

        if input_path.startswith('fw://'):
            # flywheel download
            fw_client = uwhealthaz_client()
            _, _, subject, session, _, file = fws_separate_flywheel_labels(input_path)
            if '-' in session:
                session = session.replace('-', '').split(' ')[0]
            fws_download_files_from_flywheel(fw_client, input_path, local_input_path)

        else:
            # local download
            fws_copy_file(input_path, local_input_path, self.logger)

        # run process
        command_text = ['TotalSegmentator', '-i', local_input_path, '-o', local_output_path, '-ta', 'total_mr', '-ml', '-v']
        self.logger.info(f"run unique process {log_path}")
        p = subprocess.run(command_text, text=True)
        # exit_code = p.wait()
        # exec(' '.join(command_text))

        # get result
        if input_path.startswith('fw://'):
            fws_upload_files_to_flywheel(uwhealthaz_client(),f'{local_output_path}', output_path, self.logger)
        else:
            fws_copy_file(f'{local_output_path}.nii', f'{output_path}.nii', self.logger)

        self.logger.info(f"run unique process {log_path} finished!!!")

    except Exception as e:
        print("exception", e)

    # always call cleanup last
    self.clean_up(script_path)


if __name__ == "__main__":
    # instantiate the ServiceInstance, give it a processor function, and start it!
    # TODO: 202504 csk find better way(s) to stop!
    instance = ServiceInstance()
    instance.processor = total_segmentator_processor
    instance.start()
