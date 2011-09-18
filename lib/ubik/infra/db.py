
import logging
import os

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

    def expandhosts(self, records):
        """Expand a list of objects to their constituent hosts, and dedupe

        >>> db=InfraDB('json', 'tests/infradb.json')
        >>> db.expandhosts(('ads',))

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
            query = '.'.join(('services',domain)).strip('.')
            log.info("attempting to list roles for: " + query )
            roles[domain] = _lookup_txt_role(query, False)
        return roles

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)
