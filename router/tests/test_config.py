import unittest
import sys

from router.config import Config 

from mock import patch, MagicMock

class TestsRouterConfig(unittest.TestCase):
	
	def setUp(self):
		pass
		self.config = Config()
		self.mock = MagicMock()

	def tearDown(self):
		pass

	def test_return_config(self):
		with patch('__builtin__.open', self.mock):
		    	manager = self.mock.return_value.__enter__.return_value
			manager.read.return_value = 'some data'

			output = self.config.return_config()
			self.assertEqual({'servers': 'some data', 'upstreams': 'some data'}, output)
			
