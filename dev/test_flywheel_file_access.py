import flywheel

from radlib.fw.flywheel_clients import uwhealthaz_client

fw_client = uwhealthaz_client()

group_label = 'prostatespore'
project_label = 'csk test_processor project'
subject_label = 'csk_test_subject'
series_label = 'csk_test_session'
ack_label = 'PET'
file1_label = 'PET AC Prostate.zip'
file2_label = ''
file3_label = ''

def is_dcm_file(file_name):
    if file_name.ends_with('.dcm'):
        return True
    if file_name.ends_with('.zip'):
        return True
    return False

project = fw_client.projects.find_one(f'label={project_label}')
subject = fw_client.subjects.find_one(f'label={subject_label}')
for session in subject.sessions():
    for ack in session.acquisitions():
        for file in [file for file in ack.files if is_dcm_file(file.name)]:
            print(file.name)
