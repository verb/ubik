
import dns.resolver
import logging
import os

log = logging.getLogger('infra.dns')

if 'RUG_RESOLV_CONF' in os.environ:
    r = dns.resolver.Resolver(os.environ['RUG_RESOLV_CONF'])
else:
    r = dns.resolver.get_default_resolver()

def _lookup_a(query):
    records = []
    log.debug("Looking up A record for '%s'" % query)
    try:
        for record in r.query(query, 'A').rrset:
            records.append(record)
    except dns.resolver.NXDOMAIN:
        pass
    except dns.resolver.NoAnswer:
        pass
    return records

# takes a single name "query", performs a TXT lookup, and returns the result as
# a list with any potential role formatting removed.
# If to_hosts is true, this function will only valid, fully-qualified hostnames.  
# This will also cause any sub-roles to be expanded
def _lookup_txt_role(query, to_hosts=True):
    records = []
    log.debug("Looking up TXT record for '%s'" % query)
    try:
        answer = r.query(query, 'TXT')
        for record in answer.rrset:
            for txt in str(record).split():
                # Remove spurious quotes and tags
                host = txt.translate(None,"'\"").split(':')[-1]
                if to_hosts:
                    # Return FQDN
                    fqdn = '.'.join((host,str(answer.qname.parent())))
                    if _lookup_a(fqdn):
                        records.append(fqdn)
                    else:
                        records.extend(_lookup_txt_role(fqdn))
                else:
                    records.append(host)
    except dns.resolver.NXDOMAIN:
        pass
    except dns.resolver.NoAnswer:
        pass
    return records

def expandhosts(records):
    hosts = []
    log.info("attempting to expand hostnames for: " + ' '.join(records))
    for record in records:
        if len(_lookup_a(record)) > 0:
            # If this is a host, use it verbatim
            hosts.append(record)
        else:
            # try to expand as txt record
            hosts.extend(_lookup_txt_role(record))

    # Dedupe hosts, but preserve order
    # Caveat: dedupe is currently naiive because TXT records are expanded to
    # FQDN while A records remain unqualified
    seen = set()
    return [x for x in hosts if x not in seen and not seen.add(x)]

def listroles(domains=None):
    if domains == None or len(domains) == 0:
        domains = ('.',)
    roles = {}
    for domain in domains:
        query = '.'.join(('services',domain)).strip('.')
        log.info("attempting to list roles for: " + query )
        roles[domain] = _lookup_txt_role(query, False)
    return roles

class InfraDBDriverDNS(object):
    pass

