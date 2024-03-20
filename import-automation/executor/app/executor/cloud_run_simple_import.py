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
"""Utilities to run simple imports as cloud run jobs.

For mre details on simple imports, please refer to:
https://github.com/datacommonsorg/import/tree/master/simple
"""
import datetime
import os
import sys
import time

from absl import logging
import pytz

# Set path for import modules.
_SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_SCRIPT_DIR)

import cloud_run
import file_io

# Default settings.
_DEFAULT_PROJECT = os.environ.get('GCS_PROJECT',
                                  'datcom-import-automation-prod')
_DEFAULT_SIMPLE_IMAGE = os.environ.get(
    'DOCKER_IMAGE', 'gcr.io/datcom-ci/datacommons-simple:stable')
_DEFAULT_LOCATION = os.environ.get('CLOUD_REGION', 'us-central1')
_DEFAULT_GCS_BUCKET = os.environ.get('GCS_BUCKET', 'datcom-prod-imports')
_DEFAULT_CONFIG_PREFIX = 'import_config'

# Path for simple import config spec under data/scripts/simple
_IMPORT_CONFIG_DIR = '/simple_imports/'


def get_simple_import_job_id(import_spec: dict, import_script: str) -> str:
    """Returns the job id if the script is a simple import config, else ''.

  Args:
    import_spec: Import specification dictionary with import name, script.
    import_script: Specific import script being processed

  Returns:
    job_is as a string simple-import-<import_name> for simple-imports
    or '' for other imports.
  """
    # Create a job is for simple import cloud run as
    # <config_path>-<import_name>
    import_name = import_spec.get('import_name')
    import_pos = import_script.find(_IMPORT_CONFIG_DIR)
    if import_pos < 0 or _DEFAULT_CONFIG_PREFIX not in import_script:
        # Not a simple import
        return ''
    # Get the import config path under .../simple_imports/
    job_str = [
        import_script[import_script.find(_IMPORT_CONFIG_DIR) + 1:].replace(
            _DEFAULT_CONFIG_PREFIX, '').removesuffix('.json')
    ]
    if import_name:
        job_str.append(import_name)
    return cloud_run.get_job_id('-'.join(job_str))


def get_simple_import_gcs_config(
    config_file: str,
    import_name: str,
    version: str,
    gcs_bucket: str = _DEFAULT_GCS_BUCKET,
    config_dir: str = _IMPORT_CONFIG_DIR,
    copy_file: bool = True,
) -> str:
    """Returns path to a copy of the import config file on GCS.

  Simple imports are processed as a Cloud Run job that cannot access local
  files.  So import config and output files are saved in the GCS folder:
    <GCS-Bucket>/simple_imports/<import>/<version>/

  Args:
    config_file: Import config json
    import_name: name of the import
    version: dated version string for the import run
    gcs_bucket: GCS bucket for the import config and outputs.
    copy_file: if True copies the config file to GCS.

  Returns:
    GCS path to the config file,
    like gs://<GCS-BUCKET>/simple_imports/<import>/<version>/import_config.json
  """
    path = []
    if config_dir.startswith('gs://'):
        # Use the provided gcs folder
        path.append(config_dir)
    else:
        # Use the gcs path: gs://<bucket>/simple_imports/<import>/
        if not gcs_bucket:
            gcs_bucket = _DEFAULT_GCS_BUCKET
        path.append(gcs_bucket)
        path.append(config_dir)
        config_file_path = os.path.dirname(config_file)
        config_pos = config_file_path.find(config_dir)
        if config_pos >= 0:
            config_pos += len(config_dir)
        else:
            config_pos = 0
        path.extend(config_file_path[config_pos:].split('/'))
        path.append(import_name)
    path.append(version)
    path.append(os.path.basename(config_file))
    gcs_config_file = '/'.join([d.strip('/') for d in path if d])
    if not gcs_config_file.startswith('gs://'):
        gcs_config_file = 'gs://' + gcs_config_file
    if copy_file and config_file != gcs_config_file:
        logging.info(
            f'Copying import config: {config_file} to {gcs_config_file}')
        file_io.file_copy(config_file, gcs_config_file)
    return gcs_config_file


def cloud_run_simple_import_job(
    import_spec: dict,
    config_file: str,
    env: dict = {},
    version: str = '',
    job_id: str = '',
    project_id: str = _DEFAULT_PROJECT,
    location: str = _DEFAULT_LOCATION,
    image: str = _DEFAULT_SIMPLE_IMAGE,
) -> str:
    """Create and run a Cloud Run job for simple a import.

  Args:
    import_spec: dict with import parameters such as 'import_name'. Folder for
      output will have the import_name in the path.
    config_file: json file with config for simple import run. For an example,
      see simple_imports/sample/import_config.json
    env: dictionary of environment variables for the job. Additional variabled
      for CONFIG_FILE and OUTPUT_DIR are added.
    version: a dated version string for file path for output folder.
    project_id: Google project id for the cloud run. The compute engine service
      account for the project should have access to the GCS folder for output.
    location: Region for the cloud run instance.
    image: container image URL for the simple-importer.

  Returns:
    Output directory with the script outputs.
  """
    if not version:
        version = _get_time_version()
    # TODO: support parameters from import_config.json instead of manifest.json
    import_name = import_spec.get('import_name', '')
    # Copy the config file to GCS versioned folder.
    # Cloud run can only access GCS for config files, input and output.
    gcs_config = get_simple_import_gcs_config(config_file,
                                              import_name,
                                              version,
                                              copy_file=True)
    gcs_output_dir = os.path.dirname(gcs_config)

    # Setup environment variables for simple import run.
    # Settings for each import run have to be passed in through ENV variables.
    env_vars = {
        'CONFIG_FILE': gcs_config,
        'OUTPUT_DIR': gcs_output_dir,
    }
    # Add any user script env vars such as DC_API_KEY
    if env:
        env_vars.update(env)

    # Generate job-id from config_file path if not specified.
    if not job_id:
        job_id = get_simple_import_job_id(import_spec, config_file)

    # Create the job for the config.
    # An existing job is updated with new env variables for versioned output
    if not image:
        image = _DEFAULT_SIMPLE_IMAGE
    logging.info(
        f'Setting up simple import cloud run {project_id}:{job_id} for'
        f' {config_file} with output: {gcs_output_dir}, env: {env_vars}')
    job = cloud_run.create_or_update_cloud_run_job(project_id, location, job_id,
                                                   image, env_vars)
    if not job:
        logging.error(
            f'Failed to setup cloud run job {job_id} for {config_file}')
        return None

    # Execute the cloud run job.
    logging.info(f'Running {project_id}:{job_id} for {config_file} with output:'
                 f' {gcs_output_dir}')
    job = cloud_run.execute_cloud_run_job(project_id, location, job_id)
    if not job:
        logging.error(
            f'Failed to execute cloud run job {job_id} for {config_file}')
        return None

    logging.info(
        f'Completed run {project_id}:{job_id} for {config_file} with output:'
        f' {gcs_output_dir}')
    # TODO: get processing status from <output>/report.json
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
