
import logging
import os
import warnings

if 'DEBUG' in os.environ:
    loglevel = logging.DEBUG
    warnings.simplefilter('default')
elif 'VERBOSE' in os.environ:
    loglevel = logging.INFO
else:
    loglevel = logging.WARNING
logging.basicConfig(level=loglevel)

log = logging.getLogger('ubik')
log.debug("Logging initialized")
