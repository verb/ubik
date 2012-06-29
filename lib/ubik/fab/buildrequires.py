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
import platform
import subprocess

log = logging.getLogger('buildrequires')

class BuildRequiresException(Exception):
    pass

def _check_dpkg_prereq(pkgs):
    subprocess.check_call(['dpkg-query','-W'] + pkgs)

def _check_rpm_prereq(pkgs):
    subprocess.call(['rpm','-q'] + pkgs)

def check_build_reqs(config, **kwargs):
    cmd_table = {
        'Ubuntu': _check_dpkg_prereq,
        'redhat': _check_rpm_prereq,
    }    
    dist = platform.linux_distribution()[0]    
    
    log.info("Checking for required packages")
    try:
        cmd_table[dist](config.get('buildrequires', dist.lower()).split())
    except KeyError:
        log.error("Cannot find package command for %s", dist)            
    except ConfigParser.NoOptionError:
        log.warning('No requirements for dist %s', dist)
    except subprocess.CalledProcessError:
        raise BuildRequiresException("Missing required package")
