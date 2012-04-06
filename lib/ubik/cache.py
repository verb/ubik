"Utilities for caching files in directory"

import logging
import mimetypes
import os, os.path
import sqlite3
import shutil
import subprocess

log = logging.getLogger('ubik.cache')

INSPECT_CMD_TAB = {
    'deb': ('dpkg-deb', '--showformat',
            '${Package}\t${Architecture}\t${Version}', '--show'),
    'rpm': ('rpm', '-q', '--qf', '%{NAME}\t%{ARCH}\t%{VERSION}', '-p'),
}

class CacheException(Exception):
    pass

class UbikPackageCache(object):
    """Cache specifically for software packages, such as RPM & DEB

    >>> u=UbikPackageCache('tests/out/cache')
    >>> u.add('tests/testpkg_1.0_all.deb')
    >>> u.add('tests/testpkg_1.0_all.deb')
    >>> u.get(name='testpkg')
    'tests/out/cache/deb/testpkg_1.0_all.deb'
    >>> u.get(name='testpkg', version='1.0')
    'tests/out/cache/deb/testpkg_1.0_all.deb'
    >>> u.get(name='testpkg', version='1.0', type='deb')
    'tests/out/cache/deb/testpkg_1.0_all.deb'
    >>> u.get(name='testpkg', version='1.0', type='deb', arch='all')
    'tests/out/cache/deb/testpkg_1.0_all.deb'
    >>> u.get()
    Traceback (most recent call last):
       ...
    CacheException: Missing filters for get

    >>> from pprint import pprint
    >>> pprint(u.list()) #doctest: +ELLIPSIS
    [{'added': ...,
      'arch': u'all',
      'filename': u'testpkg_1.0_all.deb',
      'name': u'testpkg',
      'type': u'deb',
      'version': u'1.0'}]
    >>> pprint(u.list('testpkg_1.*')) #doctest: +ELLIPSIS
    [{'added': ...,
      'arch': u'all',
      'filename': u'testpkg_1.0_all.deb',
      'name': u'testpkg',
      'type': u'deb',
      'version': u'1.0'}]
    >>> pprint(u.list(name='testpkg', arch='all', version='1.0', type='deb'))
    ... #doctest: +ELLIPSIS
    [{'added': ...,
      'arch': u'all',
      'filename': u'testpkg_1.0_all.deb',
      'name': u'testpkg',
      'type': u'deb',
      'version': u'1.0'}]

    >>> u.remove('testpkg_1.0_all.deb')
    >>> u.list()
    []
    >>> u.prune()

    """
    def __init__(self, cache_dir):
        cache_dir = os.path.expanduser(cache_dir)
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        # TODO: detect previous version index and offer to reindex

        dbfile=os.path.join(cache_dir, 'index.db')
        self.conn = sqlite3.connect(dbfile)
        self.conn.row_factory = sqlite3.Row

        c = self.conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS packages ('
                    'filename TEXT PRIMARY KEY,'
                    'name TEXT NOT NULL,'
                    'version TEXT,'
                    'type TEXT,'
                    'arch TEXT,'
                    'added TEXT DEFAULT CURRENT_TIMESTAMP,'
                    'UNIQUE(name, version, type, arch)'
                  ');')

    @staticmethod
    def _inspect(filepath, pkg_type=None):
        """Tries to guess the type of package located at filepath

        >>> UbikPackageCache._inspect('tests/testpkg_1.0_all.deb')
        {'arch': 'all', 'version': '1.0', 'type': 'deb', 'name': 'testpkg'}

        """
        if not pkg_type:
            # Try to guess the package type
            mimetype = mimetypes.guess_type(filepath)[0]
            if mimetype == 'application/x-debian-package':
                pkg_type = 'deb'
            elif mimetype == 'application/x-rpm':
                pkg_type = 'rpm'
        pkg = {'type': pkg_type}

        if pkg_type in ('deb', 'rpm'):
            command = INSPECT_CMD_TAB[pkg_type] + (filepath,)
            try:
                process = subprocess.Popen(command, stdout=subprocess.PIPE)
            except OSError as e:
                raise CacheException("Error running %s to inspect %s: %s"
                                     % (command[0], filepath, str(e)))
            else:
                output = process.communicate()[0]
                if process.poll():
                    raise CacheException("%s unsuccessful exit" % command[0])
            pkg.update(dict(zip(('name','arch','version'), output.split())))
        else:
            raise CacheException("Not sure how to inspect pkg type " + pkg_type)

        return pkg

    def add(self, filepath, **kwargs):
        """Adds a package to the cache, copying the file to cache_dir

        It is not an error to add a package that already exists.  That package
        is simply overwritten.

        """
        filename = os.path.basename(filepath)
        pkg = {'filename': filename}
        for v in 'name', 'version', 'type', 'arch':
            pkg[v] = kwargs.get(v)

        if not (pkg['name'] and pkg['type'] and
                pkg['arch'] and pkg['version']):
            guess = self._inspect(filepath, pkg['type'])
            for f in 'name', 'type', 'arch', 'version':
                if not pkg[f]:
                    pkg[f] = guess[f]

        log.debug('Adding package %s to cache' % filename)
        with self.conn:
            self.conn.execute('REPLACE INTO packages '
                              '(name, version, type, arch, filename) VALUES '
                              '(:name, :version, :type, :arch, :filename);',
                              pkg)

        cache_dir_type = os.path.join(self.cache_dir, pkg['type'])
        if not os.path.exists(cache_dir_type):
            os.mkdir(cache_dir_type)
        shutil.copy(filepath, cache_dir_type)

    def get(self, **kwargs):
        """Look up a package and return its path"""
        args = ('name', 'version', 'type', 'arch')
        # Create a dictionary from kwargs of only the args we want
        where = dict(zip([a for a in args if a in kwargs],
                         [kwargs[a] for a in args if a in kwargs]))
        if len(where) == 0:
            raise CacheException("Missing filters for get")

        c = self.conn.execute('SELECT type,filename FROM packages WHERE ' +
                              ' GLOB ? AND '.join(where.keys()) + ' GLOB ?' + 
                              ' ORDER BY added DESC;', where.values())
        r = c.fetchone()
        if r:
            cache_path = str(os.path.join(r['type'], r['filename']))
            return os.path.relpath(os.path.join(self.cache_dir, cache_path))
        return None

    def list(self, filename='*', **kwargs):
        '''Return a list of dictionaries describing requested cache entries'''
        args = ('name', 'version', 'type', 'arch')
        where = dict(zip([a for a in args if a in kwargs],
                         [kwargs[a] for a in args if a in kwargs]))
        where['filename'] = filename

        c = self.conn.execute('SELECT filename,name,version,type,arch,added '
                              'FROM packages WHERE ' +
                              ' GLOB ? AND '.join(where.keys()) + ' GLOB ?;',
                              where.values())

        results = []
        for row in c:
            results.append(dict(row))

        return results

    # TODO: Deleting packages needs to be tested
    def prune(self, keep_per_version=None):
        "Clean up the cache in various ways"

        # This bit validates that all of the filenames still exist
        pkgs = self.conn.execute('SELECT filename,type FROM packages;')
        for pkg in pkgs:
            if not os.path.exists(os.path.join(self.cache_dir, pkg['type'],
                                               pkg['filename'])):
                log.debug("Package %s missing from cache.  Removing." %
                          pkg['filename'])
                self.remove(pkg['filename'], pkg['type'])

        # This bit removes old package versions
        if keep_per_version:
            pkg_groups = self.conn.execute('SELECT DISTINCT name,arch,type '
                                           'FROM packages;')
            for pkg_group in pkg_groups:
                values = dict(pkg_group)
                values['keep'] = keep_per_version
                pkgs = self.conn.execute('SELECT filename '
                                         'FROM packages '
                                         'WHERE name = :name AND arch = :arch '
                                               'AND type = :type '
                                         'ORDER BY added DESC '
                                         'LIMIT -1 OFFSET :keep;',
                                         values)
                for pkg in pkgs:
                    self.remove(pkg['filename'])
        self.conn.execute('VACUUM;')

    def remove(self, filename, pkg_type=None):
        '''Remove a particular filename from the cache'''
        if not pkg_type:
            c = self.conn.execute('SELECT type FROM packages '
                                  'WHERE filename = ?', (filename,))
            r = c.fetchone()
            if not r:
                raise CacheException('Filename %s not in the cache' % filename)
            pkg_type = r['type']

        log.debug('Removing package %s from cache' % filename)
        with self.conn:
            self.conn.execute('DELETE FROM packages WHERE filename = ?;',
                              (filename,))
        filepath = os.path.join(self.cache_dir, pkg_type, filename)
        if os.path.exists(filepath):
            os.unlink(filepath)

if __name__ == '__main__':
    import doctest
    if os.path.exists('tests/out/cache'):
        shutil.rmtree('tests/out/cache')
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)
