__author__ = 'oliver'

import unittest
import sys
import flask

sys.path.append( '../' )

from mock import patch, MagicMock

import api
from api.resources.globalconfig import *

class TestGlobal(unittest.TestCase):

    def setUp(self):
        self.config = MagicMock()
        self.config.redis_host = "127.0.0.1"
        self.global_config = GlobalConfig(self.config)
        self.environment_variable = "ENVIRONMENT1"
        self.environment_variable_value = "VALUE1"

        self.add_global_environment = { "environment": { self.environment_variable: self.environment_variable_value }}
        self.remove_global_environment = { "environment": { self.environment_variable: "" }}

        self.hosts = [ "127.0.0.1" ]
        self.no_hosts = []
        self.add_host_entry = { "hosts": self.hosts }
        self.remove_host_entry = { "hosts": self.no_hosts }

    def tearDown(self):
        pass


    def test_hosts_entries(self):
        output = self.global_config.update_environment( self.add_host_entry )
        self.assertEqual(self.hosts, output['hosts'])

        output = self.global_config.get("hosts")
        self.assertEqual(self.hosts, output)

        output = self.global_config.update_environment( self.remove_host_entry )

        self.assertEqual(self.no_hosts, output['hosts'])

        output = self.global_config.get("hosts")
        self.assertEqual(self.no_hosts, output)


    def test_global_config(self):
        output = self.global_config.update_environment( self.add_global_environment)

        self.assertEqual(self.environment_variable_value, output['environment'][self.environment_variable])

        output = self.global_config.get("environment")

        self.assertEqual(self.environment_variable_value,output[self.environment_variable])