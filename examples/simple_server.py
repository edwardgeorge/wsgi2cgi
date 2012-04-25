#!/usr/bin/env python
#
# Example using wsgiref.simple_server included in
# Python stock modules
#

from wsgiref.simple_server import make_server

import wsgi2cgi

def app(environ, start_response):
    wapp = wsgi2cgi.CGI('/path/to/executable.cgi')
    return wapp.application(environ, start_response)

if __name__ == "__main__":
    httpd = make_server('127.0.0.1', 8000, app)
    print "Serving on 127.0.0.1:8000..."
    httpd.serve_forever()

