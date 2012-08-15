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
import logging

import ubik.config

from ubik.hats import HatException
from ubik.hats.base import BaseHat

log = logging.getLogger('ubik.hats.config')

class ConfigHat(BaseHat):
    "Modify configuration files"

    name = 'config'
    desc = "Modify configuration"

    @staticmethod
    def areyou(string):
        "Confirm or deny whether I am described by string"
        if string in ('config', 'configure'):
            return True
        return False

    def __init__(self, argv, config=None, options=None):
        super(ConfigHat, self).__init__(argv, config, options)
        self.args = argv[1:]

    def run(self):
        if len(self.args) == 0:
            self.config.write(self.output)
        elif len(self.args) == 1:
            value = self._get(*self.args)
            if value:
                print >>self.output, value
        elif len(self.args) == 2:
            if self.args[0].lower() == 'unset':
                self._unset(self.args[1])
            else:
                self._set(*self.args)
            if self.config_file:
                self.config.write(self.config_file)
        else:
            raise HatException("Invalid number of arguments to config")

    def _get(self, key):
        '''config [ OPTION ]

        Print the configured value for OPTION.  If OPTION is omitted, dump the
        entire config.
        '''
        try:
            section, option = key.split('.', 2)
        except ValueError:
            section = 'DEFAULT'
            option = key

        try:
            value = self.config.get(section, option)
        except ConfigParser.NoOptionError:
            value = None
        except ConfigParser.NoSectionError:
            value = None

        return value

    def _set(self, key, value):
        '''config OPTION VALUE

        Set configuration OPTION to VALUE in the local user config.
        '''
        try:
            section, option = key.split('.', 2)
        except ValueError:
            section = 'DEFAULT'
            option = key

        if not section == 'DEFAULT' and not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)

    def _unset(self, key):
        '''config unset OPTION

        Remove the option named OPTION.
        '''
        try:
            section, option = key.split('.', 2)
        except ValueError:
            section = 'DEFAULT'
            option = key

        # The option may exist as a default or in the system config file,
        # but not in the user config, so we can ignore errors to remove
        # options/sections that don't exist
        try:
            self.config.remove_option(section, option)
            if len(self.config.options(section)) == 0:
                self.config.remove_section(section)
        except (ConfigParser.NoOptionError,
                ConfigParser.NoSectionError):
            pass

    command_list = ( _get, _set, _unset )

