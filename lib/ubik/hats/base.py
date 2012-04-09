#!/usr/bin/python

import StringIO
import logging
import sys
import textwrap

import ubik.defaults

log = logging.getLogger('ubik.hats.base')

# Base class for hats.  common functions.
class BaseHat(object):
    output = sys.stdout

    @staticmethod
    def areyou(string):
        return False

    def __init__(self, argv, config=None, options=None):
        log.debug("Initialize args %s" % repr(argv))
        self.argv = argv
        self.config = config
        self.options = options
        if self.options:
            self.config_file = self.options.conf
        else:
            self.config_file = ubik.defaults.CONFIG_FILE
        if not self.config:
            self.config = ubik.config.UbikConfig()
            self.config.read(self.config_file, ubik.defaults.GLOBAL_CONFIG_FILE)

    def __repr__(self):
        return "<Hat Object: %s>" % self.name

    def help(self, out):
        '''
        For hats that don't need dynamically generated help, generate help from
        the doc strings of commands in command_list and (potentially)
        command_map
        '''

        log.debug("Using help function from base class")
        help_list = []
        if len(self.args) > 0 and hasattr(self, 'command_map'):
            i = 0
            for arg in self.args:
                i += 1
                if arg == ';':
                    break
                if arg in self.command_map:
                    help_list.append(self.command_map[arg])
            del self.args[:i]

        if not help_list:
            help_list = self.command_list

            print >>out
            print >>out, "%s - %s" % (self.name, self.desc)
            print >>out
            print >>out, "Usage:"
        print >>out

        tw = textwrap.TextWrapper(width=80, initial_indent=' '*8,
                                  subsequent_indent=' '*8)
        for command in help_list:
            if command.__doc__:
                helptxt = StringIO.StringIO(command.__doc__)
                line = ''
                while not line:
                    line = textwrap.dedent(helptxt.readline()).rstrip()
                while line:
                    print >>out, ' '*4 + line
                    line = textwrap.dedent(helptxt.readline()).rstrip()
                print >>out, tw.fill(textwrap.dedent(helptxt.read()))
                print >>out

    def run(self):
        self.runhat()

    def set_options(self, options):
        'Register command line options with this hat'
        self.options = options

