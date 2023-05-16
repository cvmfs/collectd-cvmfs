import collectd
import xattr
import os
import psutil
import threading
import time
import uuid

try:
    from os import scandir
except ImportError:
    from scandir import scandir

CVMFS_ROOT = '/cvmfs'
PLUGIN_NAME = 'cvmfs'

CONFIG_DEFAULT_MEMORY = True
CONFIG_DEFAULT_MOUNTTIME = True
CONFIG_DEFAULT_INTERVAL = -1
CONFIG_DEFAULT_MOUNTTIMEOUT = 5

class CvmfsProbeConfig(object):
    def __init__(self):
        self.repos = []
        self.attributes = []
        self.memory = CONFIG_DEFAULT_MEMORY
        self.mounttime = CONFIG_DEFAULT_MOUNTTIME
        self.mounttimeout = CONFIG_DEFAULT_MOUNTTIMEOUT
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


    def safe_scandir(self, directory, timeout):
        contents = []
        t = threading.Thread(target=lambda: contents.extend(scandir(directory)))
        t.daemon = True
        t.start()
        t.join(timeout)
        if t.is_alive():
            raise Exception("Scandir timed out after {0} seconds".format(timeout))
        return contents


    def read_mounttime(self, repo_mountpoint, timeout):
        start = time.time()
        self.safe_scandir(repo_mountpoint, timeout)
        end = time.time()
        # Did we really mount it ?
        try:
          xattr.getxattr(repo_mountpoint, 'user.fqrn') == repo_mountpoint
          return end - start
        except:
          raise Exception("Repository was not mounted correctly")

    def read_memory(self, repo_mountpoint):
        repo_pid = int(xattr.getxattr(repo_mountpoint, 'user.pid'))
        process = psutil.Process(repo_pid)
        if callable(getattr(process, "get_memory_info", None)):
            return process.get_memory_info()
        else:
            return process.memory_info()

    def read(self, config):
        self.debug("probing config: {0}".format((config)), config.verbose)
        val = collectd.Values(plugin=PLUGIN_NAME)
        for repo in config.repos:
            val.plugin_instance = repo
            val.interval = config.interval
            repo_mountpoint = os.path.join(CVMFS_ROOT, repo)

            try:
                mounttime = self.read_mounttime(repo_mountpoint, config.mounttimeout)
                if config.mounttime:
                    val.dispatch(type='mounttime', values=[mounttime], interval=config.interval)
                    val.dispatch(type='mountok', values=[1], interval=config.interval)
            except Exception as e:
                collectd.warning('cvmfs: failed to get MountTime for repo %s: %s' % (repo, e))
                val.dispatch(type='mountok', values=[0], interval=config.interval)
                continue

            if config.memory:
                try:
                    repo_mem = self.read_memory(repo_mountpoint)
                    val.dispatch(type='memory', type_instance='rss', values=[repo_mem.rss], interval=config.interval)
                    val.dispatch(type='memory', type_instance='vms', values=[repo_mem.vms], interval=config.interval)
                except Exception:
                    collectd.warning('cvmfs: failed to get Memory for repo %s' % repo)
                    val.dispatch(type='memory', type_instance='rss', values=[0], interval=config.interval)
                    val.dispatch(type='memory', type_instance='vms', values=[0], interval=config.interval)
                    continue

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
            elif key == 'mounttimeout':
                config.mounttimeout = int(node.values[0])
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
