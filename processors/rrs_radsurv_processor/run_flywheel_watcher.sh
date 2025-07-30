#!/bin/bash
clear
sudo rm -rf docker_app start_docker.sh
sudo docker image rm -f ${PWD##*/}
cd ../../processor
if [ -z "$1" ]
  then
     sudo nohup python3 flywheel_watcher.py
else
     sudo python3 flywheel_watcher.py
fi