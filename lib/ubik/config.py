'Utility functions to read/write config for all ubik modules.'

import logging
import os.path

import ConfigParser

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

    def get(self, *args):
        try:
            ConfigParser.SafeConfigParser.get(self, *args)
        except ConfigParser.Error as e:
            if ((isinstance(e, ConfigParser.NoOptionError) or
                 isinstance(e, ConfigParser.NoSectionError)) and
                self.global_config.has_option(*args)):
                return self.global_config.get(*args)
            raise NoOptionError("Option %s.%s not configured" % args)
