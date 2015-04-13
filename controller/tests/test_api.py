__author__ = 'oliver'

import unittest
import sys

sys.path.append( '../' )

import server

from mock import patch, MagicMock
from common.applications import *

class TestServer(unittest.TestCase):

    def setUp(self):
        self.data = "123"
        self.config = MagicMock()
        self.config.redis_host = "127.0.0.1"
        self.flask_app = server.app.test_client()
	self.test_application = "unittestapp"

	self.setup_application()

    def tearDown(self):
	self.flask_app.delete('/app/{}'.format(self.test_application))

    def setup_application(self):
	self.flask_app.post('/app/', data=dict(name=self.test_application))

    def test_api_json_validation(self):
        response = self.flask_app.patch("/app/{}".format(self.test_application))
	self.assertRegexpMatches(response.data, "Content-type must be application/json")
        response = self.flask_app.patch("/app/{}".format(self.test_application), content_type='application/json')
	self.assertRegexpMatches(response.data, "Not valid json")

        response = self.flask_app.post("/app/")
	self.assertRegexpMatches(response.data, "Content-type must be application/json")
        response = self.flask_app.post("/app/", content_type='application/json')
	self.assertRegexpMatches(response.data, "Not valid json")

    def test_api_fatal_errors(self):
	response = self.flask_app.patch("/app/unknownapp", content_type='application/json', data='{ "testjson": "testjson" }')
        self.assertRegexpMatches(response.data, "Application not found")
	self.assertEquals(500, response.status_code)
