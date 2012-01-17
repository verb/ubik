
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
        >>> db.hosts(('alpha.dc1','webserver')) #doctest: +NORMALIZE_WHITESPACE
        ['InfraHost: alpha.dc1', 
         'InfraHost: bravo.dc1',
         'InfraHost: charlie.dc2',
         'InfraHost: delta.dc3']

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

#    def expandhosts(self, records):
#        """Expand a list of objects to their constituent hosts, and dedupe
#
#        >>> db=InfraDB('json', 'tests/infradb.json')
#        >>> db.expandhosts(('webserver',))
#        [u'alpha.dc1', u'bravo.dc1', u'charlie.dc2', u'delta.dc3']
#        >>>
#
#        """
#        hosts = []
#        log.debug("attempting to expand hostnames for: " + ' '.join(records))
#        for record in records:
#            if self.driver.lookup_host(record):
#                # If this is a host, use it verbatim
#                hosts.append(record)
#            else:
#                # try to expand role to host
#                hosts.extend(self.driver.resolve_service(record))
#
#        # Dedupe hosts, but preserve order
#        # Caveat: dedupe is currently naiive because TXT records are expanded to
#        # FQDN while A records remain unqualified
#        seen = set()
#        return [x for x in hosts if x not in seen and not seen.add(x)]

    def listroles(self, domains=None):
        if domains == None or len(domains) == 0:
            domains = ('.',)
        roles = {}
        for domain in domains:
            query = '.'.join(('services', domain)).strip('.')
            log.info("attempting to list roles for: " + query )
            #roles[domain] = _lookup_txt_role(query, False)
        return roles

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
    def __repr__(self):
        return "'InfraHost: %s'" % self._name

    def services(self):
        """Figure out what services run on this host

        Currently, this returns list of strings

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> h=db.host('alpha.dc1')
        >>> h
        'InfraHost: alpha.dc1'
        >>> h.services()
        [u'webserver', u'mailserver']
        >>>

        """
        return self._driver.lookup_host(self._name)['services']

class InfraService(InfraObject):
    def __repr__(self):
        return "'InfraService: %s'" % self._name

    def hosts(self):
        """Resolve this service to its constituent hosts

        Currently, this is just a list of strings

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> srv=db.service('webserver')
        >>> srv
        'InfraService: webserver'
        >>> srv.hosts()
        [u'alpha.dc1', u'bravo.dc1', u'charlie.dc2', u'delta.dc3']
        >>>

        """
        return self._driver.resolve_service(self._name)

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)
