
import logging

import ubik.hats

from ubik.hats.base import BaseHat

log = logging.getLogger('ubik.hats.helper')

class HelperHat(BaseHat):
    "Return helpful messages"

    name = 'help'
    desc = "Display helpful messages"

    @staticmethod
    def areyou(string):
        "True/False am I described by <string>?"
        if string in ('help', 'wtf'):
            return True
        return False

    def help(self, out):
        '''Print help message to specified file object

        This method is called on an instance so that it can give help specific
        to the arguments that have been parsed by __init__()
        '''
        print >>out, "Usage: help [ command [ arguments ] ]"
        print >>out
        print >>out, "Use without arguments to get a command list"
        print >>out

    def __init__(self, argv, config=None, options=None):
        '''Figure out what we're helping with

        Helper is a unique in that it has to interact with other hats to do its
        job.  For that reason, this module re-invokes hats.hatter() to figure
        out what module needs helping.
        '''
        super(HelperHat, self).__init__(argv, config, options)
        mystery_argv = argv[1:]
        if len(mystery_argv) > 0:
            self.mystery = ubik.hats.hatter(mystery_argv, self.config,
                                            self.options)
            log.debug("Helper going to help with hat %s" % self.mystery.name)
        else:
            self.mystery = None

    def run(self):
        '''Prints help messages to the output file object'''
        if self.mystery:
            self._print_hat_help(self.output, self.mystery)
        else:
            self._print_hat_list(self.output)

    def _print_hat_list(self, out):
        print >>out, "The following commands are available:"
        print >>out

        for hat in sorted(ubik.hats.ALL_HATS, key=lambda h: h.name):
            print >>out, "%-8s - %s" % (hat.name, hat.desc)
        print >>out

    def _print_hat_help(self, out, whut):
        log.debug("Invoking help for %s" % whut.name)
        whut.help(out)
