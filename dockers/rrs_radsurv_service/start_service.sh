#!/bin/bash
 sudo docker build -t rrs_radsurv_service .
 sudo docker run -it --gpus all --ipc=host -v /home/aa-cxk023/idia/Data/_Brain/Radiology/_Adult/_Glioma/GBM_Cohort_brucegroup/UW-GBM:/local -v /mnt/RadServiceCache/rrs_radsurv_service/in:/in -v /mnt/RadServiceCache/rrs_radsurv_service/out:/out -v /mnt/RadServiceCache/rrs_radsurv_service/logs:/logs -v /mnt/RadServiceCache/rrs_radsurv_service/scratch:/scratch rrs_radsurv_service /bin/bash
