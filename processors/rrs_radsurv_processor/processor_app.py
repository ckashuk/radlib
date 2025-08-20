import os
import subprocess

import numpy as np
import yaml
import time
import sys
import SimpleITK as sitk

sys.path.append('/home/aa-cxk023/share/radlib')
sys.path.append('/home/aa-cxk023/share/RRS_RadSurv')

from radlib.dcm.sorter import DicomSorter
from radlib.fws.fws_fileset import FWSFileSetException

from radlib.fws.fws_utils import fws_create_paths, fws_copy_file, \
    fws_separate_flywheel_labels, fws_in_docker, \
    fws_is_flywheel_path, fws_assign_modalities
from radlib.processor.processor import Processor
# from radlib.graphics.nrrd_to_vtk import jpg_brain_three_view


class RrsRadsurvProcessor(Processor):

    def processor_script(self):
        # rrs radsurv preprocessing
        t1 = time.time()

        try:
            # get filesets
            dicom_raw = self.get_fileset('dicom_raw')
            dicom_sorted = self.get_fileset('dicom_sorted')
            nifti_raw = self.get_fileset('nifti_raw')

            # TODO: 2025-07 csk is this all necessary?
            if fws_is_flywheel_path(nifti_raw.original_path):
                flywheel_labels = fws_separate_flywheel_labels(nifti_raw.original_path)
                group_label = flywheel_labels[0]
                project_label = flywheel_labels[1]
                subject_label = flywheel_labels[2]
                session_label = flywheel_labels[3]
                acquisition_label = 'Baseline'
            else:
                # TODO: 202507 csk get subject label from local file path somehow
                group_label = 'group'
                project_label = 'project'
                subject_label = 'subject'
                session_label = 'session'
                acquisition_label = 'Baseline'

            preprocessed = self.get_fileset('preprocessed')
            self.log_path = f'{self.scratch_path}/{self.get_unique_name()}.log'
            fws_create_paths([os.path.dirname(self.log_path), '/logs'])

            # ingest from dicom files
            # pull them down first!
            dicom_raw.load_local_files()
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
            self.logger.info("assigning modalities")
            try:
                niiQuery = self.get_fileset('nifti_raw_modalities_niiQuery.csv')
                copy_from = niiQuery.get_local_paths()[0]

            except FWSFileSetException:
                # generate from tags
                copy_from = f'{self.scratch_path}/niiQuery.csv'
                with open(copy_from, 'w') as f:
                    dicom_sorted.load_local_files()
                    mods = fws_assign_modalities(dicom_sorted, nifti_raw)
                    self.logger.info(subject_label, session_label, mods)
                    if len(mods) < 4:
                        raise Exception("not enough modalities were identified!")
                    f.write('ID,time_point,acquisition_tag,mri_modalities (original nifti),n_modalities_per_case,included_modality,mri_tag\n')
                    for mod, file_name in mods.items():
                        f.write(f'{subject_label},{session_label},{acquisition_label},{file_name.replace(".dicom.zip", ".nii.gz")},4,TRUE,{mod}\n')

            # copy_to = f'{self.log_path}/nifti_raw_modalities_niiQuery.csv'
            copy_to = f'/logs/nifti_raw_modalities_niiQuery.csv'
            fws_copy_file(copy_from, copy_to)


            # TODO: 202507 csk run ./bash_requirements.sh to install hd-bet until we find a better way to do it!
            self.logger.info("running bash_requirements.sh")
            b = subprocess.Popen('/app/bash_requirements.sh', text=True)
            exit_code = b.wait()

            """
            # edit config files from script
            # TODO: 202507 csk revisit this

            for config_name, config in self.script_info['configs'].items():
                config_path = config['config_path']
                with open(config_path, 'r') as path:
                    config_data = yaml.safe_load(path)
                    if fws_in_docker():
                        config_data['root_path'] = '/'  # self.scratch_path
                    else:
                        config_data['root_path'] = '/scratch'

                    for keys, value in fws_traverse_yaml_tree(config):
                        if 'SUBJECT' in value:
                            value = value.replace('SUBJECT', subject)
                        level = config
                        for key in keys:
                            level = level[key]

            """
            # edit config files manually
            self.code_path = '/app'  # '/home/aa-cxk023/share/RRS_RadSurv/'
            self.logger.info("editing config files")
            main_config_path = f'{self.code_path}/config/main_config.yaml'
            with open(main_config_path, 'r') as path:
                main_config = yaml.safe_load(path)
                if fws_in_docker():
                    main_config['root_path'] = '/'  # self.scratch_path
                else:
                    main_config['root_path'] = '/scratch'
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
                example_config['input']['data_dir'] = f"/{self.scratch_path}/preprocessed/{subject_label}/{acquisition_label}"
                example_config['output']['file_path'] = f"/{self.scratch_path}/preprocessed/{subject_label}/{acquisition_label}/tumor_seg_swinUNETR.nii.gz"

            with open(example_config_path, 'w') as path:
                yaml.safe_dump(example_config, path, sort_keys=False)

            # run process
            try:
                command_text = ['python3', f'{self.code_path}/radiomics_rscore_main.py', f'{self.log_path}/{self.processor_name()}_run.log']
                self.logger.info("running command ", command_text)
                p = subprocess.Popen(command_text, text=True)
                exit_code = p.wait()

            except Exception as e:
                self.logger.info(f"Error: {e}")

            # "report"
            self.logger.info("generating report")
            brain_path = f"/{self.scratch_path}/preprocessed/{subject_label}/{acquisition_label}/{subject_label}_T2_reg_SkullS_BiasC.nii.gz"
            roi_path = f"/{self.scratch_path}/preprocessed/{subject_label}/{acquisition_label}/tumor_seg_swinUNETR.nii.gz"

            brain = sitk.GetArrayFromImage(sitk.ReadImage(brain_path))
            brain = np.rot90(brain, 2, [0, 2])
            roi = sitk.GetArrayFromImage(sitk.ReadImage(roi_path))
            roi = np.rot90(roi, 2, [0, 2])

            import matplotlib.pyplot as plt

            plt.subplot(1, 3, 1)
            plt.imshow(brain[int(brain.shape[0] / 2), :, :], cmap='gray')
            plt.imshow(roi[int(roi.shape[0] / 2), :, :], alpha=0.3, cmap='Reds', vmin=1, vmax=4)
            plt.subplot(1, 3, 2)
            plt.imshow(brain[:, int(brain.shape[1] / 2), :], cmap='gray')
            plt.imshow(roi[:, int(roi.shape[1] / 2), :], alpha=0.3, cmap='Reds', vmin=1, vmax=4)
            plt.subplot(1, 3, 3)
            plt.imshow(brain[:, :, int(brain.shape[2] / 2)], cmap='gray')
            plt.imshow(roi[:, :, int(roi.shape[2] / 2)], alpha=0.3, cmap='Reds', vmin=1, vmax=4)

            plt.savefig(f"/{self.scratch_path}/preprocessed/{subject_label}/{acquisition_label}/{subject_label}_report.pdf")
            # jpg_brain_three_view(brain, roi, f"/{self.scratch_path}/preprocessed/{subject_label}/{acquisition_label}/{subject_label}_report.jpg")

            # output
            preprocessed.save_files()

        except Exception as e:
            self.logger.info(f"{self.processor_name()} exception", e)

        t2 = time.time()
        self.logger.info(f"{self.processor_name()} finished in f{t2-t1} s")

if __name__ == "__main__":
    RrsRadsurvProcessor.run_processor()
