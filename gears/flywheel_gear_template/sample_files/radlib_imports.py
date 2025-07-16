# packages needed for all flywheel scripts
import numpy as np
import SimpleITK as sitk
import flywheel
from flywheel.client import Client as flywheel_client
import pydicom
import logging
import tempfile
import shutil
import yaml

# add radlib path TODO: 202503 csk find better way to handle this!
import sys
import os
module_path = os.path.abspath(os.path.join('../../..'))
if module_path not in sys.path:
    sys.path.append(module_path)

# radlib-specific imports
from radlib.fw.flywheel_clients import uwhealthaz_client
from radlib.fws.fws_utils import fws_input_file_list, fws_load_image, fws_in_jupyter_notebook
from radlib.fws.fws_image import FWSImageFile, FWSImageFileList
from radlib.idia.idia_dicom_selection import DicomSelectionSingle, convert_dataset_to_nifti, mri_data_check