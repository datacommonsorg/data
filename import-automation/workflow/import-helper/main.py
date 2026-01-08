import base64
import functions_framework
import json
import logging
import os
from datetime import datetime, timezone
from google.cloud import spanner
from google.cloud.spanner_v1 import Transaction
import google.cloud.workflows

logging.getLogger().setLevel(logging.INFO)

PROJECT_ID = os.environ.get('PROJECT_ID')
LOCATION = os.environ.get('LOCATION')
WORKFLOW_ID = os.environ.get('WORKFLOW_ID', 'spanner-ingestion-workflow')
SPANNER_PROJECT_ID = os.environ.get('SPANNER_PROJECT_ID')
SPANNER_INSTANCE_ID = os.environ.get('SPANNER_INSTANCE_ID')
SPANNER_DATABASE_ID = os.environ.get('SPANNER_DATABASE_ID')
DEFAULT_GRAPH_PATH = "/**/*.mcf*"


def invoke_ingestion_workflow(import_name):
    """Invokes the spanner ingestion workflow."""
    execution_client = executions_v1.ExecutionsClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/workflows/{WORKFLOW_ID}"
    workflow_args = {"imports": [import_name]}
    try:
        execution_req = workflows.executions_v1.Execution(
            argument=json.dumps(workflow_args))
        response = execution_client.create_execution(parent=parent,
                                                     execution=execution_req)
        logging.info(
            f"Triggered workflow {WORKFLOW_ID} for {import_name}. Execution ID: {response.name}"
        )
    except Exception as e:
        logging.error(f"Error triggering workflow: {e}")


def update_import_status(import_name, dest_dir, status):
    """Updates the status for the specified import job."""
    logging.info(f"Updating import status for {import_name} to {status}")
    try:
        spanner_client = spanner.Client(
            project=SPANNER_PROJECT_ID,
            client_options={'quota_project_id': SPANNER_PROJECT_ID})
        instance = spanner_client.instance(SPANNER_INSTANCE_ID)
        database = instance.database(SPANNER_DATABASE_ID)
        job_id = ''
        exec_time = 0
        data_volume = 0
        version = dest_dir
        next_refresh = datetime.now(timezone.utc)
        graph_paths = [DEFAULT_GRAPH_PATH]

        def _record(transaction: Transaction):
            columns = [
                "ImportName", "State", "JobId", "ExecutionTime", "DataVolume",
                "NextRefreshTimestamp", "LatestVersion", "GraphDataPaths",
                "StatusUpdateTimestamp"
            ]
            row_values = [
                import_name, status, job_id, exec_time, data_volume,
                next_refresh, version, graph_paths, spanner.COMMIT_TIMESTAMP
            ]
            if status == 'READY':
                columns.append("DataImportTimestamp")
                row_values.append(spanner.COMMIT_TIMESTAMP)
            transaction.insert_or_update(table="ImportStatus",
                                         columns=columns,
                                         values=[row_values])
            logging.info(f"Marked {import_name} as {status}.")

        database.run_in_transaction(_record)
        logging.info(f"Updated Spanner status for {import_name}")
    except Exception as e:
        logging.error(f'Error updating import status for {import_name}: {e}')


# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def handle_feed_event(cloud_event):
    # Updates status in spanner and triggers ingestion workflow
    # for an import using CDA feed
    pubsub_message = cloud_event.data['message']
    logging.info(f"Received Pub/Sub message: {pubsub_message}")
    try:
        data_bytes = base64.b64decode(pubsub_message["data"])
        notification_json = data_bytes.decode("utf-8")
        logging.info(f"Notification content: {notification_json}")
    except Exception as e:
        logging.error(f"Error decoding message data: {e}")

    attributes = pubsub_message.get('attributes', {})
    if attributes.get('transfer_status') == 'TRANSFER_COMPLETED':
        feed_type = attributes.get('feed_type')
        import_name = attributes.get('import_name')
        dest_dir = attributes.get('dest_dir')
        if feed_type == 'cns_to_gcs':
            logging.info(f'Updating {import_name} import status')
            update_import_status(import_name, dest_dir, 'READY')
            invoke_ingestion_workflow(import_name)
        else:
            logging.info(f'Unknown feed type: {feed_type}')
