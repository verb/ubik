#!/usr/bin/env python
#
# Copyright 2011 Lee Verberne <lee@blarg.org>
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
#

VERSION = "0.01"
DESCRIPTION='''\
dtrigger will monitor a queue directory for changes (i.e. a file being added to
the directory) and run an arbitrary command.'''

import logging
import optparse
import os
import select
import subprocess
import sys

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s")

log     = logging.getLogger()
options = None

from select import kqueue, kevent, \
    KQ_FILTER_VNODE, \
    KQ_EV_ADD, KQ_EV_CLEAR, KQ_EV_DELETE, \
    KQ_NOTE_WRITE

def init_options():
    global options

    parser = optparse.OptionParser(version=VERSION, description=DESCRIPTION,
        usage="%prog [options] -- directory trigger")
    parser.add_option("-d", "--debug", action="store_const", 
                      dest="loglevel", const=logging.DEBUG,
                      help="Enable debugging logging")
    parser.add_option("-v", "--verbose", action="store_const", 
                      dest="loglevel", const=logging.INFO,
                      help="Enable verbose logging")

    parser.disable_interspersed_args()
    (options, trigger) = parser.parse_args()
    options.directory = trigger.pop(0)
    options.command = trigger

    if options.loglevel:
        log.setLevel(options.loglevel)
    log.debug("Log level set to %s" % options.loglevel)
    log.info("dtrigger configured")
    log.info("Watching directory '%s'" % options.directory)
    log.info("Will run command '%s'" % ' '.join(options.command))

def kqueue_event_loop():
    kq = kqueue()
    fd = os.open(options.directory, os.O_RDONLY)

    don = kevent(fd, KQ_FILTER_VNODE, KQ_EV_ADD|KQ_EV_CLEAR, KQ_NOTE_WRITE)
    doff = kevent(fd, KQ_FILTER_VNODE, KQ_EV_DELETE, KQ_NOTE_WRITE)

    log.debug("kqueue intialized, entering event loop")
    while True:
        ev = kq.control([don,], 1)[0]
        if ev.ident == fd:
            log.debug("Received event %d on fd %s" % (ev.fflags, ev.ident))
            kq.control([doff,], 0)
            run_command()

def run_command():
    log.info("Running command '%s'" % ' '.join(options.command))
    retcode = subprocess.call(options.command)
    log.debug("Command returned %d" % retcode)

def main():
    init_options()

    # Enter event loop
    if select.kqueue:
        kqueue_event_loop()
    else:
        log.error("Currently only kqueue() is supported, "
                  "and this system doesn't support it")
        sys.exit(5)

if __name__ == '__main__':
    main()

