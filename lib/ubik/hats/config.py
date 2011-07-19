
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

    def help(self, out):
        '''Print help message to specified file object

        This method is called on an instance so that it can give help specific
        to the arguments that have been parsed by __init__()
        '''
        print >>out, "Usage: config"
        print >>out

    def __init__(self, args):
        pass

    def run(self):
        pass