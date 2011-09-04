
import ConfigParser
import json
import logging
import os, os.path
import shutil as sh
import subprocess
import tempfile

from fabric.api import abort, cd, local, prompt, warn

from infra import packager
from infra import builder

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
