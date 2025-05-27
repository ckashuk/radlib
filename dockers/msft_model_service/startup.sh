#!/bin/bash
ls -1
# conda env create -y -n cxr-rep-gen-env -f cxr_report_gen_environment.yaml
# conda init
# conda activate cxr-rep-gen-env
ipython kernel install --user --name=cxr-rep-gen-kernel
jupyter lab
# sudo docker run --runtime=nvidia --gpus "device=3" -it -p 8889:8888 --shm-size=1g --ulimit memlock=-1 --name cxrreportgeninference --rm -v "/mnt/cxrscratch":/workingdir -v /mnt/CXRReportCheckCohort:/data nvcr.io/uwsmphrad/florenceinferenceuw:1.0
