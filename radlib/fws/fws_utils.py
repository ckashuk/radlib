from flywheel.client import Client as flywheel_client

from fw.flywheel_data import load_image_from_local_path, load_image_from_flywheel


def uwhealthaz_client():
    return flywheel_client('flywheelaz.uwhealth.org:djESGL039D5xmVq81ZknQS4tT2nEg2IYNcd3z-ubX_3wzwCyLaUJ1WeAg',
                           request_timeout=1000)


def fws_in_jupyter_notebook():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False


def create_new_cell(contents):
    from IPython.core.getipython import get_ipython
    shell = get_ipython()
    shell.set_next_input(contents, replace=False)


def fws_load_image(group_label, project_label, subject_label, session_label, acquisition_label, file_name, local_path):
    if local_path is not None:
        return load_image_from_local_path(local_path)

    return load_image_from_flywheel(group_label, project_label, subject_label, session_label, acquisition_label,
                                    file_name)


def fws_generate_data_dictionary(fw_client, project_label,
                                 project_labels=None,
                                 subject_labels=None,
                                 session_labels=None,
                                 acquisition_labels=None,
                                 generate_code=False):
    # important flywheel objects
    project = fw_client.projects.find_one(f'label={project_label}').reload()
    group = [group for group in fw_client.groups() if group.id == project.group][0].reload()
    subject = project.subjects()[0].reload()

    # generate data dictionary
    data = {'fw_client': fw_client,
            # 'project': project,
            'files': []
            }
    code = [
        '# FWS-INPUTS edit this cell to the flywheel file references that you need, add local_path(s) if necessary, then TURN OFF generate_code above']

    # traverse the flwheel object tree
    # TODO: 202503 add project (and group?) to this
    for session in project.subjects()[0].sessions():

        if session_labels is not None and session.label not in session_labels:
            continue

        for acquisition in session.acquisitions():

            if acquisition_labels is not None and acquisition.label not in acquisition_labels:
                continue

            for file in acquisition.files:
                data['files'].append({"group": group.id,
                                      "project": project.label,
                                      "subject": subject.label,
                                      "session": session.label,
                                      "acquisition": acquisition.label,
                                      "file": file.name})
                file_var = f'{session.label.replace(" ", "_")}_{file.name.replace(" ", "_").split(".")[0]}'
                code.append(
                    f'{file_var} = fws_load_image("{group.id}", "{project.label}", "{subject.label}", "{session.label}", "{acquisition.label}", "{file.name}", local_path=None)')

    if generate_code and fws_in_jupyter_notebook():
        # add a new code cell
        create_new_cell('\n'.join(code))

    return data

