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
"""Utilities to run simple imports (RSI) as cloud run jobs."""
import datetime
import os
import sys
import time

from absl import logging
import pytz

# Set path for import modules.
_SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.join(_SCRIPT_DIR.split('/data/', 1)[0], 'data', 'util'))

import cloud_run
import file_util

# Default settings.
_DEFAULT_PROJECT = 'datcom-import-automation-prod'
_DEFAULT_RSI_IMAGE = 'gcr.io/datcom-ci/datacommons-simple:stable'
_DEFAULT_LOCATION = 'us-central1'
_DEFAULT_GCS_BUCKET = 'datcom-prod-imports'
_DEFAULT_CONFIG_PREFIX = 'simple_config'

# Path for simple import config spec under data/scripts/simple
_IMPORT_CONFIG_DIR = '/scripts/simple/'


def get_rsi_import_job_id(
    import_spec: dict, script: str, import_dir: str
) -> str:
  """Returns the job id if the script is a simple import (RSI) config.

  Args:
    import_spec: dictionary loaded from manifest.json
    script: script for import
    import_dir: path to the import script

  Returns:
    job_is as a string <import_path>-<import_name>-<script>
  """
  # Create a job is for simple import cloud run as
  # <script_path>-<import_name>-<config>
  job_parts = []
  config_dir_pos = import_dir.find(_IMPORT_CONFIG_DIR)
  if config_dir_pos:
    job_parts.append(import_dir[config_dir_pos:])
  else:
    job_parts.append(import_dir)
  job_parts.append(import_spec.get('import_name'))
  job_parts.append(
      script.replace(_DEFAULT_CONFIG_PREFIX, '').replace('.json', '')
  )
  job_id = '-'.join([s for s in job_parts if s])
  return cloud_run.get_job_id(job_id)


def get_rsi_import_gcs_config(
    config_file: str,
    gcs_bucket: str = _DEFAULT_GCS_BUCKET,
    config_dir: str = _IMPORT_CONFIG_DIR,
    copy_file: bool = True,
) -> str:
  """Returns the import config file on GCS.

  Simple imports are processed as a Cloud Run job that cannot access local
  files.
  So import config and output files are saved in the GCS folder:
    <GCS-Bucket>/scripts/simple/<import>

  Args:
    config_file: Import config json
    gcs_bucket: GCS bucket for the import config and outputs.
    copy_file: if True copies the config file to GCS.

  Returns:
    GCS path to the config file,
    like gs://<GCS-BUCKET>/scipts/simple/<import>/simple_config.json
  """
  gcs_config_file = config_file
  if config_file.startswith('gs://'):
    # Config already on GCS. Use as is.
    return gcs_config_file

  path = []
  if config_dir.startswith('gs://'):
    # Use the provided gcs folder
    path.append(config_dir)
    if not config_dir.endswith('.json'):
      path.append(os.path.basename(config_file))
  else:
    # Use the gcs path: gs://<bucket>/scripts/simple/<import>/<config>
    if not gcs_bucket:
      gcs_bucket = _DEFAULT_GCS_BUCKET
    path.append(gcs_bucket)
    path.append(config_dir)
    config_pos = config_file.find(config_dir)
    if config_pos >= 0:
      config_pos += len(config_dir)
    else:
      config_pos = 0
    path.extend(config_file[config_pos:].split('/'))
  gcs_config_file = '/'.join([d.strip('/') for d in path if d])
  if not gcs_config_file.startswith('gs://'):
    gcs_config_file = 'gs://' + gcs_config_file
  if copy_file and config_file != gcs_config_file:
    logging.info(f'Copying import config: {config_file} to {gcs_config_file}')
    file_util.file_copy(config_file, gcs_config_file)
  return gcs_config_file


def cloud_run_rsi_job(
    config_file: str,
    env: dict = {},
    job_id: str = '',
    version: str = '',
    project_id: str = _DEFAULT_PROJECT,
    location: str = _DEFAULT_LOCATION,
    gcs_dir: str = '',
    image: str = _DEFAULT_RSI_IMAGE,
) -> str:
  """Create and run a Cloud Run job for simple import.

  Args:
    config_file: json file with config for simple import run. For an example,
      see scripts/simple/sample/config.json
    project_id: Google project id for the cloud run. The compute engine service
      account for the project should have access to the GCS folder for output.

  Returns:
    Output directory with the script outputs.
  """
  # Copy the config file to GCS if needed.
  # Cloud run can only access GCS for config files, input and output.
  gcs_config = get_rsi_import_gcs_config(config_file, copy_file=True)
  gcs_dir = os.path.dirname(gcs_config)

  # Create a dated version output folder for each run.
  if not version:
    version = _get_time_version()
  gcs_output_dir = os.path.join(gcs_dir, 'output', version)
  # Setup environment variables for simple import run.
  # Settings for each import run have to be passed in through ENV variables.
  env_vars = {
      'CONFIG_FILE': gcs_config,
      'OUTPUT_DIR': gcs_output_dir,
  }
  if env:
    env_var.update(env)

  # Generate job-id from config_file path if not specified.
  if not job_id:
    job_id = cloud_run.get_job_id(
        config_file[config_file.find(_IMPORT_CONFIG_DIR) :]
    )

  # Create and run the job for the config.
  logging.info(
      f'Creating simple import cloud run {project_id}:{job_id} for'
      f' {config_file} with output: {gcs_output_dir}, env: {env_vars}'
  )
  job = cloud_run.create_or_update_cloud_run_job(
      project_id, location, job_id, image, env_vars
  )
  if not job:
    logging.error(f'Failed to create cloud run job {job_id} for {config_file}')
    return None

  logging.info(
      f'Running {project_id}:{job_id} for {config_file} with output:'
      f' {gcs_output_dir}'
  )
  job = cloud_run.execute_cloud_run_job(project_id, location, job_id)
  if not job:
    logging.error(f'Failed to execute cloud run job {job_id} for {config_file}')
    return None

  logging.info(
      f'Completed run {project_id}:{job_id} for {config_file} with output:'
      f' {gcs_output_dir}'
  )
  return gcs_output_dir


def _get_time_version() -> str:
  """Returns the current datetime as a string with only alnum chars and '_'."""
  t = datetime.datetime.now(pytz.timezone('America/Los_Angeles')).isoformat()
  version = []
  for c in t:
    if c.isalnum() or c == '_':
      version.append(c)
    else:
      version.append('_')
  return ''.join(version)
