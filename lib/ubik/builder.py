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

import copy
import logging
import os, os.path
import subprocess
import tempfile
import urllib

import ubik.config

log = logging.getLogger('ubik.builder')

# module will be called if '[module name]' section exists in package's
# config file.  Order probably matters here.
build_modules = [
    # module name, python name, function to call
    ['buildrequires', 'ubik.fab.buildrequires', 'check_build_reqs'],
    # Source creation modules
    ['git', 'ubik.fab.git', 'clone'],
    ['svn', 'ubik.fab.svn', 'checkout'],
    # Source and/or build modules
    ['tgz', 'ubik.fab.tgz', 'untar'],
    ['copy', 'ubik.fab.copy', 'copysrc'],
    # Primary build modules
    ['ant', 'ubik.fab.ant', 'build'],
    ['fab', 'ubik.fab.fab', 'build'],
    ['make', 'ubik.fab.make', 'build'],
    ['distutils', 'ubik.fab.distutils', 'build'],
    ['pip', 'ubik.fab.pip', 'build'],
    # Post processing modules
    ['jettypathhack', 'ubik.fab.jettypathhack', 'hackthepath'],
    ['monit', 'ubik.fab.monit', 'write_monit_config'],
    ['supervisor', 'ubik.fab.supervisor', 'write_supervisor_config'],
    ['symlinks', 'ubik.fab.symlinks', 'makelinks'],
]

class BuildError(Exception):
    pass

class BuildEnv(object):
    def __init__(self, builddir='_build', rootdir='_root', srcdir='.'):
        self._dirs = {
            'builddir': builddir,
            'rootdir':  rootdir,
            'srcdir':   srcdir
        }
        for idir in self._dirs:
            edir = 'RUG_' + idir.upper()
            if edir in os.environ:
                self._dirs[idir] = os.environ[edir]
            else:
                os.environ[edir] = os.path.abspath(self._dirs[idir])

    def __getattr__(self, name):
        if name in self._dirs:
            return self._mkdirreturn(self._dirs[name])
        else:
            raise AttributeError("Invalid Attribute: %s" % name)

    def __setattr__(self, name, value):
        if '_dirs' in self.__dict__ and name in self._dirs:
            self._dirs[name] = value
        else:
            object.__setattr__(self, name, value)

    def _mkdirreturn(self, dirname):
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        return dirname

    def exists(self, dirname):
        if dirname in self._dirs:
            return os.path.exists(self._dirs[dirname])
        return False

class Builder(object):
    def __init__(self, usercfg=None, workdir=None):
        if not workdir:
            workdir = tempfile.mkdtemp(prefix='builder-bob-')
        elif not os.path.exists(workdir):
            os.makedirs(workdir)
        os.chdir(workdir)
        self.workdir = workdir
        log.debug("workdir is " + self.workdir)

        if usercfg:
            self.usercfg = usercfg
        else:
            self.usercfg = ubik.config.UbikConfig()

        self.env = BuildEnv('_build', '_root', '_src')

    def build_from_config(self, pkgcfg, version):
        '''Use a config file to build software'''

        if type(pkgcfg) == str:
            pkgcfg = self.get_config(pkgcfg)

        log.info('Commence to build package ' + pkgcfg.get('package', 'name'))
        pkgcfg_modules = set(s.split(':', 1)[0] for s in pkgcfg.sections())
        for section, module, buildfunc in build_modules:
            if section in pkgcfg_modules:
                log.info("Found %s section!  Importing the needful..." % section)
                module_statement = ("import %s; %s.%s(version=version, "
                    "config=pkgcfg, env=self.env)" %
                    (module, module, buildfunc))
                log.debug("Running statement: " + module_statement)
                exec(module_statement)

    def clean(self):
        if self.env.exists('builddir'):
            subprocess.call(['rm', '-rf', self.env.builddir])
        if self.env.exists('srcdir'):
            subprocess.call(['rm', '-rf', self.env.srcdir])

    def get_config(self, pkgname):
        log.info(pkgname + ": Can we build it?")
        pkgcfg = copy.copy(self.usercfg)
        uri = '/'.join((self.usercfg.get('builder','iniuri'), pkgname+'.ini'))
        log.debug('Looking for package config at uri ' + uri)
        try:
            pkgcfg.readfp(urllib.urlopen(uri))
        except IOError as e:
            log.info("NO WE CAN'T!")
            raise BuildError('Error reading package config from %s: %s' % 
                             (uri, str(e)))
        else:
            log.info("YES WE CAN!")

        self.pkgcfg = pkgcfg
        return pkgcfg
