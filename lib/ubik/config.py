'Utility functions to read/write config for all ubik modules.'

import logging
import os.path

import ConfigParser

log = logging.getLogger('ubik.config')

def read(files):
    "Read list of configuration files, return config object"
    config = UbikConfig()
    return config

# Note: SafeConfigParser is old-style
class UbikConfig(ConfigParser.SafeConfigParser):
    def read(self, files):
        'Just expands paths and the calls the real config parser reader'
        if isinstance(files,str):
            files = (files,)
        paths = [os.path.expanduser(f) for f in files]
        paths_read = ConfigParser.SafeConfigParser.read(self, paths)
        log.debug("Read config files %s" % repr(paths_read))

    def write(self, fileish):
        if isinstance(fileish, str):
            with open(os.path.expanduser(fileish), 'w') as cf:
                ConfigParser.SafeConfigParser.write(self, cf)
        else:
            ConfigParser.SafeConfigParser.write(self, fileish)
