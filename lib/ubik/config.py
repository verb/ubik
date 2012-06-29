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
#
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
class NoOptionError(ConfigParser.NoOptionError):
    pass

# Note: SafeConfigParser is classic (unfortunately)
class UbikConfig(ConfigParser.SafeConfigParser):
    '''
    ConfigParser with ubik-specific extensions

    Basically just a config parser, but UbikConfig does some amount of file
    and/or section-name inheritance.  Some config files can be read as "system"
    or "global" config files.  These "system" config files will be treated the
    same as if they had been read as a standard config, but their values won't
    be written by write() The advantage of keeping it separate is that it the 
    config defaults won't be written to the users local config upon change.
    '''
    def read(self, files, system_files=()):
        """Just expands paths and the calls the real config parser reader

        >>> c=UbikConfig()
        >>> c.read('tests/config.ini')
        >>> c.read(('tests/config.ini','tests/config.ini'))
        >>> c.read('tests/config.ini','/does/not/exist/system.ini')

        """
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

    def get(self, section, option, raw=False, vars=None):
        """Returns an option from one of several config files

        Config file precedence is as follows:
            1. config files read directly into this object as "files" to read()
            2. global files read into self.global_config by read()
            3. default from ubik.defaults.config_defaults

        If the requested section contains ':' characters, the section will be
        treated as a hierarchy of paths to search.  For example, section
        "one:two:three" will try the following sections:
            1. one:two:three
            2. one:two
            3. one

        >>> c=UbikConfig()
        >>> c.read('tests/config.ini', 'tests/system.ini')
        >>> c.get('cache','dir')
        '~/.rug/cache'
        >>> c.get('test','one')
        'two'
        >>> c.get('system','three')
        'four'
        >>> c.get('package:rpm','arch')
        'noarch'
        >>> c.get('package:deb','arch')
        'all'

        """
        while section:
            if ConfigParser.SafeConfigParser.has_option(self, section, option):
                return ConfigParser.SafeConfigParser.get(self, section, option,
                                                         raw, vars)
            elif self.global_config.has_option(section, option):
                return self.global_config.get(section, option, raw, vars)
            else:
                secopt = '.'.join((section, option))
                if secopt in ubik.defaults.config_defaults:
                    return ubik.defaults.config_defaults[secopt]

            if ':' in section:
                section = section.rsplit(':', 1)[0]
            else:
                section = False

        raise NoOptionError(section, option)

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)

