# Copyright 2023 Google LLC
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
Interface for Cloud Scheduler API.

This module contains:
- How to format a request (GKE, GAE http requests are supported)
- How to call cloud Scheduler API (create_or_update is supported)
"""
import json
import os
from typing import Dict

from google.cloud import scheduler_v1
from google.protobuf import json_format
from google.api_core.exceptions import AlreadyExists, NotFound

GKE_SERVICE_DOMAIN = os.getenv('GKE_SERVICE_DOMAIN',
                               'importautomation.datacommons.org')
GKE_CALLER_SERVICE_ACCOUNT = os.getenv('CLOUD_SCHEDULER_CALLER_SA')
GKE_OAUTH_AUDIENCE = os.getenv('CLOUD_SCHEDULER_CALLER_OAUTH_AUDIENCE')


def _base_job_request(absolute_import_name, schedule: str):
    """Base of http_job_request and appengine_job_request."""
    return {
        'name': _fix_absolute_import_name(absolute_import_name),
        'description': absolute_import_name,
        'schedule': schedule,
        'time_zone': 'Etc/UTC',
        'retry_config': {
            'retry_count': 2,
            'min_backoff_duration': {
                # 1h
                'seconds': 60 * 60
            }
        },
        'attempt_deadline': {
            # 30m is the max allowed deadline
            'seconds': 60 * 30
        }
        # <'http_request'|'appengine_job_request'>: {...}
    }


def http_job_request(absolute_import_name,
                     schedule,
                     json_encoded_job_body: str,
                     gke_caller_service_account: str = "",
                     gke_oauth_audience: str = "") -> Dict:
    """Cloud Scheduler request that targets executors launched in GKE."""

    # If the service account and oauth audience are provided as
    # function args, use them. If not, look for them in the
    # environment (GKE_CALLER_SERVICE_ACCOUNT and GKE_OAUTH_AUDIENCE
    # are set to read from environment variables).
    service_account = gke_caller_service_account
    oauth_audience = gke_oauth_audience

    if not service_account:
        service_account = GKE_CALLER_SERVICE_ACCOUNT
    if not oauth_audience:
        oauth_audience = GKE_OAUTH_AUDIENCE

    job = _base_job_request(absolute_import_name, schedule)
    job['name'] = f'{job["name"]}_GKE'
    job['http_target'] = {
        'uri': f'https://{GKE_SERVICE_DOMAIN}/update',
        'http_method': 'POST',
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json_encoded_job_body,
        'oidc_token': {
            'service_account_email': service_account,
            'audience': oauth_audience,
        }
    }
    return job


def appengine_job_request(absolute_import_name, schedule,
                          json_encoded_job_body: str) -> Dict:
    """Cloud Scheduler request that targets executors launched in GAE."""
    job = _base_job_request(absolute_import_name, schedule)
    job['name'] = f'{job["name"]}_GAE'
    job['app_engine_http_target'] = {
        'http_method': 'POST',
        'app_engine_routing': {
            'service': 'default',
        },
        'relative_uri': '/update',
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json_encoded_job_body
    }
    return job


def create_or_update_job(project_id, location: str, job: Dict) -> Dict:
    """Creates/updates a Cloud Scheduler job.

    Args:
        project_id: GCP project id of the scheduler
        location:   GCP location of the scheduler
        job_req:    appengine_job_request(...) or http_job_request(...)

    Returns:
        json transcoded cloud scheduler job created.
    """
    client = scheduler_v1.CloudSchedulerClient()
    # Name requires the full GCP resource path.
    parent = f'projects/{project_id}/locations/{location}'
    job['name'] = f'{parent}/jobs/{job["name"]}'

    try:
        job = client.create_job(
            scheduler_v1.CreateJobRequest(parent=parent, job=job))
    except AlreadyExists:
        job = client.update_job(scheduler_v1.UpdateJobRequest(job=job))

    scheduled = json_format.MessageToDict(job._pb,
                                          preserving_proto_field_name=True)

    if 'app_engine_http_target' in job:
        scheduled['app_engine_http_target']['body'] = json.loads(
            job.app_engine_http_target.body)

    if 'http_target' in job:
        scheduled['http_target']['body'] = json.loads(job.http_target.body)

    return scheduled


def trigger_job(project_id, location, absolute_import_name, job_id_suffix: str):
    """Triggers a Cloud Scheduler job.

    This is equivalent to the "Force run" action on the UI.
    Note that there is no way to know the status of the actual job
    triggered from Cloud Scheduler API.

    Callers should wait for an atribtuary amount of time, up to 30min.
    """
    client = scheduler_v1.CloudSchedulerClient()
    job_id = f'{_fix_absolute_import_name(absolute_import_name)}{job_id_suffix}'
    job_name = f'projects/{project_id}/locations/{location}/jobs/{job_id}'
    try:
        job = client.run_job(scheduler_v1.RunJobRequest(name=job_name))
    except NotFound:
        raise Exception('Attempted to trigger non-existing job %s.'
                        'Please check Cloud Scheduler on UI to see '
                        'if the job exists' % job_name)


def _fix_absolute_import_name(absolute_import_name: str) -> str:
    """Replaces all the forward slashes and colons in an absolute import name
    with underscores. This is for conforming to restrictions of Cloud Scheduler
    job names."""
    return absolute_import_name.replace('/', '_').replace(':', '_')
