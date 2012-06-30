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
#
"Generic OS package creator thing"

import ConfigParser
import glob
import json
import logging
import os, os.path
import platform
import re
import shutil as sh
import tempfile

from fabric.api import *

import builder

FAKESTATE='_fakestate'
USERINI='~/.rug/rug.ini'

log = logging.getLogger('ubik.packager')

class PackagerError(Exception):
    pass

def _split_version(combined_version):
    """Utility function for splitting version-release strings.

    version-release are required with RPM and supported with deb.  They allow
    for multiple releases of a single version of software.  For example, 1.0-2
    is the second release of the 1.0 version.

    Since RPMs require a release, this function will add one if not specified.

    >>> _split_version('1.0-2')
    ('1.0', '2')
    >>> _split_version('1.0')
    ('1.0', '1')
    >>>

    """
    version_release = tuple(combined_version.split('-'))
    if len(version_release) != 2:
        return (version_release[0], '1')
    return version_release

def Package(configfile, env, pkgtype='deb'):
    """Return the appropriate packager for a given pkgtype

    >>> p=Package('tests/package.ini', builder.BuildEnv(), 'deb')
    >>> isinstance(p, DebPackage)
    True
    >>> p=Package('tests/package.ini', builder.BuildEnv(), 'rpm')
    >>> isinstance(p, RpmPackage)
    True
    >>>

    """
    if pkgtype == 'deb':
        return DebPackage(configfile, env)
    elif pkgtype == 'rpm':
        return RpmPackage(configfile, env)
    else:
        warn("Package type == %s?!  You're crazy, man.  I like you, "
             "but you're crazy." % pkgtype)

class BasePackage(object):
    def __init__(self, config, env):
        self.filename = None
        self.env = env
        if isinstance(config, ConfigParser.SafeConfigParser):
            self.config = config
        else:
            self.config = ConfigParser.SafeConfigParser()
            self.config.read(os.path.expanduser(USERINI))
            self.config.read(config)

    def _conf_getp(self, option):
        'First tries to get option from [pkgtype] section, then from "package"'
        cvars = {'root': self.env.rootdir,}
        try:
            return self.config.get(self.pkgtype, option, vars=cvars)
        except ConfigParser.NoOptionError:
            return self.config.get('package', option, vars=cvars)

    def _conf_getpb(self, option):
        'Return _conf_getp results as a boolean'
        try:
            value = self._conf_getp(option)
        except ConfigParser.NoOptionError:
            return False
        if (value.lower() == 'true' or value.lower() == 'yes' or value == '1'):
            return True
        return False

    def _conf_getps(self, option, altname=None):
        'Return _conf_getp results as printable string'
        if altname:
            name = altname
        else:
            name = option.title()
        return "%s: %s\n" % (name, self._conf_getp(option))

    def _gen_filelist(self):
        rootdir = self.env.rootdir
        noconf = self._conf_getpb('noconffiles')
        filelist = []
        if not rootdir.endswith('/'):
            rootdir += '/'
        for root, dirs, files in os.walk(rootdir):
            relroot = root.split(rootdir, 1)[1]
            if not noconf and 'etc' in root.split('/'):
                opts = ('conf',)
            else:
                opts = ()
            # Warning: in rpm-land it's important not to claim directories you
            # don't own because they could be removed with the package
            if len(dirs) == 0 and len(files) == 0:
                filelist.append([relroot, dict.fromkeys(opts + ('dir',), True)])
            for dir in dirs:
                if os.path.islink(os.path.join(root, dir)):
                    filelist.append([os.path.join(relroot, dir),
                                     dict.fromkeys(opts + ('link',), True)])
            for file in files:
                fileopts = opts
                if os.path.islink(os.path.join(root, file)):
                    fileopts += ('link',)
                filelist.append([os.path.join(relroot, file), 
                                 dict.fromkeys(fileopts, True)])
        return filelist

    def _get_filelist(self):
        config = self.config
        rootdir = self.env.rootdir
        try:
            filelist_file = self._conf_getp('filelist')
        except ConfigParser.NoOptionError:
            filelist_file = None

        if filelist_file:
            with open(filelist_file) as file:
                filelist = json.load(file)
        else:
            filelist = self._gen_filelist()

        return filelist

    def clean(self):
        '''Removes package and root dir'''
        if self.env.exists('rootdir'):
            local("rm -rf '%s'" % self.env.rootdir, capture=False)
        if self.filename and os.path.exists(self.filename):
            local("rm '%s'" % self.filename, capture=False)

    def filelist(self):
        '''Outputs default filelist as json (see details)

        Generates and prints to stdout a filelist json that can be modified and
        used with package.ini's "filelist" option to override the default.

        Useful for setting file modes in RPMs'''
        print json.dumps(self._gen_filelist(), indent=4)

