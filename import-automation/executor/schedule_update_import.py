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
from datetime import datetime, timezone
import sys
import os
import logging
import json
from typing import Dict

from absl import app
from absl import flags
from app import configs
from app.executor import import_target
from app.executor import import_executor
from app.executor import cloud_scheduler
from app.executor import validation
from app.service import email_notifier
from app.service import file_uploader
from app.service import github_api
from google.cloud import storage

_CONFIG_OVERRIDE_FILE: str = 'config_override.json'
_GKE_SERVICE_ACCOUNT_KEY: str = 'gke_service_account'
_GKE_OAUTH_AUDIENCE_KEY: str = 'gke_oauth_audience'

_FLAGS = flags.FLAGS

flags.DEFINE_string('mode', '', 'Options: update or schedule.')
flags.DEFINE_string('gke_project_id', '',
                    'GCP Project where import executor runs.')
flags.DEFINE_string('config_project_id', 'datcom-204919',
                    'GCS Project for the config file.')
flags.DEFINE_string('config_bucket', 'import-automation-configs',
                    'GCS bucket name for the config file.')
flags.DEFINE_string('config_filename', 'configs.json',
                    'GCS filename for the config file.')
flags.DEFINE_string('scheduler_config_filename', 'cloud_scheduler_configs.json',
                    'GCS filename for the Cloud Scheduler config file.')

flags.DEFINE_string(
    'absolute_import_path', '',
    'A string specifying the path of an import in the following format:'
    '<path_to_directory_relative_to_repository_root>:<import_name>.'
    'Example: scripts/us_usda/quickstats:UsdaAgSurvey')

_FLAGS(sys.argv)

logging.basicConfig(level=logging.INFO)


def _get_cron_schedule(repo_dir: str, absolute_import_path: str,
                       manifest_filename: str):

    # Retain the path to the import (ignoring the name of the import).
    path = absolute_import_path.split(":")[0]

    manifest_fp = os.path.join(repo_dir, path, manifest_filename)
    if not os.path.isfile(manifest_fp):
        raise Exception(
            f'Manifest for import could not be found. Import: {absolute_import_path}. Looking for {manifest_filename} at path: {manifest_fp}'
        )

    manifest = import_executor.parse_manifest(manifest_fp)
    validation.is_manifest_valid(manifest, repo_dir, path)

    for spec in manifest['import_specifications']:
        if absolute_import_path.endswith(':' + spec['import_name']):
            return spec['cron_schedule']

    # If we are here, the the import name was not found in the manifest.
    raise Exception(
        f'No entry found for Import ({absolute_import_path}) in manifest file {manifest_fp}'
    )


def _override_configs(filename: str,
                      config: configs.ExecutorConfig) -> configs.ExecutorConfig:
    # Read configs from the local file.
    d = json.load(open(filename))

    # Update config with any fields and values provided in the local file.
    # In case of any errors, the line below will raise an Exception which will
    # report the problem which shoud be fixed in the local config json file.
    return dataclasses.replace(config, **d["configs"])


def _get_cloud_config(filename: str) -> Dict:
    logging.info('Getting cloud config.')
    config_project_id = _FLAGS.config_project_id
    bucket_name = _FLAGS.config_bucket
    logging.info(
        f'\nProject ID: {config_project_id}\nBucket: {bucket_name}\nConfig Filename: {filename}'
    )

    bucket = storage.Client(config_project_id).bucket(
        bucket_name, user_project=config_project_id)
    blob = bucket.blob(filename)
    config_dict = json.loads(blob.download_as_string(client=None))
    return config_dict


def _get_latest_blob(project_id: str, bucket_name: str, filepath: str):
    bucket = storage.Client(project_id).bucket(bucket_name)
    blob = bucket.blob(filepath)
    return blob


