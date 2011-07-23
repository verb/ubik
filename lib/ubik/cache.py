"Utilities for caching files in directory"

import mimetypes
import os, os.path
import sqlite3
import shutil
import subprocess

class CacheException(Exception):
    pass

class UbikPackageCache(object):
    """Cache specifically for software packages, such as RPM & DEB

    >>> u=UbikPackageCache('tests/out/cache')
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
                    'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                    'name TEXT NOT NULL,'
                    'version TEXT,'
                    'type TEXT,'
                    'arch TEXT,'
                    'filename TEXT NOT NULL,'
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

        if pkg_type == 'deb':
            command = ('dpkg-deb', '--showformat',
                       '${Package}\t${Architecture}\t${Version}',
                       '--show', filepath)
            output = subprocess.check_output(command)
            pkg.update(dict(zip(('name','arch','version'), output.split())))
        else:
            raise CacheException("Package inspection failed")

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

        with self.conn:
            self.conn.execute('INSERT INTO packages '
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
                              ' = ? AND '.join(where.keys()) + ' = ?;',
                              where.values())
        r = c.fetchone()
        cache_path = str(os.path.join(r['type'], r['filename']))
        return os.path.relpath(os.path.join(self.cache_dir, cache_path))

    def prune(self):
        self.conn.execute('VACUUM;')

if __name__ == '__main__':
    import doctest
    if os.path.exists('tests/out/cache'):
        shutil.rmtree('tests/out/cache')
    doctest.testmod(verbose=False)
