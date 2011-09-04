
import ConfigParser
import json
import logging
import os, os.path
import shutil as sh
import tempfile

from fabric.api import abort, cd, local, prompt, warn

from ubik import builder, packager

NAME = 'ant'
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

    config_vars = {
        'root': os.path.abspath(env.rootdir),
    }
    
    properties = ''
    try:
        for prop in config.options('ant:properties'):
            properties += " -D%s=%s" % (prop, config.get('ant:properties', prop, 
                                                         vars=config_vars))
    except ConfigParser.Error:
        pass

    try:
        target = config.get('ant', 'target', vars=config_vars)
    except ConfigParser.Error:
        target = 'install'

    builddir = env.srcdir
    try:
        builddir = os.path.join(builddir, config.get(NAME, 'subdir',
                                                     vars=config_vars))
    except ConfigParser.Error:
        pass

    with cd(builddir):
        local("ant %s %s" % (properties, target), capture=False)

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
    if not env.exists('rootdir'):
        build(pkgtype, env)
    packager.Package('package.ini', env).filelist()

def package(version=None, config=None, env=None):
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
        build(version, config, rootdir)

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
    build('1.0', 'doc/example-ant.ini')
