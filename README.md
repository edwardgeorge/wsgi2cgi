wsgi2cgi
========

Run CGI apps under Python WSGI protocol ([PEP 333](http://www.python.org/dev/peps/pep-0333/)).

This is a simple WSGI application that executes an external process
and translates the WSGI protocol to the Common Gateway Interface (CGI).

Example:

    >>> from wsgiref.simple_server import make_server
    >>> import wsgi2cgi

    >>> def app(environ, start_response):
    >>>    wapp = wsgi2cgi.CGI('/path/to/executable.cgi')
    >>>    return wapp.application(environ, start_response)

    >>> httpd = make_server('127.0.0.1', 8000, app)
    >>> print "Serving on 127.0.0.1:8000..."
    >>> httpd.serve_forever()

The WSGI application can be used with [any server supporting WGSI](http://wsgi.readthedocs.org/en/latest/servers.html).


Install
-------

The module can be installed [from source](https://github.com/reidrac/wsgi2cgi) using setup.py:

    python setup.py install

Alternativelly it can be installed with [pip](http://pypi.python.org/pypi/pip):

    pip install wsgi2cgi


License
-------

This package is open source under the MIT license terms. Check COPYING
file for further details.


Author
------

 - Juan J. Martinez <jjm@usebox.net>

