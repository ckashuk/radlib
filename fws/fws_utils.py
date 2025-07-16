import glob
import os
import shutil
import subprocess
import time
from pathlib import Path

import flywheel
from IPython.terminal.shortcuts.auto_match import double_quote
# from IPython.core.display_functions import clear_output
from flywheel.client import Client as flywheel_client

from radlib.fw.flywheel_clients import uwhealthaz_client
from radlib.fw.flywheel_data import load_image_from_flywheel, load_image_from_local_path

# constants for the names and classes of the flywheel object hierarchy
fw_types = ['group', 'project', 'subject', 'session', 'acquisition', 'file']
fw_type_objects = [
    flywheel.models.group_output.GroupOutput,
    flywheel.models.project_output.ProjectOutput,
    flywheel.models.subject_output.SubjectOutput,
    flywheel.models.session_output.SessionOutput,
    flywheel.models.acquisition_output.AcquisitionOutput,
    flywheel.models.file_node.FileNode
]

fws_modalities = ['T1', 'T1c', 'T2', 'FLAIR']


def fws_create_new_cell(contents: str = ''):
    """
    helper to adda new notebook cell for whatever reason
    Parameters
    ----------
    contents: str
        The contents to include in the new cell, formatted by cell type
    -------

    """
    from IPython.core.getipython import get_ipython
    shell = get_ipython()
    shell.set_next_input(contents, replace=False)


def fws_in_jupyter_notebook() -> bool:
    """
    helper to test_processor if the code is running in a jupyter notebook or not

    Returns
    -------
        True if the code is running in a jupyter notebook (ipython was detected),
        False if not

    """
    try:
        # NOTE: __IPYTHON__ will probably show an error in your IDE if not within a notebook environment
        __IPYTHON__
        return True
    except NameError:
        return False


def fws_in_docker() -> bool:
    """
    helper to test if we are inside of a docker container

    Returns
    -------
    True or False

    """
    cgroup = Path('/proc/self/cgroup')
    return Path('/.dockerenv').is_file() or (cgroup.is_file() and 'docker' in cgroup.read_text())


def fws_is_flywheel_path(path: str) -> bool:
    """
    Helper to decide if a path is a flywheel path or not.
    requires use of fw:// on all flywheel paths for it to work unfortunately
    Parameters
    ----------
    path: str
        The path to test

    Returns
    -------
    True or False
    """
    return path.startswith('fw://')


def fws_get_mounted_path(file_path: str) -> str:
    """
    helper to get the ultimate path of a mounted filesystem. Sometimes we need it to decide where to load/save things

    Parameters
    ----------
    file_path: str
        The file path to test

    Returns
    The ultimate "source" path of the file, can be different if on a mounted drive
    -------

    """
    try:
        with open('/proc/mounts', 'r') as mounts_file:
            for line in mounts_file:
                # find the device/mountpoint for this path and replace it
                parts = line.split()
                device = parts[0]
                mount_point = parts[1]
                if device in file_path:
                    return file_path.replace(device, mount_point)

    except FileNotFoundError:
        # no mount point, just return the path
        return file_path

def fws_traverse_yaml_tree(data, path=None, results=None):
    """
    Recursively scans a yaml "tree' (more properly a dict) and lists all possible "leaf" nodes with full paths
    not sure here this is used anymore but let's keep it around

    Parameters
    ----------
    data: dict
        The yaml to scan
    path: str
        the prior path (list of keys) that got to this point
    results: list
        a list of tuples of each (path, node) on this subtree

    Returns
    -------
     a list of tuples of each (path, node) on this subtree

    """
    if path is None:
        path = []
    if results is None:
        results = []
    if isinstance(data, dict):
        for key, value in data.items():
            fws_traverse_yaml_tree(value, path + [key], results)
    else:
        results.append((path, data))

    return results

def fws_separate_flywheel_labels(fw_path: str)-> list[str]:
    """
    Given a flywheel path, separate it into it's "object label" components

    Parameters
    ----------
    fw_path: str
        A "flywheel path" with or without the 'fw://' header

    Returns
    -------
        A list of strings corresponding to group, project, subject, session, acquisition, file of
        the flywheel object tree, if objects are not represented in flywheel_path, they will be
        returned as None
    """
    labels = fw_path.replace('fw://', '').split("/")
    fw_labels = [None, None, None, None, None, None]

    for label_pos in [0, 1, 2, 3, 4, 5]:
        # for each position in the flywheel object hierarchy
        if len(labels) > label_pos:
            fw_labels[label_pos] = labels[label_pos]

    return fw_labels


