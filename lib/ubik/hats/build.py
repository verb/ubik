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
        self._do_sysinit()
        bob = ubik.builder.Builder(self.config, self.options.workdir)
        bob.build_from_config(*self.args[0:2])

    command_list = ( build, )

if __name__ == '__main__':
    BuildHat(())

