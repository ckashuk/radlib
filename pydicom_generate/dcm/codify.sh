#! /bin/bash
python3 codify.py 01.dcm pydicom_generate_mr_master.py
python3 codify.py 1.2.826.0.1.3680043.2.629.20190306.10034577425707046841670623789.PT.dcm pydicom_generate_pt_master.py
python3 codify.py 1.2.826.0.1.3680043.2.629.20190306.10527514967919552016108815494.CT.dcm pydicom_generate_ct_master.py
