HD_BET_path="/app/Codebase/gustavo_script/Preprocessing/Skull_stripp/dgx/HD-BET/"
%cd $HD_BET_path
%pip install -e .

pip install -r requirements.txt

import os
import glob
from antspy_pp_utils import *
from custom_pipelines import *

# T1 - Atlas registration
root_path='/app/Data/_Brain/Radiology/_Adult/_Glioma/'
mri_data='IU_Primary_Brain_Tumor'
subdir='Preprocessed'
out_subdir='Preprocessed'

time_point='Baseline'
mri_mod='T1c'
ext='.nii.gz'
pipeline='SkullS_BiasC'
mask_str='tumor_seg_swinUNETR'
brainmask_str='SkullS_mask'
file_xlsx_list='UI_QC.xlsx'
atlas_str='MNI'

# Specify ANTs parameters
aff_metric = "mattes"
type_of_transform = "Affine"
transforming_mask=True
SkullStripp=None # HD_BET or Atlas_mask Default= None

# Atlas
atlas_path='/app/Codebase/gustavo_script/_Neuroimaging/Preprocessing/ATLAS_T1/MNI152_T1_1mm_182_218_182/MNI152_T1_1mm_brain.nii.gz'

labels, imgs = getting_T1_mask_list(root_path, mri_data,subdir,time_point,mri_mod,pipeline,ext,mask_str)

