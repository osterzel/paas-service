__author__ = 'oliver'

import unittest
import sys
import flask

sys.path.append( '../../' )

from mock import patch, MagicMock

import api
from common.dockerfunctions import DockerFunctions

class TestDockerFunctions(unittest.TestCase):

    def setUp(self):
	self.env_test = [ "ENV=ENV=1" ]
	self.dockerfunctions = DockerFunctions(None, None, None)

    def tearDown(self):
        pass

    def test_dockerconfig(self):
	env = self.dockerfunctions.dockerConfigSplit(self.env_test)
	self.assertEqual(env, { "ENV": "ENV=1" })
