#!/usr/bin/env python

from StringIO import StringIO

from base import BaseTestCase
import wsgi2cgi

CGI_TEST = """#!/usr/bin/env python
import os
import sys

print "Content-Type: text/plain\\n"
print "METHOD=%s" % os.environ['REQUEST_METHOD']
indata = sys.stdin.read()
print indata
"""

class TestPostMethod(BaseTestCase):

    def test_post(self):
        self.cgi.write(CGI_TEST)
        self.cgi.close()

        expected = "Some content to be post\nsome content for the test"

        self.env['REQUEST_METHOD'] = 'POST'
        self.env['wsgi.input'] = StringIO(expected)
        self.env['CONTENT_LENGTH'] = str(len(expected))

        response = self.request_raw()

        self.assertEqual(self.status, "200 OK")
        self.assertEqual(self.headers, [('Content-Type', 'text/plain')])

        self.assertTrue(response.startswith('METHOD=POST\n'))
        self.assertEqual(response[len('METHOD=POST\n'):], expected + "\n")


if __name__ == '__main__':
        unittest.main()

