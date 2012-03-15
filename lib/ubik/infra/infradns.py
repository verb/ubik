"""DNS-backed InfraDB Driver"""

import dns.resolver
import logging
import os

log = logging.getLogger('infra.dns')

class InfraDBDriverDNS(object):
    """InfraDB DNS Driver class

    This provides access to an InfraDB created from DNS.

    >>> import os
    >>> os.environ['RUG_RESOLV_CONF'] = 'tests/named/resolv.conf'
    >>> os.environ['RUG_RESOLV_PORT'] = '5533'
    >>>

    """
    def __init__(self, domain=None):
        """Initialize a new DNS InfraDB Driver

        >>> idb=InfraDBDriverDNS()
        >>>

        """
        log.debug("Initialize InfraDB DNS driver")
        if 'RUG_RESOLV_CONF' in os.environ:
            self.resolver = dns.resolver.Resolver(os.environ['RUG_RESOLV_CONF'])
            if 'RUG_RESOLV_PORT' in os.environ:
                self.resolver.port = int(os.environ['RUG_RESOLV_PORT'])
        else:
            self.resolver = dns.resolver.get_default_resolver()

    def _query(self, query, qtype='A'):
        """Query resolver and return an answer object or None"""
        try:
            answer = self.resolver.query(query, qtype)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass
        else:
            return answer
        return None

    def _query_txt(self, query):
        """Query resolver for TXT record and return a list of strings"""
        answer = self._query(query, 'TXT')
        txts = []
        if answer:
            for record in answer:
                # Each TXT record can have a list of strings delimitted by
                # quotes.  e.g. '"one two" "three four"'
                # This should be come ('one two', 'three four')
                txts.extend([unicode(s) for s in record.strings])
        return txts

    def list_services(self, query=None):
        """Return a list of strings representing all services

        'query' is the optional subdomain

        >>> idb=InfraDBDriverDNS()
        >>> sorted(idb.list_services())
        [u'mailserver', u'webserver']
        >>> sorted(idb.list_services(''))
        [u'mailserver', u'webserver']
        >>> sorted(idb.list_services('dc1'))
        [u'mailserver.dc1', u'webserver.dc1']
        >>> sorted(idb.list_services('bogus'))
        []
        >>>

        """
        rr = '_services'
        if query:
            suffix = '.' + query
            return [s+suffix for s in self._query_txt(rr+suffix)]
        else:
            return self._query_txt(rr)

    def lookup_host(self, query):
        """Look up a host based on partial name, return FQDN

        >>> idb=InfraDBDriverDNS()
        >>> h=idb.lookup_host('alpha.dc1')
        >>> h['name']
        u'alpha.dc1'
        >>> (h['hardware'], h['os'])
        (u'hardware_tag', u'os_tag')
        >>> sorted(h['services'])
        [u'mailserver', u'webserver']
        >>> idb.lookup_host('bogus')
        >>>

        """
        log.debug("Gathering info for host '%s'", query)
        host = dict()
        answer = self._query(query, 'A')
        if answer and len(answer) > 0:
            host['name'] = unicode(query)
            host['fqdn'] = unicode(answer.canonical_name).rstrip('.')

        if host:
            answer = self._query(query, 'HINFO')
            if answer and len(answer) > 0:
                host['hardware'] = unicode(answer[0].cpu)
                host['os'] = unicode(answer[0].os)
            svcs = self._query_txt("_services."+query)
            if svcs:
                host['services'] = svcs
            return host

        return None

    def lookup_service(self, query):
        """Look up a service and return its attributes as a dict

        >>> idb=InfraDBDriverDNS()
        >>> svc=idb.lookup_service('webserver')
        >>> svc['name']
        u'webserver'
        >>> sorted(svc['services'])
        [u'webserver.dc1', u'webserver.dc2']
        >>> svc['hosts']
        [u'delta.dc3']
        >>> len(idb.lookup_service('webserver.dc1')['hosts'])
        2
        >>> idb.lookup_service('bogus')
        >>>

        """
        log.debug("Gathering info for service '%s'", query)
        svc = dict()
        svc_list = self._query_txt('_service.' + query)
        hst_list = self._query_txt('_host.' + query)
        if svc_list or hst_list:
            svc['name'] = unicode(query)

        # If service exists, gather its attributes
        if svc:
            if svc_list:
                svc["services"] = svc_list
            if hst_list:
                svc["hosts"] = hst_list
            return svc

        return None

    def resolve_service(self, query):
        """Resolve a service to a list of hosts

        >>> idb=InfraDBDriverDNS()
        >>> sorted(idb.resolve_service('webserver'))
        [u'alpha.dc1', u'bravo.dc1', u'charlie.dc2', u'delta.dc3']
        >>> sorted(idb.resolve_service('mailserver'))
        [u'alpha.dc1', u'charlie.dc2']
        >>> sorted(idb.resolve_service('webserver.dc1'))
        [u'alpha.dc1', u'bravo.dc1']
        >>> idb.resolve_service('bogus')
        []
        >>> idb.resolve_service('broken')
        []
        >>>

        """
        log.debug("Expanding service '%s'", query)
        hosts = []
        svc = self.lookup_service(query)
        if svc:
            if 'hosts' in svc:
                hosts.extend(svc['hosts'])
            if 'services' in svc and svc['services']:
                for service in svc['services']:
                    hosts.extend(self.resolve_service(service))
        return hosts

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)
