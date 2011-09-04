
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
