#!/bin/bash
# if parameter passed, send through to the docker container as an environment variable
if [ $# -eq 1]; then
    export RADSERVICE_SINGLE_SCRIPT_PATH $1

# back up so we get radlab
cd ../..

# build and run the docker
# if script was passed, should run that script and exit
# if script was not passed, should watch the folder for
sudo docker build -t radlab/dockers/ingest_service .
sudo docker run -it -v /mnt/RadServiceCache/idia_ingest_service/watch:/watch -v /mnt/RadServiceCache/idia_ingest_service/scratch:/scratch ingest_service /bin/bash
