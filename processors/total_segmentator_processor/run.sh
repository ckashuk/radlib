#!/bin/bash
clear
sudo rm -rf docker_app start_docker.sh
sudo docker image rm -f ${PWD##*/}
sudo python3 radservice_app.py --scratch_path /home/aa-cxk023/share/scratch --script_path /home/aa-cxk023/share/radlib/processors/${PWD##*/}/${PWD##*/}_test_script.yaml

