from flywheel.client import Client as flywheel_client
from radlib.fws.fws_image import FWSImageFile
from radlib.fw.flywheel_data import load_image_from_local_path, load_image_from_flywheel


def fws_in_jupyter_notebook():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False

def fws_load_image(fw_client, fw_path, file_name, local_root, local_path):
    if fw_client is not None:
        return load_image_from_flywheel(fw_client, fw_path)
    else:
        return load_image_from_local_path(local_path)


def create_new_cell(contents):
    from IPython.core.getipython import get_ipython
    shell = get_ipython()
    shell.set_next_input(contents, replace=False)


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

                    fw_path = f'{group.id}/{project.label}/{subject.label}/{session.label}/{acquisition.label}'
                    code.append(
                        f'"{file_var_name}": FWSImageFile(fw_client=fw_client, fw_path="{fw_path}", file_name="{file.name}",\n\tlocal_path="{local_path}"),')
    code.append('})')
    data['files'] = files

    if generate_code and fws_in_jupyter_notebook():
        # add a new code cell
        create_new_cell('\n'.join(code))

    return data

