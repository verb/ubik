#!/usr/bin/python

import sys

# Base class for hats.  common functions.
class BaseHat(object):
    output = sys.stdout
    options = None

    @staticmethod
    def areyou(string):
        return False


    def set_options(self, options):
        'Register command line options with this hat'
        self.options = options