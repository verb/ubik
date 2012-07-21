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

import logging
import os.path
import subprocess
import tempfile

import ubik.defaults

from fabric.api import local, prompt, put, run, settings
from fabric.state import connections

from ubik.hats import HatException
from ubik.hats.base import BaseHat

log = logging.getLogger('ubik.hats.supervisor')

# Translation map for commands supported by this hat and their 
# equivalent supervisorctl commands.  The %s is expanded to the
# application name.
SUPCTL_CMD_MAP = {
    'add': "sup -i 'reread;add %s;quit'",
    'restart': "sup restart %s",
    'start': "sup start %s",
    'status': "sup status %s",
    'stop': "sup stop %s",
    'stderr': "sup tail %s stderr",
    'stdout': "sup tail %s stdout",
}

class SupervisorHat(BaseHat):
    "Supervisor Hat"

    name = 'supervise'
    desc = "Supervise Running Software"

    @staticmethod
    def areyou(string):
        "Confirm or deny whether I am described by string"
        return string in ('sup', 'supervise', 'start', 'stop', 'restart')

    def __init__(self, argv, config=None, options=None):
        super(SupervisorHat, self).__init__(argv, config, options)
        self.args = argv[1:]

    def run(self):
        command = self.argv[0]
        if command in self.command_map:
            if len(self.args) == 0 or self.args[0] == "help":
                self.help(self.output)
            else:
                self.command_map[command](self, self.args)
        else:
            raise HatException("Unknown command: %s" % command)

    # supervisor sub-commands
    def supervise(self, pargs):
        '''supervise ACTION APP [ HOST [ HOST ... ] ]

        Supervises an application to a list of hosts.  If hosts are omitted, 
        attempts to determine host list automatically.

        ACTION may be one of the following:

        restart - Restarts the application
        '''
        action, app = pargs[0:2]

        # Translate action into supervisorctl command
        if action in SUPCTL_CMD_MAP:
            cmd = SUPCTL_CMD_MAP[action] % app
        else:
            raise HatException("Invalid action: " + action)

        # Determine receiving hosts
        hostnames = pargs[2:]
        idb = self._get_infradb()
        hosts = None
        if hostnames:
            hosts = idb.hosts(hostnames)
        else:
            try:
                service = idb.service(app)
                hosts = service.hosts()
            except ubik.infra.db.InfraDBException:
                pass
        if not hosts:
            raise HatException("Could not determine hosts for " + app)
        log.debug("hosts to supervise: %s", hosts)

        # TODO: Determine actual user via InfraDB
        deploy_user = self.config.get('deploy', 'user')

        print >>self.output, ('Running "%s" on the following hosts:' % cmd)
        for host in hosts:
            print >>self.output, "\t%s@%s" % (deploy_user, host)
        yesno = prompt("Proceed?", default='No')
        if yesno.strip()[0].upper() != 'Y':
            return

        try:
            for host in hosts:
                with settings(host_string=str(host), user=deploy_user):
                    fab_output = run(cmd, shell=False)
        finally:
            # TODO: replace with disconnect_all() w/ fabric 0.9.4+
            for key in connections.keys():
                connections[key].close()
                del connections[key]

    # supervisor sub-commands
    def add(self):
        '''sup add APP [ HOST [ HOST ... ] ]

        Causes supervisord to reread its configuration and add APP.  This is
        necessary when an application is being added to supervisor or an
        application's supervisor config has changed.
        '''
        self.supervise(['add'] + args)

    def restart(self, args):
        '''[sup] restart APP [ HOST [ HOST ... ] ]

        Restarts an application on a list of hosts.
        '''
        self.supervise(['restart'] + args)

    def start(self):
        '''[sup] start APP [ HOST [ HOST ... ] ]

        Starts an application on a list of hosts.
        '''
        self.supervise(['start'] + args)

    def status(self):
        '''sup status APP [ HOST [ HOST ... ] ]

        Reports the status of an application on a list of hosts.
        '''
        self.supervise(['start'] + args)

    def stderr(self):
        '''sup stderr APP [ HOST [ HOST ... ] ]

        Reports the output an application has sent to stderr.
        '''
        self.supervise(['start'] + args)

    def stdout(self):
        '''sup stdout APP [ HOST [ HOST ... ] ]

        Reports the output an application has sent to stdout.
        '''
        self.supervise(['start'] + args)

    def stop(self):
        '''[sup] stop APP [ HOST [ HOST ... ] ]

        Stops an application on a list of hosts.
        '''
        self.supervise(['stop'] + args)

    command_list = (add, restart, start, status, stderr, stdout, stop)
    command_map = {
        'restart': restart,
        'start': start,
        'stop': stop,
        'sup': supervise,
        'supervise': supervise,
    }

if __name__ == '__main__':
    SupervisorHat(())

