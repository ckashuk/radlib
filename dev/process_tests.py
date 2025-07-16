from radlib.processor import Processor
from processors.rrs_radsurv_processor.radservice_app import RRSRadSurvProcessor

process1 = Processor()
process2 = RRSRadSurvProcessor()

process1.run_local(scratch_path='Z:/scratch', script_path='/processors/rrs_radsurv_processor/rrs_radsurv_processor_test_script.yaml')
process2.run_local(scratch_path='Z:/scratch', script_path='/processors/rrs_radsurv_processor/rrs_radsurv_processor_test_script.yaml')
