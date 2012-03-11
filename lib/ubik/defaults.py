"Defaults across all ubik modules"

VERSION="0.0"

CACHE_DIR = '~/.rug/cache'
CONFIG_FILE = '~/.rug/rug.ini'
GLOBAL_CONFIG_FILE = '/etc/ubik.ini'

config_defaults = {
    "builder.iniuri": "https://deploy/ini",
    "cache.dir":    "~/.rug/cache",
    "infradb.driver": "dns",
}

