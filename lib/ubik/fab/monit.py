
import ConfigParser
import os, os.path

from fabric.api import cd, local, prompt, warn

def write_monit_config(version, config, env):
    'Creates a configfile to be run by pflex-appsupport monit'
    confdir = config.get('monit', 'confdir')
    service = config.get('monit', 'servicename')
    confpath = os.path.join(confdir, service + '.conf')
    local_confdir = os.path.join(env.rootdir, confdir.strip('/'))
    local_confpath = os.path.join(env.rootdir, confpath.strip('/'))
    if not os.path.exists(local_confdir):
        local('mkdir -p %s' % local_confdir, capture=False)
    with open(local_confpath, 'w') as mconf:
        mconf.write('check process %s with pidfile %s\n' % (service,
                    config.get('monit','pidfile')))
        mconf.write('    start program = "%s"\n' % config.get('monit', 'start'))
        mconf.write('    stop program = "%s"\n' % config.get('monit', 'stop'))
        if config.has_option('monit', 'depends'):
            mconf.write('    depends on %s\n' % config.get('monit', 'depends'))
        mconf.write('\n')
        mconf.write('check file %s with path %s\n' % (service + '.conf',
                    confpath))
        mconf.write('    if changed timestamp then exec '
                    '"/usr/sbin/monit reload"\n\n')

if __name__ == '__main__':
    import sys
    config = ConfigParser.SafeConfigParser()
    config.read(sys.argv[1])
    write_monit_config('1.0', config)
