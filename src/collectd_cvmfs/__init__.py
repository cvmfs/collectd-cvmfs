import collectd
import xattr
import os
import psutil
import time
import uuid

CVMFS_ROOT = '/cvmfs'
PLUGIN_NAME = 'cvmfs'

CONFIG_DEFAULT_MEMORY = True
CONFIG_DEFAULT_MOUNTTIME = True
CONFIG_DEFAULT_INTERVAL = -1

class CvmfsProbeConfig(object):
    def __init__(self):
        self.repos = []
        self.attributes = []
        self.memory = CONFIG_DEFAULT_MEMORY
        self.mounttime = CONFIG_DEFAULT_MOUNTTIME
        self.interval = CONFIG_DEFAULT_INTERVAL
        self.config_name = uuid.uuid4().hex
        self.verbose = False

    def __str__(self):
        return "CvmfsProbeConfig - Repos: {0} - Attributes: {1} - Memory: {2} - MountTime: {3} - Interval: {4} - ConfigName: {5} - Verbose: {6}".format(
            self.repos,
            self.attributes,
            self.memory,
            self.mounttime,
            "%ss" % self.interval if self.interval > 0 else "global interval",
            self.config_name,
            self.verbose
        )

class CvmfsProbe(object):
    def debug(self, msg, verbose=False):
        if verbose:
            collectd.info('{0} plugin: {1}'.format(PLUGIN_NAME, msg))

    def read_mounttime(self, repo_mountpoint):
        start = time.time()
        os.listdir(repo_mountpoint)
        end = time.time()
        return end - start

    def read(self, config):
        self.debug("probing config: {0}".format((config)), config.verbose)
        val = collectd.Values(plugin=PLUGIN_NAME)
        for repo in config.repos:
            val.plugin_instance = repo
            val.interval = config.interval
            repo_mountpoint = os.path.join(CVMFS_ROOT, repo)

            if config.mounttime:
                try:
                    val.dispatch(type='mounttime', values=[self.read_mounttime(repo_mountpoint)], interval=config.interval)
                except Exception:
                    collectd.warning('cvmfs: failed to get MountTime for repo %s' % repo)

            if config.memory:
                try:
                    repo_pid = int(xattr.getxattr(repo_mountpoint, 'user.pid'))
                    repo_mem = psutil.Process(repo_pid).get_memory_info()
                    val.dispatch(type='memory', type_instance='rss', values=[repo_mem.rss], interval=config.interval)
                    val.dispatch(type='memory', type_instance='vms', values=[repo_mem.vms], interval=config.interval)
                except Exception:
                    collectd.warning('cvmfs: failed to get Memory for repo %s' % repo)

            for attribute in config.attributes:
                attribute_name = "user.%s" % attribute
                try:
                    val.dispatch(type=attribute, values=[float(xattr.getxattr(repo_mountpoint, attribute_name))], interval=config.interval)
                except Exception:
                    collectd.warning('cvmfs: failed to inspect attribute "%s" in  repo "%s"' % (attribute_name, repo_mountpoint))

    def str2bool(self, boolstr):
        if boolstr.lower() == 'true':
            return True
        elif boolstr.lower() == 'false':
            return False
        else:
            raise TypeError('Boolean value expected.')


    def configure(self, conf):
        config = CvmfsProbeConfig()
        for node in conf.children:
            key = node.key.lower()
            if key == 'repo':
                config.repos += node.values
            elif key == 'attribute':
                config.attributes += node.values
            elif key == 'memory':
                try:
                    config.memory = self.str2bool(node.values[0])
                except:
                    collectd.info("cvmfs: Memory value %s is not valid. It must be either True or False" % (node.values[0]))
            elif key == 'mounttime':
                try:
                    config.mounttime = self.str2bool(node.values[0])
                except:
                    collectd.info("cvmfs: MountTime value %s is not valid. It must be either True or False" % (node.values[0]))
            elif key == 'interval':
                config.interval = int(node.values[0])
            elif key == 'verbose':
                config.verbose = self.str2bool(node.values[0])

        if config.interval > 0:
            collectd.register_read(callback=self.read, data=config, interval=config.interval, name=config.config_name)
        else:
            collectd.register_read(callback=self.read, data=config, name=config.config_name)

        collectd.info("cvmfs: configured callback with config: {0}".format(config))

probe = CvmfsProbe()
collectd.register_config(probe.configure)
