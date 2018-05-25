Collectd Module for CvmFS
=========================

Configuration
-------------

Example::

    <Plugin "python">

      Import "collectdcvmfs"

      <Module "collectdcvmfs">
        Repo "alice.cern.ch" "atlas.cern.ch"
        Repo "ams.cern.ch"

        MountTime True
        Memory True

        Attribute ndownload nioerr
        Attribute usedfd

        Interval "300"
      </Module>

    </Plugin>


* ``Repo``: cvmfs repository to monitor.
* ``MountTime``: boolean value to specify whether mount time should be reported or not.
* ``Memory``: boolean value to specify whether the memory footprint should be reported or not.
* ``Attribute``: attribute to monitor on the given repositories. You can get the list from of valid attributes from the type db in ``resources/collectdcvmfs.db``.
* ``Interval``: interval in seconds to probe the CVMFS repositories.

Metrics
-------

The metrics are published in the following structure::

    Plugin: cvmfs
    PluginInstance: <repo>
    Type: {<Attribute>|MountTime|Memory}
    
    # Only with Memory:
    TypeInstance: [rss|vms]


Example::

    lxplus123.cern.ch/cvmfs-lhcb.cern.ch/mounttime values=[0.000999927520751953]
    lxplus123.cern.ch/cvmfs-lhcb.cern.ch/nioerr values=[0]
    lxplus123.cern.ch/cvmfs-lhcb.cern.ch/memory-rss values=[31760384]