def fws_resolve_object(fw_client: flywheel.Client, fw_path:str, fw_type:str='project') -> object:
    """
    given a flywheel client, a flywheel path and a flywheel object type, return the object defined by fw_type
    Parameters
    ----------
    fw_client:
        A Client object to do flywheel API work with
    fw_path: str
        A flywheel path string, with or without the 'fw://' header, pointing to an object tree
    fw_type: str
        A flywheel object type to return, one of 'group', 'project', 'subject', 'session', 'acquisition', 'file'
        If undecided, the object usually contains pointers to it's parent objects

    Returns
    -------
    the flywheel API "Container" object which references the object of fw_type
    """
    # print(">>>fws_resolve_object", fw_path, fw_type)
    # get the specific tree defined by flywheel_path
    if fw_type == 'acquisition':
        fw_path = os.path.dirname(fw_path)

    try:
        objects = fw_client.resolve(fw_path.replace('fw://', ''))['path']
    except flywheel.rest.ApiException:
        # object does not exist, create it!
        fws_generate_tree(fw_client, fw_path)
        objects = fw_client.resolve(fw_path.replace('fw://', ''))['path']

    # return the object denoted by type
    index = fw_types.index(fw_type)

    if len(objects) > index:
        return objects[index]
    return None


def fws_expand_flywheel_path(fw_path, logger=None):

    # will always need the acquisition object to download files from
    fw_client = uwhealthaz_client()
    # fws_generate_tree(fw_client, fw_path)
    acquisition = fws_resolve_object(fw_client, fw_path,'acquisition')

    # if '*' in fw_path, download all files from the acquisition, otherwise download the one specificed file
    expanded_fw_paths = [fws_separate_flywheel_labels(fw_path)[5]]
    if fw_path.endswith('*'):
        expanded_fw_paths = [f'{os.path.dirname(fw_path)}/{file.name}' for file in acquisition.files]

    return expanded_fw_paths


def fws_download_files_from_flywheel(fw_client, fw_path, local_path, logger=None):
    """
    use the flywheel API to download file(s) defined by fw_path to local storage

    Parameters
    ----------
    fw_client: Client
        A Client object to do flywheel API work with
    fw_path: str
        A flywheel path string, with or without the 'fw://' header, pointing to an object tree
    local_path: str
        A local path to save file(s) to. can be a file system path, or in future, redis or other non-direct
        file system path
    logger: logging.Logger, optional
        If included, write out a log message for each file downloaded

    Returns
    -------

    """

    # will always need the acquisition object to download files from
    acquisition = fws_resolve_object(fw_client, fw_path,'acquisition')
    local_files = []

    # if '*' in fw_path, download all files from the acquisition, otherwise download the one specificed file
    files = [fws_separate_flywheel_labels(fw_path)[5]]
    if fw_path.endswith('*'):
        files = [file.name for file in acquisition.files]

    for file in files:
        local_file_path = f'{local_path}/{file}'
        acquisition.download_file(file, local_file_path)
        local_files.append(local_file_path)
        # log a message if logger provided
        if logger is not None:
            logger.info(f"download flywheel {file} to {local_path}/{file}")
    return local_files


def fws_download_file_from_flywheel(fw_client, fw_path, local_path, do_download=True, logger=None):
    """
    use the flywheel API to download file(s) defined by fw_path to local storage

    Parameters
    ----------
    fw_client: Client
        A Client object to do flywheel API work with
    fw_path: str
        A flywheel path string, with or without the 'fw://' header, pointing to an object tree
    local_path: str
        A local path to save file(s) to. can be a file system path, or in future, redis or other non-direct
        file system path
    logger: logging.Logger, optional
        If included, write out a log message for each file downloaded

    Returns
    -------

    """

    # will always need the acquisition object to download files from
    acquisition = fws_resolve_object(fw_client, fw_path, 'acquisition')
    file = fws_resolve_object(fw_client, fw_path, 'file')
    if os.path.isdir(local_path):
        local_file_path = f'{local_path}/{file.name}'
    else:
        local_file_path = local_path
    if do_download:
        acquisition.download_file(file.name, local_file_path)

    # log a message if logger provided
    if logger is not None:
        logger.info(f"download flywheel {file.name} to {local_file_path}")

    return local_file_path

