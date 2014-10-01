__author__ = 'oliver'

import unittest
import sys
import flask

sys.path.append( '../' )

from mock import patch, MagicMock

import api
from api.resources.applications import *

class TestCluster(unittest.TestCase):

    def setUp(self):
        self.data = "123"
        self.config = MagicMock()
        self.config.redis_host = "0.0.0.0"
        self.global_config = Applications(self.config)
        self.app = flask.app

    def tearDown(self):
        pass

    def test_get_customers(self):
        data = self.global_config.get("environment")

        self.assertEqual("123",data)