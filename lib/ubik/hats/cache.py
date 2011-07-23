
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

    def runhat(self):
        self.init_cache()
        if len(self.args) == 0:
            command = 'ls'
        else:
            command = self.args.pop(0)

        if command in ('ls', 'list'):
            self.list()

    def list(self, verbose=False):
        for pkg in ubik.cache.list():
            print pkg["filename"]


if __name__ == '__main__':
    CacheHat(())