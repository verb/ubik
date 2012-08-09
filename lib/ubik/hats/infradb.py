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

import ubik.infra.db
import ubik.defaults

from ubik.hats import HatException
from ubik.hats.base import BaseHat

log = logging.getLogger('ubik.hats.infradb')

class InfraDBHat(BaseHat):
    "Infra DB Lookup Hat"

    name = 'infradb'
    desc = "Infra DB lookups"

    @staticmethod
    def areyou(string):
        "Confirm or deny whether I am described by string"
        return string in ('hosts', 'services')

    def __init__(self, argv, config=None, options=None):
        super(InfraDBHat, self).__init__(argv, config, options)
        self.args = argv[:]

        try:
            driver = config.get('infradb', 'driver')
        except ubik.config.NoOptionError:
            driver = 'dns'

        confstr = None
        try:
            if driver == 'dns':
                confstr = config.get('infradb', 'domain')
            elif driver == 'json':
                confstr = config.get('infradb', 'jsonfile')
        except ubik.config.NoOptionError:
            pass

        self.idb = ubik.infra.db.InfraDB(driver, confstr)

    def run(self):
        try:
            command = self.argv[0]
            if command in self.command_map:
                self.command_map[command](self, self.argv[1:])
            elif command == 'help':
                self.help(self.output)
            else:
                raise HatException("Unknown command: %s" % command)
        except ubik.infra.db.InfraDBException as e:
            raise HatException(str(e))

    def hosts(self, args):
        """hosts SERVICE [ SERVICE ... ]

        Print the hosts defined for SERVICE.
        """
        if len(args) == 0:
            self.help(self.output)
        else:
            for service in self.idb.services(args):
                for host in sorted(service.hosts()):
                    if host.label:
                        print >>self.output, "(%s)\t" % host.label,
                    print >>self.output, unicode(host)

    def services(self, args):
        '''services [ DOMAIN ... ]

        Display the list of services.  If specified, the query is restricted to
        one or more partially qualified sub domains.
        '''
        service_list = self.idb.list_services(args)
        for service in sorted(service_list):
            print >>self.output, service

    command_list = ( hosts, services )
    command_map = {
        'hosts':    hosts,
        'services': services,
    }

if __name__ == '__main__':
    InfraDBHat(())

