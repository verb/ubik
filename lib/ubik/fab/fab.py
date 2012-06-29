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
import json
import logging
import os, os.path
import shutil as sh
import subprocess
import tempfile

from fabric.api import abort, cd, local, prompt, warn

from ubik import builder, packager

# Ok, so this part gets a little complicated.
# This is a rug module that uses the fabric library to call the 
# "fab" unix command.  In this instance, think of "fab" like "make"

NAME = 'fab'
defenv = builder.BuildEnv('_root', '_root', '.')
log = logging.getLogger(NAME)

def _get_config(configfile='package.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    return config

def build(version, config, env=defenv):
    'Builds this package into a directory tree'
    if not version:
        version = prompt("What version did you want packaged there, hotshot?")
    if not isinstance(config, ConfigParser.SafeConfigParser):
        if config:
            config = _get_config(config)
        else:
            config = _get_config()

    # These are the variables that can be percent expanded in the ini
    config_vars = {
        'root': os.path.abspath(env.rootdir),
    }

    task = config.get(NAME, 'task', vars=config_vars)
    with cd(env.srcdir):
        local("printenv", capture=False)
        local("fab %s" % task, capture=False)

if __name__ == '__main__':
    build('1.0', 'doc/example-%s.ini' % NAME, 
        builder.BuildEnv("test/out", "test/src"))
