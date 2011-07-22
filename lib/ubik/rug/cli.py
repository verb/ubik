#!/usr/bin/python

# Command line front end to all these hats
DESCRIPTION='''\
This is the command line front end to a collection of platform control scripts
referred to herein as "hats".  I guess this could be a reference to the number
hats worn by your systems guru, but mainly I just needed a new namespace to
avoid collisions.  Also, NEW HAT!'''

import logging
import optparse
import os
import sys

import ubik.config
import ubik.defaults
import ubik.hats

config = ubik.config.UbikConfig()
options = None
log = logging.getLogger('rug.cli')

def init_cli(args=None):
    global config, options
    p = optparse.OptionParser(usage='%prog [global_options] THING HAT [ARG ...]',
                              version='%prog ' + ubik.defaults.VERSION,
                              description=DESCRIPTION,
                              epilog='Use the help sub-command for more '
                                     'details.')
    p.add_option('--conf', '-c', metavar='FILE',
                 default=ubik.defaults.CONFIG_FILE,
                 help='Use config FILE instead of %default')
    p.add_option('--debug', '-d', action='store_true',
                 help='Enable debug logging')
#    p.add_option('--workdir', metavar='DIR',
#                 help="Use DIR as working directory, creating if necessary")
    p.add_option('--verbose', '-v', action='store_true',
                 help='Enable verbose logging')
    p.disable_interspersed_args()
    (options, args) = p.parse_args(args=args)

    if 'DEBUG' in os.environ:
        options.debug = True
    if options.debug:
        log.setLevel(logging.DEBUG)
    elif options.verbose:
        log.setLevel(logging.INFO)

    if 'RUG_GLOBAL_CONFIG' in os.environ:
        global_cf = os.environ['RUG_GLOBAL_CONFIG']
    else:
        global_cf = ubik.defaults.GLOBAL_CONFIG_FILE
    config.read(options.conf, global_cf)

    if len(args) == 0:
        args = ['help',]

    return args

def main(args=None):
    args = init_cli(args)

    # Try to figure out what hat we're using here
    hatstr = args.pop(0)
    hat = ubik.hats.hatter(hatstr, args, config, options)
    try:
        hat.run()
    except ubik.hats.HatException as e:
        print >>sys.stderr, "ERROR:", str(e)
        if options.debug:
            raise e

if __name__ == '__main__':
    main()

