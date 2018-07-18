import sys

import pytest
from mock import MagicMock, Mock, mock_open, patch

configure_data = [
    (["ams.cern.ch"], ["nioerr"], True, True, 200),
    (["alice.cern.ch", "atlas.cern.ch", "cms.cern.cn"], ["ndownload", "nioerr", "usedfd"], False, False, 200)
]

MOCK_METRICS_XATTR = 2
MOCK_METRICS_MOUNTTIME = 0.1
MOCK_METRICS_MEM_RSS = 1000
MOCK_METRICS_MEM_VMS = 2000

@pytest.fixture
def collectd_cvmfs():
    collectd = MagicMock()
    with patch.dict('sys.modules', {'collectd': collectd}):
        import collectd_cvmfs
        yield collectd_cvmfs

@pytest.fixture
def config():
    pass

def test_configure_defaults(collectd_cvmfs):
    collectd_cvmfs.configure(Mock(children = []))

    assert collectd_cvmfs.REPOS == collectd_cvmfs.CONFIG_DEFAULT_REPOS
    assert collectd_cvmfs.ATTRIBUTES == collectd_cvmfs.CONFIG_DEFAULT_ATTRIBUTES
    assert collectd_cvmfs.MEMORY == collectd_cvmfs.CONFIG_DEFAULT_MEMORY
    assert collectd_cvmfs.MOUNTTIME == collectd_cvmfs.CONFIG_DEFAULT_MOUNTTIME

    collectd_cvmfs.collectd.register_read.assert_called_once_with(collectd_cvmfs.read)

@pytest.mark.parametrize("repos,attributes,memory,mounttime,interval", configure_data)
def test_configure_single_ok(collectd_cvmfs, repos, attributes, memory, mounttime, interval):
    # TODO: Simplify/fixturize the config init logic
    config = Mock()
    config.children = [
        Mock(key = 'Repo', values = repos),
        Mock(key = 'Attribute', values = attributes),
        Mock(key = 'Memory', values = [str(memory)]),
        Mock(key = 'MountTime', values = [str(mounttime)]),
        Mock(key = 'Interval', values=[str(interval)])
    ]

    collectd_cvmfs.configure(config)

    assert collectd_cvmfs.REPOS == repos
    assert collectd_cvmfs.ATTRIBUTES == attributes
    assert collectd_cvmfs.MEMORY == memory
    assert collectd_cvmfs.MOUNTTIME == mounttime

    collectd_cvmfs.collectd.register_read.assert_called_once_with(collectd_cvmfs.read, interval)

@pytest.mark.parametrize("repos,attributes,memory,mounttime,interval", configure_data)
def test_configure_multiple_ok(collectd_cvmfs, repos, attributes, memory, mounttime, interval):
    # TODO: Simplify/fixturize the config init logic
    config = Mock()
    config.children = [Mock(key = 'Repo', values = [repo]) for repo in repos] + \
        [Mock(key = 'Attribute', values = [attr]) for attr in attributes] + \
        [Mock(key = 'Memory', values = [str(memory)]),
        Mock(key = 'MountTime', values = [str(mounttime)]),
        Mock(key = 'Interval', values=[str(interval)])]

    collectd_cvmfs.configure(config)

    assert collectd_cvmfs.REPOS == repos
    assert collectd_cvmfs.ATTRIBUTES == attributes
    assert collectd_cvmfs.MEMORY == memory
    assert collectd_cvmfs.MOUNTTIME == mounttime

    collectd_cvmfs.collectd.register_read.assert_called_once_with(collectd_cvmfs.read, interval)


@pytest.mark.parametrize("strvalue,boolvalue", [("True", True), ("tRue", True), ("false", False), ("False", False)])
def test_str2bool_valid(collectd_cvmfs, strvalue, boolvalue):
    assert collectd_cvmfs.str2bool(strvalue) == boolvalue


@pytest.mark.parametrize("strvalue", [("Si"), ("On"), ("Off"), ("Noooo")])
def test_str2bool_invalid(collectd_cvmfs, strvalue):
    with pytest.raises(TypeError):
        collectd_cvmfs.str2bool(strvalue)


def test_read_empty(collectd_cvmfs):
    collectd_cvmfs.configure(Mock(children = []))
    with patch('collectd.Values') as val_mock:
        collectd_cvmfs.read()
        val_mock.return_value.assert_not_called()


@pytest.mark.parametrize("repos,attributes,memory,mounttime,interval", configure_data)
def test_read_ok(collectd_cvmfs, repos, attributes, memory, mounttime, interval):
    # TODO: Simplify/fixturize the config init logic
    config = Mock()
    config.children = [
        Mock(key = 'Repo', values = repos),
        Mock(key = 'Attribute', values = attributes),
        Mock(key = 'Memory', values = [str(memory)]),
        Mock(key = 'MountTime', values = [str(mounttime)]),
        Mock(key = 'Interval', values=[str(interval)])
    ]

    collectd_cvmfs.configure(config)

    with patch('collectd_cvmfs.read_mounttime', return_value=MOCK_METRICS_MOUNTTIME):
        with patch('xattr.getxattr', return_value=str(MOCK_METRICS_XATTR)):
            with patch('psutil.Process') as psutil_mock:
                with patch('collectd.Values') as val_mock:
                    psutil_mock.return_value.get_memory_info.return_value = Mock(rss=MOCK_METRICS_MEM_RSS, vms=MOCK_METRICS_MEM_VMS)
                    collectd_cvmfs.read()

                    collectd_cvmfs.collectd.Values.assert_called_once_with(plugin=collectd_cvmfs.PLUGIN_NAME)
                    if mounttime:
                        val_mock.return_value.dispatch.assert_any_call(type='mounttime', values=[MOCK_METRICS_MOUNTTIME])
                    if memory:
                        psutil_mock.assert_any_call(MOCK_METRICS_XATTR)
                        val_mock.return_value.dispatch.assert_any_call(type='memory', type_instance='rss', values=[MOCK_METRICS_MEM_RSS])
                        val_mock.return_value.dispatch.assert_any_call(type='memory', type_instance='vms', values=[MOCK_METRICS_MEM_VMS])
                    for attr in attributes:
                        val_mock.return_value.dispatch.assert_any_call(type=attr, values=[MOCK_METRICS_XATTR])