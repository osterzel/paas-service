__author__ = 'oliver'

import unittest
import sys
import flask

sys.path.append( '../' )

from mock import patch, MagicMock

import api
from api.resources.applications import *

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

        self.update_record = {
            "urls": "testapplication.localdomain.com",
            "memory_in_mb": 128,
            "command": "test command",
            "docker_image": "test dockerimage",
            "type": "daemon"
        }


    def tearDown(self):
        self.teardown_application_record()
        pass

    def setup_application_record(self):
        try:
            output = self.application.get(self.test_application)
        except:
            output = None

        if output:
            output = self.application.delete_application(self.test_application)

        output = self.application.create_application(self.create_record)
        return output

    def teardown_application_record(self):
        try:
            output = self.application.delete_application(self.test_application)
        except Exception:
            print "Record does not exist"

    def test_application_lifecycle(self):
        self.setup_application_record()
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

    def test_parameters(self):
        output = self.setup_application_record()

        self.assertEqual(output['name'], "testapplication")

        output = self.application.update_application(self.test_application,self.update_record)
        self.assertEqual(output['urls'], self.update_record['urls'])
        self.assertEqual(output['memory_in_mb'], self.update_record['memory_in_mb'])
        self.assertEqual(output['docker_image'], self.update_record['docker_image'])
        self.assertEqual(output['command'], self.update_record['command'])
        self.assertEqual(output['type'], self.update_record['type'])







