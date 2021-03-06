# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Writes the csv files for upload to Cloud SQL."""

from contextlib import contextmanager
import csv
import os
import tempfile

from google.cloud.security.common.data_access.errors import CSVFileError

FOLDERS_FIELDNAMES = [
    'folder_id',
    'name',
    'display_name',
    'lifecycle_state',
    'parent_type',
    'parent_id',
    'raw_folder',
    'create_time',
]


GROUP_MEMBERS_FIELDNAMES = [
    'group_id',
    'member_kind',
    'member_role',
    'member_type',
    'member_status',
    'member_id',
    'member_email',
    'raw_member'
]

GROUPS_FIELDNAMES = [
    'group_id',
    'group_email',
    'group_kind',
    'direct_member_count',
    'raw_group'
]

ORGANIZATIONS_FIELDNAMES = [
    'org_id',
    'name',
    'display_name',
    'lifecycle_state',
    'raw_org',
    'creation_time',
]

ORG_IAM_POLICIES_FIELDNAMES = [
    'org_id',
    'role',
    'member_type',
    'member_name',
    'member_domain'
]

POLICY_VIOLATION_FIELDNAMES = [
    'resource_id',
    'resource_type',
    'rule_index',
    'rule_name',
    'violation_type',
    'role',
    'member'
]

PROJECTS_FIELDNAMES = [
    'project_number',
    'project_id',
    'project_name',
    'lifecycle_state',
    'parent_type',
    'parent_id',
    'raw_project',
    'create_time'
]

PROJECT_IAM_POLICIES_FIELDNAMES = [
    'project_number',
    'role',
    'member_type',
    'member_name',
    'member_domain'
]

RAW_ORG_IAM_POLICIES_FIELDNAMES = [
    'org_id',
    'iam_policy'
]

RAW_PROJECT_IAM_POLICIES_FIELDNAMES = [
    'project_number',
    'iam_policy'
]

# TODO: Add pydoc to describe the mapping of the custom field naming
# to the field names in the resource objects.
# https://cloud.google.com/storage/docs/json_api/v1/buckets#resource
BUCKETS_FIELDNAMES = [
    'project_number',
    'bucket_id',
    'bucket_name',
    'bucket_kind',
    'bucket_storage_class',
    'bucket_location',
    'bucket_create_time',
    'bucket_update_time',
    'bucket_selflink',
    'bucket_lifecycle_raw',
    'raw_bucket'
]

RAW_BUCKETS_FIELDNAMES = [
    'project_number',
    'buckets'
]

BUCKETS_ACL_FIELDNAMES = [
    'bucket',
    'domain',
    'email',
    'entity',
    'entity_id',
    'acl_id',
    'kind',
    'project_team',  # TODO: flatten this
    'role',
    'bucket_acl_selflink',
    'raw_bucket_acl'
]

FORWARDING_RULES_FIELDNAMES = [
    'id',
    'project_id',
    'creation_timestamp',
    'name',
    'description',
    'region',
    'ip_address',
    'ip_protocol',
    'port_range',
    'ports', # json list
    'target',
    'load_balancing_scheme',
    'subnetwork',
    'network',
    'backend_service',
]

BUCKETS_ACL_VIOLATIONS = [
    'resource_type',
    'resource_id',
    'rule_name',
    'rule_index',
    'violation_type',
    'role',
    'entity',
    'email',
    'domain',
    'bucket'
]

CSV_FIELDNAME_MAP = {
    'buckets': BUCKETS_FIELDNAMES,
    'buckets_acl': BUCKETS_ACL_FIELDNAMES,
    'buckets_acl_violations': BUCKETS_ACL_VIOLATIONS,
    'folders': FOLDERS_FIELDNAMES,
    'forwarding_rules': FORWARDING_RULES_FIELDNAMES,
    'group_members': GROUP_MEMBERS_FIELDNAMES,
    'groups': GROUPS_FIELDNAMES,
    'org_iam_policies': ORG_IAM_POLICIES_FIELDNAMES,
    'organizations': ORGANIZATIONS_FIELDNAMES,
    'policy_violations': POLICY_VIOLATION_FIELDNAMES,
    'project_iam_policies': PROJECT_IAM_POLICIES_FIELDNAMES,
    'projects': PROJECTS_FIELDNAMES,
    'raw_buckets': RAW_BUCKETS_FIELDNAMES,
    'raw_org_iam_policies': RAW_ORG_IAM_POLICIES_FIELDNAMES,
    'raw_project_iam_policies': RAW_PROJECT_IAM_POLICIES_FIELDNAMES,
}


@contextmanager
def write_csv(resource_name, data, write_header=False):
    """Start the csv writing flow.

    Args:
        resource_name: String of the resource name.
        data: An iterable of data to be written to csv.
        write_header: If True, write the header in the csv file.

    Returns:
       The CSV temporary file.
    """
    csv_file = tempfile.NamedTemporaryFile(delete=False)
    try:
        writer = csv.DictWriter(csv_file, doublequote=False, escapechar='\\',
                                quoting=csv.QUOTE_NONE,
                                fieldnames=CSV_FIELDNAME_MAP[resource_name])
        if write_header:
            writer.writeheader()

        for i in data:
            writer.writerow(i)

        # This must be closed before returned for loading.
        csv_file.close()
        yield csv_file

        # Remove the csv file after loading.
        os.remove(csv_file.name)
    except (IOError, OSError, csv.Error) as e:
        raise CSVFileError(resource_name, e)
