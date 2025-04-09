import glob
import inspect
import multiprocessing
import os
import random
import subprocess
import sys
import time
import shutil
import logging

import yaml





class ServiceInstance:
    # necessary input environmet variable paths
    INPUT_PATH_ENV = 'RADSERVICE_INPUT_PATH'
    OUTPUT_PATH_ENV = 'RADSERVICE_OUTPUT_PATH'
    LOGS_PATH_ENV = 'RADSERVICE_LOGS_PATH'
    SCRATCH_PATH_ENV = 'RADSERVICE_SCRATCH_PATH'

    SERVICE_NAME_ENV = 'RADSERVICE_NAME'

    def __init__(self, processor=None, service_name = None):
        # get paths
        self.input_path = os.environ[self.INPUT_PATH_ENV]
        self.output_path = os.environ[self.OUTPUT_PATH_ENV]
        self.scratch_path = os.environ[self.SCRATCH_PATH_ENV]
        self.logs_path = os.environ[self.LOGS_PATH_ENV]

        # get name
        self.service_name = os.environ[self.SERVICE_NAME_ENV]

        if service_name is not None:
            self.service_name = service_name

        # define processor
        if processor is None:
            self.processor = self.default_processor
        else:
            self.processor = processor

        # set up logging
        self.service_log_path = f'{self.logs_path}/{self.service_name}.log'
        self.logger = logging.getLogger(self.service_name)
        logging.basicConfig(
            filename=self.service_log_path,
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')

        # not active on create
        self.active = False
        self.proc = False

    def default_processor(self, script_path):
        # always call setup first
        self.set_up(script_path)

        # write to an output file
        with open(f'{self.output_path}/{self.script_name}.txt', 'a') as f:
            f.writelines(f'default_processor on script {self.script_name} service {self.service_name}')

        # always call cleanup last
        self.clean_up(script_path)
        self.logger.info(f'finished default_processor on {os.path.basename(script_path)}')

    def set_up(self, script_path):
        # replace this with a custom name that you want to use
        self.processor_name = inspect.currentframe().f_code.co_name

        # load the script
        self.logger.info(f'started {self.processor_name} on {os.path.basename(script_path)}')

        with open(script_path) as yaml_path:
            self.script_info = yaml.safe_load(yaml_path)

        # get the script name
        self.script_name = self.script_info.get('service_name', 'NO_NAME')


    def clean_up(self, script_path):
        new_path = f'{self.output_path}/processed/{os.path.basename(script_path)}'
        shutil.move(script_path, new_path)
        self.logger.info(f'finished {self.processor_name} on {os.path.basename(script_path)}')

    def is_active(self):
        return self.active

    def is_separate_process(self):
        return self.proc is not None

    def watch(self, active_path=None, finished_path=None):
        # csk need to get the logger again when run in a separate process!
        new_logger = logging.getLogger(self.service_name)
        logging.basicConfig(
            filename=self.service_log_path,
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')

        if active_path is None:
            active_path = f'{self.input_path}/active'
        if finished_path is None:
            finished_path = f'{self.output_path}/finished'
        while self.is_active():
            # check folder
            script_paths = glob.glob(f'{self.input_path}/*.yaml')

            if len(script_paths) > 0:
                # move the file with a try to avoid race condition
                new_path = f'{active_path}/{os.path.basename(script_paths[0])}'
                try:
                    # move next script to active after some random time to avoid race condition
                    time.sleep(random.randint(2, 6))
                    shutil.move(script_paths[0], new_path)

                    # start process on script
                    # we are cheating a little here, to allow the function variable to from from within and without an object. better to subclass?
                    self.processor(self, new_path)
                except Exception as e:
                    continue

            # pause?
            time.sleep(5)


    def start(self, active_path=None, finished_path=None, same_process=False):
        self.active = True

        if same_process:
            self.watch(active_path, finished_path)
        else:
            self.proc = multiprocessing.Process(target=self.watch, args=(active_path, finished_path))
            self.proc.start()

        self.logger.info(f'starting service {self.service_name}')


    def stop(self):
        # TODO: 202504 csk make this better, more functions??
        self.active = False
        if self.is_separate_process():
            self.proc.kill()
        self.logger.info(f'stopping service {self.service_name}')
