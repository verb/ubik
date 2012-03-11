
import logging
import os.path

import ubik.builder
import ubik.defaults

from ubik.hats import HatException
from ubik.hats.base import BaseHat

log = logging.getLogger('ubik.hats.build')

class BuildHat(BaseHat):
    "Builder Hat"

    name = 'build'
    desc = "Build Software"

    @staticmethod
    def areyou(string):
        "Confirm or deny whether I am described by string"
        if string == 'build':
            return True
        return False

    def __init__(self, argv, config=None, options=None):
        super(BuildHat, self).__init__(argv, config, options)
        self.args = argv[1:]

    def run(self):
        if len(self.args) != 2 or self.args[0] == 'help':
            self.help(self.output)
        else:
            self.build()

    # build sub-commands
    # these functions are expected to consume self.args
    def build(self):
        '''build APP VERSION

        Builds version VERSION of app APP, as directed by ini configuration
        '''
        bob = ubik.builder.Builder(self.config, self.options.workdir)
        bob.build_from_config(*self.args[0:2])

    command_list = ( build, )

if __name__ == '__main__':
    BuildHat(())

