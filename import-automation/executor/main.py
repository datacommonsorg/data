# Copyright 2025 Google LLC
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
Import executor entrypoint.
"""
import logging
import json
import os
import sys
import time

REPO_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(REPO_DIR)
sys.path.append(os.path.join(REPO_DIR, 'util'))

from absl import flags
from absl import app

from app import configs
from app.executor import import_executor
from app.service import file_uploader
from app.service import github_api
from app.service import email_notifier
import dataclasses
from app.executor.import_executor import ImportStatus, ImportStage
from google.cloud import secretmanager

import log_util

_FLAGS = flags.FLAGS
flags.DEFINE_string('import_name', '', 'Absoluate import name.')
flags.DEFINE_string('import_config', '{}', 'Import executor configuration.')
flags.DEFINE_boolean(
    'enable_cloud_logging', True,
    'Enable Google Cloud Logging for proper severity levels in GCP.')


def _override_configs(import_name: str, import_dir: str,
                      config: configs.ExecutorConfig,
                      import_config: str) -> configs.ExecutorConfig:
    """
    Overrides import configs in the following order:
    Values from latter configs will overwrite the values from the former configs.
      - Base config (configs.py)
      - Local config (config_override.json)
      - Cloud config (secret manager)
      - Manifest config (manifest.json)
      - User config (command line)
    """
    user_config = json.loads(import_config)
    # Use user provided config for further config processing.
    config = dataclasses.replace(config, **user_config)

    local_config = {}
    if config.config_override_file:
        override_file = os.path.join(REPO_DIR, config.config_override_file)
        logging.info(
            f'Reading import config from override file {override_file}')
        with open(override_file, "r") as f:
            local_config = json.load(f)
            config = dataclasses.replace(config,
                                         **local_config.get("configs", {}))

    cloud_config = {}
    if config.import_config_secret:
        version_id = 'latest'
        secret_id = f"projects/{config.gcp_project_id}/secrets/{config.import_config_secret}/versions/{version_id}"
        logging.info(f'Reading import config from secret {secret_id}')
        secret_value = secretmanager.SecretManagerServiceClient(
        ).access_secret_version(name=secret_id).payload.data.decode("UTF-8")
        cloud_config = json.loads(secret_value)
        config = dataclasses.replace(config, **cloud_config.get("configs", {}))

    manifest_path = os.path.join(config.local_repo_dir, import_dir,
                                 config.manifest_filename)
    manifest_config = {}
    with open(manifest_path, "r") as f:
        logging.info('Overriding config from manifest %s', manifest_path)
        manifest_config = json.load(f)
        logging.info(f'Import manifest: {json.dumps(manifest_config)}')
        for import_spec in manifest_config.get("import_specifications", []):
            if import_spec.get("import_name") == import_name:
                config = dataclasses.replace(
                    config, **import_spec.get("config_override", {}))
                break

    config = dataclasses.replace(config, **user_config)
    return config


def run_import_job(absolute_import_name: str, import_config: str):
    """
    Invokes import update workflow.
    """
    logging.info(
        f"Running import {absolute_import_name} with config:{import_config}")
    start_time = time.time()
    import_dir, import_name = absolute_import_name.split(':', 1)
    base_config = configs.ExecutorConfig()
    config = _override_configs(import_name, import_dir, base_config,
                               import_config)
    logging.info(f'Import config: {config}')
    if config.dc_api_key:
        os.environ['DC_API_KEY'] = config.dc_api_key
    if config.autopush_dc_api_key:
        os.environ['AUTOPUSH_DC_API_KEY'] = config.autopush_dc_api_key
    executor = import_executor.ImportExecutor(
        uploader=file_uploader.GCSFileUploader(
            project_id=config.gcs_project_id,
            bucket_name=config.storage_prod_bucket_name),
        github=github_api.GitHubRepoAPI(
            repo_owner_username=config.github_repo_owner_username,
            repo_name=config.github_repo_name,
            auth_username=config.github_auth_username,
            auth_access_token=config.github_auth_access_token),
        config=config,
        notifier=email_notifier.EmailNotifier(config.email_account,
                                              config.email_token),
        local_repo_dir=config.local_repo_dir)
    import_executor.log_import_status(import_name, ImportStage.INIT,
                                      ImportStatus.SUCCESS)
    result = executor.execute_imports_on_update(absolute_import_name)
    import_executor.log_import_status(import_name, ImportStage.FINISH,
                                      result.status)
    logging.info(f'Import result: {result}')
    elapsed_time_secs = int(time.time() - start_time)
    message = (f"Import Job [{absolute_import_name}] completed with status= "
               f"[{result.status}] in [{elapsed_time_secs}] seconds.)")
    logging.info(message)
    if result.status != ImportStatus.SUCCESS:
        return 1
    return 0


def main(_):
    log_util.configure_logging(_FLAGS.enable_cloud_logging)
    return run_import_job(_FLAGS.import_name, _FLAGS.import_config)


if __name__ == '__main__':
    app.run(main)
