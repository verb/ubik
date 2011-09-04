
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

