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
"""
Configurations for the executor.

The app endpoints accept a configs field that allows customization of all the
configurations. See main.py.
"""

import os
import typing
import dataclasses

from google.cloud import logging
from google.cloud import datastore


def _production():
    return 'EXECUTOR_PRODUCTION' in os.environ


@dataclasses.dataclass
class ExecutorConfig:
    """Configurations for the executor."""
    # ID of the Google Cloud project that hosts the executor. The project
    # needs to enable App Engine, Cloud Storage, and Cloud Scheduler.
    gcp_project_id: str = 'google.com:datcom-data'
    # Oauth Client ID used to authenticate with the import progress dashboard.
    # which is protected by Identity-Aware Proxy. This can be found by going
    # to the Identity-Aware Proxy of the Google Cloud project that hosts
    # the dashboard and clicking 'Edit OAuth Client'.
    dashboard_oauth_client_id: str = ''
    # Access token of the account used to authenticate with GitHub. This is not
    # the account password. See
    # https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token.
    github_auth_access_token: str = ''
    # Username of the account used to authenticate with GitHub.
    github_auth_username: str = 'intrepiditee'
    # Name of the repository that contains all the imports.
    # On commits, this is the repository to which the pull requests must be sent
    # to trigger the executor. The source repositories of the pull requests
    # are downloaded.
    # On updates, this is the repository that is downloaded.
    github_repo_name: str = 'data'
    # Username of the owner of the repository that contains all the imports.
    github_repo_owner_username: str = 'datacommonsorg'
    # Manifest filename. The executor uses this name to identify manifests.
    manifest_filename: str = 'manifest.json'
    # Python module requirements filename. The executor installs the modules
    # listed in these files before running the user scripts.
    requirements_filename: str = 'requirements.txt'
    # Name of the Cloud Storage bucket to store the generated data files.
    storage_bucket_name: str = 'import-inputs'
    # Name of the file that specifies the most recently generated data files
    # of an import. These files are stored in the bucket at a level higher
    # than the data files. For example,
    # import-inputs
    # -- scripts
    # ---- us_fed
    # ------ treasury
    # -------- latest_version.txt
    # -------- 2020_07_15T12_07_17_365264_07_00
    # ---------- data.csv
    # -------- 2020_07_14T12_07_12_552234_07_00
    # ---------- data.csv
    # The content of latest_version.txt would be a single line of
    # '2020_07_15T12_07_17_365264_07_00'.
    storage_version_filename: str = 'latest_version.txt'
    # Types of inputs accepted by the Data Commons importer. These are
    # also the accepted fields of an import_inputs value in the manifest.
    import_input_types: typing.List[str] = ('template_mcf', 'cleaned_csv',
                                            'node_mcf')
    # ID of the location where Cloud Scheduler is hosted.
    scheduler_location: str = 'us-central1'
    # Maximum time a user script can run for in seconds.
    user_script_timeout: float = 600
    # Maximum time venv creation can take in seconds.
    venv_create_timeout: float = 600
    # Maximum time downloading a file can take in seconds.
    file_download_timeout: float = 600
    # Maximum time downloading the repo can take in seconds.
    repo_download_timeout: float = 600


def _setup_logging():
    client = logging.Client(project=ExecutorConfig.gcp_project_id)
    client.get_default_handler()
    client.setup_logging()


if _production():
    _setup_logging()
