"""
Run CGI apps under Python WSGI protocol (PEP 333).

This is a simple WSGI application that executes an external process
and translates the WSGI protocol to the Common Gateway Interface (CGI).

For example usage, see the CGI class.
"""
__author__  =  'Juan J. Martinez'
__version__ =  '0.2.1'
__all__ = "CGI"

import os
import select
import sys
import re
from subprocess import Popen, PIPE, STDOUT

try:
    import fcntl
    has_fcntl = True
except ImportError:
    has_fcntl = False

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


def _set_nonblocking(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    if flags & os.O_NONBLOCK:
        return
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)


def _iter_lines(stdout, stderr, stderr_obj):
    _set_nonblocking(stdout)
    _set_nonblocking(stderr)
    output_buffer = ''

    while True:
        first_newline = output_buffer.find('\n')
        if first_newline != -1:
            nln = first_newline + 1
            out, output_buffer = output_buffer[:nln], output_buffer[nln:]
            yield out
            continue

        to_read = [i for i in (stdout, stderr) if not i.closed]
        if not to_read:
            if output_buffer:
                yield output_buffer
            yield ''
            return
        r, w, e = select.select(to_read, [], [])

        if stderr in r:
            d = stderr.read(BUFFER)
            if not d:
                stderr.close()
                continue
            stderr_obj.write(d)
            stderr_obj.flush()

        if stdout in r:
            d = stdout.read(BUFFER)
            if not d:
                stdout.close()
                continue
            output_buffer = output_buffer + d


def _iter_single(stdout):
    while True:
        line = stdout.readline()
        if not line:
            stdout.close()
            yield ''
            return
        yield line


def _iter_windows_fallback(process, stderr_obj):
    stdout, stderr = process.communicate()
    stderr_obj.write(stderr)
    stderr_obj.flush()
    for line in stdout.splitlines(True):
        yield line
    yield ''


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
    def __init__(self, command, extra_env=None, redirect_stderr=False):
        """
        CGI class constructor.

        Args:
            command: the command to be executed (absolute path).
            extra_env: additional environment variables, useful to pass
                configuration information to some CGI applications.
            redirect_stderr: redirect stderr to stdout. default is to send
                stderr to the file provided by the 'wsgi.errors'
                environment variable.

        Raises:
            ValueError: extra_env is not a dictionary.
        """
        self.cmd = [arg.strip() for arg in command.split(' ')]
        self.extra_env = extra_env
        self.env = dict()
        self.redirect_stderr = redirect_stderr

        if extra_env and not isinstance(extra_env, dict):
            raise ValueError("extra_env is not a dictionary")

    def log_error(self, message):
        """
        Logs errors to wsgi.errors.

        Args:
            message: string to be logged.

        The destination of the error messages depends on the WSGI server.
        """
        fd = self.env.get('wsgi.errors', sys.stderr)
        fd.write("%s: %s\n" % (self.cmd, message))
        fd.flush()

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

        if self.redirect_stderr:
            stderr = STDOUT
        else:
            stderr = environ.get('wsgi.errors', sys.stderr)
            if hasattr(stderr, 'fileno'):
                stderr_arg = stderr
                select_for_stderr = False
            else:
                stderr_arg = PIPE
                select_for_stderr = True

        try:
            process = Popen(self.cmd, stdin=PIPE, stdout=PIPE, stderr=stderr_arg, env=cgi_env)
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

        stdin = environ.get('wsgi.input', None)
        while stdin and content_length > 0:
            data = stdin.read(BUFFER)
            if not data:
                break
            content_length -= len(data)
            process.stdin.write(data)
        process.stdin.close()

        if select_for_stderr:
            if not has_fcntl:
                line_iterator = _iter_windows_fallback(process, stderr)
            else:
                line_iterator = _iter_lines(process.stdout, process.stderr, stderr)
        else:
            line_iterator = _iter_single(process.stdout)

        response = None
        headers = []
        while True:
            line = next(line_iterator).strip()
            if not line:
                break

            if re.match(r'Status: [0-9]{3}.*', line):
                if response:
                    self.log_error('duplicated Status header: %s' % line)
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
            data = next(line_iterator)
            if not data:
                break
            yield data

        return
