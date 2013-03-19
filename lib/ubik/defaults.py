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
"Defaults across all ubik modules"

VERSION="0.10.10"

CACHE_DIR = '~/.rug/cache'
CONFIG_FILE = '~/.rug/rug.ini'
GLOBAL_CONFIG_FILE = '/etc/ubik.ini'

config_defaults = {
    "builder.iniuri": "https://deploy/ini",
    "cache.dir":    "~/.rug/cache",
    "deploy.user": "prod",
    "deploy.restart": "false",
    "infradb.driver": "dns",
    "package.license": "Proprietary",
    "package.maintainer": "%(login)s@%(node)s",
    "package:deb.lintian_suppress": (
        'file-in-etc-not-marked-as-conffile,'
        'file-in-usr-local,'
        'description-starts-with-package-name,'
        'description-synopsis-is-duplicated,'
        'dir-in-usr-local,'
        'dir-or-file-in-opt,'
        'missing-dependency-on-libc,'
        'no-copyright-file,'
        'non-etc-file-marked-as-conffile,'
        'package-installs-python-bytecode,'
        'python-script-but-no-python-dep,'
        'shlib-with-executable-bit,'
        'unstripped-binary-or-object,'
        'wrong-file-owner-uid-or-gid'
    ),
    "package:rpm.autoreqprov": "no",
    "package:rpm.group": "Miscellaneous",
    "package:rpm.vendor": "Unspecified",
}

