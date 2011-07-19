
import logging

log = logging.getLogger('ubik.hats')
log.debug("Logging initialized")

from .config import ConfigHat

hats = (
    ConfigHat,
    )

def hatter(hat_str, args):
    '''Given an arbitrary string, attempt to figure out which hat we should
    wear, then initialize and return an object instance.'''

    if not hat_str or hat_str == 'help':
        for hat in hats:
            print "%s - %s" % (hat.name, hat.desc)
    else:
        log.debug("Looking for hat %s" % hat_str)
        for hat in hats:
            if hat.areyou(hat_str):
                log.debug("%s matched hat %s" % (hat_str, hat__name__))
                return hat(args)

    # Could not find a hat
    return None