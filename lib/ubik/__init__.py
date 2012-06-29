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
