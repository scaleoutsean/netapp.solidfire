''' unit test for Ansible module: na_elementsw_backup_s3.py '''

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

from ansible_collections.community.solidfire.plugins.modules.na_elementsw_backup_s3 import ElementSWBackupS3 as my_module  # module under test


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

    def start_bulk_volume_read(self, volume_id, fmt, script=None, script_parameters=None, attributes=None):
        # return an object with attributes similar to SDK
        return self.Bunch(async_handle=123, key='abc123', url='https://10.0.0.1:8443/')


class TestMyModule(unittest.TestCase):

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    @patch('ansible_collections.community.solidfire.plugins.module_utils.netapp.create_sf_connection')
    def test_backup_s3_basic(self, mock_create_sf_connection):
        args = dict(
            hostname='host', username='user', password='pw',
            src_volume_id=201,
            dest_s3_hostname='s3.my.org',
            dest_s3_access_key='ABC',
            dest_s3_secret_key='XYZ',
            dest_s3_destination_bucket='backups',
            format='native'
        )
        set_module_args(args)
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        assert exc.value.args[0]['key'] == 'abc123'
