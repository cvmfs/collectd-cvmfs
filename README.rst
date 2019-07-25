Collectd Module for CvmFS
=========================

Configuration
-------------

Example::

    TypesDB "/usr/share/collectd/collectd_cvmfs.db"
    <Plugin "python">
      Import "collectd_cvmfs"
      <Module "collectd_cvmfs">
        Repo "alice.cern.ch" "atlas.cern.ch"
        Repo "ams.cern.ch"
        MountTime True
        MountTimeout 10
        Memory True
        Attribute ndownload nioerr
        Attribute usedfd
        Verbose False
        Interval "300"
      </Module>
    </Plugin>

* ``TypesDB``: types used by the plugin and shipped with the package.
* ``Repo``: cvmfs repository to monitor.
* ``MountTime``: boolean value to specify whether mount time should be reported or not.
* ``MountTimeout``: timeout in seconds while trying to mount the repositories.
* ``Memory``: boolean value to specify whether the memory footprint should be reported or not.
* ``Attribute``: attribute to monitor on the given repositories. You can get the list from of valid attributes from the type db in ``resources/collectd_cvmfs.db``.
* ``Interval``: interval in seconds to probe the CVMFS repositories.
* ``Verbose``: boolean value to produce logs more verbosed in collectd. It is false by default.

The plugin allows multiple instances for different configurations. This allows probing different repos at different intervals or probing different attributes depending on the repository.

Metrics
-------

The metrics are published in the following structure::

    Plugin: cvmfs
    PluginInstance: <repo>
    Type: {<Attribute>|MountTime|Memory|Mountok}

    # Only with Memory:
    TypeInstance: [rss|vms]

Example::

    lxplus123.cern.ch/cvmfs-lhcb.cern.ch/mounttime values=[0.000999927520751953]
    lxplus123.cern.ch/cvmfs-lhcb.cern.ch/nioerr values=[0]
    lxplus123.cern.ch/cvmfs-lhcb.cern.ch/memory-rss values=[31760384]
    lxplus123.cern.ch/cvmfs-repo.domain.ch/mountok values=[1]
