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

import logging
import os.path
import subprocess
import tempfile

import ubik.builder
import ubik.cache
import ubik.defaults
import ubik.packager

from ubik.hats import HatException
from ubik.hats.base import BaseHat

log = logging.getLogger('ubik.hats.package')

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
        if self.args[0] == 'help':
            self.help(self.output)
        else:
            self.package()

    # package sub-commands
    def package(self):
        '''package [ deb|rpm ] APP VERSION

        Builds version VERSION of app APP, as directed by ini configuration,
        and add it to the package cache.
        '''
        if self.argv[0] in PKGTYPES:
            pkgtypes_to_build = (self.argv[0],)
        elif len(self.args) > 2 and self.args[0] in PKGTYPES:
            pkgtypes_to_build = (self.args.pop(0),)
        else:
            pkgtypes_to_build = PKGTYPES
        name, version = self.args[0:2]

        # First thing is to build the package
        self._do_sysinit()
        if self.options.workdir:
            workdir = self.options.workdir
        else:
            workdir = tempfile.mkdtemp(prefix='packager-bob-')
        bob = ubik.builder.Builder(self.config, workdir)
        bob.build_from_config(name, version)

        cache_dir = self.config.get('cache', 'dir')
        cache = ubik.cache.UbikPackageCache(cache_dir)
        for pkgtype in pkgtypes_to_build:
            # After the build_from_config() call above, self.config will contain
            # all of the configuration for this package
            if self.config.has_section(pkgtype):
                pkgr = ubik.packager.Package(bob.pkgcfg, bob.env, pkgtype)
                pkgfile = pkgr.build(version)
                log.debug("Successfully created package file %s", pkgfile)
                cache.add(pkgfile, type=pkgtype, version=version)
            else:
                logf = log.info if len(pkgtypes_to_build) > 1 else log.error
                logf("Config files does not specify package type '%s'",
                     pkgtype)

        if not (self.options.debug or self.options.workdir):
            log.info("Removing working directory '%s'", workdir)
            subprocess.check_call(('rm', '-rf', workdir))

    command_list = ( package, )

if __name__ == '__main__':
    PackageHat(())

