
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

