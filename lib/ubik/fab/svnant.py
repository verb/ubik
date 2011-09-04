
import json
import logging
import os, os.path
import shutil as sh
import tempfile

from fabric.api import abort, cd, local, prompt, warn

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