def _check_filepath(filepath: str, bucket_name: str, project_id):
    logging.info(
        f'Checking file: {filepath} in Bucket: {bucket_name} [Project: {project_id}]'
    )
    blob = _get_latest_blob(project_id, bucket_name, filepath)
    blob.reload()
    version = blob.download_as_string(client=None).decode("utf-8")
    updated = blob.updated
    updated_duration = int((datetime.now(timezone.utc) - updated).seconds)
    folder = os.path.join(bucket_name, filepath, version)
    logging.info(f'GCS Project for output: {project_id}')
    logging.info(f'Corresponding directory path on GCS: {folder}')
    logging.info(f'Latest Version: {version}')
    logging.info(f'Updated at: {updated}')
    logging.info(f'Last updated ~{updated_duration} seconds ago.')


def _print_fileupload_results(cfg: configs.ExecutorConfig,
                              absolute_import_path: str):
    # Check and print the latest versions written to GCP for this import.
    filepath = os.path.join(absolute_import_path.replace(":", "/"),
                            cfg.storage_version_filename)

    logging.info("===========================================================")
    logging.info("============ IMPORT FILE UPLOAD DIAGNOSTICS ===============")
    logging.info("===========================================================")
    # Prod Path.
    try:
        _check_filepath(filepath, cfg.storage_prod_bucket_name,
                        cfg.gcs_project_id)
    except Exception as e:
        logging.error(
            f'Error when accessing the expected PROD file. Error: {e}')

    logging.info("===========================================================")
    logging.info("===========================================================")


def _print_schedule_results(cfg: configs.ExecutorConfig, result: Dict):
    logging.info("===========================================================")
    logging.info("============ CLOUD SCHEDULER JOB DIAGNOSTICS ==============")
    logging.info("===========================================================")

    logging.info("Cloud Scheduler job scheduled with the following:")
    logging.info(result)
    logging.info("===========================================================")
    logging.info("===========================================================")
    logging.info(
        f"Check all scheduled jobs at: console.cloud.google.com/cloudscheduler?project={cfg.gcp_project_id}"
    )

    if "name" in result:
        logging.info(f"Job scheduled as: {result['name']}.")

        try:
            date_format = '%Y-%m-%dT%H:%M:%S%z'
            updated = datetime.strptime(result["user_update_time"], date_format)
            updated_duration = int(
                (datetime.now(timezone.utc) - updated).seconds)
            logging.info(
                f'Last Updated: {updated_duration} seconds ago (UTC: {result["user_update_time"]}).'
            )
        except Exception:
            # Just means we couldn't parse the user_update_time which is not terrible.
            pass
    else:
        logging.error(
            'The result dictionary has an unexpected form. Key \"name\" missing. Check job details on GCP console to confirm successful scheduling.'
        )

    logging.info("===========================================================")
    logging.info("===========================================================")


