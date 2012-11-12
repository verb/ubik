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

from fabric.api import local, prompt, warn
# Fabric 1.0 changed changed the scope of cd() to only affect remote calls.
# This bit of kludgery maintains compatibility of this file with fabric 0.9,
# but it is only possible because no remote calls are made in this file
try:
    from fabric.api import lcd as cd
except ImportError:
    from fabric.api import cd

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
