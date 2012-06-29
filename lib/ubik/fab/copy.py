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

NAME = 'copy'
log = logging.getLogger(NAME)

def _get_config(configfile='package.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    return config

def copysrc(version, config, env):
    'Copies source from a local directory'
    if not version:
        version = ''
    if not config:
        config = _get_config()

    destdir = env.builddir
    try:
        if config.get(NAME, 'destination') == 'root':
            destdir = env.rootdir
        elif config.get(NAME, 'destination') == 'src':
            destdir = env.srcdir
        destdir = os.path.join(destdir, config.get(NAME, 'prefix').lstrip('/'))
    except ConfigParser.NoOptionError:
        pass
    if not os.path.exists(destdir):
        os.makedirs(destdir)

    sourcedir = config.get(NAME, 'dir', False, 
                      {'version': version.split('-',1)[0],})
    log.debug('Using source dir of %s' % sourcedir)

    # The secret sauce is RSYNC!
    if os.path.exists(sourcedir):
        local("rsync -rvC --delete %s/ %s/" % (sourcedir, destdir), capture=False)
    else:
        log.error("Source directory %s does not exist" % sourcedir)
