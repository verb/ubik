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
import os, os.path

from ubik import builder

from fabric.api import local, prompt, warn

NAME = 'supervisor'
DEFAULT_CONFDIR = '/etc/opt/pflex/supervisor/conf.d'
SUP_PROGRAM_KEYS = (
    'autostart',
    'command',
    'directory',
    'startsecs',
    'stopwaitsecs'
)

def _get_config(configfile='package.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    return config

def _write_supervisor_section(fp, config, section, config_vars):
    try:
        service = config.get(section, 'service', vars=config_vars)
    except ConfigParser.NoOptionError:
        # A section with no service definition is legal for changing config
        # for this module, but it means we have nothing to do here.
        pass
    else:
        fp.write('[program:%s]\n' % service)
        for option in SUP_PROGRAM_KEYS:
            if config.has_option(section, option):
                fp.write('%s = %s\n' % (option,
                         config.get(section, option, vars=config_vars)))
        fp.write('\n')

def write_supervisor_config(version, config, env):
    'Creates a configfile to be run by pflex-appsupport supervisord'
    if not isinstance(config, ConfigParser.SafeConfigParser):
        if config:
            config = _get_config(config)
        else:
            config = _get_config()

    # These are the variables that can be percent expanded in the ini
    config_vars = {
        'root': os.path.abspath(env.rootdir),
        'version': version.split('-',1)[0],
    }

    try:
        confdir = config.get(NAME, 'confdir', vars=config_vars)
    except ConfigParser.NoOptionError:
        confdir = DEFAULT_CONFDIR
    local_confdir = os.path.join(env.rootdir, confdir.strip('/'))

    pkgname = config.get('package', 'name', vars=config_vars)
    confpath = os.path.join(confdir, pkgname + '.conf')
    local_confpath = os.path.join(env.rootdir, confpath.strip('/'))
    if not os.path.exists(local_confdir):
        local('mkdir -m 750 -p %s' % local_confdir, capture=False)

    with open(local_confpath, 'w') as sconf:
        for section in config.sections():
            if section == 'supervisor' or section.startswith('supervisor:'):
                _write_supervisor_section(sconf, config, section, config_vars)

if __name__ == '__main__':
    write_supervisor_config('1.0', 'doc/example-%s.ini' % NAME,
                            builder.BuildEnv(rootdir='test/out'))
