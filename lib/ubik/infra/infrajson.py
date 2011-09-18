
import json
import logging

log = logging.getLogger('ubik.infra.infrajson')

class InfraDBDriverJSON(object):
    def __init__(self, confstr='infradb.json'):
        """Initial a new JSON InfraDB Driver

        >>> idb=InfraDBDriverJSON()
        >>> idb.confstr
        'infradb.json'
        >>> len(idb.db['roles'])
        0
        >>> idb=InfraDBDriverJSON('tests/infradb.json')
        >>> idb.confstr
        'tests/infradb.json'
        >>> len(idb.db['roles'])
        5
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
        >>> idb.lookup_host('balboa')
        u'balboa.sjc1.pontiflex.net'
        >>> idb.lookup_host('bogus')
        >>> 

        """
        log.debug("Looking up host '%s'" % query)
        return self.db['hosts'].get(query, None)

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)
