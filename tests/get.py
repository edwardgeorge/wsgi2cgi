#!/usr/bin/env python

from StringIO import StringIO

from base import BaseTestCase
import wsgi2cgi

CGI_TEST_JSON = """#!/usr/bin/env python
import os
import json

print "Content-Type: text/plain\\n"
print json.dumps(dict(os.environ))
"""

CGI_TEST_JSON_STATUS = """#!/usr/bin/env python
import os
import json

print "Status: %s"
print "Content-Type: text/plain\\n"
print json.dumps(dict(os.environ))
"""

class TestGetMethod(BaseTestCase):

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

