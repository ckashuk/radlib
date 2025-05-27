import glob
import subprocess
import yaml
import time

from radlib.fw.flywheel_clients import uwhealthaz_client
from radlib.fws.fws_utils import fws_create_paths, fws_copy_file, \
    fws_separate_flywheel_labels, fws_download_files_from_flywheel, fws_upload_files_to_flywheel
from radlib.service.service_instance import ServiceInstance


def rrs_radsurv_processor(self, script_path):
    # always call setup first
    self.set_up(script_path)

    # unique name for the processor
    self.processor_name = 'RRS RadSurv processor'
    self.logger.info(self.processor_name)

    # this is where you do what needs to be done
    # rrs radsurv preprocessing
    t1 = time.time()

    try:
        # get scratch space
        unique_name = self.get_unique_name()
        scratch_path = f'/scratch/{unique_name}'
        log_path = f'/logs/{unique_name}.log'

        fws_create_paths([f'{scratch_path}/nifti_raw',
                          f'{scratch_path}/preprocessed',
                          f'{scratch_path}/logs'])

        fws_copy_file(f'/scratch/nifti_raw_modalities_niiQuery.csv', f'{scratch_path}/logs/nifti_raw_modalities_niiQuery.csv')

        # copy input files
        for input_path in self.script_info['input_paths']:
            if input_path.startswith('fw://'):
                # flywheel download
                fw_client = uwhealthaz_client()
                _, _, subject, session, _, _ = fws_separate_flywheel_labels(input_path)
                if '-' in session:
                    session = session.replace('-', '').split(' ')[0]
                print("download files from flywheel!")
                fws_create_paths([f'{scratch_path}/nifti_raw/{subject}/{session}'])
                fws_download_files_from_flywheel(fw_client, input_path, f'{scratch_path}/nifti_raw/{subject}/{session}')

            else:
                # local download
                subject = input_path.split("/")[-3]
                session = input_path.split("/")[-2]
                fws_create_paths([f'{scratch_path}/nifti_raw/{subject}/{session}'])
                input_path = f'/local/{input_path}'
                print("download files from local!!!")
                input_paths = [input_path]
                if input_path.endswith('*'):
                    input_paths = glob.glob(input_path)

                for input_path in input_paths:
                    fws_copy_file(input_path, f'{scratch_path}/nifti_raw/{subject}/{session}', self.logger)

        # edit config files:
        print("configs!!!")
        main_config_path = '/app/IDIA/config/main_config.yaml'
        with open(main_config_path, 'r') as path:
            main_config = yaml.safe_load(path)
            main_config['root_path'] = scratch_path
            main_config['mri_sites']['site'] = ""
            main_config['mri_data'] = ["site"]
            main_config['run_dicomSelection'] = False
            main_config['run_dicomConversion'] = False
            main_config['run_niftiSelection'] = True
            main_config['run_preprocessing'] = True
            main_config['run_segmentation'] = True
            main_config['run_radiomics'] = False
            main_config['run_survival_train'] = False
            main_config['run_survival_test'] = False
            main_config['run_deep_learning'] = False
            main_config['run_feature_visualization'] = False

        with open(main_config_path, 'w') as path:
            yaml.safe_dump(main_config, path)


        preprocessing_config_path = '/app/IDIA/config/preprocessing_config.yaml'
        with open(preprocessing_config_path, 'r') as path:
            pass

        segmentation_config_path = '/app/IDIA/config/segmentation_config.yaml'
        with open(segmentation_config_path, 'r') as path:
            pass

        example_config_path = '/app/IDIA/segmentation/tumor_seg/config/example_config.yaml'
        with open(example_config_path, 'r') as path:
            example_config = yaml.safe_load(path)
            example_config['input']['compute_dice'] = False
            example_config['input']['mode'] = 'single'
            example_config['input']['single_scan']['flair'] = f"{subject}_FLAIR_reg_SkullS_BiasC.nii.gz"
            example_config['input']['single_scan']['t1c'] = f"{subject}_T1c_SRI24_SkullS_BiasC.nii.gz"
            example_config['input']['single_scan']['t1'] = f"{subject}_T1_reg_SkullS_BiasC.nii.gz"
            example_config['input']['single_scan']['t2'] = f"{subject}_T2_reg_SkullS_BiasC.nii.gz"
            example_config['input']['data_dir'] = f"/{scratch_path}/preprocessed/{subject}/Baseline"
            example_config['output']['file_path'] = f"/{scratch_path}/preprocessed/{subject}/Baseline/tumor_seg_swinUNETR.nii.gz"

        with open(example_config_path, 'w') as path:
            yaml.safe_dump(example_config, path)


        # run process
        try:
            command_text = ['python3', './radiomics_rscore_main.py', log_path]
            self.logger.info(f"run unique process {log_path}")
            p = subprocess.Popen(command_text, text=True)
            exit_code = p.wait()
            self.logger.info(f"run unique process {log_path} finished!!!")
        except Exception as e:
            print(f"Error: {e}")

    except Exception as e:
        print(f"{self.processor_name} exception", e)

    # always call cleanup just before writing output files
    self.clean_up(script_path)

    # output
    print(self.script_info['output_paths'])
    for local_path, output_path in self.script_info['output_paths']:
        if output_path.startswith('fw://'):
            # flywheel upload
            fw_client = uwhealthaz_client()
            _, _, subject, session, acquisition, _ = fws_separate_flywheel_labels(output_path)
            if '-' in session:
                session = session.replace('-', '').split(' ')[0]
            print("upload files to flywheel!",subject, session, acquisition, output_path)
            local_path = f'{scratch_path}{local_path}'
            fws_upload_files_to_flywheel(fw_client, local_path, output_path)

        else:
            # local upload
            subject = output_path.split("/")[-3]
            session = output_path.split("/")[-2]
            output_to = f'/local/{output_path}'
            print("upload files from local!!!")
            output_paths = [output_path]
            if output_path.endswith('*'):
                output_paths = glob.glob(output_path)

            for output_path in output_paths:
                fws_copy_file(output_path, output_to, self.logger)

    t2 = time.time()
    print(f"{self.processor_name} finished in f{t2-t1} s")

if __name__ == "__main__":
    # instantiate the ServiceInstance, give it a processor function, and start it!
    # TODO: 202504 csk find better way(s) to stop!
    instance = ServiceInstance()
    instance.processor = rrs_radsurv_processor
    instance.start()


