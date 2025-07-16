import flywheel

from radlib.fw.flywheel_clients import uwhealthaz_client

fw_client = uwhealthaz_client()

group_label = "brucegroup"
project_label = "GBM Cohort new"

project = fw_client.projects.find_one(f"label={project_label}")

for subject in project.subjects():
    print(subject.label)
    fw_client.delete_subject(subject.id)
