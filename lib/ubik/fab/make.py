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
import json
import logging
import os, os.path
import shutil as sh
import subprocess
import tempfile
import shlex

from fabric.api import abort, cd, local, prompt, warn

from ubik import builder, packager

NAME = 'make'
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

    builddir = env.srcdir
    try:
        builddir = os.path.join(builddir, config.get(NAME, 'subdir',
                                                     vars=config_vars))
    except ConfigParser.Error:
        pass

    install_path = os.path.abspath(env.rootdir)
    try:
        install_path = os.path.join(install_path,
                                    config.get(NAME, 'prefix').lstrip('/'))
    except ConfigParser.Error:
        pass

    with cd(builddir):
        if not os.path.exists(os.path.join(builddir, 'Makefile')):
            log.info("Makefile doesn't exist, attempting to create")
            if not os.path.exists(os.path.join(builddir, 'configure')):
                log.info("configure script doesn't exist, attempting to create")
                local('./automake.sh', capture=False)
            try:
                configure_options = config.get(NAME, 'configure_options',
                                               vars=config_vars)
            except ConfigParser.NoOptionError:
                configure_options = ''
            # use subprocess/shell=False because configure_options is tainted
            # ...  heh.  taint.
            args = shlex.split('./configure '+configure_options)
            subprocess.check_call(args, shell=False, cwd=builddir)
        try:
            target = config.get(NAME, 'build_target', vars=config_vars)
        except ConfigParser.NoOptionError:
            target = ''
        local("make " + target, capture=False)
        try:
            target = config.get(NAME, 'install_target')
        except ConfigParser.NoOptionError:
            target = 'install'
        local("make %s DESTDIR=%s" % (target, install_path), capture=False)

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

    for pkgtype in 'deb','rpm':
        if config.has_section(pkgtype):
            pkg = packager.Package(config, env, pkgtype)
            pkg.build(version)

    if cleanitup:
        local('rm -rf %s' % env.rootdir)

def rpm(version=None):
    'Build a Red Hat package'
    package(version, 'rpm')


if __name__ == '__main__':
    build('1.0', ('doc/example-%s.ini' % NAME), 'test/out', 'test')