class DebPackage(BasePackage):
    """An object that packages a directory described by env into a deb file

    >>> if not os.path.exists('tests/out'):
    ...   os.mkdir('tests/out')
    >>> os.chdir('tests/out')
    >>> env=builder.BuildEnv(rootdir='../root')
    >>> pkgr=DebPackage('../package.ini', env)
    >>> isinstance(pkgr, DebPackage)
    True
    >>> pkg=pkgr.build('1.0')   #doctest: +ELLIPSIS
    [localhost] ...
    >>> os.path.basename(pkg)
    'packager-test_1.0_amd64.deb'
    >>>

    """
    pkgtype = 'deb'

    def _write_deb_conffiles(self, filelist):
        conffiles = [cf for cf,opts in filelist if opts.get('conf') 
                     and not opts.get('dir')]
        with open(os.path.join(self.env.rootdir, 'DEBIAN', 'conffiles'), 'w') as f:
            for cf in conffiles:
                f.write('/' + cf + '\n')

    def _write_deb_control(self, version):
        config = self.config
        debdir = os.path.join(self.env.rootdir, 'DEBIAN')
        if not os.path.exists(debdir):
            os.mkdir(debdir)
        # All items in config2control_trans are copied from the package config
        # file to the deb control file, and the values are what they're called
        # in debianville, if different from configville
        config2control_trans = {
            'arch': 'Architecture',
            'depends': None,
            'conflicts': None,
            'homepage': None,
            'maintainer': None,
            'name': 'Package',
            'priority': None,
            'provides': None,
            'recommends': None,
            'replaces': None,
            'section': None,
            'suggests': None,
        }
        machine2arch_trans = {
            'i686': 'i386',
            'x86_64': 'amd64',
        }
        with open(os.path.join(debdir,'control'), 'w') as control:
            for option, name in config2control_trans.items():
                try:
                    control.write(self._conf_getps(option, name))
                except ConfigParser.NoOptionError:
                    if option == 'arch':
                        arch = platform.machine()
                        if arch in machine2arch_trans:
                            arch = machine2arch_trans[arch]
                        control.write('Architecture: %s\n' % arch)
            control.write('Version: %s\n' % version)
            control.write(self._conf_getps('summary', 'Description'))
            for line in self._conf_getp('description').split('\n'):
                control.write(' ')
                control.write(line)
                control.write('\n')
        for script in 'preinst','postinst','prerm','postrm':
            if config.has_option(self.pkgtype, script):
                sh.copy(self._conf_getp(script), os.path.join(debdir, script))

    def _write_deb_md5sums(self, filelist):
        debdir = os.path.join(self.env.rootdir, 'DEBIAN')
        if not os.path.exists(debdir):
            os.mkdir(debdir)

        with open(os.path.join(debdir, 'md5sums'), 'w') as md5sums:
            prevdir = os.getcwd()
            os.chdir(self.env.rootdir)
            try:
                for filename, options in filelist:
                    if not options.get('dir') and not options.get('link'):
                        md5str = local("md5sum '%s'" % filename, capture=True)
                        print >>md5sums, md5str
            finally:
                os.chdir(prevdir)

    # Runs before DEBIAN/ is created
    def _write_fake_perms(self, filelist):
        log.debug("Faking permissions in advance of deb creation")
        # If there's a default user or group, go ahead and set it recursively
        try:
            owner = self._conf_getp('owner')
        except ConfigParser.NoOptionError:
            owner = ''
        try:
            group = ':' + self._conf_getp('group')
        except ConfigParser.NoOptionError:
            group = ''
        # if there's a prefix in the package or builder section, only set
        # ownership for files further down the tree as this is frequently
        # the correct behavior
        prefix = ''
        for section in self.pkgtype, 'package', 'svnant':
            if self.config.has_option(section, 'prefix'):
                prefix = self._conf_getp(section, 'prefix')
                break
        if owner or group:
            local("fakeroot -s %s -- chown -R %s%s '%s'" %
                  (FAKESTATE, owner, group, 
                   os.path.join(self.env.rootdir, prefix.strip('/'))),
                  capture=False)

        # per-file settings from filelist
        loadstate = ''
        for filename, options in filelist:
            usergroup = ''
            if 'owner' in options:
                usergroup = options['owner']
            if 'group' in options:
                usergroup += ':' + options['group']

            # if usergroup or mode is not null, then we've got changes to make
            # Optimization: don't stat FAKESTATE if loadstate is already set
            if not loadstate and ((usergroup or 'mode' in options) and
               os.path.exists(FAKESTATE)):
                loadstate = ' -i ' + FAKESTATE
            if usergroup:
                local("fakeroot -s %s%s -- chown -h %s '%s'" %
                      (FAKESTATE, loadstate, usergroup, 
                       os.path.join(self.env.rootdir, filename)),
                      capture=False)
            if not loadstate and ((usergroup or 'mode' in options) and
               os.path.exists(FAKESTATE)):
                loadstate = ' -i ' + FAKESTATE
            if 'mode' in options:
                local("fakeroot -s %s%s -- chmod %s '%s'" %
                      (FAKESTATE, loadstate, options['mode'],
                       os.path.join(self.env.rootdir, filename)),
                      capture=False)

    def _write_debian_dir(self, version):
        '''Creates the DEBIAN dir in rootdir'''
        filelist = self._get_filelist()
        debdir = os.path.join(self.env.rootdir, 'DEBIAN')
        # If the dir already exists it's generally due to a previous failed build
        if os.path.exists(debdir):
            log.info("%s exists.  Removing and re-creating.", debdir)
            local("rm -r '%s'" % debdir, capture=False)
        os.mkdir(debdir)
        self._write_fake_perms(filelist)
        self._write_deb_md5sums(filelist)
        self._write_deb_conffiles(filelist)
        self._write_deb_control(version)

    def build(self, version):
        '''Creates deployable packages in the current dir from files in rootdir

        Note that a directory named rootdir/DEBIAN will be created and
        removed afterward.'''
        log.debug("Building debian package version %s", version)
        rootdir = self.env.rootdir
        config = self.config

        self._write_debian_dir(version)

        fakeoptions = '--'
        if os.path.exists(FAKESTATE):
            fakeoptions = '-i ' + FAKESTATE + ' ' + fakeoptions
        output = local("fakeroot %s dpkg -b '%s' ." % (fakeoptions, rootdir), 
              capture=True)
        log.debug(output)

        m = re.match("dpkg-deb: building package \S+ in `(\S+)'", output)
        if m and os.path.exists(m.group(1)):
            self.filename = os.path.abspath(m.group(1))
        else:
            raise PackagerError("Error creating debian package")
        local("rm -r '%s'" % os.path.join(rootdir, 'DEBIAN'), capture=False)

        lintian_suppress = ','.join((
            'file-in-etc-not-marked-as-conffile',
            'file-in-usr-local',
            'description-starts-with-package-name',
            'description-synopsis-is-duplicated',
            'dir-in-usr-local',
            'dir-or-file-in-opt',
            'missing-dependency-on-libc',
            'non-etc-file-marked-as-conffile',
            'python-script-but-no-python-dep',
            'unstripped-binary-or-object',
            'wrong-file-owner-uid-or-gid',
        ))
        local("lintian -L '>=important' -X cpy,chg,shl --suppress-tags=%s '%s'" %
              (lintian_suppress, self.filename), capture=False)

        return self.filename

    def debiandir(self, version):
        self._write_debian_dir(version)

