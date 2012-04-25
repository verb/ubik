
import logging
import os.path
import subprocess
import tempfile

import ubik.builder
import ubik.cache
import ubik.defaults
import ubik.packager

from fabric.api import local, prompt, put, run, settings
from fabric.state import connections

from ubik.hats import HatException
from ubik.hats.base import BaseHat

log = logging.getLogger('ubik.hats.deploy')

PKGTYPES = ('deb', 'rpm')
PKG_INSTALL_CMD = {
    'deb': "fakeroot dpkg -i",
    'rpm': "rpm -U --oldpackage",
}

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
        log.debug("hosts to deploy: %s", hosts)

        # Determine the package types we need
        pkgpath = dict.fromkeys([h.pkgtype() for h in hosts])
        log.debug("pkg types to deploy: %s", pkgpath.keys())
        
        cache = self._get_package_cache()
        self._add_package_config(name)
        for pkgtype in pkgpath:
            filename = cache.get(name=name, version=version, type=pkgtype)

            # 'name' could be the package config name rather than the actual
            # package name, so we should try dereferencing using build config
            if not filename:
                try:
                    pkgname = self.config.get('package', 'name')
                    filename = cache.get(name=pkgname, version=version, 
                                         type=pkgtype)
                except:
                    pass

            if filename:
                pkgpath[pkgtype] = filename
            else:
                log.error("Package for %s doesn't exist.  Please build.",
                          pkgtype)

        print >>self.output, "About to deploy the following packages:"
        for pkgname in pkgpath.values():
            print >>self.output, "\t%s" % pkgname
        print >>self.output, "To the following hosts:"
        for host in hosts:
            print >>self.output, "\t%s" % host
        yesno = prompt("Proceed?", default='No')
        if yesno.strip()[0].upper() != 'Y':
            return

        deploy_user = self.config.get('deploy', 'user')
        try:
            for host in hosts:
                host_pkgtype = host.pkgtype()
                host_pkgpath = pkgpath[host_pkgtype]
                host_pkgfilename = os.path.basename(host_pkgpath)

                with settings(host_string=str(host), user=deploy_user):
                    fab_output = run("mkdir -p pkgs/", shell=False)
                    if fab_output:
                        print >>self.output, fab_output
                    put(host_pkgpath, "pkgs/")

                    pkg_delete = True
                    if host_pkgtype in PKG_INSTALL_CMD.keys():
                        output = run(PKG_INSTALL_CMD[host_pkgtype] + " pkgs/%s"
                                     % host_pkgfilename, shell=False)
                    else:
                        fab_output = ("Unable to determine install command for "
                                      "package type %s.  Leaving package "
                                      "~%s/pkgs/%s for manual install." %
                                      (host_pkgtype, deploy_user, 
                                       host_pkgfilename))
                        pkg_delete = False
                    if fab_output:
                        print >>self.output, fab_output

                    if pkg_delete:
                        fab_output = run("rm pkgs/" + host_pkgfilename, shell=False)
                        if fab_output:
                            print >>self.output, fab_output
        finally:
            # TODO: replace with disconnect_all() w/ fabric 0.9.4+
            for key in connections.keys():
                connections[key].close()
                del connections[key]

    command_list = ( deploy, )

if __name__ == '__main__':
    DeployHat(())

