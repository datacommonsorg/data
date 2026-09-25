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
"""Utility functions for import helper."""

import base64
from datetime import datetime, timezone
import json
import logging
import os
import re
import config
import google.auth
from google.auth import jwt
from google.auth.transport.requests import Request
from google.cloud import storage
from google.cloud.workflows import executions_v1
from google.oauth2 import id_token
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests

logging.getLogger().setLevel(logging.INFO)


def get_full_version_path(gcs_bucket_id: str,
                          import_name: str,
                          import_version: str,
                          graph_path: str = "/**/*.mcf*") -> str:
    """Constructs the full GCS path including the graph path pattern."""
    base_path = f"gs://{gcs_bucket_id}/{import_name.replace(':', '/')}/{import_version}"
    return f"{base_path.rstrip('/')}/{graph_path.lstrip('/')}"


def parse_message(request_json: dict) -> dict | None:
    """Processes incoming Pub/Sub push message payload."""
    if not request_json or 'message' not in request_json:
        logging.error('Invalid Pub/Sub message format')
        return None

    pubsub_message = request_json['message']
    logging.info(f"Received Pub/Sub message: {pubsub_message}")
    try:
        data_bytes = base64.b64decode(pubsub_message.get("data", ""))
        notification_json = data_bytes.decode("utf-8")
        logging.info(f"Notification content: {notification_json}")
    except Exception as e:
        logging.error(f"Error decoding message data: {e}")

    return pubsub_message


def check_duplicate(gcs_bucket_id: str, message_id: str) -> bool:
    """Checks for duplicate messages using a GCS sentinel file."""
    if not message_id or not gcs_bucket_id:
        return False
    logging.info(f"Checking for existing message: {message_id}")
    storage_client = storage.Client()
    bucket = storage_client.bucket(gcs_bucket_id)
    blob = bucket.blob(f"google3/transfers/{message_id}")
    try:
        blob.upload_from_string("", if_generation_match=0)
        return False
    except Exception:
        return True


def invoke_spanner_ingestion_workflow(project_id: str,
                                      location: str,
                                      workflow_id: str,
                                      import_name: str,
                                      latest_version: str = ""):
    """Triggers the Spanner ingestion workflow."""
    workflow_args = {
        "importList": [{
            "importName": import_name.split(':')[-1],
            "latestVersion": latest_version
        }]
    }

    logging.info(f"Invoking {workflow_id} for {import_name}")
    execution_client = executions_v1.ExecutionsClient()
    parent = f"projects/{project_id}/locations/{location}/workflows/{workflow_id}"
    execution_req = executions_v1.Execution(argument=json.dumps(workflow_args))
    response = execution_client.create_execution(parent=parent,
                                                 execution=execution_req)
    logging.info(
        f"Triggered workflow {workflow_id} for {import_name}. Execution ID: {response.name}"
    )
    return response


def invoke_import_automation_workflow(project_id: str,
                                      location: str,
                                      workflow_id: str,
                                      import_name: str,
                                      latest_version: str,
                                      import_size: str = 'small',
                                      graph_path: str = "/**/*.mcf*",
                                      cron_schedule: str = "",
                                      skip_import_job: bool | None = None,
                                      skip_staging_ingestion: bool | None = None,
                                      skip_prod_ingestion: bool | None = None):
    """Triggers the import automation workflow."""
    import_config = {
        "user_script_args": [f"--version={latest_version}"],
        "import_version_override": latest_version,
        "graph_data_path": graph_path,
        "cron_schedule_override": cron_schedule
    }
    workflow_args = {
        "importName": import_name,
        "importConfig": json.dumps(import_config),
    }
    if skip_import_job is not None:
        workflow_args["skipImportJob"] = skip_import_job
    if skip_staging_ingestion is not None:
        workflow_args["skipStagingIngestion"] = skip_staging_ingestion
    if skip_prod_ingestion is not None:
        workflow_args["skipProdIngestion"] = skip_prod_ingestion

    if import_size == 'large':
        workflow_args["resources"] = {
            "machine": "n2-highmem-16",
            "cpu": 16000,
            "memory": 131072,
            "disk": 100
        }
    elif import_size == 'medium':
        workflow_args["resources"] = {
            "machine": "n2-highmem-8",
            "cpu": 8000,
            "memory": 65536,
            "disk": 100
        }
    else:
        workflow_args["resources"] = {
            "machine": "n2-standard-8",
            "cpu": 8000,
            "memory": 32768,
            "disk": 100
        }

    logging.info(f"Invoking {workflow_id} for {import_name}")
    execution_client = executions_v1.ExecutionsClient()
    parent = f"projects/{project_id}/locations/{location}/workflows/{workflow_id}"
    execution_req = executions_v1.Execution(argument=json.dumps(workflow_args))
    response = execution_client.create_execution(parent=parent,
                                                 execution=execution_req)
    logging.info(
        f"Triggered workflow {workflow_id} for {import_name}. Execution ID: {response.name}"
    )
    return response


