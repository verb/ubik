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
import os, os.path

from fabric.api import cd, local, prompt

from ubik import builder

NAME = 'git'
log = logging.getLogger(NAME)

def _get_config(configfile='package.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    return config

def clone(version, config, env):
    'Clones a git repo and potentially chooses a tag'
    if not version:
        version = ''
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
    repo = config.get(NAME, 'repo', vars=config_vars)

    # Clone if doesn't exist, but don't touch repo otherwise
    if not os.path.exists(os.path.join(env.srcdir, '.git')):
        local("git clone %s %s" % (repo, env.srcdir), capture=False)

    with cd(env.srcdir):
        if config.has_option(NAME, 'tag'):
            local("git checkout %s" %
                  config.get(NAME, 'tag', vars=config_vars), capture=False)
        elif config.has_option(NAME, 'branch'):
            local("git checkout %s" %
                  config.get(NAME, 'branch', vars=config_vars), capture=False)

if __name__ == '__main__':
    clone("0.9.13", "doc/example-%s.ini" % NAME,
        builder.BuildEnv(builddir='test/out'))
