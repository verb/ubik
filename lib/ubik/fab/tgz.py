
import ConfigParser
import logging
import os, os.path

from fabric.api import cd, local, prompt

NAME = 'tgz'
log = logging.getLogger(NAME)

def _get_config(configfile='package.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    return config

def untar(version, config, env):
    'Downloads a file URI and untars to builddir'
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

    sourceurl = config.get(NAME, 'source', False, 
                      {'version': version.split('-',1)[0],})
    log.debug('Using source URL of %s' % sourceurl)

    # For now just use system tools for this
    if not os.path.exists('src.tgz'):
        local("curl -f -o src.tgz " + sourceurl, capture=False)
    local("tar -C %s -xvf src.tgz" % destdir, capture=False)
