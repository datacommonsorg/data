# Copyright 2024 Google LLC
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
import dataclasses
import sys
import os
import logging
import json
from typing import List

from absl import app
from absl import flags
from app import configs
from app.executor import import_target
from app.executor import import_executor
from app.executor import cloud_scheduler
from app.service import file_uploader
from app.service import github_api
from google.cloud import storage

_FLAGS = flags.FLAGS

flags.DEFINE_string('mode', '', 'Options: update or schedule.')
flags.DEFINE_string('config_project_id', '', 'GCS Project for the config file.')
flags.DEFINE_string('config_bucket', 'import-automation-configs', 'GCS bucket name for the config file.')
flags.DEFINE_string('config_filename', 'configs.json', 'GCS filename for the config file.')

flags.DEFINE_string(
    'absolute_import_path', '',
    'A string specifying the path of an import in the following format:'
    '<path_to_directory_relative_to_repository_root>:<import_name>.'
    'Example: scripts/us_usda/quickstats:UsdaAgSurvey')

flags.DEFINE_string(
    'import_script_args', '',
    'One string of command line args for the import script,'
    'e.g. "--flag1=value1 --flag2=value2"')

_FLAGS(sys.argv)

logging.basicConfig(level=logging.INFO)


def _get_cloud_config() -> configs.ExecutorConfig:
    logging.info('Getting cloud config.')
    project_id = _FLAGS.config_project_id
    bucket = _FLAGS.config_bucket
    fname = _FLAGS.config_filename
    logging.info(
        f'\nProject ID: {project_id},\nBucket: {bucket};\nConfig Filename: {fname}'
    )

    bucket = storage.Client(project_id).bucket(bucket)
    blob = bucket.blob(fname)
    config_dict = json.loads(blob.download_as_string(client=None))

    return configs.ExecutorConfig(**config_dict['configs'])


def update(
        cfg: configs.ExecutorConfig,
        absolute_import_path: str,
        import_script_args: List[str] = []) -> import_executor.ExecutionResult:
    """Executes an update on the specified import.

    Note: the sub-routine will clone the data repo at the most recent commit in
    the branch master. Therefore, any local changes in the repo or import script
    will not be reflected.

    Args:
        cfg: a configs.ExecutorConfig object with all the fields required for
            the update script. Since it contains authentication information,
            the configs should be read from a secure location, e.g. a Cloud
            bucket, and then parsed and passed here as a configs.ExecutorConfig
            object.
        absolute_import_path: a string specifying the import's path in the
            following format:
                <path_to_directory_relative_to_repository_root>:<import_name>
            example:
                scripts/us_usda/quickstats:UsdaAgSurvey
        import_script_args: a list of strings, each to be used as a command
            line arg for the import script,
            e.g. ['--flag1=value1', '--flag2=value2'].

    Returns:
        An import_executor.ExecutionResult object.
    """
    # Update the configs with user script args, if provided.
    if import_script_args:
        cfg.user_script_args = import_script_args

    executor = import_executor.ImportExecutor(
        uploader=file_uploader.GCSFileUploader(
            project_id=cfg.gcs_project_id,
            bucket_name=cfg.storage_prod_bucket_name),
        github=github_api.GitHubRepoAPI(
            repo_owner_username=cfg.github_repo_owner_username,
            repo_name=cfg.github_repo_name,
            auth_username=cfg.github_auth_username,
            auth_access_token=cfg.github_auth_access_token),
        config=cfg)

    return executor.execute_imports_on_update(absolute_import_path)


def main(_):
    mode = _FLAGS.mode
    absolute_import_path = _FLAGS.absolute_import_path
    import_script_args = _FLAGS.import_script_args

    if not _FLAGS.config_project_id:
        raise Exception("Flag: config_project_if must be provided.")

    if not mode or (mode not in ['update', 'schedule']):
        raise Exception('Flag: mode must be set to \'update\' or \'schedule\'')

    if not import_target.is_absolute_import_name(absolute_import_path):
        raise Exception('Flag: absolute_import_path is invalid. Path should be like:'
                      'scripts/us_usda/quickstats:UsdaAgSurvey')

    # Converting string to list
    args_list =  import_script_args.split(' ')
    if type(args_list) != type([]):
        raise Exception('Flag: import_script_args could not be parsed into a list.')

    # Get the root repo directory (data). Assumption is that this script is being
    # called from a path within the data repo.
    cwd = os.getcwd()
    repo_dir = cwd.split("data")[0] + "data"
    logging.info(f'{mode} called with the following:')
    logging.info(f'Config Project ID: {_FLAGS.config_project_id}')
    logging.info(f'Import: {absolute_import_path}')
    logging.info(f'Import script args: {args_list}')
    logging.info(f'Repo root directory: {repo_dir}')


    cfg = _get_cloud_config()
    if mode == 'update':
        res = dataclasses.asdict(update(cfg, absolute_import_path, import_script_args=args_list))
        print(res)
    elif mode == 'schedule':
        # TODO: implement this.
        pass


if __name__ == '__main__':
    app.run(main)
