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

import ConfigParser
import logging
import os.path

import ubik.cache
import ubik.defaults

from ubik.hats import HatException
from ubik.hats.base import BaseHat

log = logging.getLogger('ubik.hats.cache')

class CacheHat(BaseHat):
    "Cache Management Hat"

    name = 'cache'
    desc = "Cache Management"

    @staticmethod
    def areyou(string):
        "Confirm or deny whether I am described by string"
        if string == 'cache':
            return True
        return False

    def __init__(self, argv, config=None, options=None):
        super(CacheHat, self).__init__(argv, config, options)
        self.args = argv[1:]

        cache_dir = os.path.expanduser(self.config.get('cache','dir'))
        self.cache = ubik.cache.UbikPackageCache(cache_dir)

    def run(self):
        # If cache.autoprune is true, run prune anytime a cache
        # command is called
        try:
            autoprune = self.config.get('cache', 'autoprune')
        except ConfigParser.Error:
            pass
        else:
            if autoprune.lower() == 'true':
                self.prune()

        if len(self.args) == 0:
            self.args.insert(0, 'ls')

        try:
            while len(self.args) > 0:
                command = self.args.pop(0)
                if command in self.command_map:
                    self.command_map[command](self)
                elif command == 'help':
                    self.help(self.output)
                else:
                    raise HatException("Unknown cache command: %s" % command)
        except ubik.cache.CacheException as e:
            raise HatException(str(e))

    # cache sub-commands
    # these functions are expected to consume self.args
    def add(self):
        '''cache add FILE

        Adds FILE to the package cache.'''
        i = 0
        for filepath in self.args:
            i += 1
            if filepath == ';':
                break
            self.cache.add(filepath)
        del self.args[:i]

    # TODO: add file command

    def last(self):
        '''cache last [ NAME ]

        Returns the path to the latest package file for package NAME, as
        determined by creation date. Defaults to all packages.'''
        if len(self.args) == 0:
            self.args.insert(0, '*')
        filename = self.cache.get(name=self.args.pop(0))
        if filename:
            print >>self.output, os.path.abspath(filename)

    def ls(self):
        '''cache [ ls [ GLOB ] ]

        Display the contents of the cache, potentially filtered by GLOB.
        '''
        if len(self.args) == 0:
            self.args.insert(0, '*')
        i = 0
        for glob in self.args:
            i += 1
            for pkg in self.cache.list(glob):
                print pkg["filename"]
        del self.args[:i]

    def prune(self):
        '''cache prune

        Prune contents of cache according to cache.keep_packages setting.
        Also tidies the index by removing packages that have been deleted
        on disk.
        '''
        try:
            keep_versions = self.config.get('cache', 'keep_packages')
        except ConfigParser.Error:
            keep_versions = None
        self.cache.prune(keep_versions)

    def remove(self):
        '''cache remove FILENAME

        Find and remove the file named FILENAME from the package cache.'''
        i = 0
        for filepath in self.args:
            i += 1
            if filepath == ';':
                break
            self.cache.remove(filepath)
        del self.args[:i]

    command_list = ( add, last, ls, prune, remove )
    command_map = {
        'add':      add,
        'del':      remove,
        'delete':   remove,
        'last':     last,
        'list':     ls,
        'ls':       ls,
        'prune':    prune,
        'remove':   remove,
        'rm':       remove,
    }

if __name__ == '__main__':
    CacheHat(())

