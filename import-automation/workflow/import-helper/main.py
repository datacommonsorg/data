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
import functions_framework
import json
import logging
import os
from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google.cloud.workflows import executions_v1
import requests

logging.getLogger().setLevel(logging.INFO)

PROJECT_ID = os.environ.get('PROJECT_ID')
LOCATION = os.environ.get('LOCATION')
GCS_BUCKET_ID = os.environ.get('GCS_BUCKET_ID')
WORKFLOW_ID = 'spanner-ingestion-workflow'
INGESTION_HELPER_URL = f"https://{LOCATION}-{PROJECT_ID}.cloudfunctions.net/spanner-ingestion-helper"


def invoke_ingestion_workflow(import_name):
    """Invokes the spanner ingestion workflow."""
    execution_client = executions_v1.ExecutionsClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/workflows/{WORKFLOW_ID}"
    workflow_args = {"importList": [import_name]}
    try:
        execution_req = executions_v1.Execution(
            argument=json.dumps(workflow_args))
        response = execution_client.create_execution(parent=parent,
                                                     execution=execution_req)
        logging.info(
            f"Triggered workflow {WORKFLOW_ID} for {import_name}. Execution ID: {response.name}"
        )
    except Exception as e:
        logging.error(f"Error triggering workflow: {e}")


def update_import_status(import_name, request_json):
    """Updates the status for the specified import job."""
    try:
        auth_req = Request()
        token = id_token.fetch_id_token(auth_req, INGESTION_HELPER_URL)
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(INGESTION_HELPER_URL,
                                 json=request_json,
                                 headers=headers)
        response.raise_for_status()
        logging.info(f"Updated status for {import_name}")
    except Exception as e:
        logging.error(f'Error updating import status for {import_name}: {e}')


# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.http
def handle_feed_event(request):
    # Updates status in spanner and triggers ingestion workflow
    # for an import using CDA feed
    request_json = request.get_json(silent=True)
    if not request_json or 'message' not in request_json:
        return 'Invalid Pub/Sub message format', 400

    pubsub_message = request_json['message']
    logging.info(f"Received Pub/Sub message: {pubsub_message}")
    try:
        data_bytes = base64.b64decode(pubsub_message["data"])
        notification_json = data_bytes.decode("utf-8")
        logging.info(f"Notification content: {notification_json}")
    except Exception as e:
        logging.error(f"Error decoding message data: {e}")

    attributes = pubsub_message.get('attributes', {})
    if attributes.get('transfer_status') == 'TRANSFER_COMPLETED':
        import_name = attributes.get('import_name')
        import_status = attributes.get('import_status', 'STAGING')
        import_version = 'gs://' + GCS_BUCKET_ID + '/' + import_name.replace(
            ':', '/') + '/' + attributes.get(
                'import_version',
                datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        graph_path = attributes.get('graph_path', "/**/*mcf*")
        request = {
            'actionType': 'update_import_status',
            'importName': import_name,
            'status': import_status,
            'latestVersion': import_version,
            'nextRefresh': datetime.now(timezone.utc).isoformat(),
            'graphPath': graph_path
        }

        logging.info(
            f"Updating import status for {import_name} to {import_status}")
        update_import_status(import_name, request)
        if import_status == 'READY':
            invoke_ingestion_workflow(import_name)

    return 'OK', 200
