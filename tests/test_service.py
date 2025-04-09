import os
import shutil
import time
import unittest
from unittest.mock import MagicMock, patch

from radlib.service.service_instance import ServiceInstance
from radlib.service.utils import parse_script

"""
tests for FWSImageFile object, a class to hold information on an image file which could come
from a local file share or from a Flywheel instance. BIG ASSUMPTION is that the file name in 
both cases is the same
"""
class TestRadService(unittest.TestCase):
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

    def test_parse_yaml(self):
        script = parse_script(self.test_yaml_path)
        print(script.keys())

        self.assertEqual(script['service_name'], f'{self.test_name}', "Failed during yaml parsing")
        self.assertEqual(script['service_root_folder'], f'{self.test_root_path}/radservice', "Failed during yaml parsing")
        self.assertEqual(script['input_image_path'], f'{self.test_root_path}/images/mr7.nii.gz', "Failed during yaml parsing")
        self.assertEqual(script['docker_image'], 'csktests:test1', "Failed during yaml parsing")
        self.assertEqual(script['output_image_path'], f'{self.test_root_path}/outputs/mr7.png', "Failed during yaml parsing")

    def test_create_service(self):
        service = ServiceInstance()

        self.assertIsInstance(service, ServiceInstance, "Failed ServiceInstance creation")

    def test_create_service_processor(self):
        def new_processor():
            return "this is a fake processor"

        service = ServiceInstance(new_processor)
        self.assertTrue(callable(service.processor))

        ret = service.processor()
        self.assertEqual(ret, "this is a fake processor")

    def test_run_service(self):
        service = ServiceInstance()
        service.start()
        self.assertTrue(service.active)

        time.sleep(5)

        service.stop()
        self.assertFalse(service.active)


    def test_grab_script(self):
        service = ServiceInstance()
        service.start()
        self.assertTrue(service.active)

        time.sleep(10)

        shutil.copy(self.test_yaml_path, self.test_input_path)
        time.sleep(15)

        service.stop()
        self.assertFalse(service.active)


    def test_two_services(self):
        service1 = ServiceInstance(service_name='service1')
        service2 = ServiceInstance(service_name='service2')
        service1.start()
        service2.start()

        time.sleep(10)

        shutil.copy(self.test_yaml_path, self.test_input_path)
        time.sleep(15)

        service1.stop()
        service2.stop()

