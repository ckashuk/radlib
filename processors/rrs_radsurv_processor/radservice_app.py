import subprocess
import yaml
import time
import sys

sys.path.append('/home/aa-cxk023/share/radlib')
sys.path.append('/home/aa-cxk023/share/RRS_RadSurv')

from radlib.dcm.sorter import DicomSorter
from radlib.fws.fws_fileset import FWSFileSetException

from radlib.fws.fws_utils import fws_create_paths, fws_copy_file, \
    fws_separate_flywheel_labels, fws_in_docker, \
    fws_is_flywheel_path, fws_assign_modalities
from radlib.processor.processor import Processor


class RrsRadsurvProcessor(Processor):

    def processor_script(self):
        # rrs radsurv preprocessing
        t1 = time.time()

        try:
            dicom_raw = self.get_fileset('dicom_raw')
            files_dicom_raw = dicom_raw.get_local_paths()
            nifti_raw = self.get_fileset('nifti_raw')
            if fws_is_flywheel_path(nifti_raw.original_path):
                group_label = fws_separate_flywheel_labels(nifti_raw.original_path)[0]
                project_label = fws_separate_flywheel_labels(nifti_raw.original_path)[1]
                subject_label = fws_separate_flywheel_labels(nifti_raw.original_path)[2]
                session_label = fws_separate_flywheel_labels(nifti_raw.original_path)[3]
                acquisition = 'Baseline'
            else:
                # TODO: 202507 csk get subject label from local file path somehow
                group_label = 'group'
                project_label = 'project'
                subject_label = 'subject'
                session_label = 'session'
                acquisition = 'Baseline'

            preprocessed = self.get_fileset('preprocessed')
            self.log_path = f'/logs'
            fws_create_paths([self.log_path])

            # ingest
            sorter = DicomSorter('/dicom_raw',
                                 f'{self.scratch_path}/dicom_sorted',
                                 converted_folder='/nifti_raw',
                                 preserve_input_files=False,
                                 send_to_flywheel=True,
                                 service=False,
                                 flywheel_group=group_label,
                                 flywheel_project=project_label,
                                 logger=self.logger)
            sorter.start()

            # modalities
            # get hardcoded file
            # TODO: 202505 csk need to find better way for this!
            try:
                niiQuery = self.get_fileset('nifti_raw_modalities_niiQuery.csv')
                copy_from = niiQuery.get_local_paths()[0]
            except FWSFileSetException:
                # generate from tags
                copy_from = f'{self.scratch_path}/tmp.csv'
                with open(copy_from, 'w') as f:
                    mods = fws_assign_modalities(dicom_raw, nifti_raw)
                    if len(mods) < 4:
                        raise Exception("not enough modalities were identified!")
                    f.write('ID,time_point,acquisition_tag,mri_modalities (original nifti),n_modalities_per_case,included_modality,mri_tag\n')
                    for mod, file_name in mods.items():
                        f.write(f'{subject_label},{session_label},{acquisition},{file_name.replace(".dicom.zip", ".nii.gz")},4,TRUE,{mod}\n')

            copy_to = f'{self.log_path}/nifti_raw_modalities_niiQuery.csv'
            fws_copy_file(copy_from, copy_to)


            # TODO: 202507 csk run ./bash_requirements.sh to install hd-bet until we find a better way to do it!
            b = subprocess.Popen('/app/bash_requirements.sh', text=True)
            exit_code = b.wait()

            """
            # edit config files from script
            # TODO: 202507 csk revisit this

            print("configs")
            for config_name, config in self.script_info['configs'].items():
                config_path = config['config_path']
                with open(config_path, 'r') as path:
                    config_data = yaml.safe_load(path)
                    if fws_in_docker():
                        config_data['root_path'] = '/'  # self.scratch_path
                        print(f"within docker, root_path is {self.scratch_path}")
                    else:
                        config_data['root_path'] = '/scratch'
                        print(f"not within docker, root_path is /scratch")

                    for keys, value in fws_traverse_yaml_tree(config):
                        if 'SUBJECT' in value:
                            value = value.replace('SUBJECT', subject)
                        level = config
                        for key in keys:
                            level = level[key]
                        print(keys, level, value)

                # print(config_name, config_path, os.path.exists(config_path))
            exit()
            """
            # edit config files manually
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
                example_config['input']['single_scan']['flair'] = f"{subject_label}_FLAIR_reg_SkullS_BiasC.nii.gz"
                example_config['input']['single_scan']['t1c'] = f"{subject_label}_T1c_SRI24_SkullS_BiasC.nii.gz"
                example_config['input']['single_scan']['t1'] = f"{subject_label}_T1_reg_SkullS_BiasC.nii.gz"
                example_config['input']['single_scan']['t2'] = f"{subject_label}_T2_reg_SkullS_BiasC.nii.gz"
                example_config['input']['data_dir'] = f"/{self.scratch_path}/preprocessed/{subject_label}/{acquisition}"
                example_config['output']['file_path'] = f"/{self.scratch_path}/preprocessed/{subject_label}/{acquisition}/tumor_seg_swinUNETR.nii.gz"

            with open(example_config_path, 'w') as path:
                yaml.safe_dump(example_config, path, sort_keys=False)

            # run process
            try:
                command_text = ['python3', f'{self.code_path}/radiomics_rscore_main.py', f'{self.log_path}/{self.processor_name()}_run.log']
                # self.logger.info(f"run unique process {command_text}")
                # print(command_text)
                p = subprocess.Popen(command_text, text=True)
                exit_code = p.wait()
                #  self.logger.info(f"run unique process {command_text} finished!!!")
            except Exception as e:
                print(f"Error: {e}")

            # output
            preprocessed.save_files()

        except Exception as e:
            print(f"{self.processor_name()} exception", e)

        t2 = time.time()
        print(f"{self.processor_name()} finished in f{t2-t1} s")

if __name__ == "__main__":
    RrsRadsurvProcessor.run_processor()
