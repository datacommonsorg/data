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
"""Utility functions for the ingestion helper."""

import logging
import re
from datetime import datetime, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth import jwt


def get_next_refresh(project_id: str, location: str, import_name: str) -> str:
    """Fetches the next scheduled run time for the import job from Cloud Scheduler.

    Args:
        project_id: The GCP project ID.
        location: The location of the Cloud Scheduler job.
        import_name: The name of the import (used as the job name).

    Returns:
        The next scheduled run time as an ISO formatted string, or None if not found/error.
    """
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


def get_caller_identity(request):
    """Extracts the caller's email from the Authorization header (JWT).

    Args:
        request: The HTTP request object.

    Returns:
        The email of the caller, or an error string/warning if extraction fails.
    """
    auth_header = request.headers.get('Authorization')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]
            unverified_claims = {}
            try:
                unverified_claims = jwt.decode(token, verify=False)
                id_info = id_token.verify_oauth2_token(token,
                                                       requests.Request())
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


def get_import_params(request) -> dict:
    """Extracts and calculates import parameters from the request JSON.

    Args:
        request_json: A dictionary containing request parameters.

    Returns:
        A dictionary with import params.
    """
    # Convert CamelCase or mixedCase to snake_case.
    request_json = {
        re.sub(r'(?<!^)(?=[A-Z])', '_', k).lower(): v
        for k, v in request.items()
    }

    import_name = request_json.get('import_name', '').split(':')[-1]
    status = request_json.get('status', '').removeprefix('ImportStatus.')
    job_id = request_json.get('job_id', '')
    execution_time = request_json.get('execution_time', 0)
    data_volume = request_json.get('data_volume', 0)
    latest_version = request_json.get('latest_version', '')
    graph_path = request_json.get('graph_path', '')
    next_refresh = request_json.get('next_refresh',
                                    datetime.now(timezone.utc).isoformat())

    return {
        'import_name': import_name,
        'status': status,
        'job_id': job_id,
        'execution_time': execution_time,
        'data_volume': data_volume,
        'latest_version': latest_version,
        'graph_path': graph_path,
        'next_refresh': next_refresh
    }


def get_ingestion_metrics(project_id, location, job_id):
    """Fetches graph metrics (nodes, edges, observations) and execution time from a Dataflow job.

    Args:
        project_id: The GCP project ID.
        location: The location of the Dataflow job.
        job_id: The Dataflow job ID.

    Returns:
        A dictionary containing 'obs_count', 'node_count', 'edge_count', and 'execution_time'.
    """
    dataflow = build('dataflow', 'v1b3', cache_discovery=False)
    # Fetch Dataflow metrics
    node_count = 0
    edge_count = 0
    obs_count = 0
    execution_time = 0
    if project_id and job_id:
        try:
            # Fetch Job details for execution time
            job = dataflow.projects().locations().jobs().get(
                projectId=project_id, location=location,
                jobId=job_id).execute()

            start_time_str = job.get('startTime')
            current_state_time_str = job.get('currentStateTime')

            if start_time_str and current_state_time_str:
                # Handle potential 'Z' suffix by replacing it with '+00:00' for compatibility
                start_time = datetime.fromisoformat(
                    start_time_str.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(
                    current_state_time_str.replace('Z', '+00:00'))
                execution_time = int((end_time - start_time).total_seconds())

            metrics = dataflow.projects().locations().jobs().getMetrics(
                projectId=project_id, location=location,
                jobId=job_id).execute()
            for metric in metrics.get('metrics', []):
                name = metric['name']['name']
                if name == 'graph_node_count':
                    node_count += int(metric['scalar'])
                elif name == 'graph_edge_count':
                    edge_count += int(metric['scalar'])
                elif name == 'graph_observation_count':
                    obs_count += int(metric['scalar'])
        except HttpError as e:
            logging.error(
                f"Error fetching dataflow metrics for job {job_id}: {e}")
    return {
        'obs_count': obs_count,
        'node_count': node_count,
        'edge_count': edge_count,
        'execution_time': execution_time
    }
