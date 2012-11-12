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
import logging
import os, os.path
import shutil as sh
import tempfile

from fabric.api import abort, local, prompt, warn
# Fabric 1.0 changed changed the scope of cd() to only affect remote calls.
# This bit of kludgery maintains compatibility of this file with fabric 0.9,
# but it is only possible because no remote calls are made in this file
try:
    from fabric.api import lcd as cd
except ImportError:
    from fabric.api import cd

from ubik import packager

log = logging.getLogger('svnant')

def _get_config(configfile='package.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    return config

def build(version, config, rootdir='_root', builddir='_svn'):
    'Builds this package into a directory tree'
    if os.path.exists(rootdir):
        log.warning("Directory %s exists, so skipping build", rootdir)
        return 
    if not version:
        version = prompt("What version did you want packaged there, hotshot?")
    if not config:
        config = _get_config()
    if not os.path.exists(builddir):
        os.mkdir(builddir)

    repo = config.get('svnant', 'repo', False, 
                      {'version': version.split('-',1)[0],})
    try:
        prefix = config.get('svnant', 'prefix').strip('/')
    except ConfigParser.NoOptionError:
        prefix = ''

    if not os.path.exists(os.path.join(builddir, '.svn')):
        local("svn co %s %s" % (repo, builddir), capture=False)
    else:
        with cd(builddir):
            local("svn update")

    with cd(os.path.join(builddir, 'build')):
        local("ant -Dpflex.env=%s -Dbuild.path=%s %s" % (
               config.get('svnant', 'env'),
               os.path.join(os.path.abspath(rootdir), prefix),
               config.get('svnant', 'target')), capture=False)

def clean(builddir):
    'Remove build directory and packages'
    local('rm -rf _* *.deb *.rpm *.pyc', capture=False)

def deb(version=None):
    'Build a debian package'
    package(version, 'deb')

def filelist(pkgtype='deb', builddir='_build'):
    '''Outputs default filelist as json (see details)

    Generates and prints to stdout a filelist json that can be modified and
    used with package.ini's "filelist" option to override the default.

    Useful for setting file modes in RPMs'''
    if not os.path.exists(builddir):
        build(pkgtype, builddir)
    packager.Package('package.ini', builddir).filelist()

def package(version=None, config=None, pkgtype='deb', rootdir=None):
    'Creates deployable packages'
    cleanitup = False
    if not version:
        version = prompt("What version did you want packaged there, hotshot?")
    if not rootdir:
        rootdir = tempfile.mkdtemp(prefix='builder-root-')
        cleanitup = True
        build(version, config, rootdir)
    elif not os.path.exists(rootdir):
        os.mkdir(rootdir)
        build(version, config, rootdir)

    for pkgtype in 'deb','rpm':
        if config.has_section(pkgtype):
            pkg = packager.Package(config, rootdir, pkgtype)
            pkg.build(version)

    if cleanitup:
        local('rm -rf %s' % rootdir)

def rpm(version=None):
    'Build a Red Hat package'
    package(version, 'rpm')

