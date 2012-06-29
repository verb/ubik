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

from fabric.api import cd, local, prompt, warn
from ubik import builder, packager

NAME = 'symlinks'
log = logging.getLogger(NAME)

defenv = builder.BuildEnv('_root','_root','.')

def _get_config(configfile='package.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    return config

def makelinks(version=None, config=_get_config(), env=defenv):
    'Creates specific symlinks requested in configuration'
    for link in config.options(NAME):
        log.debug('Creating symlink for ' + link)
        linkpath = os.path.join(env.rootdir, link)

        # Link prep
        if os.path.exists(linkpath):
            log.warning("Link path %s already exists, attempting to remove." %
                        link)
            local('rmdir %s' % linkpath, capture=False)
        elif not os.path.exists(os.path.dirname(linkpath)):
            log.info("Creating parent directory for link %s" % link)
            os.makedirs(os.path.dirname(linkpath))

        # Target prep
        target = config.get(NAME, link)
        targetpath = os.path.join(env.rootdir, target.lstrip('/'))
        if not os.path.exists(targetpath):
            log.warning("Target %s does not exist, so creating as dir" % target)
            os.makedirs(targetpath)

        local('ln -s %s %s' % (config.get(NAME, link), linkpath), capture=False)

