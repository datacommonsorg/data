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
Interface for cloud
"""
import json
import os
from typing import Dict

from google.cloud import scheduler
from google.protobuf import json_format


GKE_SERVICE_DOMAIN = os.getenv('GKE_SERVICE_DOMAIN', 'import.datacommons.dev')


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
            # 24h
            'seconds': 24 * 60 * 60
        }
        # <'http_request'|'appengine_job_request'>: {...}
    }


def http_job_request(
    absolute_import_name, schedule, json_encoded_job_body: str) -> Dict:
    """Cloud Scheduler request that targets executors launched in GKE."""
    req =  _base_job_request(absolute_import_name, schedule)
    req['name'] = f'{req["name"]}_GKE'
    req['http_request'] = {
        'url': GKE_SERVICE_DOMAIN + '/update',
        'http_method': 'POST',
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json_encoded_job_body
    }
    return req


def appengine_job_request(
    absolute_import_name, schedule, json_encoded_job_body: str) -> Dict:
    """Cloud Scheduler request that targets executors launched in GAE."""
    req =  _base_job_request(absolute_import_name, schedule)
    req['name'] = f'{req["name"]}_GAE'
    req['app_engine_http_target'] = {
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
    return req



def create_job(
    project_id, location: str,
    job_req: Dict) -> Dict:
    """Creates a Cloud Scheduler job.

    Args:
        project_id: GCP project id of the scheduler
        location:   GCP location of the scheduler
        absolute_import_name: ex: scripts/covid19_india/cases_count_states_data:covid19IndiaCasesCountStatesData
        job_req:    appengine_job_request(...) or http_job_request(...)

    Returns:
        json transcoded cloud scheduler job created.
    """
    client = scheduler.CloudSchedulerClient()
    location_path = client.location_path(project_id, location)
    # Name requires the full GCP resource path.
    job_req['name'] = f'projects/{project_id}/locations/{location}/jobs/{job_req["name"]}'

    job = client.create_job(location_path, job_req)

    scheduled = json_format.MessageToDict(
        job, preserving_proto_field_name=True)

    if 'app_engine_http_target' in job_req:
        scheduled['app_engine_http_target']['body'] = json.loads(
            job.app_engine_http_target.body)

    if 'http_request' in job_req:
        scheduled['http_request']['body'] = json.loads(
            job.http_request.body)

    return scheduled


def _fix_absolute_import_name(absolute_import_name: str) -> str:
    """Replaces all the forward slashes and colons in an absolute import name
    with underscores. This is for conforming to restrictions of Cloud Scheduler
    job names."""
    return absolute_import_name.replace('/', '_').replace(':', '_')
