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

NAME = "qmon"
VERSION = "0.01"
DESCRIPTION='''\
qmon will monitor a queue directory for changes (i.e. a file being added to
the directory) and run an arbitrary command on that file.'''

import logging, logging.handlers
import optparse
import os, os.path
import select
import signal
import subprocess
import sys
import time

log     = None
options = None

from select import kqueue, kevent, \
    KQ_FILTER_SIGNAL, KQ_FILTER_VNODE, \
    KQ_EV_ADD, KQ_EV_CLEAR, KQ_EV_DELETE, \
    KQ_NOTE_ATTRIB, KQ_NOTE_DELETE, KQ_NOTE_RENAME, KQ_NOTE_WRITE

def init_logging():
    global log

    log = logging.getLogger(NAME)
    if options.loglevel:
        log.setLevel(options.loglevel)

    fmt = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
    if options.foreground or not (options.logfile or options.syslog):
        h = logging.StreamHandler()
        h.setFormatter(fmt)
        log.addHandler(h)
    if options.logfile:
        h = logging.FileHandler(options.logfile)
        h.setFormatter(fmt)
        log.addHandler(h)
    if options.syslog:
        h = logging.handlers.SysLogHandler('/dev/log','user')
        h.setFormatter(fmt)
        log.addHandler(h)

    log.debug("Log level set to %s" % options.loglevel)
    log.info(NAME + " configured")
    log.info("Watching directory '%s'" % options.directory)
    log.info("Will run command '%s'" % ' '.join(options.command))

def init_options():
    global options

    parser = optparse.OptionParser(version=VERSION, description=DESCRIPTION,
        usage="%prog [options] -- directory trigger")
    parser.add_option("--age", action="store", type="int", default=5,
                      help="Age of file in seconds before it will be processed")
    parser.add_option("-d", "--debug", action="store_const", 
                      dest="loglevel", const=logging.DEBUG,
                      help="Enable debugging logging")
    parser.add_option("-n", "--foreground", action="store_true", 
                      help="Stay in the foreground and log to stdout")
    parser.add_option("--logfile", action="store",
                      help="Log %s messages to LOGFILE" % NAME)
    parser.add_option("--syslog", action="store_true", 
                      help="Log to syslog")
    parser.add_option("-v", "--verbose", action="store_const", 
                      dest="loglevel", const=logging.INFO,
                      help="Enable verbose logging")

    parser.disable_interspersed_args()
    (options, trigger) = parser.parse_args()
    options.directory = trigger.pop(0)
    options.command = trigger.pop(0)

def kevent_unlink(fd):
    return kevent(fd, KQ_FILTER_VNODE, KQ_EV_ADD|KQ_EV_CLEAR,
                  KQ_NOTE_DELETE|KQ_NOTE_RENAME)

def kqueue_event_loop():
    kq = kqueue()
    dirfd = os.open(options.directory, os.O_RDONLY)
    os.chdir(options.directory)

    kev_in = [kevent(dirfd, KQ_FILTER_VNODE, KQ_EV_ADD|KQ_EV_CLEAR, 
                     KQ_NOTE_WRITE|KQ_NOTE_ATTRIB),]
    # Touching the directory generates an initial event so that the
    # event loop will scan for new files
    kq.control(kev_in, 0)
    os.utime(options.directory, None)

    kev_in = [kevent(signal.SIGCHLD, KQ_FILTER_SIGNAL, KQ_EV_ADD),]
    fn2fd = {}
    fd2fn = {}
    files_to_run = []
    child_running = False
    log.debug("kqueue intialized, entering event loop")
    while True:
        if len(fn2fd) == 0:
            kev_out = kq.control(kev_in, 5)
        else:
            kev_out = kq.control(kev_in, 5, 1)
        kev_in = []

        now = time.time()
        for kev in kev_out:
            # First check if this is a SIGCHLD event, which means our child
            # process has exited.
            if kev.filter == KQ_FILTER_SIGNAL and kev.ident == signal.SIGCHLD:
                child_running = False
            # Next we're concerned about a VNODE event on the directory, which
            # could signal that the dir ents have changed
            elif kev.filter == KQ_FILTER_VNODE and kev.ident == dirfd:
                log.debug("Received event %d on fd %s" % 
                          (kev.fflags, kev.ident))
                log.debug("Checking for new files")
                for A,B,files in os.walk(options.directory):
                    break
                for fn in files:
                    if not fn in fn2fd:
                        log.debug("Found new file: %s" % fn)
                        try:
                            fd = os.open(fn, os.O_RDONLY)
                        except OSError as e:
                            log.warning("Couldn't track file %s: %s" %
                                        (fn, str(e)))
                        else:
                            fn2fd[fn] = fd
                            fd2fn[fn2fd[fn]] = fn
                            kev_in.append(kevent_unlink(fn2fd[fn]))
                            files_to_run.append(fn)
            # This is a VNODE event on one of the files in the directory we're
            # following.  If the file is removed or renamed we can stop
            # tracking it
            elif (kev.filter == KQ_FILTER_VNODE and
                  kev.fflags & KQ_NOTE_DELETE|KQ_NOTE_RENAME):
                # A file was unlinked, but not necessarily from this dir
                log.debug("Received event on fd %s" % kev.ident)
                if kev.ident in fd2fn:
                    fn = fd2fn[kev.ident]
                    if not os.path.exists(fn):
                        log.debug("File %s was removed" % fn)
                        os.close(kev.ident)     # Also removes from kqueue
                        if fn in files_to_run:
                            files_to_run.remove(fn)
                        del fn2fd[fn]
                        del fd2fn[kev.ident]
                else:
                    log.warning("Got unlink event on untracked file.  Guh.")
            log.debug("File list is: " + repr(fd2fn))

        # See if any of these files are old enough to process
        # TODO: stop stating the files and use kevent to keep track of when it
        # was last updated
        if len(kev_out) == 0 and not child_running and len(files_to_run) > 0:
            log.debug("Checking for mature files")
            log.debug("Run list is: " + repr(files_to_run))
            for fn in files_to_run:
                try:
                    if os.stat(fn).st_mtime < now - options.age:
                        files_to_run.remove(fn)
                        child_running = True
                        run_command(fn)
                        break
                except OSError as e:
                    log.warning("Problem finding %s: %s" % (fn, str(e)))

def run_command(filename):
    log.info("Running command '%s %s'" % (options.command, filename))
    retcode = subprocess.call([options.command, filename])
    log.debug("Command returned %d" % retcode)

def main():
    init_options()
    init_logging()

    # Enter event loop
    if select.kqueue:
        kqueue_event_loop()
    else:
        log.error("Currently only kqueue() is supported, "
                  "and this system doesn't support it")
        sys.exit(5)

if __name__ == '__main__':
    main()

