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

from datetime import datetime, timezone
import json
import os
import sys
import time

from absl import app
from absl import logging
from google.cloud import bigquery
from google.cloud.workflows import executions_v1

PROJECT_ID = os.environ.get('PROJECT_ID', 'datcom-ci')
LOCATION = os.environ.get('LOCATION', 'us-central1')
BQ_DATASET_ID = os.environ.get('BQ_DATASET_ID', 'import_automation')
GCS_BUCKET_ID = os.environ.get('GCS_BUCKET_ID', 'datcom-ci-test')
GCS_MOUNT_BUCKET = os.environ.get('GCS_MOUNT_BUCKET', 'datcom-ci-test')
IMPORT_WORKFLOW_ID = os.environ.get('IMPORT_WORKFLOW_ID',
                                    'import-automation-workflow')

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


def verify_bigquery_data(import_name: str, start_timestamp: datetime):
    """Verifies that the import data exists in ImportSummary and ImportHistory in BigQuery."""
    logging.info('Verifying BigQuery data for import: %s in %s.%s', import_name,
                 PROJECT_ID, BQ_DATASET_ID)
    bq_client = bigquery.Client(project=PROJECT_ID)

    summary_table = f'`{PROJECT_ID}.{BQ_DATASET_ID}.ImportSummary`'
    history_table = f'`{PROJECT_ID}.{BQ_DATASET_ID}.ImportHistory`'

    job_config = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter('import_name', 'STRING', import_name),
        bigquery.ScalarQueryParameter('start_ts', 'TIMESTAMP', start_timestamp),
    ])

    query_summary = f"""
        SELECT State, LatestVersion, StatusUpdateTimestamp
        FROM {summary_table}
        WHERE ImportName = @import_name
          AND StatusUpdateTimestamp >= @start_ts
    """
    results_summary = list(
        bq_client.query(query_summary, job_config=job_config).result())

    if not results_summary:
        raise AssertionError(
            f'Import {import_name} not found in {summary_table} with StatusUpdateTimestamp >= {start_timestamp.isoformat()}.'
        )

    row_summary = results_summary[0]
    logging.info(
        'Import %s verified in ImportSummary with state: %s, latest_version: %s, updated_at: %s',
        import_name, row_summary.State, row_summary.LatestVersion,
        row_summary.StatusUpdateTimestamp)

    query_history = f"""
        SELECT Version, Status, Comment, UpdateTimestamp
        FROM {history_table}
        WHERE ImportName = @import_name
          AND UpdateTimestamp >= @start_ts
        ORDER BY UpdateTimestamp DESC
        LIMIT 1
    """
    results_history = list(
        bq_client.query(query_history, job_config=job_config).result())

    if not results_history:
        raise AssertionError(
            f'Import {import_name} not found in {history_table} with UpdateTimestamp >= {start_timestamp.isoformat()}.'
        )

    row_history = results_history[0]
    logging.info(
        'Import %s verified in ImportHistory: version=%s, status=%s, comment=%s, updated_at=%s',
        import_name, row_history.Version, row_history.Status,
        row_history.Comment, row_history.UpdateTimestamp)


def main(argv):
    del argv  # Unused.
    try:
        short_import_name = TEST_IMPORT_NAME.split(':')[-1]
        start_timestamp = datetime.now(timezone.utc)

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

        logging.info('Step 2: Verifying Data in BigQuery...')
        verify_bigquery_data(short_import_name, start_timestamp)

        logging.info('Import automation test completed successfully.')

    except Exception as e:
        logging.error('Import automation test Failed: %s', e)
        sys.exit(1)


if __name__ == '__main__':
    app.run(main)
