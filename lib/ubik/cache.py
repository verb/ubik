"Utilities for caching files in directory"

import mimetypes
import os, os.path
import sqlite3
import shutil
import subprocess

class CacheException(Exception):
    pass

class UbikPackageCache(object):
    "Cache specifically for software packages, such as RPM & DEB"
    def __init__(self, cache_dir):
        cache_dir = os.path.expanduser(cache_dir)
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        # TODO: detect previous version index and offer to reindex

        dbfile=os.path.join(cache_dir, 'index.db')
        self.conn = sqlite3.connect(dbfile)

        c = self.conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS packages ('
                    'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                    'name TEXT NOT NULL,'
                    'version TEXT,'
                    'type TEXT,'
                    'arch TEXT,'
                    'filename TEXT NOT NULL,'
                    'added TEXT DEFAULT CURRENT_TIMESTAMP'
                  ');')

    def _inspect(self, filepath, pkg_type=None):
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
        filename = os.path.basename(filepath)
        c = self.conn.cursor()
        pkg = {'filename': filename}
        for v in 'name', 'version', 'type', 'arch':
            pkg[v] = kwargs.get(v)

        if not (pkg['name'] and pkg['type'] and
                pkg['arch'] and pkg['version']):
            guess = self._inspect(filepath, pkg['type'])
            for f in 'name', 'type', 'arch', 'version':
                if not pkg[f]:
                    pkg[f] = guess[f]

        c.execute('INSERT INTO packages (name, version, type, arch, filename) '
                  'VALUES (:name, :version, :type, :arch, :filename);', pkg)
        self.conn.commit()

        cache_dir_type = os.path.join(self.cache_dir, pkg['type'])
        if not os.path.exists(cache_dir_type):
            os.mkdir(cache_dir_type)
        shutil.copy(filepath, cache_dir_type)

    def prune(self):
        c = self.conn.cursor()
        c.execute('VACUUM;')

if __name__ == '__main__':
    pass
