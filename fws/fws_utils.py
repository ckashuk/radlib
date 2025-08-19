import glob
import os
import shutil
import time

import flywheel
# from IPython.core.display_functions import clear_output
from flywheel.client import Client as flywheel_client

from radlib.fw.flywheel_data import load_image_from_flywheel, load_image_from_local_path

fw_types = ['group', 'project', 'subject', 'session', 'acquisition', 'file']
fw_type_objects = [
    flywheel.models.group_output.GroupOutput,
    flywheel.models.project_output.ProjectOutput,
    flywheel.models.subject_output.SubjectOutput,
    flywheel.models.session_output.SessionOutput,
    flywheel.models.acquisition_output.AcquisitionOutput,
    flywheel.models.file_node.FileNode
]

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


def fws_in_jupyter_notebook():
    """
    helper to test if the code is running in a jupyter notebook or not

    Returns
    -------
        True if the code is running in a jupyter notebook (ipython was detected),
        False if not

    """
    try:
        __IPYTHON__
        return True
    except NameError:
        return False


def fws_separate_flywheel_labels(fw_path: str)-> list[str]:
    """
    Given a flywheel path, separate it into it's "object label" components

    Parameters
    ----------
    flywheel_path: str
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
        if len(labels) > label_pos:
            fw_labels[label_pos] = labels[label_pos]
    return fw_labels


def fws_resolve_object(fw_client, fw_path:str, fw_type:str='project'):
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

    # traverse flywheel the object hierarchy


    # get the specific tree defined by flywheel_path
    if fw_type == 'acquisition':
        fw_path = os.path.dirname(fw_path)
    print("resolve", fw_path)
    objects = fw_client.resolve(fw_path.replace('fw://', ''))['path']

    # return the object denoted by type
    index = fw_types.index(fw_type)
    if len(objects) > index:
        return objects[index]
    return None


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
    # if '*' in fw_path, download all files from the acquisition, otherwise download the one specificed file
    files = [fws_separate_flywheel_labels(fw_path)[5]]
    if fw_path.endswith('*'):
        files = acquisition.files

    for file in files:
        acquisition.download_file(file.name, f'{local_path}/{file.name}')
        # log a message if logger provided
        if logger is not None:
            logger.info(f"download flywheel {file} to {local_path}/{file.name}")

def fws_generate_tree(fw_client, fw_path):
    # construct the tree if needed (ignore 0=file if presented)
    for i in (5, 4, 3, 2, 1):
        try:
            fw_obj_path = fw_path.replace("fw://", "").rsplit('/', i)[0]
            obj = fw_client.resolve(fw_obj_path)['path'][-1]
        except Exception as e:
            fw_type = fw_types[5-i]
            print(fw_path.replace("fw://", "").rsplit('/'))
            fw_label = fw_path.replace("fw://", "").rsplit('/')[5-i]
            # TODO: 202505 csk add project and group?
            if fw_type == 'acquisition':
                print(f"add {fw_type} named {fw_label} from {fw_path} to {type(obj)}")
                obj.add_acquisition({'label': fw_label})
            if fw_type == 'session':
                print(f"add {fw_type} named {fw_label} from {fw_path} to {type(obj)}")
                obj.add_session({'label': fw_label})
            if fw_type == 'subject':
                print(f"add {fw_type} named {fw_label} from {fw_path} to {type(obj)}")
                obj.add_subject({'label': fw_label})

    # exit()

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
    print("local_path", local_path)
    if local_path.endswith('*'):
        files = glob.glob(local_path)
    print(files)
    for file in files:
        acquisition.upload_file(file)
        # log a message if logger provided
        if logger is not None:
            logger.info(f"upload flywheel {local_path}/{file} to {file}")


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


