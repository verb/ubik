
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
        if string == 'hosts' or string == 'services':
            return True
        return False

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
                    print >>self.output, unicode(host)

    def services(self, args):
        '''services [ DOMAIN ... ]

        Display the list of services.  If specified, the query is restricted to
        one or more partially qualified sub domains.
        '''
        service_list = self.idb.list_services(args)
        for service in service_list:
            print >>self.output, service

    command_list = ( hosts, services )
    command_map = {
        'hosts':    hosts,
        'services': services,
    }

if __name__ == '__main__':
    InfraDBHat(())

