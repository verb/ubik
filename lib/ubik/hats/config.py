
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

    command_list = ( _get, _set )

