__author__ = 'oliver'

import unittest
import sys

sys.path.append( '../' )

from mock import MagicMock

from common.globalconfig import *

class TestGlobal(unittest.TestCase):

    def setUp(self):
        self.global_config = GlobalConfig()
	self.host = "127.0.0.1"
	self.hosts = { "hosts": [ self.host ] }

    def tearDown(self):
        pass

    def test_hosts_entries(self):
        output = self.global_config.add_hosts(self.hosts)
        self.assertIn(self.host, output)

	output = self.global_config.get_hosts()
	self.assertIn(self.host, output)

	output = self.global_config.remove_hosts(self.hosts) 
        self.assertNotIn(self.host, output)
