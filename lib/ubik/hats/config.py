
from ubik.hats.base import BaseHat

class ConfigHat(BaseHat):
    "Modify configuration files"

    name = 'config'
    desc = "Modify configuration"

    @staticmethod
    def areyou(string):
        "Confirm or deny whether I am described by string"
        if string in ('config', 'configure'):
            return True
        return False

    @staticmethod
    def help(args):
        pass

    def __init__(self, args):
        pass
