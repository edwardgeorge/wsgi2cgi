"""
Run CGI apps under Python WSGI protocol (PEP 333).

This is a simple WSGI application that executes an external process
and translates the WSGI protocol to the Common Gateway Interface (CGI).

For example usage, see the CGI class.
"""
__author__  =  'Juan J. Martinez'
__version__ =  '0.1'
__all__ = "CGI"

import re
from subprocess import Popen, PIPE, STDOUT

# Allowed CGI environmental variables
CGI_VARS = """
SERVER_SOFTWARE
SERVER_NAME
GATEWAY_INTERFACE
SERVER_PROTOCOL
SERVER_PORT
REQUEST_METHOD
PATH_INFO
PATH_TRANSLATED
SCRIPT_NAME
QUERY_STRING
REMOTE_HOST
REMOTE_ADDR
AUTH_TYPE
REMOTE_USER
REMOTE_IDENT
CONTENT_TYPE
CONTENT_LENGTH
""".split('\n')

# Buffer size for buffered input/output
BUFFER = 1024*64

class CGI(object):
    """
    Run a CGI app with WSGI.

    Example:
    >>> from wsgiref.simple_server import make_server
    >>> import wsgi2cgi

    >>> def app(environ, start_response):
    >>>    wapp = wsgi2cgi.CGI('/path/to/executable.cgi')
    >>>    return wapp.application(environ, start_response)

    >>> httpd = make_server('127.0.0.1', 8000, app)
    >>> print "Serving on 127.0.0.1:8000..."
    >>> httpd.serve_forever()

    """
    def __init__(self, command, extra_env=None):
        """
        CGI class constructor.

        Args:
            command: the command to be executed (absolute path).
            extra_env: additional environment variables, useful to pass
                configuration information to some CGI applications.

        Raises:
            ValueError: extra_env is not a dictionary.
        """
        self.cmd = [arg.strip() for arg in command.split(' ')]
        self.extra_env = extra_env

        if extra_env and not isinstance(extra_env, dict):
            raise ValueError("extra_env is not a dictionary")

    def log_error(self, message):
        """
        Logs errors to wsgi.errors.

        Args:
            message: string to be logged.

        The destination of the error messages depends on the WSGI server.
        """
        self.env['wsgi.errors'].write("%s: %s\n" % (self.cmd, message))
        self.env['wsgi.errors'].flush()

    def application(self, environ, start_response):
        """
        WSGI application.

        Args:
            environ: WSGI enviroment.
            start_response: start response callable.

        Any internal error executing the CGI application will be logged
        in wsgi.errors and a HTTP 500 error response will be sent to the
        client.
        """
        self.env = environ
        cgi_env = dict()
        for key, value in environ.iteritems():
            if key in CGI_VARS or key.startswith('HTTP_'):
                cgi_env[key] = value

        if self.extra_env:
            cgi_env.update(self.extra_env)

        try:
            process = Popen(self.cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, env=cgi_env)
        except (OSError, ValueError), e:
            self.log_error(str(e))
            start_response("500 Internal Server Error", [('Content-Type', 'text/plain')])
            yield "500 Internal Server Error\n"
            return

        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0) or 0)
        except ValueError:
            self.log_error("invalid Content-Length header")
            start_response("500 Internal Server Error", [('Content-Type', 'text/plain')])
            yield "500 Internal Server Error\n"
            return

        stdin = environ['wsgi.input']
        while content_length:
            data = stdin.read(BUFFER)
            if not data:
                break
            content_length -= len(data)
            process.stdin.write(data)
        process.stdin.close()

        response = None
        headers = []
        while True:
            line = process.stdout.readline().strip()
            if not line:
                break

            if response is None:
                if re.match(r'Status: [0-9]{3}.*', line):
                    response = line[len("Status :"):]
                    continue

            if ':' not in line:
                self.log_error('invalid header: %s' % line)
                start_response("500 Internal Server Error", [('Content-Type', 'text/plain')])
                yield "500 Internal Server Error\n"
                return

            header, value = line.split(':', 1)
            headers.append((header.strip(), value.strip()))

        start_response(response or "200 OK", headers)

        while True:
            data = process.stdout.read(BUFFER)
            if not data:
                break
            yield data

        process.stdout.close()
        return
