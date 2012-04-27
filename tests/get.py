#!/usr/bin/env python

import os
import unittest
import tempfile
import json
from StringIO import StringIO
from wsgiref.util import setup_testing_defaults

import wsgi2cgi

CGI_TEST_JSON = """#!/usr/bin/env python
import os
import json

print "Content-Type: text/plain\\n\\n"
print json.dumps(dict(os.environ))
"""

CGI_TEST_JSON_STATUS = """#!/usr/bin/env python
import os
import json

print "Status: %s"
print "Content-Type: text/plain\\n"
print json.dumps(dict(os.environ))
"""

class TestGetMethod(unittest.TestCase):

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

    def test_wsgiref_defaults(self):
        self.cgi.write(CGI_TEST_JSON)
        self.cgi.close()

        response = self.request()

        self.assertEqual(self.status, "200 OK")
        self.assertEqual(self.headers, [('Content-Type', 'text/plain')])

        self.assertEqual(response['REQUEST_METHOD'], 'GET')

        for key, value in response.iteritems():
            if not key.startswith("HTTP_"):
                self.assertTrue(key in wsgi2cgi.CGI_VARS)

    def test_http_headers(self):
        self.cgi.write(CGI_TEST_JSON)
        self.cgi.close()

        self.env['HTTP_EXTRA_HEADER'] = 'extra-http-header'
        response = self.request()

        self.assertEqual(self.status, "200 OK")
        self.assertEqual(self.headers, [('Content-Type', 'text/plain')])

        self.assertEqual(response['REQUEST_METHOD'], 'GET')

        for key, value in response.iteritems():
            if not key.startswith("HTTP_"):
                self.assertTrue(key in wsgi2cgi.CGI_VARS)

        self.assertEqual(response['HTTP_EXTRA_HEADER'], 'extra-http-header')

    def test_extra_env(self):
        self.cgi.write(CGI_TEST_JSON)
        self.cgi.close()

        self.extra_env = dict(EXTRA_HEADER='extra-header')
        response = self.request()

        self.assertEqual(self.status, "200 OK")
        self.assertEqual(self.headers, [('Content-Type', 'text/plain')])

        self.assertEqual(response['REQUEST_METHOD'], 'GET')
        self.assertEqual(response['EXTRA_HEADER'], 'extra-header')

    def test_status_ok(self):
        self.cgi.write(CGI_TEST_JSON_STATUS % "200 OK")
        self.cgi.close()

        response = self.request()

        self.assertEqual(self.status, "200 OK")
        self.assertEqual(self.headers, [('Content-Type', 'text/plain')])

        self.assertEqual(response['REQUEST_METHOD'], 'GET')

    def test_status_not_found(self):
        self.cgi.write(CGI_TEST_JSON_STATUS % "404 Not Found")
        self.cgi.close()

        response = self.request()

        self.assertEqual(self.status, "404 Not Found")
        self.assertEqual(self.headers, [('Content-Type', 'text/plain')])

        self.assertEqual(response['REQUEST_METHOD'], 'GET')

    def test_internal_error_popen_format_error(self):
        self.cgi.write("FORMAT-ERROR")
        self.cgi.close()

        self.env['wsgi.errors'] = StringIO()
        response = self.request_raw()

        self.assertEqual(self.status, "500 Internal Server Error")
        self.assertEqual(self.headers, [('Content-Type', 'text/plain')])

        self.assertTrue("Exec format error" in self.env['wsgi.errors'].getvalue())
        self.env['wsgi.errors'].close()

    def test_internal_error_popen_not_such_file(self):
        self.cgi.write("#!/donotexist\n")
        self.cgi.close()

        self.env['wsgi.errors'] = StringIO()
        response = self.request_raw()

        self.assertEqual(self.status, "500 Internal Server Error")
        self.assertEqual(self.headers, [('Content-Type', 'text/plain')])

        self.assertTrue("No such file" in self.env['wsgi.errors'].getvalue())
        self.env['wsgi.errors'].close()

    def test_internal_error_invalid_content_length(self):
        self.cgi.write(CGI_TEST_JSON)
        self.cgi.close()

        self.env['CONTENT_LENGTH'] = 'invalid'
        self.env['wsgi.errors'] = StringIO()
        response = self.request_raw()

        self.assertEqual(self.status, "500 Internal Server Error")
        self.assertEqual(self.headers, [('Content-Type', 'text/plain')])

        self.assertTrue("invalid Content-Length header" in self.env['wsgi.errors'].getvalue())
        self.env['wsgi.errors'].close()

    def test_internal_error_invalid_header(self):
        self.cgi.write('#!/bin/sh\n\necho -e "Content-Type: text/plain\\nInvalid-Header value\n\nERROR"')
        self.cgi.close()

        self.env['wsgi.errors'] = StringIO()
        response = self.request_raw()

        self.assertEqual(self.status, "500 Internal Server Error")
        self.assertEqual(self.headers, [('Content-Type', 'text/plain')])

        self.assertTrue("invalid header" in self.env['wsgi.errors'].getvalue())
        self.env['wsgi.errors'].close()


if __name__ == '__main__':
        unittest.main()

