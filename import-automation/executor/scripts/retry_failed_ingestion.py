#!/usr/bin/env python3
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
"""Script to automate the retry process for failed Dataflow ingestion jobs.

This script identifies failed imports within a specific Dataflow job,
reverts the failed imports in the Spanner database to their last known
good version, resets any 'PENDING' imports back to 'STAGING', and
optionally retriggers the Spanner ingestion workflow.

Usage:
    python3 retry_failed_ingestion.py --job_id=<DATAFLOW_JOB_ID> \
        --project_id=datcom-import-automation-prod \
        --spanner_project=datcom-store \
        --spanner_instance=dc-kg-test \
        --spanner_database=dc_graph_import
"""

import json
import sys

from absl import app
from absl import flags
from absl import logging
from google.cloud import spanner
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

FLAGS = flags.FLAGS

flags.DEFINE_string("project_id", "datcom-import-automation-prod",
                    "GCP Project ID")
flags.DEFINE_string("location", "us-central1", "GCP Location")
flags.DEFINE_string("job_id", None, "Failed Dataflow Job ID", required=True)
flags.DEFINE_string("spanner_project", "datcom-store", "Spanner Project ID")
flags.DEFINE_string("spanner_instance", "dc-kg-test", "Spanner Instance ID")
flags.DEFINE_string("spanner_database", "dc_graph_import",
                    "Spanner Database ID")
flags.DEFINE_string("workflow_name", "spanner-ingestion-workflow",
                    "Workflow name")


def get_failed_imports(dataflow, project_id, location, job_id):
    """Identifies failed import names from Dataflow job messages and parameters.

    Args:
        dataflow: An authenticated Google Cloud Dataflow API client.
        project_id: The GCP Project ID where the Dataflow job ran.
        location: The GCP location of the Dataflow job (e.g., 'us-central1').
        job_id: The unique ID of the failed Dataflow job.

    Returns:
        A list of strings representing the names of the imports that failed
        during the Dataflow job.
    """
    failed_imports = set()
    try:
        logging.info(f"Fetching job details for {job_id}...")
        job = dataflow.projects().locations().jobs().get(
            projectId=project_id,
            location=location,
            jobId=job_id,
            view='JOB_VIEW_ALL').execute()

        # Get all imports involved in this job from displayData.
        all_import_names = set()
        import_list_json = None
        for item in job.get('pipelineDescription', {}).get('displayData', []):
            if item.get('key') == 'importList':
                import_list_json = item.get('strValue')
                break

        if import_list_json:
            try:
                all_imports_data = json.loads(import_list_json)
                all_import_names = {
                    i['importName'].split(':')[-1] for i in all_imports_data
                }
                logging.info(
                    f"Imports involved in this job: {all_import_names}")
            except Exception as e:
                logging.error(f"Error parsing importList parameter: {e}")

        logging.info(f"Fetching error messages for Dataflow job {job_id}...")
        messages = dataflow.projects().locations().jobs().messages().list(
            projectId=project_id,
            location=location,
            jobId=job_id,
            minimumImportance='JOB_MESSAGE_ERROR').execute()

        for msg in messages.get('jobMessages', []):
            text = msg.get('messageText', '')
            # If we find a valid import name in the error message, add it.
            for name in all_import_names:
                if name in text:
                    failed_imports.add(name)

        # If the job failed globally and we haven't identified specific imports,
        # or if we want to be safe, include all imports if the state is failed.
        if job.get('currentState') in [
                'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED'
        ]:
            if not failed_imports:
                logging.warning(
                    "Job failed globally. Reverting all involved imports.")
                failed_imports.update(all_import_names)
            else:
                logging.info(
                    f"Job failed. Identified specific failed imports: {failed_imports}"
                )

    except HttpError as e:
        logging.error(f"Error querying Dataflow API: {e}")

    return list(failed_imports)


