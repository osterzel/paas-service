__author__ = 'oliver'

import unittest
import sys

sys.path.append( '../' )


import server

from mock import patch, MagicMock

class TestServer(unittest.TestCase):

    def setUp(self):
        self.data = "123"
        self.config = MagicMock()
        self.config.redis_host = "127.0.0.1"
        self.flask_app = server.app.test_client()

    def tearDown(self):
        pass

    def test_toplevel_url(self):
        output = self.flask_app.get("/")
        self.assertEqual(404, output.status_code)

    def test_api_endpoint_codes(self):
        output = self.flask_app.get("/api")
        self.assertEqual(404, output.status_code)

        output = self.flask_app.get("/api/app/")
        self.assertEqual(200, output.status_code)

        output = self.flask_app.get("/api/global/")
        self.assertEqual(200, output.status_code)

    def test_web_endpoint_codes(self):
        output = self.flask_app.get("/web/")
        self.assertEqual(200, output.status_code)

        output = self.flask_app.get("/web/dashboard")
        self.assertEqual(200, output.status_code)

        output = self.flask_app.get("/web/events")
        self.assertEqual(200, output.status_code)


