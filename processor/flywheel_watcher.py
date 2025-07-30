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
from radlib.fws.fws_utils import fws_is_flywheel_path, fws_has_more_scripts, fws_get_next_script, fws_resolve_object

from radlib.processors.rrs_radsurv_processor.processor_app import RrsRadsurvProcessor


class FlywheelWatcherException(Exception):
    pass

# TODO: 202507 csk add
class FlywheelWatcher():
    def __init__(self, config_path, scratch_path=None):
        self.config = FlywheelWatcher.load_config(config_path)
        self.scratch_path = tempfile.mkdtemp() if scratch_path is None else scratch_path
        self.watch_log_path = f'{self.scratch_path}/{self.watch_name()}.log'
        self.active = True
        self.fw_client = uwhealthaz_client()

        self.active_processors = {'rrs_radsurv_processor': RrsRadsurvProcessor, 'rrs_radsurv': RrsRadsurvProcessor}

    @staticmethod
    def load_config(config_path):
        with open(config_path, 'r') as yaml_path:
            script_info = yaml.safe_load(yaml_path)
        return script_info

    def watch_name(self):
        if self.config.get('watch_name') is not None:
            return self.config.get('watch_name')
        return 'unnamed_watcher'

    def watch(self):
        # csk need to get the logger again when run in a separate process!
        new_logger = logging.getLogger(self.watch_name())
        logging.basicConfig(
            filename=self.watch_log_path,
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')

        while self.active:

            # for each project being watched
            for project_def in self.config.get('projects', []):
                watch_path = f'{project_def.get("group_label", "")}/{project_def.get("project_label", "")}/analyses/{project_def.get("analysis_label", "")}'
                print(f"watch {watch_path}...")
                # check for analysis, create if it does not exist
                try:
                    analysis = self.fw_client.resolve(f'{watch_path}')['path'][-1]
                except Exception:
                    # raise FlywheelWatcherException(f"analysis {watch_path} does not exist!")
                    project = self.fw_client.resolve(f'{project_def.get("group_label", "")}/{project_def.get("project_label", "")}')['path'][-1]
                    analysis = project.add_analysis(label=project_def.get("analysis_label"))

                analysis = analysis.reload()
                info = analysis.info
                info['active'] = True
                info['script_template'] = {}  #rrs_radsurv_template
                analysis.update_info(info)

                while fws_has_more_scripts(analysis):
                    try:
                        script_info = fws_get_next_script(analysis, remove=True)
                        script_path = f'{self.scratch_path}/script.yaml'
                        Processor.save_script(script_info, script_path)
                        processor = self.active_processors.get(script_info['base_image'])
                        processor.run_processor(scratch_path=self.scratch_path, script_path=script_path)

                    except OverflowError as e:
                        print("Exception", e)
                        continue

            # pause?
            time.sleep(5)


def get_analysis(object, analysis_label):
    # TODO 202507 csk better way to do this?
    for a in object.analyses:
        if a.label == analysis_label:
            return a
    return None


def add_analysis(object, analysis_label):
    try:
        return object.add_analysis(label=analysis_label)
    except flywheel.rest.ApiException:
        # analysis already exists, have to find it
        return get_analysis(object, analysis_label)


watcher = FlywheelWatcher("flywheel_watcher_config.yaml", "/home/aa-cxk023/share/scratch")
watcher.watch()