def revert_import(database, import_name, job_id):
    """Reverts an import to its previous version in Spanner and sets it to STAGING.

    This function updates the ImportStatus and ImportVersionHistory tables in
    Spanner to effectively rollback an import that failed during the Dataflow job.

    Args:
        database: An initialized Spanner Database object.
        import_name: The name of the import to revert (e.g., 'foo:bar:import').
        job_id: The ID of the failed Dataflow job, used for commenting.

    Returns:
        True if the revert was successful, 'ALREADY_REVERTED' if the import
        was recently reverted, or False if no version history was found or an
        error occurred.
    """
    short_name = import_name.split(':')[-1]

    def _revert_txn(transaction):
        # 1. Fetch the most recent version and comment from ImportVersionHistory.
        sql = """
            SELECT Version, Comment FROM ImportVersionHistory
            WHERE ImportName = @importName
            ORDER BY UpdateTimestamp DESC
            LIMIT 1
        """
        results = transaction.execute_sql(
            sql,
            params={'importName': short_name},
            param_types={'importName': spanner.param_types.STRING})
        rows = list(results)

        if not rows:
            logging.warning(
                f"No version history found for '{short_name}'. Cannot revert.")
            return False

        previous_version = rows[0][0]
        previous_comment = rows[0][1] if len(rows[0]) > 1 else ""

        if previous_comment and "Reverted due to Dataflow failure" in previous_comment:
            logging.error(
                f"Import '{short_name}' was already reverted recently. Aborting to prevent infinite loop."
            )
            return "ALREADY_REVERTED"

        logging.info(
            f"Reverting '{short_name}' to last known good version: {previous_version}"
        )

        # 2. Update ImportStatus to point to the previous version and set state to STAGING.
        param_types = {
            'version': spanner.param_types.STRING,
            'importName': spanner.param_types.STRING
        }

        transaction.execute_update("""
            UPDATE ImportStatus
            SET LatestVersion = @version, State = 'STAGING', StatusUpdateTimestamp = PENDING_COMMIT_TIMESTAMP()
            WHERE ImportName = @importName
            """,
                                   params={
                                       'version': previous_version,
                                       'importName': short_name
                                   },
                                   param_types=param_types)

        # 3. Add an entry to ImportVersionHistory to record the revert action.
        transaction.execute_update(
            """
            INSERT INTO ImportVersionHistory (ImportName, Version, UpdateTimestamp, Comment)
            VALUES (@importName, @version, PENDING_COMMIT_TIMESTAMP(), @comment)
            """,
            params={
                'importName': short_name,
                'version': previous_version,
                'comment': f"Reverted due to Dataflow failure ({job_id})"
            },
            param_types={
                'importName': spanner.param_types.STRING,
                'version': spanner.param_types.STRING,
                'comment': spanner.param_types.STRING
            })
        return True

    try:
        return database.run_in_transaction(_revert_txn)
    except Exception as e:
        logging.error(f"Transaction failed for '{short_name}': {e}")
        return False


def reset_pending_imports(database):
    """Resets all imports with state 'PENDING' back to 'STAGING'.

    This ensures that any imports that were stuck in a PENDING state due to
    the failure are put back into the queue for processing.

    Args:
        database: An initialized Spanner Database object.
    """
    logging.info("Resetting all PENDING imports to STAGING...")

    def _reset_txn(transaction):
        return transaction.execute_update("""
            UPDATE ImportStatus
            SET State = 'STAGING', StatusUpdateTimestamp = PENDING_COMMIT_TIMESTAMP()
            WHERE State = 'PENDING'
            """)

    try:
        count = database.run_in_transaction(_reset_txn)
        logging.info(f"Successfully reset {count} PENDING imports to STAGING.")
    except Exception as e:
        logging.error(f"Failed to reset PENDING imports: {e}")


def retrigger_workflow(project_id, location, workflow_name):
    """Retriggers the Spanner ingestion workflow with a retry flag.

    Args:
        project_id: The GCP Project ID where the workflow is hosted.
        location: The GCP location of the workflow (e.g., 'us-central1').
        workflow_name: The name of the workflow to execute.
    """
    logging.info(f"Retriggering workflow '{workflow_name}'...")
    try:
        service = build('workflowexecutions', 'v1', cache_discovery=False)
        parent = f"projects/{project_id}/locations/{location}/workflows/{workflow_name}"
        # Pass is_retry=True as a workflow argument.
        execution = service.projects().locations().workflows().executions(
        ).create(parent=parent,
                 body={
                     "argument": json.dumps({"is_retry": True})
                 }).execute()
        logging.info(
            f"Retriggered successfully. New execution: {execution.get('name')}")
    except Exception as e:
        logging.error(f"Failed to retrigger workflow: {e}")


def main(argv):
    """Main entry point for the script.

    Args:
        argv: Command-line arguments passed to the script.
    """
    dataflow = build('dataflow', 'v1b3', cache_discovery=False)
    failed_imports = get_failed_imports(dataflow, FLAGS.project_id,
                                        FLAGS.location, FLAGS.job_id)

    if not failed_imports:
        logging.error("No failed imports identified.")
        sys.exit(1)

    logging.info(f"Processing failed imports: {failed_imports}")
    spanner_client = spanner.Client(project=FLAGS.spanner_project)
    instance = spanner_client.instance(FLAGS.spanner_instance)
    database = instance.database(FLAGS.spanner_database)

    can_retrigger = True
    for imp in failed_imports:
        status = revert_import(database, imp, FLAGS.job_id)
        if status == "ALREADY_REVERTED":
            can_retrigger = False

    if can_retrigger:
        reset_pending_imports(database)
        retrigger_workflow(FLAGS.project_id, FLAGS.location,
                           FLAGS.workflow_name)
    else:
        logging.warning(
            "Skipping re-trigger because at least one import was already reverted."
        )


if __name__ == "__main__":
    app.run(main)
