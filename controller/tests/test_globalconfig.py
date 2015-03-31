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

    def tearDown(self):
        pass

    def test_hosts_entries(self):
        output = self.global_config.add_host(self.host)
        self.assertIn(self.host, output)

	output = self.global_config.get_hosts()
	self.assertIn(self.host, output)

	output = self.global_config.remove_host(self.host) 
        self.assertNotIn(self.host, output)
