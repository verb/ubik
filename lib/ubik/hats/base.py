#!/usr/bin/python
#
# Copyright 2012 Lee Verberne <lee@blarg.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import StringIO
import logging
import os
import sys
import textwrap
import urllib

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


    ### Utility methods for hats
    #
    # These snippets perform tasks common to multiple hats, but will
    # not be used by all subclassed hats

    def _add_package_config(self, pkgname):
        '''Look up the package config for pkgname and adds to running config

        Reading multiple package configs can result in undesirable behavior 
        due to the additive nature of reading multiple configs.  That is,
        subsequent configs may not entirely replace prior configs and result
        undesirable side effects.

        As such, calling this method after at least one successful package
        config read is intentionally made a no-op.
        '''
        # I'm not sure here whether it would be better to return a new 
        # ConfigParser object or to add the package config to self.config
        if self.config.has_option('package', 'name'):
            log.debug("Attempt to add config from multiple packages.")
            return

        uri = '/'.join((self.config.get('builder','iniuri'), pkgname+'.ini'))
        log.debug('Looking for package config at uri ' + uri)
        try:
            self.config.readfp(urllib.urlopen(uri))
        except IOError as e:
            log.info('Error reading package config from %s: %s', uri, str(e))
            raise e

    def _do_sysinit(self):
        '''Perform initialization for system commands

        Some initialization may be required prior to running commands 
        that interact with the OS.  This includes things like setting
        umask.
        '''
        try:
            os.umask(int(self.config.get('system', 'umask'), 0))
        except ConfigParser.NoOptionError:
            pass

    def _get_package_cache(self):
        '''Return the appropriate ubik.cache.UbikPackageCache object

        This method will return a previously initialized UbikPackageCache 
        object.  If one doesn't exist, it will create one based on config file
        values.
        '''
        try:
            return self.package_cache
        except AttributeError:
            pass

        cache_dir = self.config.get('cache', 'dir')
        self.package_cache = ubik.cache.UbikPackageCache(cache_dir)
        return self.package_cache

    def _get_infradb(self):
        '''Return the appropriate ubik.infra.db.InfraDB object

        This method will return a previously initialized InfraDB object.  If
        one doesn't exist, it will create one based on config file values.
        '''
        try:
            return self.idb
        except AttributeError:
            pass

        try:
            driver = self.config.get('infradb', 'driver')
        except ubik.config.NoOptionError:
            driver = 'dns'

        confstr = None
        try:
            if driver == 'dns':
                confstr = self.config.get('infradb', 'domain')
            elif driver == 'json':
                confstr = self.config.get('infradb', 'jsonfile')
        except ubik.config.NoOptionError:
            pass

        self.idb = ubik.infra.db.InfraDB(driver, confstr)
        return self.idb
