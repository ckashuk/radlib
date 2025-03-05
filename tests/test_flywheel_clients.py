import unittest

import SimpleITK as sitk
import numpy as np

from fw.flywheel_clients import uw_client, uwhealth_client, uwhealthaz_client

"""
tests for flywheel client functionality
"""
class TestFlywheelClients(unittest.TestCase):
    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_flywheel_clients(self):
         # try:
         #     fw = uw_client()
         # except Exception:
         #     self.fail("the uw_client test fails, may need to update the API_KEY?")

         try:
             fw = uwhealth_client()
         except Exception:
             self.fail("the uw_client test fails, may need to update the API_KEY?")
         try:
             fw = uwhealthaz_client()
         except Exception:
             self.fail("the uw_client test fails, may need to update the API_KEY?")


if __name__ == "__main__":
    unittest.main()
