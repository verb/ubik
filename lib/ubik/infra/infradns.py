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
    def __init__(self):
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

    def lookup_host(self, query):
        """Look up a host based on partial name, return FQDN

        >>> idb=InfraDBDriverDNS()
        >>> idb.lookup_host('alpha.dc1')
        u'alpha.dc1.example.com'
        >>> idb.lookup_host('bogus')
        >>>

        """
        log.debug("Looking up A record for '%s'", query)
        try:
            answer =  self.resolver.query(query, 'A')
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass
        else:
            if len(answer) > 0:
                return unicode(answer.canonical_name).rstrip('.')
        return None

    def lookup_role(self, query):
        """Resolve a role to a list of host FQDNs

        >>> idb=InfraDBDriverDNS()
        >>> idb.lookup_role('ads') #doctest: +NORMALIZE_WHITESPACE
        [u'sprite.atl1.pontiflex.net', u'bertha.dfw1.pontiflex.net',
         u'freehold.ewr2.pontiflex.net', u'balboa.sjc1.pontiflex.net']
        >>> idb.lookup_role('ads.atl1')
        [u'sprite.atl1.pontiflex.net']
        >>> idb.lookup_role('bogus')
        []
        >>> idb.lookup_role('broken')
        []
        >>>

        """
        hosts = []
        log.debug("Looking up TXT record for '%s'" % query)
        try:
            answer = self.resolver.query(query, 'TXT')
            for record in answer.rrset:
                for txt_sub in str(record).split():
                    # Remove tags and spurious quotes
                    # TODO: the following translate() is not unicode safe
                    txt_sub = txt_sub.translate(None, "'\"").split(':')[-1]
                    fqdn = '.'.join((txt_sub, str(answer.qname.parent())))
                    if self.lookup_host(fqdn):
                        hosts.append(unicode(fqdn.rstrip('.')))
                    else:
                        hosts.extend(self.lookup_role(fqdn))
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass
        return hosts

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)
