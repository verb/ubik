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

log = logging.getLogger('infra.db')

OS_PKGTYPE_MAP = {
    'DEFAULT':  'deb',
    'centos':   'rpm',
    'debian':   'deb',
    'redhat':   'rpm',
    'ubuntu':   'deb',
}

class InfraDBException(Exception):
    pass

class InfraDB(object):
    def __init__(self, type=None, confstr=None):
        """Create an InfraDB object

        An InfraDB uses some sort of database-ish driver to map one real
        infrastructure object to another for this infrastructure.  For example,
        the 'webserver' role may map to hostA, hostB and hostC

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>>

        """
        log.debug("Initializing driver type %s" % type)
        if type == 'dns' or type == None:
            from ubik.infra.infradns import InfraDBDriverDNS
            self.driver = InfraDBDriverDNS(confstr)
        elif type == 'json':
            from ubik.infra.infrajson import InfraDBDriverJSON
            self.driver = InfraDBDriverJSON(confstr)
        else:
            raise InfraDBException('No Such Driver: ' + type)

    def host(self, qname):
        """Looks up a single host based on qname and returns an InfraHost

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> db.host('alpha.dc1')
        'InfraHost: alpha.dc1'
        >>> db.host('bogus')
        Traceback (most recent call last):
            ...
        InfraDBException: Could not locate host 'bogus'

        """
        log.debug("db.host looking up host: " + qname)
        host = self.driver.lookup_host(qname)
        if host:
            return InfraHost(host, self.driver)
        else:
            raise InfraDBException("Could not locate host '%s'" % qname)

    def hosts(self, qnames):
        """Look up several hosts (or roles) and return a list of InfraHosts

        This function tries as hard as it can to convert anything you throw at
        it into InfraHosts.  Deduplication is attempted on the results.

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> db.hosts(('alpha.dc1','charlie.dc2'))
        ['InfraHost: alpha.dc1', 'InfraHost: charlie.dc2']
        >>> db.hosts(('alpha.dc1','webserver.dc2'))
        ['InfraHost: alpha.dc1', 'InfraHost: charlie.dc2']
        >>> db.hosts(('alpha.dc1','bogus'))
        Traceback (most recent call last):
            ...
        InfraDBException: Could not locate host 'bogus'
        >>> db.hosts(('alpha.dc1','broken'))
        Traceback (most recent call last):
            ...
        InfraDBException: Could not locate host 'broken'
        >>> sorted(db.hosts(('alpha.dc1','mailserver')))
        ['InfraHost: alpha.dc1', 'InfraHost: charlie.dc2']

        """
        hosts = []
        log.debug("attempting to expand hostnames for: " + ' '.join(qnames))
        for qname in qnames:
            try:
                hosts.append(self.host(qname))
            except InfraDBException:
                # self.host() couldn't find a host named 'qname'
                # qname could be a service, though, so try that
                service_hosts = self.hosts(self.driver.resolve_service(qname))
                if len(service_hosts) > 0:
                    hosts.extend(service_hosts)
                else:
                    raise

        # Dedupe hosts, but preserve order
        seen = set()
        return [x for x in hosts if str(x) not in seen and not seen.add(str(x))]

    def service(self, qname):
        """Looks up a single service based on qname and returns an InfraService

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> db.service('webserver')
        'InfraService: webserver'
        >>> db.service('webserver.dc1')
        'InfraService: webserver.dc1'
        >>> db.service('bogus')
        Traceback (most recent call last):
            ...
        InfraDBException: Could not locate service 'bogus'
        >>> db.service('broken')
        Traceback (most recent call last):
            ...
        InfraDBException: Could not locate service 'broken'

        """
        log.debug("db.service looking up service: " + qname)
        service_dict = self.driver.lookup_service(qname)
        if service_dict:
            service = InfraService(service_dict, self.driver)
        else:
            raise InfraDBException("Could not locate service '%s'" % qname)

        return service

    def services(self, qnames):
        """Example multiple roles, Return a list of InfraServices

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> db.services(('webserver',))
        ['InfraService: webserver']
        >>> db.services(('webserver.dc2','webserver.dc3'))
        ['InfraService: webserver.dc2', 'InfraService: webserver.dc3']
        >>> db.services(('webserver.dc1','broken'))
        Traceback (most recent call last):
            ...
        InfraDBException: Could not locate service 'broken'

        """
        services = []
        for qname in qnames:
            services.append(self.service(qname))
        return services

    def list_services(self, domains=None):
        """Compile a list of available services

        if `domains` is specified, it is a list of sub-domains to query.
        Otherwise only top level services are returned.

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> sorted(db.list_services())
        [u'mailserver', u'webserver']
        >>> sorted(db.list_services(('dc1','dc3')))
        [u'mailserver.dc1', u'webserver.dc1', u'webserver.dc3']
        >>>

        """
        if domains == None or len(domains) == 0:
            domains = (None,)
        services = []
        for domain in domains:
            services.extend(self.driver.list_services(domain))
        return services

