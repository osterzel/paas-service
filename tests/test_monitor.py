__author__ = 'oliver'

import unittest
import sys

sys.path.append( '../' )

from mock import MagicMock

from common.applications import *

class TestApplication(unittest.TestCase):

    def setUp(self):
        self.data = "123"
        self.config = MagicMock()
        self.config.redis_host = "127.0.0.1"
        self.application = Applications(self.config)

        self.test_application = "testapplication"
        self.create_record = {
            "name": self.test_application
        }


    def tearDown(self):
        pass

    def test_application_lifecycle(self):
        try:
            output = self.application.get(self.test_application)
        except:
            output = None

        if output:
            output = self.application.delete_application(self.test_application)
            self.assertEqual("Application deleted", output['message'])


        output = self.application.create_application(self.create_record)

        self.assertEqual(self.test_application, output['name'])
        self.assertEqual(512, output['memory_in_mb'])
        self.assertEqual("testapplication", output['urls'])

        output = self.application.get(self.test_application)
        self.assertEqual(self.test_application, output['name'])

        output = self.application.delete_application(self.test_application)
        self.assertEqual("Application deleted", output['message'])


