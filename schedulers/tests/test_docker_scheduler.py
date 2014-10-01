__author__ = 'oliver'

import unittest
import sys

sys.path.append( '../' )

from mock import patch, MagicMock

from schedulers.docker import DockerClient

class TestInstanceStart(unittest.TestCase):

    def setUp(self):
        self.data = "123"
        self.cluster_name = "test_cluster"
        self.hosts = [ "127.0.0.1" ]
        self.auth = "123"
        self.domain = "bob.com"
        self.options = "123"
        self.SchedulerClient = DockerClient(self.cluster_name, self.hosts, self.auth, self.domain, self.options)
        # self.api = api.app.test_client()

    def test_get_customers(self):
        output = self.SchedulerClient.create()

        self.assertEqual("123",output)
