#!/usr/bin/python

import sys

# Base class for hats.  common functions.
class BaseHat(object):
    output = sys.stdout

    @staticmethod
    def areyou(string):
        return False

