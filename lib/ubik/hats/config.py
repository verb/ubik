
import ConfigParser
import logging

import ubik.config

from ubik.hats import HatException
from ubik.hats.base import BaseHat

CONFIG_FILE = "~/.rug/rug.ini"

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
        print >>out, "Usage: config"
        print >>out

    def __init__(self, args):
        log.debug("Initialize args %s" % repr(args))
        self.args = args

    def run(self):
        self._read_config()
        if len(self.args) == 1:
            value = self._get(*self.args)
            if value:
                print >>self.output, value
        elif len(self.args) == 2:
            self._set(*self.args)
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
        pass

    def _read_config(self):
        if self.options:
            cf = self.options.conf
        else:
            cf = CONFIG_FILE
        self.config = ubik.config.read(cf)
        self.cf_path = cf