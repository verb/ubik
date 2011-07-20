'Utility functions to read/write config for all ubik modules.'

import logging
import os.path

import ConfigParser

log = logging.getLogger('ubik.config')

def read(files):
    "Read list of configuration files, return config object"
    config = ConfigParser.SafeConfigParser()

    if isinstance(files,str):
        files = (files,)
    paths = [os.path.expanduser(f) for f in files]
    paths_read = config.read(paths)
    log.debug("Read config files %s" % repr(paths_read))

    return config