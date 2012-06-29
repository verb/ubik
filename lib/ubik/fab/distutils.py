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
import stat
import subprocess
import tempfile

from fabric.api import abort, cd, local, prompt, warn

from ubik import builder, packager

NAME = 'distutils'
POSTINST_TEMPLATE = """#!/bin/sh
set -e

# Automatically added by ubik.fab.distutils:
if which pycompile >/dev/null 2>&1; then
        pycompile -V %(pyvers)s -p %(pkgname)s
fi

# End automatically added section"""
PRERM_TEMPLATE = """#!/bin/sh
set -e

# Automatically added by ubik.fab.distutils:
if which pyclean >/dev/null 2>&1; then
        pyclean -V %(pyvers)s -p %(pkgname)s
else
        dpkg -L %(pkgname)s | grep \.py$ | while read file
        do
                rm -f "${file}"[co] >/dev/null
        done
fi

# End automatically added section"""

log = logging.getLogger(NAME)
def _create_pycompile_scripts(scriptdir, config):
    """Creates postinst/prerm scripts compatible with debian pycompile paradigm

    >>> config = ConfigParser.SafeConfigParser()
    >>> config.read('tests/package.ini')
    ['tests/package.ini']
    >>> scriptdir = 'tests/out/scripts'
    >>> if os.path.exists(scriptdir):
    ...     sh.rmtree(scriptdir)
    >>> _create_pycompile_scripts(scriptdir, config)
    >>> config.get('deb', 'postinst')
    'tests/out/scripts/postinst'
    >>> import hashlib
    >>> md5 = hashlib.md5()
    >>> with open(os.path.join(scriptdir, 'postinst')) as f:
    ...     md5.update(f.read())
    >>> md5.hexdigest()
    '360984dd36c60df0e7bfdc1216af2f2d'
    >>>

    """
    if not os.path.exists(scriptdir):
        os.makedirs(scriptdir)
    pkgname = config.get('package', 'name')
    try:
        pyvers = config.get('deb', 'python_version_range')
    except ConfigParser.Error:
        pyvers = '2.6-3.0'

    for script, templ in (('postinst', POSTINST_TEMPLATE),
                          ('prerm', PRERM_TEMPLATE)):
        if not config.has_option('deb', script):
            script_path = os.path.join(scriptdir, script)
            with open(script_path, 'a') as f:
                print >>f, templ % {'pkgname': pkgname, 'pyvers': pyvers}
            os.chmod(script_path, 0755)
            config.set('deb', script, script_path)

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

    rootdir_path = os.path.abspath(env.rootdir)
    # pyversions(1) is a script that exists on debian-derived distributions
    # that lists the different python runtimes installed.
    #
    # try to use it, but it's no big deal if it doesn't exist
    try:
        pyvertag = config.get(NAME, 'pyversions', vars=config_vars)
    except ConfigParser.NoOptionError:
        pyvertag = 'installed'
    try:
        pyverproc = subprocess.Popen(['/usr/bin/pyversions', '--'+pyvertag],
                                     stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE)
        (pyverout, pyvererr) = pyverproc.communicate()
        if pyverproc.returncode == 0:
            pyvers = pyverout.split()
        else:
            pyvers = ['python']
            if not pyverproc.returncode:
                pyverproc.kill()
    except OSError:
        pyvers = ['python']

    log.debug("Python versions are: %s", repr(pyvers))
    for pyver in pyvers:
        log.debug("Running setup.py for %s", pyver)
        pyver_args = [pyver, 'setup.py', 'install', '--root', rootdir_path]
        try:
            if config.get(NAME, 'layout') == 'deb':
                pyver_args.extend(['--no-compile',
                                   '--install-layout',
                                   'deb'])
                _create_pycompile_scripts(env.builddir, config)
        except ConfigParser.NoOptionError:
            pass
        subprocess.check_call(pyver_args, cwd=builddir)

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
