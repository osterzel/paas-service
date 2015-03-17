import unittest
import sys

import server

from mock import patch, MagicMock

class TestsRouterAPI(unittest.TestCase):
	
	def setUp(self):
		pass
		self.flask_app = server.app.test_client()

	def tearDown(self):
		pass

	def test_rest_api(self):
		response = self.flask_app.get("/")
		self.assertEqual(404, response.status_code)

		self.assertEqual(200, self.flask_app.get("/router").status_code)
