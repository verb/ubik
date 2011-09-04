
import ConfigParser
import os, os.path

from ubik import builder

from fabric.api import cd, local, prompt, warn

NAME = 'supervisor'
DEFAULT_CONFDIR = '/etc/opt/pflex/supervisor/conf.d'

def _get_config(configfile='package.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    return config

def write_supervisor_config(version, config, env):
    'Creates a configfile to be run by pflex-appsupport supervisord'
    if not isinstance(config, ConfigParser.SafeConfigParser):
        if config:
            config = _get_config(config)
        else:
            config = _get_config()

    # These are the variables that can be percent expanded in the ini
    config_vars = {
        'root': os.path.abspath(env.rootdir),
        'version': version.split('-',1)[0],
    }

    try:
        confdir = config.get(NAME, 'confdir', vars=config_vars)
    except ConfigParser.NoOptionError:
        confdir = DEFAULT_CONFDIR
    service = config.get(NAME, 'service', vars=config_vars)
    confpath = os.path.join(confdir, service + '.conf')
    local_confdir = os.path.join(env.rootdir, confdir.strip('/'))
    local_confpath = os.path.join(env.rootdir, confpath.strip('/'))
    if not os.path.exists(local_confdir):
        local('mkdir -m 750 -p %s' % local_confdir, capture=False)
    with open(local_confpath, 'w') as sconf:
        sconf.write('[program:%s]\n' % service)
        sconf.write('command = %s\n' % 
                    config.get(NAME, 'command', vars=config_vars))
        for option in ('directory','autostart','startsecs','stopwaitsecs'):
            if config.has_option(NAME, option):
                sconf.write('%s = %s\n' % (option,
                            config.get(NAME, option, vars=config_vars)))
        ### TODO: remove once config files migration 'workdir' -> 'directory'
        if config.has_option(NAME, 'workdir'):
            sconf.write('directory = %s\n' % 
                        config.get(NAME, 'workdir', vars=config_vars))
        ### TODONE

if __name__ == '__main__':
    write_supervisor_config('1.0', 'doc/example-%s.ini' % NAME,
                            builder.BuildEnv(rootdir='test/out'))
