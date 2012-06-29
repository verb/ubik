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

import logging

log = logging.getLogger('ubik.hats')
log.debug("Logging initialized")

class HatException(Exception):
    pass

from ubik.hats.build import BuildHat
from ubik.hats.cache import CacheHat
from ubik.hats.config import ConfigHat
from ubik.hats.deploy import DeployHat
from ubik.hats.helper import HelperHat
from ubik.hats.infradb import InfraDBHat
from ubik.hats.package import PackageHat
from ubik.hats.supervisor import SupervisorHat

ALL_HATS = (
    HelperHat,
    ConfigHat,
    CacheHat,
    BuildHat,
    PackageHat,
    InfraDBHat,
    DeployHat,
    SupervisorHat,
    )

def hatter(argv, config=None, options=None):
    """Given an arbitrary command string, attempt to figure out which hat we should
    wear, then initialize and return an object instance.

    >>> hatter(('help',))
    <Hat Object: help>
    >>> hatter(('help','config'))
    <Hat Object: help>
    >>> hatter(('config',))
    <Hat Object: config>
    >>>

    """

    log.debug("Looking for hat %s" % argv[0])
    for hat in ALL_HATS:
        if hat.areyou(argv[0]) or hat.name == argv[0]:
            log.debug("%s matched hat %s" % (argv[0], hat.__name__))
            return hat(argv, config, options)

    # Could not find a hat
    return None
