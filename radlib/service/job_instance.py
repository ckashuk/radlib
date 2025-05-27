import glob
import inspect
import os
import random
import sys
import time
import shutil
import logging

import yaml


class JobInstance:


    def __init__(self, service_instance, job_name, job_script):
        # get paths
        self.service_instance = service_instance

        # get name
        self.job_name = "job_instance"

        if job_name is not None:
            self.job_name = job_name

        self.job_script = job_script

        # set up logging
        self.job_log_path = f'{service_instance.logs_path}/{self.job_name}.log'
        self.logger = logging.getLogger(self.job_name)
        logging.basicConfig(
            filename=self.job_log_path,
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')

        # not active on create
        self.active = False

        self.set_up(self.script_info)


    def get_unique_name(self):
        # TODO: 202504 csk better way to handle this!
        time.sleep(1)
        timestamp = time.time()
        return f'{self.job_name}_{timestamp}'


    def set_up(self, script_info):
        self.script_info = script_info
        self.processor_name = self.script_info['service_name']

        # get some scratch space
        self.scratch_path = f'{self.service_instance.scratch_path}/{self.get_unique_name()}'

        # get the script name
        self.script_name = self.script_info.get('service_name', 'NO_NAME')


    def clean_up(self, script_path):
        print("clean up!!!")
        new_path = f'{self.service_instance.output_path}/processed/{os.path.basename(script_path)}'
        shutil.move(script_path, new_path)
        self.logger.info(f'finished {self.processor_name} on {os.path.basename(script_path)}')

    def is_active(self):
        return self.active


    def run(self):
        self.logger = logging.getLogger(self.job_name)
