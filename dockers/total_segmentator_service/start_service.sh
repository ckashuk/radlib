 #!/bin/bash
 sudo docker build -t total_segmentator_service .
 sudo docker run -it --gpus all --ipc=host -v /home/aa-cxk023/idia/Data/_Brain/Radiology/_Adult/_Glioma/GBM_Cohort_brucegroup/UW-GBM:/local -v /home/aa-cxk023/share/radservice_share/total_segmentator_service/in:/in -v /home/aa-cxk023/share/radservice_share/total_segmentator_service/out:/out -v /home/aa-cxk023/share/radservice_share/total_segmentator_service/logs:/logs -v /home/aa-cxk023/share/radservice_share/total_segmentator_service/scratch:/scratch total_segmentator_service /bin/bash
