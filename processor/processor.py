import copy
import glob
import os
import re
import sys
import time
import shutil
import logging
import tempfile
import yaml
import argparse

from radlib.fw.flywheel_clients import uwhealthaz_client
from radlib.fws.fws_fileset import FWSFileSet, FWSFileSetException
from radlib.fws.fws_utils import (fws_create_paths, fws_expand_flywheel_path,
                                  fws_download_file_from_flywheel, fws_in_docker)

# templates for docker files

docker_compose_template_yaml = {
    'services': {
         'service_name': {
            'image': 'service_name_service',
            'build': '.',
            'ports': ['8003:8003'],
            'volumes': [
                '/home/aa-cxk023/share/scratch:/scratch',
                '/mnt/RadServiceCache/files:/files'
            ],
            'stdin_open': True,
            'tty': True,
            'ipc': 'host',
            'deploy': {
                'resources': {
                    'reservations': {
                        'devices': [
                            {
                                'driver': 'nvidia',
                                'count': 'all',
                                'capabilities': ['gpu']
                            }
                        ]
                    }
                }
            }
        }
    },
    'volumes': {
        'scratch': None,
        'files': None
    }
}

dockerfile_template = '''
# start with base image
FROM {base_image}

# add radlib stuff
COPY --from=radlib / /

LABEL authors="ckashuk@wisc.edu"

# uw cert stuff
# RUN DEBIAN_FRONTEND=noninteractive apt-get -y update
# RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates wget curl
COPY UWHEALTHROOT.crt /usr/local/share/ca-certificates/UWHEALTHROOT.crt
RUN chmod 644 /usr/local/share/ca-certificates/UWHEALTHROOT.crt && update-ca-certificates

# package dependencies
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

WORKDIR /app
COPY ../radservice_app.py /app/

# run it!
CMD ["python", "radservice_app.py"]
# CMD ["/bin/bash"]
'''

shell_script_template = '''
cd docker_app
# csk see if we can do without no-cache
# sudo docker compose build --no-cache && docker compose up
sudo docker compose up
'''

