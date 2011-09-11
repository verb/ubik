
import logging

log = logging.getLogger('ubik.hats')
log.debug("Logging initialized")

class HatException(Exception):
    pass

from .build import BuildHat
from .cache import CacheHat
from .config import ConfigHat
from .helper import HelperHat
from .package import PackageHat

ALL_HATS = (
    HelperHat,
    ConfigHat,
    CacheHat,
    BuildHat,
    PackageHat,
    )

def hatter(hat_str, args, config=None, options=None):
    '''Given an arbitrary string, attempt to figure out which hat we should
    wear, then initialize and return an object instance.'''

    log.debug("Looking for hat %s" % hat_str)
    for hat in ALL_HATS:
        if hat.areyou(hat_str):
            log.debug("%s matched hat %s" % (hat_str, hat.__name__))
            return hat(args, config, options)

    # Could not find a hat
    return None
