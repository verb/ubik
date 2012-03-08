
import logging

log = logging.getLogger('infra.db')

class InfraDBException(Exception):
    pass

class InfraDB(object):
    def __init__(self, type='json', confstr=None):
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
    def __repr__(self):
        return "'InfraHost: %s'" % self._name

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

        Currently, this is just a list of strings

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> sorted(db.service('webserver').hosts())
        [u'alpha.dc1', u'bravo.dc1', u'charlie.dc2', u'delta.dc3']
        >>> sorted(db.service('webserver.dc1').hosts())
        [u'alpha.dc1', u'bravo.dc1']
        >>>

        """
        return self._driver.resolve_service(self._name)

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)