class Processor:
    """
    A Processor sets up an area for scratch space, defines a "processor_script" which runs
    specific code, and sets up basic logging and start/stop functions

    A Processor takes it's orders from a "script" which is a yaml file of general and specific
    values needed to run the job.

    """
    counter = 0

    def __init__(self, script_path=None, scratch_path=None ):
        # save the passed-in parameters
        self.script_path = script_path
        self.scratch_path = scratch_path

        args = Processor.parse_args()

        # update the parameters if not passed to the constructor
        if scratch_path is None:
            self.scratch_path = args.scratch_path
        if self.script_path is None and fws_in_docker():
            self.script_path = "/script.yaml"

        # must be called with a script path!
        if self.script_path is None:
            print("must be called with a script path!")
            exit()

        # save the script info
        self.script_info = Processor.load_script(script_path)


    @classmethod
    def processor_name(cls) -> str:
        """
        cheat and use the name of the class to get this automatically!

        Returns
        -------
        A string name of the processor

        """
        name = re.sub('([A-Z]+)', r'_\1',cls.__name__).lower()
        if name.startswith('_'):
            name = name[1:]
        return name


    # this method is replaced for each new processor
    def processor_script(self):
        """
        Each processor subclass has to overload this method

        """
        # print a message
        print(f"This is {self.processor_name()}!")


    def process(self, script_path):
        """

        Parameters
        ----------
        script_path

        Returns
        -------

        """
        # always call setup first
        self.set_up(script_path)

        # run it!
        self.processor_script()

        # always call cleanup last
        self.clean_up(script_path)


    @classmethod
    def run_local(cls, scratch_path, script_path):
        processor = cls(scratch_path)
        processor.process(script_path=script_path)
        # if cls.logger is not None:
        #     cls.logger.info("run_local is not implemented")
        #    exit()

    @staticmethod
    def watch_name(watch_path):
        name = watch_path
        if name.endswith('in'):
            name = os.path.dirname(name)
        return os.path.basename(name)

    @classmethod
    def run_watcher(cls, watch_path):
        # processor = cls(scratch_path)
        # processor.process(script_path=script_path)
        print(f"run_watcher {cls.__name__} on {Processor.watch_name(watch_path)} {watch_path}")

    @staticmethod
    def replace_token(strn, token, value):
        strn = strn.replace(token, value, 1)
        return strn

    @staticmethod
    def replace_tokens(strn, tokens):
        for token, value in tokens.items():
            tokenized_token = '{' + token + '}'
            while tokenized_token in strn:
                strn = Processor.replace_token(strn, tokenized_token, value)
        return strn

    @staticmethod
    def write_file(file_path, file_name, content):
        with open(os.path.join(file_path, file_name), "w") as f:
            f.write(content.strip())

    def add_script_to_docker_compose(self, dc_content, script_path, script_mount_name='script.yaml'):
        mount_string = f'{script_path}:/{script_mount_name}'
        # print("mount_string", mount_string)
        dc_content['services'][self.processor_docker_image_name()]['volumes'].append(mount_string)
        dc_content['volumes'][script_mount_name] = None

    def add_fileset_to_docker_compose(self, dc_content, fileset):
        mount_string = fileset.get_mount_string()
        # print("mount_string", mount_string)
        dc_content['services'][self.processor_docker_image_name()]['volumes'].append(fileset.get_mount_string())
        dc_content['volumes'][fileset.fileset_name] = None

    def processor_docker_image_name(self):
        return self.processor_name().lower()

    def run_dockerized(self):
        self.set_up()
        # Create working directory
        work_dir = 'docker_app'  # self.script_info.get('base_image', 'docker_app')
        os.makedirs(work_dir, exist_ok=True)
        # 202506 csk passing as volume now
        # shutil.copy(script_path, work_dir)
        # find folder for items to copy
        copy_dir = f'{os.path.dirname(os.path.dirname(__file__))}/processors/{self.processor_name()}'
        shutil.copy(f'{copy_dir}/radservice_app.py', work_dir)
        shutil.copy(f'{copy_dir}/requirements.txt', work_dir)
        shutil.copy(f'{copy_dir}/UWHEALTHROOT.crt', work_dir)

        # create docker-compose
        # TODO 202506 csk break this out into a separate function??
        docker_compose_content = copy.deepcopy(docker_compose_template_yaml)

        # replace processor name
        # TODO 202506 csk may be a cleaner way to do this??
        docker_compose_content['services'][self.processor_docker_image_name()] = docker_compose_content['services']['service_name']
        del docker_compose_content['services']['service_name']
        docker_compose_content['services'][self.processor_docker_image_name()]['image'] = self.processor_docker_image_name()

        # add defined filesets as volumes
        docker_compose_content['services'][self.processor_docker_image_name()]['volumes'] = [
            f'{self.scratch_path}:/scratch',
            '/mnt/RadServiceCache/files:/files'
        ]

        docker_compose_content['volumes'] = {'scratch': None, 'files': None}
        docker_compose_content['services'][self.processor_docker_image_name()]['environment'] = {}
        mount_points = {}
        for fileset in self.filesets:
            if fileset.original_path == 'scratch':
                continue

            self.add_fileset_to_docker_compose(docker_compose_content, fileset)
            mount_points[f'{fileset.fileset_name}_MOUNT_POINT'] = fileset.get_common_path()

        self.add_script_to_docker_compose(docker_compose_content, self.script_path)

        docker_compose_content['services'][self.processor_docker_image_name()]['environment'] = mount_points

        with open(os.path.join(work_dir, "docker-compose.yaml"), "w") as f:
            yaml.safe_dump(docker_compose_content, f)

        # create Dockerfile
        dockerfile_content = Processor.replace_tokens(dockerfile_template, self.script_info)
        dockerfile_content = Processor.replace_tokens(dockerfile_content, {'script_name': os.path.basename(self.script_path)})
        Processor.write_file(work_dir, "Dockerfile", dockerfile_content.strip())

        # create shell_script
        shell_script_content = Processor.replace_tokens(shell_script_template, self.script_info)
        Processor.write_file(work_dir, "start_docker.sh", shell_script_content.strip())

        # start the docker
        os.system(f'/bin/bash {os.path.join(work_dir, "start_docker.sh")}')


    def set_up(self, script_path=None):
        class StreamToLogger:
            def __init__(self, logger, log_level):
                self.logger = logger
                self.log_level = log_level
                self.line_buffer = ""

            def write(self, message):
                if message.strip():  # Avoid logging empty lines
                    self.logger.log(self.log_level, message.strip())

            def flush(self):
                pass  # Required for compatibility with sys.stdout and sys.stderr

        # get unique name for the run
        self.script_info['unique_name'] = self.get_unique_name()
        if fws_in_docker():
            self.scratch_path = "/scratch"
        else:
            self.scratch_path = f'{tempfile.mkdtemp()}/{self.script_info.get("unique_name")}' if self.scratch_path is None else f'{self.scratch_path}/{self.script_info.get("unique_name")}'
        fws_create_paths([self.scratch_path])
        # self.script_path = script_path
        # for each set of files
        self.filesets = []
        for name, path in self.script_info['filesets'].items():
            self.filesets.append(FWSFileSet(fileset_name=name, original_path=path, scratch_path=self.scratch_path))
            print("added fileset", name, path) # , self.filesets[-1].get_common_path(), self.filesets[-1].original_path, self.filesets[-1].get_local_paths())

        # set up logging (based on script)
        if type(self.scratch_path) is tempfile.TemporaryDirectory:
            self.log_path = f'{self.scratch_path}/{self.get_unique_name()}.log'
        else:
            self.log_path = f'{self.scratch_path}/{self.get_unique_name()}.log'
        self.logger = logging.getLogger(self.processor_name())
        logging.basicConfig(
            filename=self.log_path,
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')
        # this sends to the screen too (for debugging))
        # self.logger.addHandler(logging.StreamHandler())
        # these redirect stdout, stderr to the logger
        sys.stdout = StreamToLogger(self.logger, logging.INFO)
        sys.stderr = StreamToLogger(self.logger, logging.ERROR)

        self.logger.info(f'started {self.processor_name()} on {os.path.basename(self.script_path)}')

    def clean_up(self, script_path=None):
        # move script so it doesn't get picked up again
        # new_path = f'{os.path.dirname(script_path)}/processed/'
        # os.makedirs(os.path.dirname(new_path), exist_ok=True)
        # shutil.move(script_path, new_path)
        if script_path is None:
            self.logger.info(f'finished {self.processor_name()} on {os.path.basename("/script.yaml")}')
        else:
            self.logger.info(f'finished {self.processor_name()} on {os.path.basename(script_path)}')
        logging.shutdown()

    def get_fileset(self, fileset_name):
        for fileset in self.filesets:
            if fileset.fileset_name == fileset_name:
                return fileset
        raise FWSFileSetException(f'fileset {fileset_name} does not exist!')

    def get_unique_name(self, reset_each_time=False):
        # TODO: 202504 csk better way to handle this!
        if not reset_each_time:
            try:
                return self.script_info['unique_name']
            except Exception as e:
                print("unique name not assigned yet")

        time.sleep(1)
        timestamp = time.time()
        self.unique_name = f'{self.processor_name().replace(" ", "_")}_{timestamp}'
        return self.unique_name

    def expand_file_paths(self, file_paths):
        # expand any * into the list of files
        expanded_file_paths = []
        for file_path in file_paths:
            if file_path.endswith('*'):
                if file_path.starts_with('fw://'):
                    # flywheel path, have to use client to find out what files are there
                    expanded_paths = fws_expand_flywheel_path(file_path)
                else:
                    # local storage path,just glob with ** to traverse subfolders!
                    expanded_paths = glob.glob(f'{file_path}*/*')
            else:
                expanded_paths = [file_path]

            expanded_file_paths.extend(expanded_paths)

        return expanded_file_paths


    def translate_file_paths(self, script_label, script_files, do_download=True):
        # script_files are the file paths originally sent in the script
        # expand wildcard paths to get "full list"
        script_files = self.expand_file_paths(script_files)

        # external_files are the file paths that are pointed to in the file system (non-local items such as
        # flywheel paths are downladed to scratch space!). for local file system these are the same as script_files
        external_files = []

        # local_files are the file paths that are accessed locally, from within the docker for example
        local_files = []

        for script_file in script_files:
            if script_file.startswith('fw://'):
                # flywheel path
                local_path = f'{self.scratch_path}/{script_label}'
                os.makedirs(local_path, exist_ok=True)

                # download to scratch space
                downloaded_file_path = f'{os.path.dirname(script_file)}'
                fw_client = uwhealthaz_client()
                external_file_name = fws_download_file_from_flywheel(fw_client, script_file, downloaded_file_path, do_download=do_download)
                external_files.append(external_file_name)

            else:
                external_files.append(script_file)
                local_files.append(script_file)

        self.script_info[script_label] = local_files
        self.script_info[f'{script_label}_external'] = external_files

    def get_common_file_path(self, script_label):
        # go through all io files and find the common parent folder
        self.script_info[f'{script_label}_common'] = os.path.dirname(os.path.commonpath(self.script_info.get(script_label, [])))
        self.script_info[f'{script_label}_local'] = []
        for file in self.script_info.get(script_label, []):
            self.script_info[f'{script_label}_local'].append(file.replace(self.script_info[f'{script_label}_common'], f'/{script_label}'))


    @staticmethod
    def load_script(script_path):
        # load the script
        with open(script_path, 'r') as yaml_path:
            script_info = yaml.safe_load(yaml_path)
        return script_info

    @staticmethod
    def save_script(script_info, script_path):
        # save the script
        with open(script_path, 'w') as yaml_path:
           yaml.safe_dump(script_info, yaml_path)

    @staticmethod
    def parse_args():
       parser = argparse.ArgumentParser()
       parser.add_argument("-s", "--script_path", help="path to a script file")
       parser.add_argument("-c", "--scratch_path", help="path to scratch (storage, temp file) space")
       args = parser.parse_args()
       return args

    @classmethod
    def run_processor(cls, scratch_path=None, script_path=None):
        args = Processor.parse_args()
        if fws_in_docker() and script_path is None:
            script_path = '/script.yaml'
        if scratch_path is None:
            scratch_path = args.scratch_path

        script_info = Processor.load_script(script_path)
        processor = cls(scratch_path=script_info.get("scratch_path", scratch_path), script_path=script_path)
        if fws_in_docker():
            # process
            processor.process(script_path=script_path)

        elif script_info is not None:
            # build and run docker image
            if scratch_path is not None:
                # save scratch_path to script
                script_info['scratch_path'] = scratch_path
                Processor.save_script(script_info, script_path)
            processor.run_dockerized()

        else:
            # start watcher
            watch_path = script_path
            watcher = Watcher(watch_path, cls)
            watcher.watch()

class Watcher():
    def __init__(self, watch_path, cls):
        self.watch_path = watch_path
        self.watch_log_path = f'{self.watch_path}/logs/{self.watch_name()}.log'
        os.makedirs(os.path.dirname(self.watch_log_path), exist_ok=True)
        self.active_path = f'{self.watch_path}/active'
        os.makedirs(self.active_path, exist_ok=True)
        self.finished_path = f'{self.watch_path}/finished'
        os.makedirs(self.finished_path, exist_ok=True)
        self.processor_class = cls
        self.active = True

    def watch_name(self):
        name = self.watch_path
        if name.endswith('in'):
            name = os.path.dirname(name)
        return os.path.basename(name)

    def watch(self):
        # csk need to get the logger again when run in a separate process!
        new_logger = logging.getLogger(self.watch_name())
        logging.basicConfig(
            filename=self.watch_log_path,
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')

        while self.active:
            new_logger.info("watch")
            print("watch")
            # check folder
            script_paths = glob.glob(f'{self.watch_path}/*.yaml')

            if len(script_paths) > 0:
                # move the file with a try to avoid race condition
                new_path = f'{self.active_path}/{os.path.basename(script_paths[0])}'

                try:
                    # move next script to active
                    # time.sleep(random.randint(2, 6))
                    shutil.move(script_paths[0], new_path)

                    # test that it's the right type?

                    # start process on script
                    # self.processor(self, new_path)
                    print(f"processing {new_path} with class {self.processor_class}")
                    processor = self.processor_class()
                    script_path = new_path
                    processor.run_processor(script_path=new_path)

                except Exception as e:
                    print("Exception", e)
                    continue

            # pause?
            time.sleep(5)

