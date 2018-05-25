import collectd
import xattr
import os
import psutil
import time


CVMFS_ROOT = '/cvmfs'
PLUGIN_NAME = 'cvmfs'


def read_mounttime(repo_mountpoint):
    start = time.time()
    os.listdir(repo_mountpoint)
    end = time.time()
    return end - start

def read():
    val = collectd.Values(plugin=PLUGIN_NAME)
    for repo in REPOS:
        val.plugin_instance = repo
        repo_mountpoint = os.path.join(CVMFS_ROOT, repo)

        if MOUNTTIME:
            try:
                val.dispatch(type='mounttime', values=[read_mounttime(repo_mountpoint)])
            except Exception:
                collectd.warning('cvmfs: failed to get MountTime for repo %s' % repo)

        if MEMORY:
            try:
                repo_pid = int(xattr.getxattr(repo_mountpoint, 'user.pid'))
                repo_mem = psutil.Process(repo_pid).get_memory_info()
                val.dispatch(type='memory', type_instance='rss', values=[repo_mem.rss])
                val.dispatch(type='memory', type_instance='vms', values=[repo_mem.vms])
            except Exception:
                collectd.warning('cvmfs: failed to get Memory for repo %s' % repo)

        for attribute in ATTRIBUTES:
            attribute_name = "user.%s" % attribute
            try:
                val.dispatch(type=attribute, values=[float(xattr.getxattr(repo_mountpoint, attribute_name))])
            except Exception:
                collectd.warning('cvmfs: failed to inspect attribute "%s" in  repo "%s"' % (attribute_name, repo_mountpoint))


def str2bool(boolstr):
    if boolstr.lower() == 'true':
        return True
    elif boolstr.lower() == 'false':
        return False
    else:
        raise TypeError('Boolean value expected.')


def configure(conf):
    global REPOS, ATTRIBUTES, MEMORY, MOUNTTIME
    REPOS = []
    ATTRIBUTES = []
    MEMORY = True
    MOUNTTIME = True
    for node in conf.children:
        key = node.key.lower()
        if key == 'repo':
            REPOS += node.values
        elif key == 'attribute':
            ATTRIBUTES += node.values
        elif key == 'memory':
            try:
                MEMORY = str2bool(node.values[0])
            except:
                collectd.info("cvmfs: Memory value %s is not valid. It must be either True or False" % (node.values[0]))
        elif key == 'mounttime':
            try:
                MOUNTTIME = str2bool(node.values[0])
            except:
                collectd.info("cvmfs: MountTime value %s is not valid. It must be either True or False" % (node.values[0]))
        elif key == 'interval':
            interval=int(node.values[0])

    try:
        collectd.register_read(read, interval)
    except NameError:
        collectd.register_read(read)

    collectd.info("cvmfs: plugin configured to monitor %s in %s using %s." % (ATTRIBUTES, REPOS, "%ss interval" % interval if 'interval' in locals() else "global interval"))


collectd.register_config(configure)

