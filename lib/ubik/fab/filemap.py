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

import json
import os, os.path
import shutil as sh
import sys

from fabric.api import abort, cd, local, prompt, warn

from ubik import builder, packager

# filemap copies files directly from source to root, there is no build step
defenv = builder.BuildEnv('_root','_root','.')

file_map, file_map_table = None, None

def _install_file_map(fmap, installdir):
    for src, dst in fmap:
        _install(src, os.path.join(installdir,dst))

def _install(src, dst):
    if src and os.path.isdir(src):
        sh.copytree(src, dst)
    else:
        if not os.path.exists(os.path.dirname(dst)):
            os.makedirs(os.path.dirname(dst))
        if src:
            sh.copy(src, dst)

def build(pkgtype='deb', env=defenv):
    'Builds this package into a directory tree'
    if file_map:
        _install_file_map(file_map, env.rootdir)
    elif file_map_table:
        _install_file_map(file_map_table[pkgtype], env.rootdir)
    else:
        abort("You must register a filemap with this module using register().")

def clean(env=defenv):
    'Remove build directory and packages'
    with cd(env.srcdir):
        local('rm -rf _* *.deb *.rpm', capture=False)
        local('find . -name \*.pyc -print -exec rm \{\} \;', capture=False)

def deb(version=None):
    'Build a debian package'
    package(version, 'deb')

def debiandir(version='0.0', env=defenv):
    "Generate DEBIAN dir in rootdir, but don't build package"
    if not env.exists('builddir'):
        build('deb', env)
    packager.DebPackage('package.ini', env).debiandir(version)

def filelist(pkgtype='deb', env=defenv):
    '''Outputs default filelist as json (see details)

    Generates and prints to stdout a filelist json that can be modified and
    used with package.ini's "filelist" option to override the default.

    Useful for setting file modes in RPMs'''
    if not env.exists('builddir'):
        build(pkgtype, env)
    packager.Package('package.ini', env).filelist()

def package(version=None, pkgtype='deb', env=defenv):
    'Creates deployable packages'
    if not version:
        version = prompt("What version did you want packaged there, hotshot?")
    if not env.exists('builddir'):
        warn('Implicitly invoking build')
        build(pkgtype, env)

    pkg = packager.Package('package.ini', env, pkgtype)
    pkg.build(version)

def register(filemap_or_table):
    'Register a filemap for use with this module'
    global file_map, file_map_table
    if isinstance(filemap_or_table, list):
        file_map = filemap_or_table
    elif isinstance(filemap_or_table, dict):
        file_map_table = filemap_or_table
    else:
        abort("I don't even know what you're talking about.")

def rpm(version=None):
    'Build a Red Hat package'
    package(version, 'rpm')

def rpmspec(version='0.0', env=defenv):
    'Output the generated RPM spec file'
    if not env.exists('builddir'):
        build('rpm', env)
    packager.RpmPackage('package.ini', env).rpmspec(sys.stdout, version)
