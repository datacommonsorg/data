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
- How to format a request (CLOUD_BATCH, CLOUD_RUN http requests are supported)
- How to call cloud Scheduler API (create_or_update is supported)
"""
import json
import os
from typing import Dict

from google.api_core.exceptions import AlreadyExists
from google.api_core.exceptions import NotFound
from google.cloud import scheduler_v1
from google.protobuf import json_format

CLOUD_RUN_SERVICE_ACCOUNT = os.getenv('CLOUD_SCHEDULER_CALLER_SA')


def _base_job_request(absolute_import_name, schedule: str):
    """Base of cloud_batch_job_request and cloud_run_job_request."""
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
    }


def cloud_batch_job_request(absolute_import_name, schedule,
                            cloud_batch_job_url: str,
                            json_encoded_job_body: bytes,
                            compute_service_account: str) -> Dict:
    """Cloud Scheduler request that targets jobs in CLOUD_BATCH."""
    job = _base_job_request(absolute_import_name, schedule)
    job['name'] = absolute_import_name.split(':')[1]
    job['http_target'] = {
        'uri': f'{cloud_batch_job_url}',
        'http_method': 'POST',
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json_encoded_job_body,
        'oauth_token': {
            'service_account_email': f'{compute_service_account}',
            'scope': 'https://www.googleapis.com/auth/cloud-platform'
        }
    }
    return job


def cloud_run_job_request(absolute_import_name, schedule,
                          cloud_run_job_url: str,
                          cloud_run_service_account: str) -> Dict:
    """Cloud Scheduler request that targets jobs in CLOUD_RUN."""
    json_encoded_job_body = json.dumps({}).encode("utf-8")
    job = _base_job_request(absolute_import_name, schedule)
    job_name = absolute_import_name.split(':')[1]
    job['name'] = f'{job_name}'
    job['http_target'] = {
        'uri': f'https://{cloud_run_job_url}',
        'http_method': 'POST',
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json_encoded_job_body,
        'oauth_token': {
            'service_account_email': f'{cloud_run_service_account}',
            'scope': 'https://www.googleapis.com/auth/cloud-platform'
        }
    }
    return job


def create_or_update_job(project_id, location: str, job: Dict) -> Dict:
    """Creates/updates a Cloud Scheduler job.

    Args:
        project_id: GCP project id of the scheduler
        location:   GCP location of the scheduler
        job:        http_job_request(...)

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
        client.run_job(scheduler_v1.RunJobRequest(name=job_name))
    except NotFound:
        raise Exception('Attempted to trigger non-existing job %s.'
                        'Please check Cloud Scheduler on UI to see '
                        'if the job exists' % job_name)


def _fix_absolute_import_name(absolute_import_name: str) -> str:
    """Replaces all the forward slashes and colons in an absolute import name
    with underscores. This is for conforming to restrictions of Cloud Scheduler
    job names."""
    return absolute_import_name.replace('/', '_').replace(':', '_')
