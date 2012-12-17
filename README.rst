ubik
====

Collection of things that do various other things.  Right now that means some
libraries and a single CLI utility named ``rug``.

These things have generally been written for (2.6 <= python < 3)

rug
---

rug scratched an itch for developers that wanted OS package semantics for
software deploys and a system administrator that wanted insulation against
inexperienced developers clobbering system files with OS-level packages.

It turned out to also be useful for building OS packages in situations where
the assumptions made by the existing debian build utilities were unsound.

rug provides the following

    * Package builds from config fetched locally or from a remote server
    * Deploys via python Fabric_
    * Lookup against an infra hosts/services database stored via DNS or JSON
    * Interact with a supervisord_ process running on remote hosts
    * Plus, it really ties the room together.

.. _Fabric: http://docs.fabfile.org
.. _supervisord: http://supervisord.org
