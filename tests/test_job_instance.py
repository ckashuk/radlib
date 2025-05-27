import os
import shutil
import time
import unittest
from unittest.mock import MagicMock, patch

from radlib.service.service_instance import ServiceInstance
from radlib.service.job_instance import JobInstance
from radlib.service.utils import parse_script

class TestJobInstance(unittest.TestCase):
    def setUp(self):
        self.test_root_path = '//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Research/test_data/radservice'
        self.test_yaml_path = '//onfnas01.uwhis.hosp.wisc.edu/radiology/Groups/GarrettGroup/Research/test_data/radservice/scripts/test_script.yaml'

        self.test_input_path = f'{self.test_root_path}/radservice/in'
        self.test_output_path = f'{self.test_root_path}/radservice/out'
        self.test_scratch_path = f'{self.test_root_path}/radservice/scratch'
        self.test_logs_path = f'{self.test_root_path}/radservice/logs'

        self.test_name = 'test_service'

        # necessary environment paths for the service
        os.environ[ServiceInstance.INPUT_PATH_ENV] = self.test_input_path
        os.environ[ServiceInstance.OUTPUT_PATH_ENV] = self.test_output_path
        os.environ[ServiceInstance.SCRATCH_PATH_ENV] = self.test_scratch_path
        os.environ[ServiceInstance.LOGS_PATH_ENV] = self.test_logs_path

        os.environ[ServiceInstance.SERVICE_NAME_ENV] = self.test_name

    def test_create_job(self):
        job_instance = JobInstance(None)

        self.assertIsInstance(job_instance, JobInstance, "Failed JobInstance creation")

    def test_unique_scratch_name(self):

        service = ServiceInstance(service_name='test_service')
        job_instance_1 = JobInstance(service_instance=service, job_name='job_name_1')
        job_instance_1a = JobInstance(service_instance=service, job_name='job_name_1a')
        job_instance_2 = JobInstance(service_instance=service, job_name='job_name_2')

        job_unique_1 = job_instance_1.get_unique_name()
        job_unique_1a = job_instance_1a.get_unique_name()
        job_unique_2 = job_instance_2.get_unique_name()

        print(job_unique_1)
        print(job_unique_1a)
        print(job_unique_2)

        self.assertNotEqual(job_unique_1, job_unique_2, "Failed unique name with different job names")
        self.assertNotEqual(job_unique_1, job_unique_1a, "Failed unique name with the same job name")




