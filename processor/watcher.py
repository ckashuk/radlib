import glob
import os
import sys
import tempfile
import time
import logging
import yaml

import flywheel

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)

from radlib.fw.flywheel_clients import uwhealthaz_client
from radlib.processor.processor import Processor
from radlib.fws.fws_utils import fws_has_more_scripts, fws_get_next_script, fws_is_flywheel_path
from radlib.processors.rrs_radsurv_processor.processor_app import RrsRadsurvProcessor


class WatcherException(Exception):
    pass

# TODO: 202507 csk add
class Watcher():
    # a Watcher has a config file that contains a set of "areas" to watch, each item can contain "items" that will be "processed"
    # by the watcher. This will be the base class for:
    #    PathWatcher: watch one or more file paths for new files, and do something with the files
    #    ScriptWatcher: watch one or more file paths for processor scripts, and process the scripts as the come in
    #    FlywheelWatcher: watch one or more flywheel "processor analyses" for new scripts, and process the scripts as they come in

    def __init__(self, config_path, scratch_path=None, fw_client=None, active_processors=None):
        self.config = Watcher.load_script(config_path)
        self.scratch_path = tempfile.mkdtemp() if scratch_path is None else scratch_path
        self.watch_log_path = f'{self.scratch_path}/{self.watch_name()}.log'
        self.active = True
        self.fw_client = uwhealthaz_client() if fw_client is None else fw_client

        self.active_processors = {'rrs_radsurv_processor': RrsRadsurvProcessor, 'rrs_radsurv': RrsRadsurvProcessor} if active_processors is None else active_processors
        self.start_logging()

    def watched_areas(self):
        raise NotImplementedError("You should implement this method on a subclass of Watcher")


    def items_for_area(self, area):
        raise NotImplementedError("You should implement this method on a subclass of Watcher")


    def process_item(self, item):

        raise NotImplementedError("You should implement this method on a subclass of Watcher")

    def watch_once(self):
        for watched_area in self.watched_areas():
            for item in self.items_for_area(watched_area):
                 self.process_item(item)
            time.sleep(3)


    def watch(self):
        while self.active:
            self.watch_once()
            time.sleep(3)


    def start_logging(self):
        # csk need to get the logger again when run in a separate process!
        new_logger = logging.getLogger(self.watch_name())
        print(">>>>>watcher logger! named ", self.watch_name(), "path", self.watch_log_path)
        logging.basicConfig(
            filename=self.watch_log_path,
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')


    @staticmethod
    def load_script(script_data):
        if isinstance(script_data, str) and os.path.exists(script_data):
            # local file
            with open(script_data, 'r') as yaml_path:
                return yaml.safe_load(script_data)
        # direct data
        return script_data


    def watch_name(self):
        if self.config.get('watch_name') is not None:
            return self.config.get('watch_name')
        # TODO: 202508 csk update this to "all" active_processors
        return self.active_processors.keys[0]


def fws_glob(area):
    pass


class FileWatcher(Watcher):
    def watched_areas(self):
        return self.config.get('paths', [])

    def items_for_area(self, area):
        if fws_is_flywheel_path(area):
            return fws_glob(area)
        else:
            return glob.glob(area, recursive=True)

    def process_item(self, item):
        item = item.replace('\\', '/')
        print(f'file {item}, {fws_is_flywheel_path(item)}, {os.path.exists(item)}')


class ScriptWatcher(Watcher):
    def watched_areas(self):
        return self.config.get('paths', [])

    def items_for_area(self, area):
        return glob.glob(area)

    def process_item(self, item):
        print(f'script {item}, {fws_is_flywheel_path(item)}, {os.path.exists(item)}')

