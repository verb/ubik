
import logging

log = logging.getLogger('ubik.hats')
log.debug("Logging initialized")

class HatException(Exception):
    pass

from ubik.hats.build import BuildHat
from ubik.hats.cache import CacheHat
from ubik.hats.config import ConfigHat
from ubik.hats.helper import HelperHat
from ubik.hats.infradb import InfraDBHat
from ubik.hats.package import PackageHat

ALL_HATS = (
    HelperHat,
    ConfigHat,
    CacheHat,
    BuildHat,
    PackageHat,
    InfraDBHat,
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
