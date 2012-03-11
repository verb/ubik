
import logging
import os.path

import ubik.builder
import ubik.defaults
import ubik.packager

from ubik.hats import HatException
from ubik.hats.base import BaseHat

log = logging.getLogger('ubik.hats.build')

PKGTYPES = ('deb', 'rpm')

class PackageHat(BaseHat):
    "Packager Hat"

    name = 'package'
    desc = "Package Software"

    @staticmethod
    def areyou(string):
        "Confirm or deny whether I am described by string"
        if string == PackageHat.name or string in PKGTYPES:
            return True
        return False

    def __init__(self, argv, config=None, options=None):
        super(PackageHat, self).__init__(argv, config, options)
        self.args = argv[1:]

    def run(self):
        if len(self.args) != 2 or self.args[0] == 'help':
            self.help(self.output)
        else:
            self.package()

    # package sub-commands
    def package(self):
        '''package [ deb|rpm ] APP VERSION

        Builds version VERSION of app APP, as directed by ini configuration
        '''
        # First thing is to build the package
        bob = ubik.builder.Builder(self.config, self.options.workdir)
        bob.build_from_config(*self.args[0:2])

        import pdb; pdb.set_trace()
        for pkgtype in PKGTYPES:
            pkgr = ubik.packager.Package(bob.pkgcfg, bob.env, pkgtype)

    command_list = ( package, )

if __name__ == '__main__':
    PackageHat(())