class RpmPackage(BasePackage):
    pkgtype = 'rpm'

    # 'spec' is a file-like object
    def _write_rpm_spec(self, spec, version):
        config = self.config
        (version, release) = _split_version(version)
        config2spec_trans = {
            'arch': 'BuildArch',
            'maintainer': 'Packager',
            'name': None,
            'requires': None,
            'summary': None,
        }

        for option, name in config2spec_trans.items():
            try: 
                spec.write(self._conf_getps(option, name))
            except ConfigParser.NoOptionError:
                pass
        spec.write("Version: %s\n" % version)
        spec.write("Release: %s\n" % release)
        spec.write("License: Proprietary\n")
        spec.write("Group: Pontiflex\n")
        spec.write("Vendor: Pontiflex\n")
        spec.write("AutoReqProv: no\n")
        spec.write("\n%description\n")
        spec.write(self._conf_getp('description'))
        spec.write("\n\n%files\n%defattr(-,root,root)\n")
        for filename,opts in self._get_filelist():
            if opts.get('mode') or opts.get('owner') or opts.get('group'):
                spec.write('%%attr(%s,%s,%s) ' % (opts.get('mode','-'),
                           opts.get('owner','-'), opts.get('group','-')))
            if opts.get('conf'):
                spec.write('%config ')
            if opts.get('dir'):
                spec.write('%dir ')
            spec.write('/' + filename.strip('/') + '\n')
        for script in 'pre','post','preun','postun':
            try:
                scriptname = self._conf_getp(script)
            except ConfigParser.NoOptionError:
                pass
            else:
                spec.write('\n%' + script + '\n')
                with open(scriptname) as sf:
                    spec.write(sf.read())

    def build(self, version):
        '''Creates deployable packages in the current dir from files in rootdir'''
        rootdir = self.env.rootdir
        config = self.config

        tmpdir = tempfile.mkdtemp(prefix='builder-rpm-')
        with open(os.path.join(tmpdir,'package.spec'), 'w') as specfp:
            self._write_rpm_spec(specfp, version)

        local("rpmbuild -bb --buildroot %s --define='_topdir %s' "
              "%s/package.spec" % (os.path.abspath(rootdir), tmpdir, 
              tmpdir), capture=False)
        rpmfiles = glob.glob(os.path.join(tmpdir, 'RPMS', '*', '*.rpm'))
        if len(rpmfiles) < 1:
            raise PackagerError("Error creating RPM package")

        newrpms = []
        for rpmfile in rpmfiles:
            local("mv '%s' ." % rpmfile, capture=False)
            newrpms.append(os.path.basename(rpmfile))
        rpmfiles = newrpms
        local("rm -r '%s'" % tmpdir)

        # At this point we really only support creating a single rpm
        return rpmfiles[0]

    def rpmspec(self, fp, version):
        '''Writes the generated specfile to fp'''
        self._write_rpm_spec(fp, version)

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)
