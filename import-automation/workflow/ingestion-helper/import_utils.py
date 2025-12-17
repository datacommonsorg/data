"""Utility functions for the ingestion helper."""

import logging
import croniter
from datetime import datetime, timezone
import base64
from googleapiclient.discovery import build
import json
from googleapiclient.errors import HttpError
from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth import jwt


def get_caller_identity(request):
    """Extracts the caller's email from the Authorization header (JWT)."""
    auth_header = request.headers.get('Authorization')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]
            unverified_claims = {}
            try:
                unverified_claims = jwt.decode(token, verify=False)
                #logging.info(f"Token claims (unverified): iss={unverified_claims.get('iss')}, aud={unverified_claims.get('aud')}, email={unverified_claims.get('email')}")
                logging.warning(
                    f"Could not decode unverified token for debugging: {debug_e}"
                )
                id_info = id_token.verify_oauth2_token(token,
                                                       requests.Request())
                return id_info.get('email', 'unknown_email')
            except Exception as e:
                if unverified_claims:
                    email = unverified_claims.get('email', 'unknown_email')
                    return f"{email} (unverified)"
                return 'decode_error'
        else:
            logging.warning(
                f"Invalid Authorization header format. Parts: {len(parts)}")
    else:
        logging.warning("No Authorization header received.")
    return 'no_auth_header'


def get_import_params(request_json) -> dict:
    """Extracts and calculates import parameters from the request JSON.

    Args:
        request_json: A dictionary containing request parameters.

    Returns:
        A dictionary with keys: job_id, duration, data, version, next_refresh, status.
    """
    import_name = request_json.get('importName', '')
    status = request_json.get('status', '')
    job_id = request_json.get('jobId', '')
    duration = request_json.get('duration', 0)
    data = request_json.get('data', 0)
    version = request_json.get('version', '')
    schedule = request_json.get('schedule', '')
    next_refresh = datetime.now(timezone.utc)
    try:
        next_refresh = croniter.croniter(schedule, datetime.now(
            timezone.utc)).get_next(datetime)
    except (croniter.CroniterError) as e:
        logging.error(
            f"Error calculating next refresh from schedule '{schedule}': {e}")
    return {
        'import_name': import_name,
        'status': status,
        'job_id': job_id,
        'duration': duration,
        'data': data,
        'version': version,
        'next_refresh': next_refresh
    }


def create_import_params(summary) -> dict:
    """Creates import parameters from the import summary.

    Args:
        summary: A dictionary containing import summary details.

    Returns:
        A dictionary with keys: job_id, duration, data, version, next_refresh, status.
    """
    import_name = summary.get('import_name', '')
    status = summary.get('status', '').removeprefix('ImportStatus.')
    job_id = summary.get('job_id', '')
    duration = summary.get('execution_time', 0)
    data = summary.get('data_volume', 0)
    version = summary.get('latest_version', '')
    next_refresh_str = summary.get('next_refresh', '')
    next_refresh = None
    if next_refresh_str:
        try:
            next_refresh = datetime.fromisoformat(next_refresh_str)
        except ValueError:
            logging.error(f"Error parsing next_refresh: {next_refresh_str}")

    return {
        'import_name': import_name,
        'status': status,
        'job_id': job_id,
        'duration': duration,
        'data': data,
        'version': version,
        'next_refresh': next_refresh,
    }


def get_ingestion_metrics(project_id, location, job_id):
    """Fetches graph metrics (nodes, edges, observations) from a Dataflow job.

    Args:
        project_id: The GCP project ID.
        location: The location of the Dataflow job.
        job_id: The Dataflow job ID.

    Returns:
        A dictionary containing 'obs_count', 'node_count', and 'edge_count'.
    """
    dataflow = build('dataflow', 'v1b3', cache_discovery=False)
    # Fetch Dataflow metrics
    node_count = 0
    edge_count = 0
    obs_count = 0
    if project_id and job_id:
        try:
            metrics = dataflow.projects().locations().jobs().getMetrics(
                projectId=project_id, location=location,
                jobId=job_id).execute()
            for metric in metrics.get('metrics', []):
                name = metric['name']['name']
                if name == 'graph_node_count':
                    node_count = int(metric['scalar'])
                elif name == 'graph_edge_count':
                    edge_count = int(metric['scalar'])
                elif name == 'graph_observation_count':
                    obs_count = int(metric['scalar'])
        except HttpError as e:
            logging.error(
                f"Error fetching dataflow metrics for job {job_id}: {e}")
    return {
        'obs_count': obs_count,
        'node_count': node_count,
        'edge_count': edge_count
    }
