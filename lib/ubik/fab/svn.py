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

NAME = 'svn'
log = logging.getLogger(NAME)

def _get_config(configfile='package.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    return config

def checkout(version, config, env):
    'Checks out a particular svn respository'
    if not version:
        version = ''
    if not config:
        config = _get_config()

    repo = config.get(NAME, 'repo', False, 
                      {'version': version.split('-',1)[0],})

    if not os.path.exists(os.path.join(env.srcdir, '.svn')):
        local("svn co %s %s" % (repo, env.srcdir), capture=False)
    else:
        with cd(env.srcdir):
            local("svn update")