def fws_generate_tree(fw_client, fw_path):
    # given a flywheel path, make sure all component objects exist, and create if not
    if not fws_is_flywheel_path(fw_path):
        return

    component_labels = fw_path.replace("fw://", "").rsplit('/')
    if len(component_labels) == 6:
        # do not try to generate a file!
        component_labels = component_labels[0:5]

    tree_path = ''
    for c, component_label in enumerate(component_labels):

        try:
            tree_path = component_label if tree_path=='' else f'{tree_path}/{component_label}'
            obj = fw_client.resolve(tree_path)['path'][-1]
        except flywheel.rest.ApiException as e:
            component_type = fw_types[c]
            tree_path = os.path.dirname(tree_path)
            parent_obj = fw_client.resolve(tree_path)['path'][-1]
            # TODO: 202505 csk add project and group?
            if component_type == 'acquisition':
                # print(f"add {component_type} named {component_label} from {fw_path} to {type(parent_obj)}")
                parent_obj.add_acquisition({'label': component_label})
            if component_type == 'session':
                # print(f"add {component_type} named {component_label} from {fw_path} to {type(parent_obj)}")
                parent_obj.add_session({'label': component_label})
            if component_type == 'subject':
                # print(f"add {component_type} named {component_label} from {fw_path} to {type(parent_obj)}")
                parent_obj.add_subject({'label': component_label})


def fws_upload_files_to_flywheel(fw_client, local_path, fw_path, logger=None):
    """
    use the flywheel API to upload file(s) defined by fw_path from local storage

    Parameters
    ----------
    fw_client: Client
        A Client object to do flywheel API work with
    local_path: str
        A local path where files come from. can be a file system path, or in future, redis or other non-direct
        file system path
    fw_path: str
        A flywheel path string, with or without the 'fw://' header, pointing to an object tree
    logger: logging.Logger, optional
        If included, write out a log message for each file downloaded

    Returns
    -------

    """

    fws_generate_tree(fw_client, fw_path)

    # will always need the acquisition object to send files to
    acquisition = fws_resolve_object(fw_client, fw_path, 'acquisition')
    # if '*' in local_path, upload all files to the acquisition, otherwise upload the one specificed file
    files = [local_path]

    if local_path.endswith('*'):
        files = glob.glob(local_path)

    for file in files:
        acquisition.upload_file(file)
        # log a message if logger provided
        if logger is not None:
            logger.info(f"upload flywheel {local_path}/{file} to {file}")

def fws_upload_file_to_flywheel(fw_client, local_path, fw_path, logger=None):
    """
    use the flywheel API to upload file(s) defined by fw_path from local storage

    Parameters
    ----------
    fw_client: Client
        A Client object to do flywheel API work with
    local_path: str
        A local path where files come from. can be a file system path, or in future, redis or other non-direct
        file system path
    fw_path: str
        A flywheel path string, with or without the 'fw://' header, pointing to an object tree
    logger: logging.Logger, optional
        If included, write out a log message for each file downloaded

    Returns
    -------

    """

    fws_generate_tree(fw_client, fw_path)

    # will always need the acquisition object to send files to
    # print("fws_upload_file_to_flywheel")
    # print(fw_path)
    acquisition = fws_resolve_object(fw_client, fw_path, 'acquisition')
    # if '*' in local_path, upload all files to the acquisition, otherwise upload the one specificed file
    acquisition.upload_file(local_path)
    # log a message if logger provided
    if logger is not None:
        logger.info(f"upload flywheel {local_path}/{os.path.basename(local_path)}")

def fws_create_paths(paths: list[str]):
    """
    given a set of paths, for each path make sure the folder tree exists
    Parameters
    ----------
    paths: list[str]
        A list of local file paths, with folder structure

    """

    # use os function to generate all subfolders in a path, if not already existing
    for path in paths:
        os.makedirs(path, exist_ok=True)


def fws_copy_file(path_from: str, path_to:str, logger=None):
    """
    copy a file from one local path to another local path, with log message if logger is provided
    Parameters
    ----------
    path_from: str
        The local path to copy the file from
    path_to: str
        The local path to copy the file to
    logger: logging.Logger, optional
        If provided, write a log message about the file being copied

    """
    if logger is not None:
        logger.info(f'copying {path_from} to {path_to}')
    shutil.copy(path_from, path_to)


