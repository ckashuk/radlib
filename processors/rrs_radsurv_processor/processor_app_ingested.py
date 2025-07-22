import subprocess
import yaml
import time
import sys

sys.path.append('/home/aa-cxk023/share/radlib')
sys.path.append('/home/aa-cxk023/share/RRS_RadSurv')

from radlib.fws.fws_utils import fws_create_paths, fws_copy_file, \
    fws_in_docker
from radlib.processor.processor import Processor

class RrsRadsurvProcessor(Processor):

    def processor_script(self):
        # rrs radsurv preprocessing
        t1 = time.time()

        try:
            subject = 'RAD-AI-CNS-TUMOR-0004'
            nifti_raw = self.get_fileset('nifti_raw')
            preprocessed = self.get_fileset('preprocessed')
            self.log_path = f'/logs'
            fws_create_paths([self.log_path])

            # get hardcoded file
            # TODO: 202505 csk need to find better way for this!
            niiQuery = self.get_fileset('nifti_raw_modalities_niiQuery.csv')

            copy_to = f'{self.log_path}/nifti_raw_modalities_niiQuery.csv'
            fws_copy_file(niiQuery.get_local_paths()[0], copy_to)

            # TODO: 202507 csk run ./bash_requirements.sh to install hd-bet until we find a better way to do it!
            b = subprocess.Popen('/app/bash_requirements.sh', text=True)
            exit_code = b.wait()

            # edit config files:
            print("configs")
            self.code_path = '/app'  # '/home/aa-cxk023/share/RRS_RadSurv/'

            main_config_path = f'{self.code_path}/config/main_config.yaml'
            with open(main_config_path, 'r') as path:
                main_config = yaml.safe_load(path)
                if fws_in_docker():
                    main_config['root_path'] = '/'  # self.scratch_path
                    print(f"within docker, root_path is {self.scratch_path}")
                else:
                    main_config['root_path'] = '/scratch'
                    print(f"not within docker, root_path is /scratch")
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
                main_config['submodule_configs']['preprocessing'] = f'{self.code_path}/config/preprocessing_config.yaml'
                main_config['submodule_configs']['radiomics'] = f'{self.code_path}/config/radiomics_config.yaml'
                main_config['submodule_configs']['segmentation'] = f'{self.code_path}/config/segmentation_config.yaml'

            with open(main_config_path, 'w') as path:
                yaml.safe_dump(main_config, path, sort_keys=False)

            preprocessing_config_path = f'{self.code_path}/config/preprocessing_config.yaml'
            with open(preprocessing_config_path, 'r') as path:
                preprocessing_config = yaml.safe_load(path)
                preprocessing_config['preprocessing_settings']['mri_modalities'] = ["T1c","FLAIR","T1","T2"]

            with open(preprocessing_config_path, 'w') as path:
                yaml.safe_dump(preprocessing_config, path, sort_keys=False)

            # segmentation_config_path = f'{self.code_path}/config/segmentation_config.yaml'
            # with open(segmentation_config_path, 'r') as path:
            #    pass

            example_config_path = f'{self.code_path}/segmentation/tumor_seg/config/example_config.yaml'
            with open(example_config_path, 'r') as path:
                example_config = yaml.safe_load(path)
                example_config['input']['compute_dice'] = False
                example_config['input']['mode'] = 'single'
                example_config['input']['single_scan']['flair'] = f"{subject}_FLAIR_reg_SkullS_BiasC.nii.gz"
                example_config['input']['single_scan']['t1c'] = f"{subject}_T1c_SRI24_SkullS_BiasC.nii.gz"
                example_config['input']['single_scan']['t1'] = f"{subject}_T1_reg_SkullS_BiasC.nii.gz"
                example_config['input']['single_scan']['t2'] = f"{subject}_T2_reg_SkullS_BiasC.nii.gz"
                example_config['input']['data_dir'] = f"/{self.scratch_path}/preprocessed/{subject}/Baseline"
                example_config['output']['file_path'] = f"/{self.scratch_path}/preprocessed/{subject}/Baseline/tumor_seg_swinUNETR.nii.gz"

            with open(example_config_path, 'w') as path:
                yaml.safe_dump(example_config, path, sort_keys=False)

            # run process
            try:
                command_text = ['python3', f'{self.code_path}/radiomics_rscore_main.py', f'{self.log_path}/{self.processor_name()}_run.log']
                self.logger.info(f"run unique process {command_text}")
                print(command_text)
                p = subprocess.Popen(command_text, text=True)
                exit_code = p.wait()
                self.logger.info(f"run unique process {command_text} finished!!!")
            except Exception as e:
                print(f"Error: {e}")

        except Exception as e:
            print(f"{self.processor_name()} exception", e)

        # output
        preprocessed.save_files()

        """
        for local_path, output_path in zip(preprocessed.get_local_paths(), preprocessed.get_output_paths()):
           print(local_path, output_path)
            
            if output_path.startswith('fw://'):
                # flywheel upload
                fw_client = uwhealthaz_client()
                _, _, subject, session, acquisition, _ = fws_separate_flywheel_labels(output_path)
                if '-' in session:
                    session = session.replace('-', '').split(' ')[0]
                print("upload files to flywheel!",subject, session, acquisition, output_path)
                local_path = f'{self.scratch_path}{local_path}'
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
        """
        t2 = time.time()
        print(f"{self.processor_name()} finished in f{t2-t1} s")

if __name__ == "__main__":
    RrsRadsurvProcessor.run_processor()
