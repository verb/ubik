
import ConfigParser
import json
import logging
import os, os.path
import shutil as sh
import subprocess
import tempfile

from fabric.api import abort, cd, local, prompt, warn

from ubik import builder, packager

NAME = 'distutils'
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
