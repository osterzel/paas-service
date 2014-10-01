__author__ = 'oliver'

import unittest
import sys
import flask

sys.path.append( '../' )

from mock import patch, MagicMock

import api
from api.resources.globalconfig import *

class TestCluster(unittest.TestCase):

    def setUp(self):
        self.data = "123"
        self.global_config = GlobalConfig()
        self.app = flask.app

    def tearDown(self):
        pass

    def test_get_customers(self):
        data = self.global_config.get("environment")

        self.assertEqual("123",data)