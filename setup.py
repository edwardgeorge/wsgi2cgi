#!/usr/bin/env python
from setuptools import setup
from wsgi2cgi import __version__, __author__

def readme():
    try:
        return open('README.md').read()
    except:
        return ""

setup(name='wsgi2cgi',
      version=__version__,
      description='Run CGI apps under Python WSGI protocol',
      long_description=readme(),
      author=__author__,
      author_email='jjm@usebox.net',
      license='MIT',
      url='https://github.com/reidrac/wsgi2cgi',
      include_package_data=True,
      zip_safe=False,
      packages = ['wsgi2cgi'],
      classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        ],
      )