def invoke_import_automation_airflow(import_name: str,
                                     latest_version: str,
                                     import_size: str = 'small',
                                     graph_path: str = "/**/*.mcf*",
                                     cron_schedule: str = "",
                                     dag_id: str | None = None,
                                     skip_import_job: bool | None = None,
                                     skip_staging_ingestion: bool | None = None,
                                     skip_prod_ingestion: bool | None = None):
    """Triggers the import automation DAG in Cloud Composer (Airflow).

    Args:
        import_name: The name of the import (e.g. 'scripts/entities:Schema' or 'Schema').
        latest_version: The version of the import.
        import_size: The size of the import ('small', 'medium', 'large').
        graph_path: The graph path for the import.
        cron_schedule: The cron schedule for the import.
        dag_id: Optional Airflow DAG ID to invoke; defaults to generic manual_refresh DAG.
        skip_import_job: Whether to skip the import batch job.
        skip_staging_ingestion: Whether to skip staging Spanner ingestion.
        skip_prod_ingestion: Whether to skip production Spanner ingestion.
    """
    short_import_name = import_name.split(':')[-1]
    target_dag_id = dag_id if dag_id else config.AIRFLOW_DEFAULT_DAG_ID
    full_import_name = (
        import_name if ':' in import_name else f"scripts/entities:{import_name}"
    )

    import_config = {
        "user_script_args": [f"--version={latest_version}"],
        "import_version_override": latest_version,
        "graph_data_path": graph_path,
        "cron_schedule_override": cron_schedule
    }
    if short_import_name == 'Schema' or target_dag_id == 'Schema':
        import_config.update({
            "invoke_import_validation": True,
            "invoke_import_tool": True,
            "invoke_differ_tool": True,
            "skip_input_upload": True
        })

    if import_size == 'large':
        resources = {
            "machine": "n2-highmem-16",
            "cpu": 16000,
            "memory": 131072,
            "disk": 100
        }
    elif import_size == 'medium':
        resources = {
            "machine": "n2-highmem-8",
            "cpu": 8000,
            "memory": 65536,
            "disk": 100
        }
    else:
        resources = {
            "machine": "n2-standard-8",
            "cpu": 8000,
            "memory": 32768,
            "disk": 100
        }

    conf = {
        "importName": full_import_name,
        "importConfig": import_config,
        "resources": resources,
    }
    if skip_import_job is not None:
        conf["skipImportJob"] = skip_import_job
    if skip_staging_ingestion is not None:
        conf["skipStagingIngestion"] = skip_staging_ingestion
    if skip_prod_ingestion is not None:
        conf["skipProdIngestion"] = skip_prod_ingestion

    dag_run_id = f"cda_feed__{short_import_name}__{latest_version}__{int(datetime.now(timezone.utc).timestamp())}"
    payload = {
        "dag_run_id": dag_run_id,
        "conf": conf
    }

    if not config.AIRFLOW_WEB_SERVER_URL:
        raise ValueError("AIRFLOW_WEB_SERVER_URL is not configured.")

    base_url = config.AIRFLOW_WEB_SERVER_URL.rstrip('/')
    url = f"{base_url}/api/v1/dags/{target_dag_id}/dagRuns"
    logging.info(f"Invoking Airflow DAG {target_dag_id} for {import_name} at {url}")

    if config.AIRFLOW_IAP_CLIENT_ID:
        token = id_token.fetch_id_token(Request(), config.AIRFLOW_IAP_CLIENT_ID)
    else:
        credentials, _ = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform'])
        credentials.refresh(Request())
        token = credentials.token

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    if response.status_code == 404 and target_dag_id != config.AIRFLOW_DEFAULT_DAG_ID:
        logging.warning(
            f"Airflow DAG '{target_dag_id}' not found (404). "
            f"Falling back to generic DAG '{config.AIRFLOW_DEFAULT_DAG_ID}'."
        )
        target_dag_id = config.AIRFLOW_DEFAULT_DAG_ID
        url = f"{base_url}/api/v1/dags/{target_dag_id}/dagRuns"
        response = requests.post(url, json=payload, headers=headers, timeout=60)

    response.raise_for_status()
    logging.info(
        f"Triggered Airflow DAG {target_dag_id} for {import_name}. Run ID: {dag_run_id}"
    )
    return response


