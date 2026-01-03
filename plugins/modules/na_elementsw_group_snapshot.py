#!/usr/bin/python
"""Create Group Snapshot for NetApp ElementSW"""

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'certified',
}

DOCUMENTATION = '''

module: na_elementsw_group_snapshot

short_description: NetApp Element Software Create Group Snapshot
extends_documentation_fragment:
    - community.solidfire.netapp.solidfire
version_added: 20.10.0
author: NetApp Ansible Team
description:
  - Create a group snapshot across multiple volumes.

options:
  volumes:
    description:
      - List of volume IDs or names to include in the group snapshot. Volume IDs must be integers or numeric strings.
      - If volume names are used, provide `account_id` so names can be resolved to IDs.
    required: true
    type: list
    elements: str

  name:
    description:
      - Optional name for the group snapshot. If omitted, a timestamp-based name is used.
    type: str

  enable_remote_replication:
    description:
      - Whether to enable remote replication for the created snapshots.
    type: bool

  retention:
    description:
      - Retention period as an HH:mm:ss string.
    type: str

  attributes:
    description:
      - Optional attributes to store with the group snapshot.
    type: dict

  account_id:
    description:
      - Optional account id or name to resolve volume names to IDs. Required when using volume names.
    type: str

'''

EXAMPLES = '''
  - name: Create group snapshot
    na_elementsw_group_snapshot:
      hostname: "{{ elementsw_hostname }}"
      username: "{{ elementsw_username }}"
      password: "{{ elementsw_password }}"
      volumes: [183,184,185]
      retention: "0:5:5"
      attributes:
        group_snap: true

'''

RETURN = '''
group_snapshot:
  description: The group snapshot object returned by the API.
  returned: success
  type: dict

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import traceback
import ansible_collections.community.solidfire.plugins.module_utils.netapp as netapp_utils
from ansible_collections.community.solidfire.plugins.module_utils.netapp_elementsw_module import NaElementSWModule

HAS_SF_SDK = netapp_utils.has_sf_sdk()


class ElementSWGroupSnapshot(object):
    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(
            dict(
                volumes=dict(required=True, type='list', elements='str'),
                name=dict(required=False, type='str', default=None),
                enable_remote_replication=dict(required=False, type='bool', default=False),
                retention=dict(required=False, type='str', default=None),
                attributes=dict(required=False, type='dict', default=None),
                account_id=dict(required=False, type='str', default=None),
            )
        )

        self.module = AnsibleModule(argument_spec=self.argument_spec, supports_check_mode=True)

        params = self.module.params
        self.volumes = params['volumes']
        self.name = params['name']
        self.enable_remote_replication = params['enable_remote_replication']
        self.retention = params['retention']
        self.attributes = params['attributes']
        self.account_id = params.get('account_id')

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        try:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)
        except Exception as exc:
            self.module.fail_json(msg='Failed to create SDK connection: %s' % to_native(exc))

        self.elementsw_helper = NaElementSWModule(self.sfe)

    def resolve_volume_ids(self):
        resolved = []
        for v in self.volumes:
            # numeric ids: accept directly
            if isinstance(v, int) or (isinstance(v, str) and str(v).isdigit()):
                resolved.append(int(v))
                continue

            # names: require account_id to resolve
            if self.account_id is None:
                self.module.fail_json(msg='Volume name provided but no account_id given to resolve names: %s' % to_native(v))

            vol_id = self.elementsw_helper.volume_exists(v, self.account_id)
            if vol_id is None:
                self.module.fail_json(msg='Volume name not found: %s (account=%s)' % (to_native(v), to_native(self.account_id)))
            resolved.append(int(vol_id))
        return resolved

    def create_group_snapshot(self):
        vols = self.resolve_volume_ids()
        try:
            result = self.sfe.create_group_snapshot(
                volumes=vols,
                name=self.name,
                enable_remote_replication=self.enable_remote_replication,
                retention=self.retention,
                attributes=self.attributes,
            )
            return result
        except Exception as exc:
            self.module.fail_json(msg='Error creating group snapshot: %s' % to_native(exc), exception=traceback.format_exc())

    def apply(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, msg='Check mode: group snapshot not created')

        result = self.create_group_snapshot()
        # attempt to return a dictionary representation
        try:
            gs = result.groupSnapshot if hasattr(result, 'groupSnapshot') else result
            # convert objects to dict if necessary
            if hasattr(gs, '__dict__'):
                gs = vars(gs)
        except Exception:
            gs = None

        self.module.exit_json(changed=True, group_snapshot=gs)


def main():
    module = ElementSWGroupSnapshot()
    module.apply()


if __name__ == '__main__':
    main()

            return result
        except Exception as exc:
            self.module.fail_json(msg='Error creating group snapshot: %s' % to_native(exc), exception=traceback.format_exc())

    def apply(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, msg='Check mode: group snapshot not created')

        result = self.create_group_snapshot()
        # attempt to return a dictionary representation
        try:
            gs = result.groupSnapshot if hasattr(result, 'groupSnapshot') else result
            # convert objects to dict if necessary
            if hasattr(gs, '__dict__'):
                gs = vars(gs)
        except Exception:
            gs = None

        self.module.exit_json(changed=True, group_snapshot=gs)


def main():
    module = ElementSWGroupSnapshot()
    module.apply()


if __name__ == '__main__':
    main()
