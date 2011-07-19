#!/usr/bin/python

# Command line front end to all these hats
DESCRIPTION='''\
This is the command line front end to a collection of platform control scripts
referred to herein as "hats".  I guess this could be a reference to the number
hats worn by your systems guru, but mainly I just needed a new namespace to
avoid collisions.  Also, NEW HAT!'''

import logging
import optparse

import ubik.hats

# Program Defaults
CONFFILE="~/.rug/rug.ini"
VERSION="0.0"

options = None

def init_cli(args=None):
    global options
    p = optparse.OptionParser(usage='%prog [global_options] THING HAT [ARG ...]',
                              version='%prog ' + VERSION,
                              description=DESCRIPTION,
                              epilog='Use the help sub-command for more '
                                     'details.')
    p.add_option('--conf', '-c', metavar='FILE', default=CONFFILE,
                 help='Use config FILE instead of %default')
    p.add_option('--debug', '-d', action='store_true',
                 help='Enable debug logging')
#    p.add_option('--workdir', metavar='DIR',
#                 help="Use DIR as working directory, creating if necessary")
    p.add_option('--verbose', '-v', action='store_true',
                 help='Enable verbose logging')
    p.disable_interspersed_args()
    (options, args) = p.parse_args(args=args)

    if options.debug:
        log.setLevel(logging.DEBUG)
    elif options.verbose:
        log.setLevel(logging.INFO)

    if len(args) == 0:
        args = ['help',]

    return args

def main(args=None):
    args = init_cli(args)

    # Try to figure out what hat we're using here
    hatstr = args.pop(0)
    hat = ubik.hats.hatter(hatstr, args)
    hat.run()

if __name__ == '__main__':
    main()