def get_next_refresh(project_id: str, location: str, import_name: str) -> str | None:
    """Fetches the next scheduled run time for the import job from Cloud Scheduler."""
    try:
        scheduler = build('cloudscheduler', 'v1', cache_discovery=False)
        job_id = import_name.split(':')[-1]
        job_name = f"projects/{project_id}/locations/{location}/jobs/{job_id}"
        job = scheduler.projects().locations().jobs().get(
            name=job_name).execute()
        return job.get('scheduleTime')
    except HttpError as e:
        logging.warning(f"Could not fetch scheduler job {import_name}: {e}")
        return None
    except Exception as e:
        logging.warning(f"Error connecting to Cloud Scheduler for {import_name}: {e}")
        return None


def get_caller_identity(request):
    """Extracts caller email from Authorization header (JWT)."""
    auth_header = request.headers.get('Authorization')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]
            unverified_claims = {}
            try:
                unverified_claims = jwt.decode(token, verify=False)
                id_info = id_token.verify_oauth2_token(token,
                                                       Request())
                return id_info.get('email', 'unknown_email')
            except Exception as e:
                if unverified_claims:
                    logging.warning(
                        f"Could not decode unverified token for debugging: {e}")
                    email = unverified_claims.get('email', 'unknown_email')
                    return f"{email}"
                return 'decode_error'
        else:
            logging.warning(
                f"Invalid Authorization header format. Parts: {len(parts)}")
    else:
        logging.warning("No Authorization header received.")
    return 'no_auth_header'


def get_import_params(request: dict) -> dict:
    """Extracts and calculates import parameters from the request JSON."""
    request_json = {
        re.sub(r'(?<!^)(?=[A-Z])', '_', k).lower(): v
        for k, v in request.items()
    }

    import_name = request_json.get('import_name', '')
    status = request_json.get('status', '').removeprefix('ImportStatus.')
    job_id = request_json.get('job_id', '')
    workflow_id = request_json.get('workflow_id', '')
    execution_time = request_json.get('execution_time', 0)
    data_volume = request_json.get('data_volume', 0)
    latest_version = request_json.get('latest_version', '')
    graph_path = request_json.get('graph_path', '')
    next_refresh = request_json.get('next_refresh',
                                    datetime.now(timezone.utc).isoformat())

    if graph_path:
        if graph_path.startswith('gs://'):
            latest_version = graph_path
        elif latest_version:
            clean_graph_path = graph_path.lstrip('/')
            if not latest_version.rstrip('/').endswith(clean_graph_path.rstrip('/')):
                latest_version = f"{latest_version.rstrip('/')}/{clean_graph_path}"

    return {
        'import_name': import_name,
        'status': status,
        'job_id': job_id,
        'workflow_id': workflow_id,
        'execution_time': execution_time,
        'data_volume': data_volume,
        'latest_version': latest_version,
        'graph_path': graph_path,
        'next_refresh': next_refresh
    }
