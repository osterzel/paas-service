__author__ = 'oliver'

import unittest
import sys

sys.path.append( '../' )

from mock import patch, MagicMock

import api

class TestCustomers(unittest.TestCase):

    def setUp(self):
        self.data = "123"

    def test_get_customers(self):
        data = "123"

        self.assertEqual("123",data)