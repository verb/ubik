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

from fabric.api import cd, local, prompt, warn

def _get_config(configfile='package.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    return config

def hackthepath(version, config, env):
    'Creates symlinks for backwards compatibility with jetty paths'
    prefix = config.get('jettypathhack', 'prefix').strip('/')
    targets = os.listdir(os.path.join(env.rootdir, prefix, 'jetty'))
    with cd(os.path.join(env.rootdir, prefix)):
        for target in targets:
            local('[ -e %s ] || ln -s %s' % (target, 
                os.path.join('jetty', target)), capture=False)
