#!/usr/bin/python

import logging
import sys

import ubik.defaults

log = logging.getLogger('ubik.hats.base')

# Base class for hats.  common functions.
class BaseHat(object):
    output = sys.stdout

    @staticmethod
    def areyou(string):
        return False

    def __init__(self, args, config=None, options=None):
        log.debug("Initialize args %s" % repr(args))
        self.config = config
        self.options = options

    def prerun(self):
        '''
        The prerun function of the base class does some common set up. There
        are a few things that shouldn't be initialized until immediately prior
        to run time because initializing a hat doesn't necessarily imply that
        it will ever be run.  (e.g. HelperHat creates hats but never runs them)
        '''
        if self.options:
            self.config_file = self.options.conf
        else:
            self.config_file = ubik.defaults.CONFIG_FILE
        if not self.config:
            self.config = ubik.config.UbikConfig()
            self.config.read(self.config_file)

    def set_options(self, options):
        'Register command line options with this hat'
        self.options = options
