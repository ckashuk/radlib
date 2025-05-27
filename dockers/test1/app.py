import logging
import os
import inspect

import yaml
import SimpleITK as sitk
import numpy as np

from radlib.service.service_instance import ServiceInstance


def processor(self, script_path):
    # always call setup first
    self.set_up(script_path)

    # this is where you do what needs to be done

    # write to an output file
    with open(f'{self.output_path}/{self.script_name}.txt', 'a') as f:
        f.writelines(f'{self.processor_name} on script {self.script_name} service {self.service_name} custom processor!')

    # always call cleanup last
    self.clean_up(script_path)


if __name__ == "__main__":
    # instantiate the ServiceInstance, give it a processor function, and start it!
    # TODO: 202504 csk find better way(s) to stop!
    instance = ServiceInstance()
    instance.processor = processor
    instance.start()


