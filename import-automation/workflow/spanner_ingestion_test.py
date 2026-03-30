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
"""
End-to-end test for import automation and Spanner ingestion workflows.
"""

import json
import os
import sys

from absl import app
from absl import logging

# Add path for executor modules
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../executor/app')))
from executor import cloud_workflow

from google.cloud import spanner

PROJECT_ID = os.environ.get('PROJECT_ID', 'datcom-ci')
LOCATION = os.environ.get('LOCATION', 'us-central1')
SPANNER_PROJECT_ID = os.environ.get('SPANNER_PROJECT_ID', 'datcom-ci')
SPANNER_INSTANCE_ID = os.environ.get('SPANNER_INSTANCE_ID',
                                     'datcom-spanner-test')
SPANNER_DATABASE_ID = os.environ.get('SPANNER_DATABASE_ID', 'dc-test-db')
GCS_BUCKET_ID = os.environ.get('GCS_BUCKET_ID', 'datcom-ci-test')
IMPORT_WORKFLOW_ID = 'import-automation-workflow'
INGESTION_WORKFLOW_ID = 'spanner-ingestion-workflow'

# Test Import Configuration
TEST_IMPORT_NAME = 'scripts/us_fed/treasury_constant_maturity_rates:USFed_ConstantMaturityRates_Test'


def verify_spanner_data(import_name):
    """Verifies that the import data exists and is marked as SUCCESS in Spanner."""
    logging.info(f"Verifying Spanner data for import: {import_name}")
    spanner_client = spanner.Client(project=SPANNER_PROJECT_ID)
    instance = spanner_client.instance(SPANNER_INSTANCE_ID)
    database = instance.database(SPANNER_DATABASE_ID)

    try:
        with database.snapshot(multi_use=True) as snapshot:
            # Check ImportStatus table
            query = "SELECT State FROM ImportStatus WHERE ImportName = @import_name"
            params = {"import_name": import_name}
            param_types = {"import_name": spanner.param_types.STRING}

            results = list(
                snapshot.execute_sql(query,
                                     params=params,
                                     param_types=param_types))

            if not results:
                raise AssertionError(
                    f"Import {import_name} not found in ImportStatus table.")

            state = results[0][0]
            if state != 'SUCCESS':
                raise AssertionError(
                    f"Import {import_name} state is {state}, expected 'SUCCESS'."
                )

            logging.info(
                f"Import {import_name} verified in ImportStatus with state: {state}"
            )

            # Check IngestionHistory table (optional, but good for E2E)
            # We look for a recent entry containing this import
            query_history = """
                SELECT count(*) 
                FROM IngestionHistory 
                WHERE @import_name IN UNNEST(IngestedImports)
            """
            results_history = list(
                snapshot.execute_sql(query_history,
                                     params=params,
                                     param_types=param_types))
            count = results_history[0][0]

            if count == 0:
                raise AssertionError(
                    f"Import {import_name} not found in IngestionHistory table."
                )

            logging.info(f"Import {import_name} verified in IngestionHistory.")

    except Exception as e:
        logging.error(f"Spanner verification failed: {e}")
        raise


def cleanup_spanner(import_name):
    """Cleans up the import data from Spanner to ensure a clean state."""
    logging.info(f"Cleaning up Spanner data for import: {import_name}")
    spanner_client = spanner.Client(project=SPANNER_PROJECT_ID)
    instance = spanner_client.instance(SPANNER_INSTANCE_ID)
    database = instance.database(SPANNER_DATABASE_ID)

    def _delete_import(transaction):
        query = "DELETE FROM ImportStatus WHERE ImportName = @import_name"
        params = {"import_name": import_name}
        param_types = {"import_name": spanner.param_types.STRING}
        transaction.execute_update(query,
                                   params=params,
                                   param_types=param_types)

    try:
        database.run_in_transaction(_delete_import)
        logging.info(
            f"Successfully cleaned up {import_name} from ImportStatus table.")
    except Exception as e:
        logging.warning(f"Error during Spanner cleanup: {e}")


def main(argv):
    del argv  # Unused.
    try:
        # 0. Cleanup Spanner
        logging.info("Step 0: Cleanup Spanner...")
        short_import_name = TEST_IMPORT_NAME.split(':')[-1]
        cleanup_spanner(short_import_name)

        # 1. Trigger Import Automation Workflow
        job_name = "test-import"
        import_config = {
            "gcp_project_id": PROJECT_ID,
            "gcs_project_id": PROJECT_ID,
            "storage_prod_bucket_name": GCS_BUCKET_ID,
            "gcs_bucket_volume_mount": GCS_BUCKET_ID
        }

        import_workflow_args = {
            "importName": TEST_IMPORT_NAME,
            "importConfig": json.dumps(import_config),
        }

        logging.info("Step 1: Running Import Automation Workflow...")
        cloud_workflow.trigger_workflow_and_wait(PROJECT_ID, LOCATION,
                                                 IMPORT_WORKFLOW_ID,
                                                 import_workflow_args)

        # 2. Trigger Spanner Ingestion Workflow
        ingestion_workflow_args = {"importList": [short_import_name]}

        logging.info("Step 2: Running Spanner Ingestion Workflow...")
        cloud_workflow.trigger_workflow_and_wait(PROJECT_ID, LOCATION,
                                                 INGESTION_WORKFLOW_ID,
                                                 ingestion_workflow_args)

        # 3. Verify Data in Spanner
        logging.info("Step 3: Verifying Data in Spanner...")
        verify_spanner_data(short_import_name)

        logging.info("Spanner ingestion test completed successfully.")

    except Exception as e:
        logging.error(f"Spanner ingestion test Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app.run(main)
