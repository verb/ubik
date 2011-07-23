
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

    def help(self, out):
        '''Print help message to specified file object

        This method is called on an instance so that it can give help specific
        to the arguments that have been parsed by __init__()
        '''
        print >>out, "Usage:"
        print >>out, "    cache [ ls [ glob ] ]"
        print >>out

    def __init__(self, args, config=None, options=None):
        super(CacheHat, self).__init__(args, config, options)
        self.args = args

        try:
            cache_dir = os.path.expanduser(self.config.get('cache','dir'))
        except ubik.cache.Error:
            cache_dir = os.path.expanduser(ubik.defaults.CACHE_DIR)
        self.cache = ubik.cache.UbikPackageCache(cache_dir)

    def run(self):
        if len(self.args) == 0:
            self.args.insert(0, 'ls')

        try:
            while len(self.args) > 0:
                command = self.args.pop(0)
                if command in ('ls', 'list'):
                    self.list()
                elif command == 'add':
                    self.add()
                elif command in ('rm', 'remove', 'del', 'delete'):
                    self.remove()
                elif command == 'prune':
                    self.prune()
                else:
                    raise HatException("Unknown cache command: %s" % command)
        except ubik.cache.CacheException as e:
            raise HatException(str(e))

    # cache sub-commands
    # these functions are expected to consume self.args
    def add(self):
        i = 0
        for filepath in self.args:
            i += 1
            if filepath == ';':
                break
            self.cache.add(filepath)
        del self.args[:i]

    def list(self):
        if len(self.args) == 0:
            self.args.insert(0, '*')
        i = 0
        for glob in self.args:
            i += 1
            for pkg in self.cache.list(glob):
                print pkg["filename"]
        del self.args[:i]

    def prune(self):
        self.cache.prune()

    def remove(self):
        i = 0
        for filepath in self.args:
            i += 1
            if filepath == ';':
                break
            self.cache.remove(filepath)
        del self.args[:i]

if __name__ == '__main__':
    CacheHat(())