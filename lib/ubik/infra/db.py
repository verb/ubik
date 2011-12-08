
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
        >>> db.host('balboa.sjc1')
        'InfraHost: balboa.sjc1.pontiflex.net'
        >>> db.host('foobar')
        Traceback (most recent call last):
            ...
        InfraDBException: Could not locate host 'foobar'

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
        >>> db.hosts(('balboa.sjc1','bertha.dfw1'))
        ['InfraHost: balboa.sjc1.pontiflex.net', 'InfraHost: bertha.dfw1.pontiflex.net']
        >>> db.hosts(('balboa.sjc1','ads.dfw1'))
        ['InfraHost: balboa.sjc1.pontiflex.net', 'InfraHost: bertha.dfw1.pontiflex.net']
        >>> db.hosts(('balboa.sjc1','foobar'))
        Traceback (most recent call last):
            ...
        InfraDBException: Could not locate host 'foobar'
        >>> db.hosts(('balboa.sjc1','broken'))
        Traceback (most recent call last):
            ...
        InfraDBException: Could not locate host 'broken'
        >>> db.hosts(('balboa.sjc1','ads')) #doctest: +NORMALIZE_WHITESPACE
        ['InfraHost: balboa.sjc1.pontiflex.net', 
         'InfraHost: bertha.dfw1.pontiflex.net',
         'InfraHost: freehold.ewr2.pontiflex.net',
         'InfraHost: sprite.atl1.pontiflex.net']

        """
        hosts = []
        log.debug("attempting to expand hostnames for: " + ' '.join(qnames))
        for qname in qnames:
            try:
                hosts.append(self.host(qname))
            except InfraDBException:
                # self.host() couldn't find a host named 'qname'
                # qname could be a role, though, so try that
                role_hosts = self.hosts(self.driver.lookup_role(qname))
                if len(role_hosts) > 0:
                    hosts.extend(role_hosts)
                else:
                    raise

        # Dedupe hosts, but preserve order
        seen = set()
        return [x for x in hosts if str(x) not in seen and not seen.add(str(x))]

    def role(self, qname):
        """Looks up a single role based on qname and returns an InfraRole

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> db.role('ads')
        'InfraRole: ads'
        >>> db.role('ads.sjc1')
        'InfraRole: ads.sjc1'
        >>> db.role('foobar')
        Traceback (most recent call last):
            ...
        InfraDBException: Could not locate role 'foobar'

        """
        log.debug("db.role looking up role: " + qname)
        role_names = self.driver.lookup_role(qname)
        if len(role_names) > 0:
            role = InfraRole(qname, self.driver)
        else:
            raise InfraDBException("Could not locate role '%s'" % qname)

        return role

    def roles(self, qnames):
        """Example multiple roles, Return a list of InfraRoles

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> db.roles(('ads',))
        ['InfraRole: ads']
        >>> db.roles(('ads.sjc1','ads.dfw1'))
        ['InfraRole: ads.sjc1', 'InfraRole: ads.dfw1']
        >>> db.roles(('ads.sjc1','broken'))
        Traceback (most recent call last):
            ...
        InfraDBException: Could not locate role 'broken'

        """
        roles = []
        for qname in qnames:
            roles.append(self.role(qname))
        return roles

    def expandhosts(self, records):
        """Expand a list of objects to their constituent hosts, and dedupe

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> db.expandhosts(('ads',))
        [u'bertha.dfw1', u'balboa.sjc1', u'freehold.ewr2', u'sprite.atl1']
        >>>

        """
        hosts = []
        log.debug("attempting to expand hostnames for: " + ' '.join(records))
        for record in records:
            if self.driver.lookup_host(record):
                # If this is a host, use it verbatim
                hosts.append(record)
            else:
                # try to expand role to host
                hosts.extend(self.driver.lookup_role(record))

        # Dedupe hosts, but preserve order
        # Caveat: dedupe is currently naiive because TXT records are expanded to
        # FQDN while A records remain unqualified
        seen = set()
        return [x for x in hosts if x not in seen and not seen.add(x)]

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
    def __init__(self, name, driver):
        self.name = name
        self.driver = driver

    def __str__(self):
        return str(self.name)

    def __unicode__(self):
        return unicode(self.name)

class InfraHost(InfraObject):
    def __repr__(self):
        return "'InfraHost: %s'" % self.name

class InfraRole(InfraObject):
    def __repr__(self):
        return "'InfraRole: %s'" % self.name

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)
