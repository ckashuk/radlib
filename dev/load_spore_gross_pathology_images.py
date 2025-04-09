from radlib.fw.flywheel_clients import uwhealth_client

fw_client = uwhealth_client()
fw_project = fw_client.findone(label='Complete17009PathologyArchive')

for fw_subject in fw_project.fw_subjects:
    if len(fw_subject.label) > 5:
        continue
    print(fw_subject.label)
