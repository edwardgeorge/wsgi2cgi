
import json
import os
import tempfile
import unittest

from wsgiref.util import setup_testing_defaults

import wsgi2cgi

class BaseTestCase(unittest.TestCase):
    def setup_app(self, environ, start_response):
        wapp = wsgi2cgi.CGI(self.cgi.name, extra_env=self.extra_env)
        return wapp.application(environ, start_response)

    def start_response(self, status, headers):
        self.status = status
        self.headers = headers

    def request_raw(self):
        app = self.setup_app(self.env, self.start_response)
        return ''.join(app)

    def request(self):
        return json.loads(self.request_raw())

    def setUp(self):
        self.cgi = tempfile.NamedTemporaryFile(delete=False)
        os.chmod(self.cgi.name, 0700)

        self.env = dict()
        setup_testing_defaults(self.env)

        self.extra_env = None

    def tearDown(self):
        os.unlink(self.cgi.name)

