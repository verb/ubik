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
