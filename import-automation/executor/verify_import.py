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
Integration test for import executor image rollout.
Runs a test import as a Cloud Run job and verifies output from GCS.
"""
import logging
import os

from app.executor import cloud_run
from app.executor import file_io
from test import utils

_PROJECT_ID = 'datcom-ci'
_JOB_ID = 'dc-import-prober'
_LOCATION = 'us-central1'
_GCS_BUCKET = 'datcom-ci-test'
_IMPORT_NAME = 'scripts/us_fed/treasury_constant_maturity_rates:USFed_ConstantMaturityRates'


def run_test():
    logging.basicConfig(level=logging.INFO)
    # Execute the cloud run job.
    logging.info('Running cloud run job: %s', _JOB_ID)
    job = cloud_run.execute_cloud_run_job(_PROJECT_ID, _LOCATION, _JOB_ID)
    if not job:
        logging.error('Failed to execute cloud run job: %s', _JOB_ID)
        raise (AssertionError(f'Failed to execute cloud run job {_JOB_ID}'))
    logging.info('Completed run: %s', _JOB_ID)

    # Download output data from GCS.
    gcs_path = 'gs://' + _GCS_BUCKET + '/' + _IMPORT_NAME.replace(':',
                                                                  '/') + '/'
    file_path = gcs_path + 'latest_version.txt'
    logging.info('Downloading data from GCS: %s', file_path)
    blob = file_io.file_get_gcs_blob(file_path, True)
    if not blob:
        logging.error('Failed to get data from: %s', file_path)
        raise (AssertionError(f'Failed to get data from {file_path}'))
    timestamp = blob.download_as_text()
    file_path = gcs_path + timestamp + '/' + 'treasury_constant_maturity_rates.mcf'
    logging.info('Downloading data from GCS: %s', file_path)
    blob = file_io.file_get_gcs_blob(file_path, True)
    if not blob:
        logging.error('Failed to get data from: %s', file_path)
        raise (AssertionError(f'Failed to get data from {file_path}'))

    # Compare output data with expected data.
    output_file = 'prober_output.mcf'
    blob.download_to_filename(output_file)
    golden_data_file = os.path.join('test', 'data',
                                    'treasury_constant_maturity_rates.mcf')
    if not utils.compare_lines(golden_data_file, output_file, 50):
        raise (AssertionError('Prober failure due to data mismatch'))
    logging.info("Verified mcf file content for import: %s", _IMPORT_NAME)


if __name__ == '__main__':
    run_test()
