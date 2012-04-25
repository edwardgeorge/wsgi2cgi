"""
    Run gitweb using gunicorn (http://gunicorn.org/)

    $ gunicorn --workers=2 gunicorn-gitweb:app
"""

import wsgi2cgi

def app(environ, start_response):
    wapp = wsgi2cgi.CGI('/var/www/git/gitweb.cgi')
    return wapp.application(environ, start_response)

