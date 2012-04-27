#!/usr/bin/env python

import sys
import os
import unittest

tests = os.path.dirname(os.path.abspath(__file__))
sys.path.append(tests)
sys.path.append(tests + "/..")

from get import *

if __name__ == '__main__':
        unittest.main()