class InfraObject(object):
    def __init__(self, attr, driver):
        self._name = attr['name']
        self._driver = driver
        self._hosts = attr.get('hosts', [])
        self._services = attr.get('services', [])

    def __str__(self):
        return str(self._name)

    def __unicode__(self):
        return unicode(self._name)

class InfraHost(InfraObject):
    """This represents a single host in this infrastructure

    >>> db=InfraDB('json', 'tests/infradb.json')
    >>> db.host('alpha.dc1')
    'InfraHost: alpha.dc1'
    >>>

    """
    def __init__(self, attr, driver):
        """Initialize an InfraHost

        In addition to parameters handled by InfraObject, InfraHosts also have
        'hardware' and 'os' tags.

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> ih=db.host('alpha.dc1')
        >>> ih._hardware
        u'hardware_tag'
        >>> ih._os
        u'os_tag'
        >>>

        """
        super(InfraHost, self).__init__(attr, driver)
        self._hardware = attr.get('hardware', None)
        self._os = attr.get('os', None)
        self.label = attr.get('label', None)

    def __repr__(self):
        return "'InfraHost: %s'" % self._name

    def pkgtype(self):
        """Return the type of system packages used by this host

        This is determined by looking up the os tag in a dict, but should
        probably be moved to a configuration table.

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> db.host('alpha.dc1').pkgtype()
        'deb'
        >>>

        """
        if self._os:
            for os_str in OS_PKGTYPE_MAP:
                if os_str in self._os:
                    return OS_PKGTYPE_MAP[os_str]
        return OS_PKGTYPE_MAP['DEFAULT']

    def services(self):
        """Figure out what services run on this host

        Currently, this returns list of strings

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> db.host('alpha.dc1').services()
        [u'webserver', u'mailserver']
        >>>

        """
        return self._driver.lookup_host(self._name)['services']

class InfraService(InfraObject):
    """This represents a service running on a set of hosts

    >>> db=InfraDB('json', 'tests/infradb.json')
    >>> db.service('webserver')
    'InfraService: webserver'
    >>>

    """
    def __repr__(self):
        return "'InfraService: %s'" % self._name

    def hosts(self):
        """Resolve this service to its constituent hosts

        This returns a list of InfraHosts.

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> sorted(db.service('webserver').hosts(), key=str)
        ['InfraHost: alpha.dc1', 'InfraHost: bravo.dc1', 'InfraHost: ...]
        >>> sorted(db.service('webserver.dc1').hosts(), key=str)
        ['InfraHost: alpha.dc1', 'InfraHost: bravo.dc1']
        >>>

        """
        hostlist = []
        for hoststr in self._driver.resolve_service(self._name):
            hostattr = self._driver.lookup_host(hoststr)
            if hostattr:
                hostlist.append(InfraHost(hostattr, self._driver))
        return hostlist

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)
