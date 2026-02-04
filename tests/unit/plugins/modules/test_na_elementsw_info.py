''' unit tests for Ansible module: na_elementsw_info.py '''

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import inspect
import json
import pytest

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.community.solidfire.tests.unit.compat import unittest
from ansible_collections.community.solidfire.tests.unit.compat.mock import patch
import ansible_collections.community.solidfire.plugins.module_utils.netapp as netapp_utils
from unittest.mock import MagicMock

# Validation of HAS_SDK check is done in the module, so we mock it here
if not netapp_utils.has_sf_sdk():
    netapp_utils.solidfire = MagicMock()
    class MockApiConnectionError(Exception):
        pass
    netapp_utils.solidfire.common.ApiConnectionError = MockApiConnectionError
    netapp_utils.has_sf_sdk = lambda: True

from ansible_collections.community.solidfire.plugins.modules.na_elementsw_info \
    import ElementSWInfo as my_module  # module under test


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access
    basic._ANSIBLE_PROFILE = 'modern'


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""


def exit_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


NODE_ID1 = 777
NODE_ID2 = 888
NODE_ID3 = 999


class MockSFConnection(object):
    ''' mock connection to ElementSW host '''

    class Bunch(object):  # pylint: disable=too-few-public-methods
        ''' create object with arbitrary attributes '''
        def __init__(self, **kw):
            ''' called with (k1=v1, k2=v2), creates obj.k1, obj.k2 with values v1, v2 '''
            setattr(self, '__dict__', kw)

        def __repr__(self):
            results = dict()
            for key, value in vars(self).items():
                results[key] = repr(value)
            return repr(results)

        def to_json(self):
            return json.loads(json.dumps(self, default=lambda x: x.__dict__))

    def __init__(self, force_error=False, where=None):
        ''' save arguments '''
        self.force_error = force_error
        self.where = where
        self.nodes = [NODE_ID1, NODE_ID2, NODE_ID3]
        self._port = 442
        self.called = list()
        if force_error and where == 'cx':
            raise netapp_utils.solidfire.common.ApiConnectionError('testme')

    def record(self, args, kwargs):
        name = inspect.stack()[1][3]    # caller function name
        print('%s: , args: %s, kwargs: %s' % (name, args, kwargs))
        self.called.append(name)

    def list_accounts(self, *args, **kwargs):  # pylint: disable=unused-argument
        ''' build account list: account.username, account.account_id '''
        self.record(repr(args), repr(kwargs))
        accounts = list()
        accounts.append({'username': 'user1'})
        account_list = self.Bunch(accounts=accounts)
        return account_list

    def list_all_nodes(self, *args, **kwargs):  # pylint: disable=unused-argument
        ''' build all_node list: all_node.name, all_node.all_node_id '''
        self.record(repr(args), repr(kwargs))
        all_nodes = list()
        all_nodes.append({'id': 123})
        all_node_list = self.Bunch(all_nodes=all_nodes)
        return all_node_list

    def list_drives(self, *args, **kwargs):  # pylint: disable=unused-argument
        ''' build drive list: drive.name, drive.drive_id '''
        self.record(repr(args), repr(kwargs))
        drives = list()
        drives.append({'id': 123})
        drive_list = self.Bunch(drives=drives)
        return drive_list

    def list_initiators(self, *args, **kwargs):  # pylint: disable=unused-argument
        ''' build initiator list for cluster_initiators subset '''
        self.record(repr(args), repr(kwargs))
        initiators = list()
        initiators.append({
            'alias': 's194',
            'attributes': {'proxmox': True},
            'chapUsername': None,
            'initiatorID': 10,
            'initiatorName': 'iqn.1993-08.org.debian:01:3d6ce3bd67ac',
            'initiatorSecret': None,
            'requireChap': False,
            'targetSecret': None,
            'virtualNetworkIDs': [],
            'volumeAccessGroups': [1]
        })
        initiator_list = self.Bunch(initiators=initiators)
        return initiator_list

    def list_active_volumes(self, *args, **kwargs):  # pylint: disable=unused-argument
        ''' build active volume list '''
        self.record(repr(args), repr(kwargs))
        volumes = list()
        volumes.append({
            "access": "readWrite",
            "accountID": 1,
            "attributes": {},
            "blockSize": 4096,
            "createTime": "2026-02-02T05:17:38Z",
            "currentProtectionScheme": "singleHelix",
            "deleteTime": "",
            "enable512e": True,
            "enableSnapMirrorReplication": False,
            "iqn": "iqn.2010-01.com.solidfire:juut.import-raw-vol.716",
            "name": "import-raw-vol",
            "status": "active",
            "totalSize": 1073741824,
            "volumeID": 716,
        })
        volume_list = self.Bunch(volumes=volumes)
        return volume_list

    def list_deleted_volumes(self, *args, **kwargs):  # pylint: disable=unused-argument
        ''' build deleted volume list '''
        self.record(repr(args), repr(kwargs))
        volumes = list()
        volumes.append({
            "access": "readWrite",
            "accountID": 1,
            "attributes": {},
            "blockSize": 4096,
            "createTime": "2026-02-02T05:17:38Z",
            "currentProtectionScheme": "singleHelix",
            "deleteTime": "2026-02-04T05:17:38Z",
            "enable512e": True,
            "enableSnapMirrorReplication": False,
            "iqn": "iqn.2010-01.com.solidfire:juut.import-raw-vol.717",
            "name": "volume-deleted",
            "status": "deleted",
            "totalSize": 1073741824,
            "volumeID": 717,
        })
        volume_list = self.Bunch(volumes=volumes)
        return volume_list

    def get_config(self, *args, **kwargs):  # pylint: disable=unused-argument
        self.record(repr(args), repr(kwargs))
        if self.force_error and self.where == 'get_config_exception':
            raise ConnectionError
        if self.nodes is not None:
            nodes = ['%d:%s' % (i, node) for i, node in enumerate(self.nodes)]
        else:
            nodes = list()
        cluster = self.Bunch(ensemble=nodes, cluster='cl_name')
        config = self.Bunch(cluster=cluster)
        return self.Bunch(config=config)


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    ARGS = {
        # 'state': 'present',
        'hostname': 'hostname',
        'username': 'username',
        'password': 'password',
    }

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_all_default(self, mock_create_sf_connection):
        ''' gather all by default '''
        args = dict(self.ARGS)  # deep copy as other tests can modify args
        set_module_args(args)
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        assert not exc.value.args[0]['changed']
        assert 'cluster_accounts' in exc.value.args[0]['info']
        assert 'node_config' in exc.value.args[0]['info']
        username = exc.value.args[0]['info']['cluster_accounts']['accounts'][0]['username']
        assert username == 'user1'
        assert 'list_accounts' in my_obj.sfe_node.called
        assert 'get_config' in my_obj.sfe_node.called

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_all_all(self, mock_create_sf_connection):
        ''' gather all explictly '''
        args = dict(self.ARGS)  # deep copy as other tests can modify args
        args['gather_subsets'] = ['all']
        set_module_args(args)
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        assert not exc.value.args[0]['changed']
        assert 'list_accounts' in my_obj.sfe_node.called
        assert 'get_config' in my_obj.sfe_node.called

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_all_clusters(self, mock_create_sf_connection):
        ''' gather all cluster scoped subsets '''
        args = dict(self.ARGS)  # deep copy as other tests can modify args
        args['gather_subsets'] = ['all_clusters']
        set_module_args(args)
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        assert not exc.value.args[0]['changed']
        assert 'cluster_accounts' in exc.value.args[0]['info']
        accounts = exc.value.args[0]['info']['cluster_accounts']
        print('accounts: >>%s<<' % accounts, type(accounts))
        print(my_obj.sfe_node.called)
        assert 'list_accounts' in my_obj.sfe_node.called
        assert 'get_config' not in my_obj.sfe_node.called

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_all_nodes(self, mock_create_sf_connection):
        ''' gather all node scoped subsets '''
        args = dict(self.ARGS)  # deep copy as other tests can modify args
        args['gather_subsets'] = ['all_nodes']
        set_module_args(args)
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        assert not exc.value.args[0]['changed']
        assert 'node_config' in exc.value.args[0]['info']
        config = exc.value.args[0]['info']['node_config']
        print('config: >>%s<<' % config, type(config))
        print(my_obj.sfe_node.called)
        assert 'list_accounts' not in my_obj.sfe_node.called
        assert 'get_config' in my_obj.sfe_node.called

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_all_nodes_not_alone(self, mock_create_sf_connection):
        ''' gather all node scoped subsets but fail as another subset is present '''
        args = dict(self.ARGS)  # deep copy as other tests can modify args
        args['gather_subsets'] = ['all_nodes', 'dummy']
        set_module_args(args)
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        msg = 'no other subset is allowed'
        assert msg in exc.value.args[0]['msg']

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_filter_success(self, mock_create_sf_connection):
        ''' filter on key, value - succesful match '''
        args = dict(self.ARGS)  # deep copy as other tests can modify args
        args['gather_subsets'] = ['cluster_accounts']
        args['filter'] = dict(username='user1')
        set_module_args(args)
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        username = exc.value.args[0]['info']['cluster_accounts']['accounts'][0]['username']
        assert username == 'user1'

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_filter_bad_key(self, mock_create_sf_connection):
        ''' filter on key, value - key not found  '''
        args = dict(self.ARGS)  # deep copy as other tests can modify args
        args['gather_subsets'] = ['cluster_accounts']
        args['filter'] = dict(bad_key='user1')
        set_module_args(args)
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        msg = 'Error: key bad_key not found in'
        assert msg in exc.value.args[0]['msg']

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_filter_bad_key_ignored(self, mock_create_sf_connection):
        ''' filter on key, value - key not found - ignore error '''
        args = dict(self.ARGS)  # deep copy as other tests can modify args
        args['gather_subsets'] = ['cluster_accounts']
        args['filter'] = dict(bad_key='user1')
        args['fail_on_key_not_found'] = False
        set_module_args(args)
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        assert exc.value.args[0]['info']['cluster_accounts']['accounts'] == list()

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_filter_record_not_found(self, mock_create_sf_connection):
        ''' filter on key, value - no match '''
        args = dict(self.ARGS)  # deep copy as other tests can modify args
        args['gather_subsets'] = ['cluster_accounts']
        args['filter'] = dict(bad_key='user1')
        args['fail_on_key_not_found'] = False
        set_module_args(args)
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        assert exc.value.args[0]['info']['cluster_accounts']['accounts'] == list()

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_filter_record_not_found_error(self, mock_create_sf_connection):
        ''' filter on key, value - no match - force error on empty '''
        args = dict(self.ARGS)  # deep copy as other tests can modify args
        args['gather_subsets'] = ['cluster_accounts']
        args['filter'] = dict(username='user111')
        args['fail_on_record_not_found'] = True
        set_module_args(args)
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        msg = 'Error: no match for'
        assert msg in exc.value.args[0]['msg']

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_cluster_initiators_success(self, mock_create_sf_connection):
        ''' gather cluster_initiators subset '''
        args = dict(self.ARGS)
        args['gather_subsets'] = ['cluster_initiators']
        set_module_args(args)
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        assert 'cluster_initiators' in exc.value.args[0]['info']
        initiators = exc.value.args[0]['info']['cluster_initiators']['initiators']
        assert initiators[0]['alias'] == 's194'
        assert 'list_initiators' in my_obj.sfe_node.called

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_cluster_initiators_filter_success(self, mock_create_sf_connection):
        ''' filter on initiator alias - successful match '''
        args = dict(self.ARGS)
        args['gather_subsets'] = ['cluster_initiators']
        args['filter'] = dict(alias='s194')
        set_module_args(args)
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        initiators = exc.value.args[0]['info']['cluster_initiators']['initiators']
        assert initiators[0]['alias'] == 's194'

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_cluster_initiators_filter_bad_key_ignored(self, mock_create_sf_connection):
        ''' filter on bad key - ignored when fail_on_key_not_found is False '''
        args = dict(self.ARGS)
        args['gather_subsets'] = ['cluster_initiators']
        args['filter'] = dict(bad_key='x')
        args['fail_on_key_not_found'] = False
        set_module_args(args)
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['info']['cluster_initiators']['initiators'] == list()

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_cluster_initiators_filter_record_not_found_error(self, mock_create_sf_connection):
        ''' filter on alias with no match - force error on empty '''
        args = dict(self.ARGS)
        args['gather_subsets'] = ['cluster_initiators']
        args['filter'] = dict(alias='noexist')
        args['fail_on_record_not_found'] = True
        set_module_args(args)
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        msg = 'Error: no match for'
        assert msg in exc.value.args[0]['msg']

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_active_volumes_success(self, mock_create_sf_connection):
        ''' gather cluster_active_volumes subset '''
        args = dict(self.ARGS)
        args['gather_subsets'] = ['cluster_active_volumes']
        set_module_args(args)
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        assert 'cluster_active_volumes' in exc.value.args[0]['info']
        volumes = exc.value.args[0]['info']['cluster_active_volumes']['volumes']
        assert volumes[0]['name'] == 'import-raw-vol'
        assert volumes[0]['volumeID'] == 716
        assert 'list_active_volumes' in my_obj.sfe_node.called

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_info_deleted_volumes_success(self, mock_create_sf_connection):
        ''' gather cluster_deleted_volumes subset '''
        args = dict(self.ARGS)
        args['gather_subsets'] = ['cluster_deleted_volumes']
        set_module_args(args)
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print(exc.value.args[0])
        assert 'cluster_deleted_volumes' in exc.value.args[0]['info']
        volumes = exc.value.args[0]['info']['cluster_deleted_volumes']['volumes']
        assert volumes[0]['name'] == 'volume-deleted'
        assert volumes[0]['status'] == 'deleted'
        assert 'list_deleted_volumes' in my_obj.sfe_node.called

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_connection_error(self, mock_create_sf_connection):
        ''' filter on key, value - no match - force error on empty '''
        args = dict(self.ARGS)  # deep copy as other tests can modify args
        set_module_args(args)
        # force a connection exception
        mock_create_sf_connection.side_effect = netapp_utils.solidfire.common.ApiConnectionError('testme')
        with pytest.raises(AnsibleFailJson) as exc:
            my_module()
        print(exc.value.args[0])
        msg = 'Failed to create connection for hostname:442'
        assert msg in exc.value.args[0]['msg']

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_other_connection_error(self, mock_create_sf_connection):
        ''' filter on key, value - no match - force error on empty '''
        args = dict(self.ARGS)  # deep copy as other tests can modify args
        set_module_args(args)
        # force a connection exception
        mock_create_sf_connection.side_effect = KeyError('testme')
        with pytest.raises(AnsibleFailJson) as exc:
            my_module()
        print(exc.value.args[0])
        msg = 'Failed to connect for hostname:442'
        assert msg in exc.value.args[0]['msg']
