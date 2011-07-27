'Utility functions to read/write config for all ubik modules.'

import ConfigParser
import logging
import os.path

import ubik.defaults

log = logging.getLogger('ubik.config')

def read(files):
    "Read list of configuration files, return config object"
    config = UbikConfig()
    return config

class Error(ConfigParser.Error):
    pass
class NoOptionError(Error):
    pass

# Note: SafeConfigParser is old-style
class UbikConfig(ConfigParser.SafeConfigParser):
    '''
    Basically just a config parser, but UbikConfig also keeps a system-wide
    config that is kept separate and can be used for defaults.

    The advantage of keeping it separate is that it the config defaults
    won't be written to the users local config upon change.
    '''
    def read(self, files, system_files=()):
        'Just expands paths and the calls the real config parser reader'
        # System-level config
        if isinstance(system_files,str):
            system_files = (system_files,)
        self.global_config = ConfigParser.SafeConfigParser()
        paths = [os.path.expanduser(f) for f in system_files]
        paths_read = self.global_config.read(paths)
        log.debug("Read system config files %s" % repr(paths_read))

        # User-level config
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

    def get(self, section, option):
        if ConfigParser.SafeConfigParser.has_option(self, section, option):
            return ConfigParser.SafeConfigParser.get(self, *args)
        elif self.global_config.has_option(section, option):
            return self.global_config.get(section, option)
        else:
            secopt = '.'.join((section, option))
            if secopt in ubik.defaults.config_defaults:
                return ubik.defaults.config_defaults[secopt]
            else:
                raise NoOptionError("Option %s not configured" % secopt)