def fws_load_image(fw_client, fw_path, file_name, local_root, local_path):
    """

    Parameters
    ----------
    fw_client
    fw_path
    file_name
    local_root
    local_path

    Returns
    -------

    """
    if fw_client is not None:
        return load_image_from_flywheel(fw_client, fw_path)
    else:
        return load_image_from_local_path(local_path)


def fws_input_file_list(fw_client, project_label,
                                 subject_labels=None,
                                 session_labels=None,
                                 acquisition_labels=None,
                                 generate_code=False,
                                 local_root=None):

    # generate data dictionary
    data = {'fw_client': fw_client}
    files = []
    code = [
        '# FWS-INPUTS edit this cell to the flywheel file references that you need, add local_path(s) if necessary, then TURN OFF generate_code above'
    ]

    # start the flywheel object tree
    # TODO: 202503 csk add more than one project/group/etc
    project = fw_client.projects.find_one(f'label={project_label}').reload()

    # TODO: 202503 csk better way to do this??
    group = [group for group in fw_client.groups() if group.id == project.group][0].reload()
    data['fw_root'] = f"/{group.id}/{project.label}"
    data['local_root'] = local_root

    if subject_labels is None:
        subject_labels = [subject.label for subject in project.subjects()]

    data_local_root = data['local_root']
    code.append(f'local_root = "{data_local_root}"')
    code.append('fws_input_files = FWSImageFileList( {')
    # traverse the flwheel object tree
    # TODO: 202503 add project (and group?) to this
    for subject_label in subject_labels:
        subject = project.subjects.find_one(f'label={subject_label}')
        sessions_used = [s for s in subject.sessions() if session_labels is None or s.label in session_labels]
        for session in sessions_used:

            for acquisition in [a for a in session.acquisitions()  if acquisition_labels is None or a.label in acquisition_labels]:
                fw_path = f'{session.label}/{acquisition.label}'
                if len(subject_labels) > 1:
                    fw_path = f'{subject_label}/{fw_path}'

                for file in acquisition.files:
                    # file_name = f'{file.name.replace(" ", "_").replace("-", "_").replace("*", "").replace("+", "").replace("(", "").replace(")", "").split(".")[0]}'
                    local_path = f'{local_root}'
                    # if local_root is not None:
                    #     local_path = f'{local_root}/{file.name}'

                    # TODO: 202503 csk tweak this to make unique without getting to large?
                    file_var_name = file.name
                    if len(sessions_used) > 1:
                        file_var_name = f'{session.label.replace(" ", "-").replace(".", "_").replace("-", "_").replace("(", "_").replace(")", "_")}_{file_var_name}'

                    file_item = {'fw_path': fw_path, 'file_name': file.name}
                    files.append(file_item)

                    fw_path = f'{group.id}/{project.label}/{subject.label}/{session.label}/{acquisition.label}/{file.name}'
                    local_path = f'{local_path}/{file.name}'
                    code.append(
                        f'"{file_var_name}": FWSImageFile(fw_client=fw_client, fw_path="{fw_path}",\n\tlocal_path="{local_path}"),')
    code.append('})')
    data['files'] = files

    if generate_code and fws_in_jupyter_notebook():
        # add a new code cell
        fws_create_new_cell('\n'.join(code))

    return data

def fws_contains_subfolder(folder_path):
    # Iterate through the items in the folder
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        # Check if the item is a directory (subfolder)
        if os.path.isdir(item_path):
            return True
    return False

def fws_expand_file_path(file_path):
    # expand any * into the list of files
    expanded_paths = [file_path]
    if file_path.endswith('*'):
        if fws_is_flywheel_path(file_path):
            # flywheel path, have to use client to find out what files are there
            expanded_paths = fws_expand_flywheel_path(file_path)
        else:
            # local storage path, glob for files, use ** to get files from subfolders if present
            if os.path.exists(os.path.dirname(file_path)):
                if fws_contains_subfolder(os.path.dirname(file_path)):
                    expanded_paths = glob.glob(f'{file_path}*{os.path.sep}*')
                else:
                    expanded_paths = glob.glob(file_path)

    return expanded_paths

