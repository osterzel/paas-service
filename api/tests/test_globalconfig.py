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

	self.host = "127.0.0.1"

    def tearDown(self):
        pass

    def test_hosts_entries(self):
        output = self.global_config.add_host(self.host)
        self.assertIn(self.host, output)

	output = self.global_config.get_hosts()
	self.assertIn(self.host, output)

	output = self.global_config.remove_host(self.host) 
        self.assertNotIn(self.host, output)
