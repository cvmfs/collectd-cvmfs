import sys

import pytest
from mock import MagicMock, Mock, mock_open, patch

configure_data = [
    (["ams.cern.ch"], ["nioerr"], True, True, 30, 200),
    (["alice.cern.ch", "atlas.cern.ch", "cms.cern.cn"], ["ndownload", "nioerr", "usedfd"], False, False, 30, 200)
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
    with patch('collectd.register_read') as register_mock:
        probe_instance = collectd_cvmfs.CvmfsProbe()
        probe_instance.configure(Mock(children = []))

        collectd_cvmfs.collectd.register_read.assert_called_once

        args_sent = register_mock.call_args[1]
        probe_config = args_sent['data']
        assert probe_config.repos == []
        assert probe_config.attributes == []
        assert probe_config.memory == collectd_cvmfs.CONFIG_DEFAULT_MEMORY
        assert probe_config.mounttime == collectd_cvmfs.CONFIG_DEFAULT_MOUNTTIME
        assert probe_config.mounttimeout == collectd_cvmfs.CONFIG_DEFAULT_MOUNTTIMEOUT
        assert args_sent['name'] == probe_config.config_name
        assert args_sent['callback'] == probe_instance.read


@pytest.mark.parametrize("repos,attributes,memory,mounttime,mounttimeout,interval", configure_data)
def test_configure_single_ok(collectd_cvmfs, repos, attributes, memory, mounttime, mounttimeout, interval):
    # TODO: Simplify/fixturize the config init logic
    config = Mock()
    config.children = [
        Mock(key = 'Repo', values = repos),
        Mock(key = 'Attribute', values = attributes),
        Mock(key = 'Memory', values = [str(memory)]),
        Mock(key = 'MountTime', values = [str(mounttime)]),
        Mock(key = 'MountTimeout', values =[str(mounttimeout)]),
        Mock(key = 'Interval', values=[str(interval)])
    ]

    with patch('collectd.register_read') as register_mock:
        probe_instance = collectd_cvmfs.CvmfsProbe()
        probe_instance.configure(config)

        collectd_cvmfs.collectd.register_read.assert_called_once

        args_sent = register_mock.call_args[1]
        probe_config = args_sent['data']

        assert probe_config.repos == repos
        assert probe_config.attributes == attributes
        assert probe_config.memory == memory
        assert probe_config.mounttime == mounttime
        assert probe_config.mounttimeout == mounttimeout
        assert args_sent['name'] == probe_config.config_name
        assert args_sent['callback'] == probe_instance.read
        assert args_sent['interval'] == interval


@pytest.mark.parametrize("repos,attributes,memory,mounttime,mounttimeout,interval", configure_data)
def test_configure_multiple_ok(collectd_cvmfs, repos, attributes, memory, mounttime, mounttimeout, interval):
    # TODO: Simplify/fixturize the config init logic
    config = Mock()
    config.children = [Mock(key = 'Repo', values = [repo]) for repo in repos] + \
        [Mock(key = 'Attribute', values = [attr]) for attr in attributes] + \
        [Mock(key = 'Memory', values = [str(memory)]),
        Mock(key = 'MountTime', values = [str(mounttime)]),
        Mock(key = 'MountTimeout', values =[str(mounttimeout)]),
        Mock(key = 'Interval', values=[str(interval)])]

    with patch('collectd.register_read') as register_mock:
        probe_instance = collectd_cvmfs.CvmfsProbe()
        probe_instance.configure(config)

        collectd_cvmfs.collectd.register_read.assert_called_once

        args_sent = register_mock.call_args[1]
        probe_config = args_sent['data']

        assert probe_config.repos == repos
        assert probe_config.attributes == attributes
        assert probe_config.memory == memory
        assert probe_config.mounttime == mounttime
        assert args_sent['name'] == probe_config.config_name
        assert args_sent['callback'] == probe_instance.read
        assert args_sent['interval'] == interval


@pytest.mark.parametrize("strvalue,boolvalue", [("True", True), ("tRue", True), ("false", False), ("False", False)])
def test_str2bool_valid(collectd_cvmfs, strvalue, boolvalue):
    probe_instance = collectd_cvmfs.CvmfsProbe()
    assert probe_instance.str2bool(strvalue) == boolvalue


@pytest.mark.parametrize("strvalue", [("Si"), ("On"), ("Off"), ("Noooo")])
def test_str2bool_invalid(collectd_cvmfs, strvalue):
    probe_instance = collectd_cvmfs.CvmfsProbe()
    with pytest.raises(TypeError):
        probe_instance.str2bool(strvalue)


def test_read_empty(collectd_cvmfs):
    probe_instance = collectd_cvmfs.CvmfsProbe()
    probe_instance.configure(Mock(children = []))
    with patch('collectd.Values') as val_mock:
        probe_instance.read(collectd_cvmfs.CvmfsProbeConfig())
        val_mock.return_value.assert_not_called()


@pytest.mark.parametrize("repos,attributes,memory,mounttime, mounttimeout, interval", configure_data)
def test_read_ok(collectd_cvmfs, repos, attributes, memory, mounttime, mounttimeout, interval):
    # TODO: Simplify/fixturize the config init logic
    config = Mock()
    config.children = [
        Mock(key = 'Repo', values = repos),
        Mock(key = 'Attribute', values = attributes),
        Mock(key = 'Memory', values = [str(memory)]),
        Mock(key = 'MountTime', values = [str(mounttime)]),
        Mock(key = 'MountTimeout', values =[str(mounttimeout)]),
        Mock(key = 'Interval', values=[str(interval)])
    ]

    probe_instance = collectd_cvmfs.CvmfsProbe()
    probe_instance.configure(config)

    with patch('collectd.register_read') as register_mock:
        probe_instance.configure(config)
        probe_config = register_mock.call_args[1]['data']

        with patch('collectd_cvmfs.CvmfsProbe.read_mounttime', return_value=MOCK_METRICS_MOUNTTIME):
            with patch('xattr.getxattr', return_value=str(MOCK_METRICS_XATTR)):
                with patch('psutil.Process') as psutil_mock:
                    psutil_mock.return_value.get_memory_info.return_value = Mock(rss=MOCK_METRICS_MEM_RSS, vms=MOCK_METRICS_MEM_VMS)
                    with patch('collectd.Values') as val_mock:
                        probe_instance.read(probe_config)

                        collectd_cvmfs.collectd.Values.assert_called_once_with(plugin=collectd_cvmfs.PLUGIN_NAME)
                        if mounttime:
                            val_mock.return_value.dispatch.assert_any_call(type='mounttime', values=[MOCK_METRICS_MOUNTTIME], interval=probe_config.interval)
                            val_mock.return_value.dispatch.assert_any_call(type='mountok', values=[1], interval=probe_config.interval)
                        if memory:
                            psutil_mock.assert_any_call(MOCK_METRICS_XATTR)
                            val_mock.return_value.dispatch.assert_any_call(type='memory', type_instance='rss', values=[MOCK_METRICS_MEM_RSS], interval=probe_config.interval)
                            val_mock.return_value.dispatch.assert_any_call(type='memory', type_instance='vms', values=[MOCK_METRICS_MEM_VMS], interval=probe_config.interval)
                        for attr in attributes:
                            val_mock.return_value.dispatch.assert_any_call(type=attr, values=[MOCK_METRICS_XATTR], interval=probe_config.interval)


@pytest.mark.parametrize("repos,attributes,memory,mounttime,mounttimeout,interval", configure_data)
def test_read_mounttime_failed(collectd_cvmfs, repos, attributes, memory, mounttime, mounttimeout, interval):
    # TODO: Simplify/fixturize the config init logic
    config = Mock()
    config.children = [
        Mock(key = 'Repo', values = repos),
        Mock(key = 'Attribute', values = []),
        Mock(key = 'Memory', values = ["false"]),
        Mock(key = 'MountTime', values = [str(mounttime)]),
        Mock(key = 'MountTimeout', values =[str(mounttimeout)]),
        Mock(key = 'Interval', values=[str(interval)])
    ]

    probe_instance = collectd_cvmfs.CvmfsProbe()
    probe_instance.configure(config)

    with patch('collectd.register_read') as register_mock:
        probe_instance.configure(config)
        probe_config = register_mock.call_args[1]['data']

        with patch('collectd_cvmfs.CvmfsProbe.safe_scandir', side_effect=Exception('Catacroc!')):
            with patch('collectd.Values') as val_mock:
                probe_instance.read(probe_config)
                if mounttime:
                    val_mock.return_value.dispatch.assert_any_call(type='mountok', values=[0], interval=probe_config.interval)