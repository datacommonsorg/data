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

import base64
import json
import logging
import os
import croniter
from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google.cloud import storage
from google.cloud.workflows import executions_v1
import requests

logging.getLogger().setLevel(logging.INFO)

PROJECT_ID = os.environ.get('PROJECT_ID')
LOCATION = os.environ.get('LOCATION')
GCS_BUCKET_ID = os.environ.get('GCS_BUCKET_ID')
INGESTION_HELPER_URL = f"https://{LOCATION}-{PROJECT_ID}.cloudfunctions.net/spanner-ingestion-helper"
WORKFLOW_ID = 'spanner-ingestion-workflow'

def invoke_ingestion_workflow(import_name: str):
    """Triggers the graph ingestion workflows.

    Args:
        import_name: The name of the import.
    """
    workflow_args = {"importList": [import_name.split(':')[-1]]}

    logging.info(f"Invoking {WORKFLOW_ID} for {import_name}")
    execution_client = executions_v1.ExecutionsClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/workflows/{WORKFLOW_ID}"
    execution_req = executions_v1.Execution(argument=json.dumps(workflow_args))
    response = execution_client.create_execution(parent=parent,
                                                 execution=execution_req)
    logging.info(
        f"Triggered workflow {WORKFLOW_ID} for {import_name}. Execution ID: {response.name}"
    )


def update_import_status(import_name,
                         import_status,
                         import_version,
                         graph_path,
                         job_id,
                         cron_schedule=None):
    """Updates the status for the specified import job.

    Args:
        import_name: The name of the import.
        import_status: The new status of the import.
        import_version: The version of the import.
        graph_path: The graph path for the import.
        job_id: The job ID associated with the import.
        cron_schedule: The cron schedule for the import (optional).
    """
    logging.info(f"Updating {import_name} status: {import_status}")
    latest_version = 'gs://' + GCS_BUCKET_ID + '/' + import_name.replace(
        ':', '/') + '/' + import_version
    request = {
        'actionType': 'update_import_status',
        'importName': import_name,
        'status': import_status,
        'job_id': job_id,
        'latestVersion': latest_version,
        'graphPath': graph_path
    }
    if cron_schedule:
        try:
            next_refresh = croniter.croniter(
                cron_schedule,
                datetime.now(timezone.utc)).get_next(datetime).isoformat()
            request['nextRefresh'] = next_refresh
        except (croniter.CroniterError) as e:
            logging.error(
                f"Error calculating next refresh from schedule '{cron_schedule}': {e}"
            )
    logging.info(f"Update request: {request}")
    auth_req = Request()
    token = id_token.fetch_id_token(auth_req, INGESTION_HELPER_URL)
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(INGESTION_HELPER_URL,
                             json=request,
                             headers=headers)
    response.raise_for_status()
    logging.info(f"Updated status for {import_name}")


def parse_message(request) -> dict:
    """Processes the incoming Pub/Sub message.

    Args:
        request: The flask request object.

    Returns:
        A dictionary containing the message data, or None if invalid.
    """
    request_json = request.get_json(silent=True)
    if not request_json or 'message' not in request_json:
        logging.error('Invalid Pub/Sub message format')
        return None

    pubsub_message = request_json['message']
    logging.info(f"Received Pub/Sub message: {pubsub_message}")
    try:
        data_bytes = base64.b64decode(pubsub_message["data"])
        notification_json = data_bytes.decode("utf-8")
        logging.info(f"Notification content: {notification_json}")
    except Exception as e:
        logging.error(f"Error decoding message data: {e}")

    return pubsub_message


def check_duplicate(message_id: str):
    """Checks for duplicate messages using a GCS file.

    Args:
        message_id: The ID of the message to check.

    Returns:
        True if the message is a duplicate, False otherwise.
    """
    duplicate = False
    if not message_id:
        return duplicate
    logging.info(f"Checking for existing message: {message_id}")
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_ID)
    blob = bucket.blob(f"google3/transfers/{message_id}")
    try:
        blob.upload_from_string("", if_generation_match=0)
    except Exception:
        duplicate = True
    return duplicate
