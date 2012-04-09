
import logging
import os.path
import subprocess
import tempfile

import ubik.builder
import ubik.cache
import ubik.defaults
import ubik.packager

from ubik.hats import HatException
from ubik.hats.base import BaseHat

log = logging.getLogger('ubik.hats.deploy')

PKGTYPES = ('deb', 'rpm')

class DeployHat(BaseHat):
    "Deployer Hat"

    name = 'deploy'
    desc = "Deploy Software"

    @staticmethod
    def areyou(string):
        "Confirm or deny whether I am described by string"
        return string == DeployHat.name

    def __init__(self, argv, config=None, options=None):
        super(DeployHat, self).__init__(argv, config, options)
        self.args = argv[1:]

    def run(self):
        if self.args[0] == 'help' or len(self.args) < 2:
            self.help(self.output)
        else:
            self.deploy()

    # deploy sub-commands
    def deploy(self):
        '''deploy APP VERSION [ HOST [ HOST ... ] ]

        Deploys an application to a list of hosts.  If hosts are omitted, 
        attempts to determine host list automatically.
        '''
        import pdb; pdb.set_trace()
        name, version = self.args[0:2]

        # Determine receiving hosts
        hostnames = self.args[2:]
        idb = self._get_infradb()
        hosts = None
        if hostnames:
            hosts = idb.hosts(hostnames)
        else:
            try:
                service = idb.service(name)
                hosts = service.hosts()
            except ubik.infra.db.InfraDBException:
                pass
        if not hosts:
            raise HatException("Could not determine hosts for deploy")
        
        # First thing is to build the deploy
        if self.options.workdir:
            workdir = self.options.workdir
        else:
            workdir = tempfile.mkdtemp(prefix='deployer-bob-')
        bob = ubik.builder.Builder(self.config, workdir)
        bob.build_from_config(name, version)

        cache_dir = self.config.get('cache', 'dir')
        cache = ubik.cache.UbikDeployCache(cache_dir)
        for pkgtype in pkgtypes_to_build:
            # After the build_from_config() call above, self.config will contain
            # all of the configuration for this deploy
            if self.config.has_section(pkgtype):
                pkgr = ubik.deployr.Deploy(bob.pkgcfg, bob.env, pkgtype)
                pkgfile = pkgr.build(version)
                log.debug("Successfully created deploy file %s", pkgfile)
                cache.add(pkgfile, type=pkgtype, version=version)
            else:
                logf = log.info if len(pkgtypes_to_build) > 1 else log.error
                logf("Config files does not specify deploy type '%s'",
                     pkgtype)

        if not (self.options.debug or self.options.workdir):
            log.info("Removing working directory '%s'", workdir)
            subprocess.check_call(('rm', '-r', workdir))

    command_list = ( deploy, )

if __name__ == '__main__':
    DeployHat(())

