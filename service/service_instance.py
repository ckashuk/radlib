import glob
import inspect
import os
import time
import shutil
import logging

import yaml


class ServiceInstance:
    # necessary input environmet variable paths
    WATCH_PATH_ENV = 'RADSERVICE_WATCH_PATH_ENV'
    SCRATCH_PATH_ENV = 'RADSERVICE_SCRATCH_PATH_ENV'

    SERVICE_LABEL_ENV = 'RADSERVICE_SERVICE_LABEL_ENV'
    SINGLE_SCRIPT_PATH = 'RADSERVICE_SINGLE_SCRIPT_PATH'

    def __init__(self, service_label = None):
        # get paths
        self.watch_path = os.environ[self.WATCH_PATH_ENV]
        self.log_path = f'{self.watch_path}/logs'
        os.makedirs(self.log_path, exist_ok=True)
        self.scratch_path = os.environ[self.SCRATCH_PATH_ENV]

        # get label
        self.service_label = os.environ[self.SERVICE_LABEL_ENV]

        if service_label is not None:
            self.service_name = service_label

        self.processor = None
        self.processor_name = None

        # set up logging
        self.service_log_path = f'{self.log_path}/{self.service_label}.log'
        self.logger = logging.getLogger(self.service_label)

        logging.basicConfig(
            filename=self.service_log_path,
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')

        # single run: get script path
        self.single_script_path = os.environ.get(self.SINGLE_SCRIPT_PATH, None)
        if self.single_script_path is not None:
            shutil.copy(self.single_script_path, self.watch_path)

    def default_processor(self, script_path):
        # always call setup first
        self.set_up(script_path)

        # write to an output file
        with open(f'{self.scratch_path}/{self.script_name}.txt', 'a') as f:
            f.writelines(f'default_processor on script {self.script_name} service {self.service_label}')

        # always call cleanup last
        self.clean_up(script_path)
        self.logger.info(f'finished default_processor on {os.path.basename(script_path)}')

    def set_up(self, script_path):
        # replace this with a custom name that you want to use
        if self.processor_name is None:
            self.processor_name = inspect.currentframe().f_code.co_name

        # load the script
        with open(script_path) as yaml_path:
            self.script_info = yaml.safe_load(yaml_path)
            self.processor_name = self.script_info['service_name']

        self.logger.info(f'started {self.processor_name} on {os.path.basename(script_path)}')

        # get the script name
        self.script_name = self.script_info.get('service_name', 'NO_NAME')


    def clean_up(self, script_path):
        print("clean up!!!")
        new_path = f'{self.input_path}/processed/{os.path.basename(script_path)}'
        shutil.move(script_path, new_path)
        self.logger.info(f'finished {self.processor_name} on {os.path.basename(script_path)}')

    def is_active(self):
        return self.active


    def get_unique_name(self):
        # TODO: 202504 csk better way to handle this!
        time.sleep(1)
        timestamp = time.time()
        return f'{self.service_name}_{timestamp}'


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

        while self.is_active():
            new_logger.info("watch")
            print("watch")
            # check folder
            script_paths = glob.glob(f'{self.watch_path}/*.yaml')

            if len(script_paths) > 0:
                new_logger.info("found!")
                # move the file with a try to avoid race condition
                new_path = f'{active_path}/{os.path.basename(script_paths[0])}'
                try:
                    # move next script to active
                    # time.sleep(random.randint(2, 6))
                    shutil.move(script_paths[0], new_path)

                    # test that it's the right type?

                    # start process on script
                    self.processor(self, new_path)

                except Exception as e:
                    print("Exception", e)
                    continue
            if self.single_script_path is not None:
                break

            # pause?
            time.sleep(5)


    def start(self, active_path=None, finished_path=None):
        self.active = True
        # self.proc = multiprocessing.Process(target=self.watch, args=(active_path, finished_path))
        # self.proc.start()
        self.watch(active_path, finished_path)
        self.logger.info(f'starting service {self.service_name}')


    def stop(self):
        # TODO: 202504 csk make this better, more functions??
        print("stop!!!")
        self.active = False
        self.proc.kill()
        self.logger.info(f'stopping service {self.service_name}')
