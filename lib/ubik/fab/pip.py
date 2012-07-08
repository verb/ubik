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
import os, os.path
import shlex
import subprocess
import tempfile

from fabric.api import local, prompt

from ubik import builder, packager

NAME = 'pip'

log = logging.getLogger(NAME)

def _get_config(configfile='package.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    return config

def build(version, config, env):
    'Builds this package into a directory tree'
    if not version:
        version = prompt("What version did you want packaged there, hotshot?")
    if not isinstance(config, ConfigParser.SafeConfigParser):
        if config:
            config = _get_config(config)
        else:
            config = _get_config()

    # These are the variables that can be percent expanded in the ini
    config_vars = {
        'root': os.path.abspath(env.rootdir),
        'version': version,
    }

    try:
        prefix = config.get(NAME, 'prefix', config_vars)
        rootdir_path = os.path.join(env.rootdir, prefix.lstrip('/'))
    except ConfigParser.Error:
        rootdir_path = env.rootdir
    rootdir_path = os.path.abspath(rootdir_path)

    try:
        pip_pkgs = config.get(NAME, 'packages', config_vars)
        pip_cmd = ('pip install --install-option=--prefix=' + rootdir_path +
                   ' ' + pip_pkgs)
        log.debug("pip_cmd = " + pip_cmd)
        subprocess.check_call(shlex.split(pip_cmd), shell=False)
    except ConfigParser.Error:
        pass

    try:
        pip_reqs = config.get(NAME, 'requirements', config_vars)
        pip_cmd = ('pip install --install-option=--prefix=' + rootdir_path +
                   ' -r ' + pip_reqs)
        log.debug("pip_cmd = " + pip_cmd)
        subprocess.check_call(shlex.split(pip_cmd), shell=False)
    except ConfigParser.Error:
        pass

def clean(builddir):
    'Remove build directory and packages'
    local('rm -rf _* *.deb *.rpm *.pyc', capture=False)

def deb(version=None):
    'Build a debian package'
    package(version, 'deb')

def filelist(pkgtype, env):
    '''Outputs default filelist as json (see details)

    Generates and prints to stdout a filelist json that can be modified and
    used with package.ini's "filelist" option to override the default.

    Useful for setting file modes in RPMs'''
    if not env.exists('builddir'):
        build(pkgtype, env)
    packager.Package('package.ini', env).filelist()

def package(version=None, config=None, pkgtype='deb', env=None):
    'Creates deployable packages'
    cleanitup = False
    if not env:
        env = builder.BuildEnv()
    if not version:
        version = prompt("What version did you want packaged there, hotshot?")
    if not env.rootdir:
        env.rootdir = tempfile.mkdtemp(prefix='builder-root-')
        cleanitup = True
        build(version, config, env)
    elif not env.exists('rootdir'):
        build(version, config, env)

    for pkgtype in 'deb', 'rpm':
        if config.has_section(pkgtype):
            pkg = packager.Package(config, env, pkgtype)
            pkg.build(version)

    if cleanitup:
        local('rm -rf %s' % env.rootdir)

def rpm(version=None):
    'Build a Red Hat package'
    package(version, 'rpm')


if __name__ == '__main__':
    build('1.0', ('doc/example-%s.ini' % NAME), 
          builder.BuildEnv(rootdir="tests/out/pip"))
