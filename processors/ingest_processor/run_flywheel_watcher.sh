#!/bin/bash
clear
sudo rm -rf docker_app start_docker.sh
sudo docker image rm -f ${PWD##*/}
if [ -z "$2" ]
  then
     sudo python3 processor_app.py --scratch_path /home/aa-cxk023/share/scratch
else
     sudo python3 processor_app.py --scratch_path /home/aa-cxk023/share/scratch
fi