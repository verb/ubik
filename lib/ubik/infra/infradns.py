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
#
"""DNS-backed InfraDB Driver"""

import dns.exception
import dns.name
import dns.resolver
import logging
import os

from dns.name import Name

log = logging.getLogger('infra.dns')

SVC_INDEX = '_service._services'

def _hsts_for(record):
    "Utility function to return DNS lookup listing hosts for record"
    record_name = dns.name.from_text(record, dns.name.empty)
    return Name(('_host',)).concatenate(record_name)

def _svcs_for(record):
    "Utility function to return DNS lookup listing services for record"
    record_name = dns.name.from_text(record, dns.name.empty)
    return Name(('_service',)).concatenate(record_name)

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
        >>> idb=InfraDBDriverDNS('example.com.')
        >>> idb.root
        <DNS name example.com.>
        >>> idb=InfraDBDriverDNS('dc1.example.com.')
        >>> idb.root
        <DNS name dc1.example.com.>
        >>>

        """
        log.debug("Initialize InfraDB DNS driver")
        if 'RUG_RESOLV_CONF' in os.environ:
            self.resolver = dns.resolver.Resolver(os.environ['RUG_RESOLV_CONF'])
            if 'RUG_RESOLV_PORT' in os.environ:
                self.resolver.port = int(os.environ['RUG_RESOLV_PORT'])
        else:
            self.resolver = dns.resolver.get_default_resolver()

        if domain:
            self.root = dns.name.from_text(domain)
        else:
            # Attempt to guess what my root is
            try:
                self.root = self.resolver.query('', 'NS').qname
            except dns.exception.DNSException:
                self.root = dns.name.Name([])
        log.debug("InfraDB DNS driver root " + self.root.to_text())

    def _query(self, query, qtype='A'):
        """Query resolver and return an answer object or None"""
        try:
            answer = self.resolver.query(query, qtype, tcp=False)
        except dns.resolver.NXDOMAIN:
            return None
        except dns.resolver.NoAnswer:
            answer = None

        # dnspython doesn't fallback to TCP, so answer could be too long to
        # fit in a UDP packet and we wouldn't know.  Additionally, the server
        # may return NoAnswer if the response is too long
        if not answer or len(answer) >= 13:
            try:
                answer = self.resolver.query(query, qtype, tcp=True)
            except dns.resolver.NoAnswer:
                pass
        return answer

    def _query_txt(self, query):
        "Query resolver for TXT record and return a list of relativized strings"
        if not isinstance(query, Name):
            query = dns.name.from_text(query, dns.name.empty)
        log.debug('txt query is ' + query.to_text())
        return self._txt_rel_str(self._query(query, 'TXT'))

    def _txt_rel_str(self, answer):
        """Extract a list of strings from a TXT answer record

        This function appends tags to the list of string records where
        possible in an attempt to make the relative to the current DNS domain.

        >>> idb=InfraDBDriverDNS('example.com.')
        >>> a=idb._query(SVC_INDEX + '.example.com.', 'TXT')
        >>> sorted(idb._txt_rel_str(a))
        [u'mailserver', u'webserver']
        >>> a=idb._query(SVC_INDEX + '.dc1.example.com.', 'TXT')
        >>> sorted(idb._txt_rel_str(a))
        [u'mailserver.dc1', u'webserver.dc1']

        >>> idb=InfraDBDriverDNS('dc2.example.com.')
        >>> a=idb._query(SVC_INDEX + '.dc1.example.com.', 'TXT')
        >>> sorted(idb._txt_rel_str(a))
        [u'mailserver.dc1.example.com.', u'webserver.dc1.example.com.']

        >>> idb._txt_rel_str(None)
        []
        """
        txts = []
        if answer:
            assert isinstance(answer, dns.resolver.Answer)
            for record in answer:
                # Each TXT record can have a list of strings delimitted by
                # quotes.  e.g. '"one two" "three four"'
                # This should become ('one two', 'three four')
                txts.extend([unicode(s) for s in record.strings])

            # There are two levels of parent() below because the TXT tags
            # are always 2 steps removed from their "domain".  e.g.
            #
            # _service._services.example.com.  IN TXT "webserver"
            # _service.webserver.example.com.  IN TXT "webserver.dc1"
            # _host.webserver.example.com.     IN TXT "delta.dc3"
            # _host.webserver.dc3.example.com. IN TXT "delta"
            #
            try:
                domain = answer.canonical_name.parent().parent()
            except dns.name.NoParent:
                pass
            else:
                # The texts returned here will be relative to domain,
                # but we want to return them relative to self.root
                log.debug('Relativize root=%s domain=%s' % (self.root, domain))
                txts = [dns.name.from_text(t, domain)\
                            .relativize(self.root)\
                            .to_unicode(omit_final_dot=True)
                        for t in txts]

        return txts

    def list_services(self, query=None):
        """Return a list of strings representing all services

        'query' is the optional subdomain

        >>> idb=InfraDBDriverDNS('example.com.')
        >>> sorted(idb.list_services())
        [u'mailserver', u'webserver']
        >>> sorted(idb.list_services(''))
        [u'mailserver', u'webserver']
        >>> sorted(idb.list_services('dc1'))
        [u'mailserver.dc1', u'webserver.dc1']
        >>> sorted(idb.list_services('bogus'))
        []

        >>> idb=InfraDBDriverDNS('dc1.example.com.')
        >>> sorted(idb.list_services())
        [u'mailserver', u'webserver']
        >>> sorted(idb.list_services('dc3'))
        []
        >>> sorted(idb.list_services('dc3.example.com.'))
        [u'webserver.dc3.example.com.']
        >>>

        """
        if query:
            record_str = '.'.join((SVC_INDEX, query))
        else:
            record_str = SVC_INDEX
        return self._query_txt(record_str)

    def lookup_host(self, query):
        """Look up a host based on partial name, return FQDN

        In the DNS TXT record references, addresses can be prefixed
        with a descriptive label.  i.e. "cold-standby:alpha.dc1"

        >>> idb=InfraDBDriverDNS('example.com.')
        >>> h=idb.lookup_host('alpha.dc1')
        >>> h['name']
        u'alpha.dc1'
        >>> (h['hardware'], h['os'])
        (u'hardware_tag', u'os_tag')
        >>> sorted(h['services'])
        [u'mailserver.dc1', u'webserver.dc1']
        >>> idb.lookup_host('bogus')
        >>>

        """
        log.debug("Gathering info for host '%s'", query)
        host = dict()

        # Remove label from DNS query
        if ':' in query:
            host['label'], query = query.rsplit(':', 2)

        answer = self._query(query, 'A')
        if answer and len(answer) > 0:
            host['name'] = unicode(query)
            host['fqdn'] = unicode(answer.canonical_name).rstrip('.')

        if host:
            answer = self._query(query, 'HINFO')
            if answer and len(answer) > 0:
                host['hardware'] = unicode(answer[0].cpu)
                host['os'] = unicode(answer[0].os)
            svcs = self._txt_rel_str(self._query(_svcs_for(query), 'TXT'))
            if svcs:
                host['services'] = svcs
            return host

        return None

    def lookup_service(self, query):
        """Look up a service and return its attributes as a dict

        >>> idb=InfraDBDriverDNS('example.com.')
        >>> from pprint import pprint

        >>> s=idb.lookup_service('webserver')
        >>> sorted(s['hosts'])
        [u'delta.dc3']
        >>> sorted(s['services'])
        [u'webserver.dc1', u'webserver.dc2']

        >>> s=idb.lookup_service('webserver.dc1')
        >>> sorted(s['hosts'])
        [u'alpha.dc1', u'bravo.dc1']

        >>> idb.lookup_service('bogus')
        >>>
        """
        log.debug("Gathering info for service '%s'", query)
        svc = dict()
        svc_ans = self._query(_svcs_for(query), 'TXT')
        hst_ans = self._query(_hsts_for(query), 'TXT')
        if svc_ans or hst_ans:
            svc['name'] = unicode(query)

        # If service exists, gather its attributes
        if svc:
            if hst_ans:
                svc["hosts"] = self._txt_rel_str(hst_ans)
            # When resolving services to hosts, hosts always override services,
            # but services are included (and later resolved) as long as their
            # parent domain matches.  Without this check, the svc_ans could be
            # a response from farther down the DNS search path and unrelated to
            # this entry entirely.
            if svc_ans and (not hst_ans or
                    hst_ans.qname.parent() == svc_ans.qname.parent()):
                svc["services"] = self._txt_rel_str(svc_ans)
            return svc

        return None

    def resolve_service(self, query):
        """Resolve a service to a list of hosts

        >>> idb=InfraDBDriverDNS('example.com.')
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
