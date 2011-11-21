"""InfraDB JSON-backed Driver"""

import json
import logging

log = logging.getLogger('ubik.infra.infrajson')

class InfraDBDriverJSON(object):
    """InfraDB JSON Driver class

    This provides access to an InfraDB created entirely from a JSON file.  This
    mostly only useful for debugging and unit tests.

    """
    def __init__(self, confstr='infradb.json'):
        """Initialize a new JSON InfraDB Driver

        >>> idb=InfraDBDriverJSON()
        >>> idb.confstr
        'infradb.json'
        >>> len(idb.db['roles'])
        0
        >>> idb=InfraDBDriverJSON('tests/infradb.json')
        >>> idb.confstr
        'tests/infradb.json'
        >>> len(idb.db['roles'])
        6
        >>>

        """
        log.debug("Initialize InfraDB JSON driver from %s" % confstr)
        self.confstr = confstr
        try:
            with open(confstr, 'r') as idb_fp:
                self.db = json.load(idb_fp)
        except IOError:
            self.db = {'hosts': {}, 'roles': {}}

    def lookup_host(self, query):
        """Look up a host in the json infra db

        >>> idb=InfraDBDriverJSON('tests/infradb.json')
        >>> idb.lookup_host('balboa.sjc1')
        u'balboa.sjc1.pontiflex.net'
        >>> idb.lookup_host('bogus')
        >>>

        """
        log.debug("Looking up host '%s'" % query)
        return self.db['hosts'].get(query, None)

    def lookup_role(self, query):
        """Resolve a role to a list of hosts

        >>> idb=InfraDBDriverJSON('tests/infradb.json')
        >>> idb.lookup_role('ads')
        [u'bertha.dfw1', u'balboa.sjc1', u'freehold.ewr2', u'sprite.atl1']
        >>> idb.lookup_role('bogus')
        []
        >>> idb.lookup_role('broken')
        []
        >>>

        """
        log.debug("Looking up role '%s'" % query)
        hosts = []
        for res in self.db['roles'].get(query, []):
            if self.lookup_host(res):
                hosts.append(res)
            else:
                hosts.extend(self.lookup_role(res))
        return hosts

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)
