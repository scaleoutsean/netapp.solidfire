''' unit test for Ansible module: na_elementsw_group_snapshot.py '''

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import pytest

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.community.solidfire.tests.unit.compat import unittest
from ansible_collections.community.solidfire.tests.unit.compat.mock import patch
import ansible_collections.community.solidfire.plugins.module_utils.netapp as netapp_utils

if not netapp_utils.has_sf_sdk():
    pytestmark = pytest.mark.skip('skipping as missing required SolidFire Python SDK')

from ansible_collections.community.solidfire.plugins.modules.na_elementsw_group_snapshot \
    import ElementSWGroupSnapshot as my_module  # module under test


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)
    basic._ANSIBLE_PROFILE = 'modern'


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def exit_json(*args, **kwargs):
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class MockSFConnection(object):
    class Bunch(object):
        def __init__(self, **kw):
            setattr(self, '__dict__', kw)

    def __init__(self):
        pass

    def create_group_snapshot(self, volumes=None, name=None, enable_remote_replication=None, retention=None, attributes=None):
        members = []
        for v in volumes:
            members.append(self.Bunch(snapshotID=1000+v, volumeID=v))
        group = self.Bunch(groupSnapshotID=999, name=name, members=members)
        return self.Bunch(groupSnapshot=group)


class TestMyModule(unittest.TestCase):

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_create_group_snapshot(self, mock_create_sf_connection):
        args = dict(
            hostname='host', username='user', password='pw',
            volumes=[183,184,185], retention='0:5:5', attributes={'group_snap': True}
        )
        set_module_args(args)
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
