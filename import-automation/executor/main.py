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

from absl import flags
from absl import app

from app import configs
from app.executor import import_executor
from app.service import file_uploader
from app.service import github_api
from app.service import email_notifier

FLAGS = flags.FLAGS
flags.DEFINE_string('import_name', '', 'Absoluate import name.')
flags.DEFINE_string('import_config', '', 'Import executor configuration.')


def scheduled_updates(absolute_import_name: str, import_config: str):
    """
    Invokes import update workflow.
    """
    logging.info(absolute_import_name)
    cfg = json.loads(import_config)
    config = configs.ExecutorConfig(**cfg)
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
    result = executor.execute_imports_on_update(absolute_import_name)
    logging.info(result)
    if result.status == 'failed':
        return 1
    return 0


def main(_):
    return scheduled_updates(FLAGS.import_name, FLAGS.import_config)


if __name__ == '__main__':
    app.run(main)