def fws_translate_file_path(file_path, scratch_path, fileset=None):
    # external_files are the file paths that are pointed to in the file system (non-local items such as
    # flywheel paths are downladed to scratch space!). for local file system these are the same as script_files

    # print("fws_translate_file_path", file_path)
    if file_path.startswith('fw://'):
        # flywheel path
        downloaded_path = f'{scratch_path}'
        if fileset is not None:
            downloaded_path = f'{downloaded_path}{os.path.sep}{fileset.fileset_name}'
            # TODO: 202507 csk for Gustavo's code only? from local storage
            # flywheel_labels = fws_separate_flywheel_labels(file_path)
            # downloaded_path = f'{downloaded_path}/{flywheel_labels[2]}/{flywheel_labels[3]}'

            if fileset.env_common_path is not None:
                downloaded_path = downloaded_path.replace(fileset.env_common_path, f'{os.path.sep}{fileset.fileset_name}')
            os.makedirs(downloaded_path, exist_ok=True)
        # print("final downloaded path:", downloaded_path)
        # download to scratch space
        downloaded_file_path = f'{downloaded_path}{os.path.sep}{os.path.basename(file_path)}'
        fw_client = uwhealthaz_client()
        try:
            return fws_download_file_from_flywheel(fw_client, file_path, downloaded_file_path)

        except flywheel.rest.ApiException as e:
            # if this is an output file in flywheel, it has not been created yet, but the rest of the goo needs to be done!
            print("exception ", e)
            return downloaded_file_path

    else:
        return file_path

def get_common_file_path(file_list):
    # go through all io files and find the common parent folder
    if len(file_list) == 0:
        return ''
    if len(file_list) == 1:
        return os.path.dirname(file_list[0])
    return os.path.commonpath(file_list)

def fws_update_processors():

    processor_paths = glob.glob(f'{os.path.dirname(os.path.dirname(os.path.dirname(__file__)))}/processors/*')

    for processor_path in processor_paths:
        if processor_path.endswith("_processor"):
            test_script_path = glob.glob(f'{processor_path}/*test_script.yaml')
            if len(test_script_path) < 1:
                print(f"{os.path.basename(processor_path)} does not contain a test script!")
                continue
            print(processor_path, test_script_path[0], os.path.exists(test_script_path[0]))

# fws_update_processors()

def parse_classification(file, max_size):
    try:
        intent = file.classification['Intent'] if file.classification.get('Intent') is not None else []
        i_size = [file.classification.get("Rows"), file.classification.get("Columns"), file.classification.get("Columns"),]
        print("print_classification", i_size, max_size)

        if 'Structural' not in intent:
            return 'XX'
        elif file.classification.get("Features") is not None and 'FLAIR' in file.classification.get("Features"):
            return 'FLAIR'
        elif 'T1' in file.classification.get('Measurement'):
            return 'T1'
        elif 'T2' in file.classification.get('Measurement'):
            return 'T2'
    except Exception as e:
        print(e)
    return 'XX'

def parse_nifti_tags(file):
    if 'niiQuery_T1' in file.tags:
        return 'T1'
    if 'niiQuery_T1c' in file.tags:
        return 'T1c'
    if 'niiQuery_T2' in file.tags:
        return 'T2'
    if 'niiQuery_FLAIR' in file.tags:
        return 'FLAIR'
    return 'XX'

def fws_assign_modalities(dicom_fileset, nifti_fileset, modalities=fws_modalities):
    file_names = {}
    if fws_is_flywheel_path(nifti_fileset.original_path):

        for modality in modalities:
            # first, get assigned modality from nifti tag
            for file in nifti_fileset.get_flywheel_file_objects():
                modality_nifti = parse_nifti_tags(file)
                if modality_nifti == modality:
                    # found it!
                    file_names[modality] = file.name
                    break
            if modality not in file_names.keys():
                # second, get largest file from dicoms
                for file in dicom_fileset.get_flywheel_file_objects():
                    max_size = [0, 0, 0]
                    modality_dicom = parse_classification(file, max_size)
                    if modality_dicom == modality:
                        # found one!
                        file_names[modality] = file.name
                        break
                        # max_size =

    return file_names

def fws_add_script(container, script_info):
    container = container.reload()
    info = container.info
    scripts = info.get('scripts', [])
    scripts.append(script_info)
    info['scripts'] = scripts
    container.update_info(info)

def fws_get_next_script(container, remove=True):
    container = container.reload()
    info = container.info
    scripts = info.get('scripts', [])
    if len(scripts) == 0:
        return {}
    if remove:
        script = scripts.pop()
        info['scripts'] = scripts
        container.update_info(info)
    else:
        script = scripts[0]

    return script

def fws_has_more_scripts(container):
    container = container.reload()
    info = container.info
    scripts = info.get('scripts', [])
    return len(scripts) > 0
