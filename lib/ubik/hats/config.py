
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

    def help(self, out):
        '''Print help message to specified file object

        This method is called on an instance so that it can give help specific
        to the arguments that have been parsed by __init__()
        '''
        print >>out, "Usage: config [ option [ value ] ]"
        print >>out
        print >>out, "Without arguments, dump the entire config."
        print >>out
        print >>out, "With arguments, display or set config options."

    def __init__(self, args, config=None, options=None):
        super(ConfigHat, self).__init__(args, config, options)
        self.args = args

    def run(self):
        self.prerun()
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
        try:
            section, option = key.split('.', 2)
        except ValueError:
            section = 'DEFAULT'
            option = key

        if not section == 'DEFAULT' and not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)
