# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import typing
import dataclasses

from google.cloud import logging
from google.cloud import datastore


def _standalone():
    return 'STANDALONE_MODE' in os.environ


def _production():
    return 'EXECUTOR_PRODUCTION' in os.environ


def _testing():
    return 'EXECUTOR_TESTING' in os.environ


@dataclasses.dataclass
class ExecutorConfig:
    # TODO(intrepiditee): Add descriptions
    gcp_project_id: str = 'google.com:datcom-data'
    datastore_configs_namespace: str = 'configs'
    datastore_configs_kind: str = 'config'
    dashboard_oauth_client_id: str = ''
    github_auth_access_token: str = ''
    github_auth_username: str = 'intrepiditee'
    github_repo_owner_username: str = 'datacommonsorg'
    github_repo_name: str = 'data'
    manifest_filename: str = 'manifest.json'
    requirements_filename: str = 'requirements.txt'
    storage_bucket_name: str = 'import-inputs'
    storage_version_filename: str = 'latest_version.txt'
    import_input_types: typing.List[str] = (
        'template_mcf',
        'cleaned_csv',
        'node_mcf'
    )

    user_script_timeout: float = 600
    venv_create_timeout: float = 600

    # TODO(intrepiditee): Implement these two
    file_download_timeout: float = 600
    repo_download_timeout: float = 600

    def __post_init__(self):
        access_token = 'GITHUB_AUTH_ACCESS_TOKEN'
        client_id = 'DASHBOARD_OAUTH_CLIENT_ID'
        if _standalone():
            return
        if _production():
            if not self.github_auth_access_token:
                self.github_auth_access_token = self._get_config(access_token)
            if not self.dashboard_oauth_client_id:
                self.dashboard_oauth_client_id = self._get_config(client_id)
        if _testing():
            if not self.github_auth_access_token:
                self.github_auth_access_token = os.environ[access_token]

    def _get_config(self, entity_id):
        client = datastore.Client(
            project=self.gcp_project_id,
            namespace=self.datastore_configs_kind)
        key = client.key(self.datastore_configs_kind, entity_id)
        return client.get(key)[entity_id]


def _setup_logging():
    client = logging.Client()
    client.get_default_handler()
    client.setup_logging()


if _production():
    _setup_logging()

