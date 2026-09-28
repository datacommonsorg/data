# Copyright 2026 Google LLC
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
"""End-to-end test for import automation Cloud Workflow."""

import json
import os
import sys
import time

from absl import app
from absl import logging
from google.cloud import spanner
from google.cloud.workflows import executions_v1

PROJECT_ID = os.environ.get('PROJECT_ID', 'datcom-ci')
LOCATION = os.environ.get('LOCATION', 'us-central1')
SPANNER_DATABASE_PATH = os.environ.get('SPANNER_DATABASE_PATH')
if SPANNER_DATABASE_PATH and len(SPANNER_DATABASE_PATH.split('/')) >= 6:
    _parts = SPANNER_DATABASE_PATH.split('/')
    SPANNER_PROJECT_ID = _parts[1]
    SPANNER_INSTANCE_ID = _parts[3]
    SPANNER_DATABASE_ID = _parts[5]
else:
    SPANNER_PROJECT_ID = os.environ.get('SPANNER_PROJECT_ID', 'datcom-ci')
    SPANNER_INSTANCE_ID = os.environ.get('SPANNER_INSTANCE_ID',
                                         'datcom-spanner-test')
    SPANNER_DATABASE_ID = os.environ.get('SPANNER_DATABASE_ID', 'dc-test-db')
GCS_BUCKET_ID = os.environ.get('GCS_BUCKET_ID', 'datcom-ci-test')
GCS_MOUNT_BUCKET = os.environ.get('GCS_MOUNT_BUCKET', 'datcom-ci-test')
IMPORT_WORKFLOW_ID = os.environ.get('IMPORT_WORKFLOW_ID',
                                    'import-automation-workflow-staging')

# Test Import Configuration
TEST_IMPORT_NAME = ('scripts/us_fed/treasury_constant_maturity_rates:'
                    'USFed_ConstantMaturityRates_Test')


def trigger_workflow_and_wait(project_id: str, location: str, workflow_id: str,
                              workflow_args: dict):
    """Triggers a Cloud Workflow and waits for its completion."""
    execution_client = executions_v1.ExecutionsClient()
    parent = execution_client.workflow_path(project_id, location, workflow_id)

    logging.info('Triggering workflow: %s with args: %s', workflow_id,
                 workflow_args)

    execution = executions_v1.Execution(argument=json.dumps(workflow_args))
    response = execution_client.create_execution(parent=parent,
                                                 execution=execution)
    execution_name = response.name
    logging.info('Execution started: %s', execution_name)

    backoff_delay = 1
    while True:
        execution = execution_client.get_execution(
            request={'name': execution_name})
        state = execution.state

        if state != executions_v1.Execution.State.ACTIVE:
            logging.info('Execution finished with state: %s', state)
            if state == executions_v1.Execution.State.SUCCEEDED:
                logging.info('Workflow %s succeeded.', workflow_id)
                return execution.result
            logging.error('Workflow %s failed: %s', workflow_id,
                          execution.error)
            raise RuntimeError(
                f'Workflow {workflow_id} failed with state {state}')

        time.sleep(backoff_delay)
        backoff_delay = min(backoff_delay * 2, 60)


def verify_spanner_data(import_name):
    """Verifies that the import data exists in ImportSummary and ImportHistory in Spanner."""
    logging.info('Verifying Spanner data for import: %s', import_name)
    spanner_client = spanner.Client(project=SPANNER_PROJECT_ID)
    instance = spanner_client.instance(SPANNER_INSTANCE_ID)
    database = instance.database(SPANNER_DATABASE_ID)

    with database.snapshot(multi_use=True) as snapshot:
        query_summary = ('SELECT State, LatestVersion FROM ImportSummary '
                         'WHERE ImportName = @import_name')
        params = {'import_name': import_name}
        param_types = {'import_name': spanner.param_types.STRING}

        results_summary = list(
            snapshot.execute_sql(query_summary,
                                 params=params,
                                 param_types=param_types))

        if not results_summary:
            raise AssertionError(
                f'Import {import_name} not found in ImportSummary table.')

        state, latest_version = results_summary[0]
        logging.info(
            'Import %s verified in ImportSummary with state: %s, latest_version: %s',
            import_name, state, latest_version)

        query_history = """
            SELECT Version, Status, Comment
            FROM ImportHistory
            WHERE ImportName = @import_name
            ORDER BY UpdateTimestamp DESC
            LIMIT 1
        """
        results_history = list(
            snapshot.execute_sql(query_history,
                                 params=params,
                                 param_types=param_types))

        if not results_history:
            raise AssertionError(
                f'Import {import_name} not found in ImportHistory table.')

        version, status, comment = results_history[0]
        logging.info(
            'Import %s verified in ImportHistory: version=%s, status=%s, comment=%s',
            import_name, version, status, comment)


def cleanup_spanner(import_name):
    """Cleans up the import data from Spanner to ensure a clean state."""
    logging.info('Cleaning up Spanner data for import: %s', import_name)
    spanner_client = spanner.Client(project=SPANNER_PROJECT_ID)
    instance = spanner_client.instance(SPANNER_INSTANCE_ID)
    database = instance.database(SPANNER_DATABASE_ID)

    def _delete_import(transaction):
        query1 = 'DELETE FROM ImportSummary WHERE ImportName = @import_name'
        query2 = 'DELETE FROM ImportHistory WHERE ImportName = @import_name'
        params = {'import_name': import_name}
        param_types = {'import_name': spanner.param_types.STRING}
        transaction.execute_update(query1,
                                   params=params,
                                   param_types=param_types)
        transaction.execute_update(query2,
                                   params=params,
                                   param_types=param_types)

    try:
        database.run_in_transaction(_delete_import)
        logging.info(
            'Successfully cleaned up %s from ImportSummary and ImportHistory tables.',
            import_name)
    except Exception as e:
        logging.warning('Error during Spanner cleanup: %s', e)


def main(argv):
    del argv  # Unused.
    try:
        logging.info('Step 0: Cleanup Spanner...')
        short_import_name = TEST_IMPORT_NAME.split(':')[-1]
        cleanup_spanner(short_import_name)

        import_config = {
            'gcp_project_id': PROJECT_ID,
            'gcs_project_id': PROJECT_ID,
            'storage_prod_bucket_name': GCS_BUCKET_ID,
            'gcs_bucket_volume_mount': GCS_MOUNT_BUCKET
        }

        import_workflow_args = {
            'importName': TEST_IMPORT_NAME,
            'importConfig': json.dumps(import_config),
            'dryRunIngestion': 'true',
        }
        if os.environ.get('SKIP_IMPORT_JOB'):
            import_workflow_args['skipImportJob'] = os.environ.get(
                'SKIP_IMPORT_JOB')
        if os.environ.get('IMAGE_URI'):
            import_workflow_args['imageUri'] = os.environ.get('IMAGE_URI')

        logging.info('Step 1: Running Import Automation Workflow...')
        workflow_result = trigger_workflow_and_wait(PROJECT_ID, LOCATION,
                                                    IMPORT_WORKFLOW_ID,
                                                    import_workflow_args)
        logging.info('Workflow result: %s', workflow_result)

        logging.info('Step 2: Verifying Data in Spanner...')
        verify_spanner_data(short_import_name)

        logging.info('Import automation test completed successfully.')

    except Exception as e:
        logging.error('Import automation test Failed: %s', e)
        sys.exit(1)


if __name__ == '__main__':
    app.run(main)
