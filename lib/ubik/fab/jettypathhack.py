
import ConfigParser
import os, os.path

from fabric.api import cd, local, prompt, warn

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
