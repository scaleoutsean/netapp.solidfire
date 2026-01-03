#!/usr/bin/python
# (c) 2026, Community
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Element Software Backup to S3
"""

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: na_elementsw_backup_s3

short_description: NetApp Element Software backup a volume to S3
extends_documentation_fragment:
  - community.solidfire.netapp.solidfire
version_added: 26.1.0
author: scaleoutSean (@scaleoutsean)
description:
  - Start a bulk volume read and write the output to an S3-compatible endpoint. Use no_log=True for this task.

options:
  src_volume_id:
    description:
      - ID of the source volume to read from.
    required: true
    type: int

  src_snapshot_id:
    description:
      - Optional snapshot ID to read from instead of latest volume.
    required: false
    type: int

  dest_s3_access_key:
    description:
      - S3 access key to use for upload.
    required: true
    type: str

  dest_s3_secret_key:
    description:
      - S3 secret key to use for upload.
    required: true
    type: str

  dest_s3_destination_bucket:
    description:
      - Destination S3 bucket name.
    required: true
    type: str

  dest_s3_prefix:
    description:
      - Prefix (object key path) to write objects under.
    required: false
    type: str
    default: ''

  dest_s3_endpoint:
    description:
      - S3 endpoint FQDN used by SolidFire (e.g. 's3' or custom).
    required: false
    type: str
    default: s3

  dest_s3_hostname:
    description:
      - Hostname (or endpoint URL) of the S3 service.
    required: true
    type: str

  dest_s3_tags:
    description:
      - Optional list of tags to associate with backup objects.
    required: false
    type: list
    elements: str

  format:
    description:
      - Backup format to use.
    choices: ['native','uncompressed']
    default: 'native'
    type: str

  script:
    description:
      - Script to run on source cluster (defaults to bv_internal.py)
    required: false
    type: str
    default: bv_internal.py

  script_parameters:
    description:
      - If provided, sent directly as scriptParameters to the API; otherwise built from S3 args.
    required: false
    type: dict

  api_method:
    description:
      - API method to invoke. Defaults to StartBulkVolumeRead for S3 backups.
    required: false
    type: str
    default: StartBulkVolumeRead
'''

EXAMPLES = '''
- name: SolidFire backup to S3
  na_elementsw_backup_s3:
    hostname: "{{ elementsw_hostname }}"
    username: "{{ elementsw_username }}"
    password: "{{ elementsw_password }}"
    src_volume_id: 201
    dest_s3_hostname: "s3.my.org"
    dest_s3_access_key: "{{ s3_keya }}"
    dest_s3_secret_key: "{{ s3_keys }}"
    dest_s3_destination_bucket: "backups"
    dest_s3_tags: ["monday","snap"]
    format: native
'''

RETURN = """
solidfire_bulkvolumeread_response:
    description: Returns async job handle, job key and MIP of node running the job.
    returned: always
    type: dict
    sample: '{
        "id": 1,
        "result": {
            "asyncHandle": 46,
            "key": "82e939a9ee81811096f4e43e61e6e4f7",
            "url": "https://10.128.56.54:8443/"
        }
    }'
    contains:
        raw:
            description: Raw API response (dict)
            returned: always
            type: dict
        async_handle:
            description: Async handle returned by the API (int)
            returned: always
            type: int
        key:
            description: Job key (string)
            returned: always
            type: str
        url:
            description: URL of the cluster member that will run the job (string)
            returned: always
            type: str
"""


__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible_collections.community.solidfire.plugins.module_utils.netapp as netapp_utils
from ansible_collections.community.solidfire.plugins.module_utils.netapp_elementsw_module import NaElementSWModule

HAS_SF_SDK = netapp_utils.has_sf_sdk()
try:
    import solidfire.common
except Exception:
    HAS_SF_SDK = False


class ElementSWBackupS3(object):
    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            src_volume_id=dict(required=True, type='int'),
            src_snapshot_id=dict(required=False, type='int'),
            dest_s3_access_key=dict(required=True, type='str', no_log=True),
            dest_s3_secret_key=dict(required=True, type='str', no_log=True),
            dest_s3_destination_bucket=dict(required=True, type='str'),
            dest_s3_prefix=dict(required=False, type='str', default=''),
            dest_s3_endpoint=dict(required=False, type='str', default='s3'),
            dest_s3_hostname=dict(required=True, type='str'),
            dest_s3_tags=dict(required=False, type='list', elements='str', default=None),
            format=dict(required=False, choices=['native', 'uncompressed'], default='native'),
            script=dict(required=False, type='str', default='bv_internal.py'),
            script_parameters=dict(required=False, type='dict', default=None),
            api_method=dict(required=False, type='str', default='StartBulkVolumeRead')
        ))

        self.module = AnsibleModule(argument_spec=self.argument_spec, supports_check_mode=True)

        if HAS_SF_SDK is False:
            self.module.fail_json(msg='SolidFire SDK not available')

        self.conn = netapp_utils.create_sf_connection(self.module)
        self.helper = NaElementSWModule(self.conn)

        # telemetry
        self.attributes = self.helper.set_element_attributes(source='na_elementsw_backup_s3')

    def apply(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, msg='Check mode: not starting backup')

        try:
            result = self.start_backup()
        except Exception as exc:
            self.module.fail_json(msg='Failed to start S3 backup: %s' % to_native(exc))

        # parse useful fields
        out = {'raw': result}
        async_handle = getattr(result, 'async_handle', None) if hasattr(result, '__dict__') else result.get('asyncHandle') if isinstance(result, dict) else None
        key = getattr(result, 'key', None) if hasattr(result, '__dict__') else result.get('key') if isinstance(result, dict) else None
        url = getattr(result, 'url', None) if hasattr(result, '__dict__') else result.get('url') if isinstance(result, dict) else None
        if async_handle is not None:
            out['async_handle'] = async_handle
        if key is not None:
            out['key'] = key
        if url is not None:
            out['url'] = url

        self.module.exit_json(changed=True, **out)

    def start_backup(self):
        params = None
        if self.module.params['script_parameters']:
            params = self.module.params['script_parameters']
        else:
            # build scriptParameters.write for S3
            write = dict(
                awsAccessKeyID=self.module.params['dest_s3_access_key'],
                awsSecretAccessKey=self.module.params['dest_s3_secret_key'],
                bucket=self.module.params['dest_s3_destination_bucket'],
                prefix=self.module.params['dest_s3_prefix'],
                endpoint=self.module.params['dest_s3_endpoint'],
                hostname=self.module.params['dest_s3_hostname'],
                format=self.module.params['format']
            )
            if self.module.params.get('dest_s3_tags'):
                write['tags'] = self.module.params.get('dest_s3_tags')

            params = {'write': write, 'range': {'lba': 0, 'blocks': 0}}

        # call SDK's start_bulk_volume_read which maps to StartBulkVolumeRead
        try:
            res = self.conn.start_bulk_volume_read(self.module.params['src_volume_id'],
                                                   self.module.params['format'],
                                                   script=self.module.params['script'],
                                                   script_parameters=params,
                                                   attributes=self.attributes)
            return res
        except solidfire.common.ApiServerError as err:
            raise


def main():
    m = ElementSWBackupS3()
    m.apply()


if __name__ == '__main__':
    main()
