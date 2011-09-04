
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