def update(cfg: configs.ExecutorConfig,
           absolute_import_path: str,
           local_repo_dir: str = "") -> import_executor.ExecutionResult:
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
        local_repo_dir: the full path to the GitHub repository on local. The
            path shoud be provided to the root  directory of the repo,
            e.g. `<base_path_on_disk>/data`.

    Returns:
        An import_executor.ExecutionResult object.
    """
    executor = import_executor.ImportExecutor(
        uploader=file_uploader.GCSFileUploader(
            project_id=cfg.gcs_project_id,
            bucket_name=cfg.storage_prod_bucket_name),
        github=github_api.GitHubRepoAPI(
            repo_owner_username=cfg.github_repo_owner_username,
            repo_name=cfg.github_repo_name,
            auth_username=cfg.github_auth_username,
            auth_access_token=cfg.github_auth_access_token),
        config=cfg,
        local_repo_dir=local_repo_dir)

    # Also set the email motifier if possible.
    if cfg.email_account and cfg.email_token:
        executor.notifier = email_notifier.EmailNotifier(
            cfg.email_account, cfg.email_token)

    return executor.execute_imports_on_update(absolute_import_path)


def schedule(cfg: configs.ExecutorConfig,
             absolute_import_name: str,
             repo_dir: str,
             gke_service_account: str = "",
             gke_oauth_audience: str = "") -> Dict:
    # This is the content of what is passed to /update API
    # inside each cronjob http calls from Cloud Scheduler.
    json_encoded_job_body = json.dumps({
        'absolute_import_name': absolute_import_name,
        'configs': cfg.get_data_refresh_config()
    }).encode("utf-8")

    # Retrieve the cron schedule.
    cron_schedule = _get_cron_schedule(repo_dir, absolute_import_name,
                                       cfg.manifest_filename)

    # Create an HTTP Job Request.
    req = cloud_scheduler.http_job_request(
        absolute_import_name,
        cron_schedule,
        json_encoded_job_body,
        gke_caller_service_account=gke_service_account,
        gke_oauth_audience=gke_oauth_audience)

    return cloud_scheduler.create_or_update_job(cfg.gcp_project_id,
                                                cfg.scheduler_location, req)


def main(_):
    mode = _FLAGS.mode
    absolute_import_path = _FLAGS.absolute_import_path

    if not _FLAGS.gke_project_id:
        raise Exception("Flag: gke_project_id must be provided.")

    if not mode or (mode not in ['update', 'schedule']):
        raise Exception('Flag: mode must be set to \'update\' or \'schedule\'')

    if not import_target.is_absolute_import_name(absolute_import_path):
        raise Exception(
            'Flag: absolute_import_path is invalid. Path should be like:'
            'scripts/us_usda/quickstats:UsdaAgSurvey')

    # Get the root repo directory (data). Assumption is that this script is being
    # called from a path within the data repo.
    cwd = os.getcwd()
    repo_dir = cwd.split("data")[0] + "data"
    logging.info(f'{mode} called with the following:')
    logging.info(f'Config Project ID: {_FLAGS.config_project_id}')
    logging.info(f'GKE (Import Executor) Project ID: {_FLAGS.gke_project_id}')
    logging.info(f'Import: {absolute_import_path}')
    logging.info(f'Repo root directory: {repo_dir}')

    # Loading configs from GCS and then using _CONFIG_OVERRIDE_FILE to
    # override any fields provided in the file.
    logging.info('Reading configs from GCS.')
    config_dict = _get_cloud_config(_FLAGS.config_filename)
    cfg = configs.ExecutorConfig(**config_dict['configs'])

    # Update the GCP project id to use with the configs.
    cfg.gcp_project_id = _FLAGS.gke_project_id

    logging.info(
        f'Updating any config fields from local file: {_CONFIG_OVERRIDE_FILE}.')
    cfg = _override_configs(_CONFIG_OVERRIDE_FILE, cfg)

    logging.info('Reading Cloud scheduler configs from GCS.')
    scheduler_config_dict = _get_cloud_config(_FLAGS.scheduler_config_filename)

    if mode == 'update':
        logging.info("*************************************************")
        logging.info("***** Beginning Update. Can take a while. *******")
        logging.info("*************************************************")
        res = dataclasses.asdict(
            update(cfg, absolute_import_path, local_repo_dir=repo_dir))
        logging.info("*************************************************")
        logging.info("*********** Update Complete. ********************")
        logging.info("*************************************************")
        logging.info(
            "===========================================================")
        logging.info(
            "====================== UPDATE RESULT ======================")
        logging.info(
            "===========================================================")
        logging.info(res)
        logging.info(
            "===========================================================")
        logging.info(
            "===========================================================")

        # Check expected output file/folder versions (to confirm updates).
        _print_fileupload_results(cfg, absolute_import_path)

    elif mode == 'schedule':
        # Before proceeding, ensure that the configs read from GCS have the expected fields.
        assert _GKE_SERVICE_ACCOUNT_KEY in scheduler_config_dict
        assert _GKE_OAUTH_AUDIENCE_KEY in scheduler_config_dict

        logging.info("*************************************************")
        logging.info("***** Beginning Schedule Operation **************")
        logging.info("*************************************************")
        res = schedule(
            cfg,
            absolute_import_path,
            repo_dir,
            gke_service_account=scheduler_config_dict[_GKE_SERVICE_ACCOUNT_KEY],
            gke_oauth_audience=scheduler_config_dict[_GKE_OAUTH_AUDIENCE_KEY])
        logging.info("*************************************************")
        logging.info("*********** Schedule Operation Complete. ********")
        logging.info("*************************************************")

        # Some basic diagnostics.
        _print_schedule_results(cfg, res)


if __name__ == '__main__':
    app.run(main)
