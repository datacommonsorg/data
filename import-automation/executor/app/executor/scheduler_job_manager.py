# Copyright 2020 Google LLC
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
"""Module scheduling cron jobs.

Currently scheduling can only occur through commit messages
in the format of "SCHEDULES=<target1>,<target2>,...

where a <target> is in the format of <path/to/manifest.json>:<import name>

Example commit message:
"
This change schedules the cron of india covid stats

SCHEDULES=IMPORTS=scripts/covid19_india/cases_count_states_data:covid19IndiaCasesCountStatesData
"
"""

import json
import logging

from app import configs
from app.executor import cloud_scheduler
import cloud_batch
import cloud_run

_GKE_SERVICE_ACCOUNT_KEY: str = 'gke_service_account'


def create_or_update_import_schedule(absolute_import_name: str,
                                     import_spec: dict,
                                     config: configs.ExecutorConfig,
                                     scheduler_config_dict: dict,
                                     override_config: dict):
    """Create/Update the import schedule for 1 import."""
    schedule = import_spec.get('cron_schedule')
    if not schedule:
        raise KeyError(
            f'cron_schedule not found in manifest for {absolute_import_name}')
    # Default resources (disk/mem in Gi).
    resources = {'cpu': 8, 'memory': 32, 'disk': 100}
    timeout = config.user_script_timeout
    if 'user_script_timeout' in import_spec:
        timeout = import_spec['user_script_timeout']

    if config.executor_type == "CLOUD_RUN":
        docker_image = config.importer_docker_image
        job_name = absolute_import_name.split(':')[1]

        json_encoded_config = json.dumps(config.get_data_refresh_config())
        args = [
            f'--import_name={absolute_import_name}',
            f'--import_config={json_encoded_config}', '--enable_cloud_logging'
        ]
        env_vars = {}
        if 'resource_limits' in import_spec:
            resources.update(import_spec['resource_limits'])
        resources["cpu"] = f'{resources["cpu"]}'
        resources["memory"] = f'{resources["memory"]}Gi'
        del resources["disk"]
        job = cloud_run.create_or_update_cloud_run_job(
            config.gcp_project_id, config.scheduler_location, job_name,
            docker_image, config.gcs_bucket_volume_mount,
            config.gcs_volume_mount_dir, env_vars, args, resources, timeout)
        job_id = job.name.rsplit('/', 1)[1]
        if not job:
            logging.error(
                f'Failed to setup cloud run job for {absolute_import_name}')
        cloud_run_job_url = f'{config.scheduler_location}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/{config.gcp_project_id}/jobs/{job_id}:run'
        req = cloud_scheduler.cloud_run_job_request(
            absolute_import_name, schedule, cloud_run_job_url,
            scheduler_config_dict[_GKE_SERVICE_ACCOUNT_KEY])
    elif config.executor_type == "CLOUD_BATCH":
        # This set up a cloud scheduler job which periodically invokes a GCP workflow job.
        # The workflow job runs a CLOUD BATCH job with the specified configuration in the request.
        json_encoded_body = cloud_batch.create_job_request(
            absolute_import_name, override_config, import_spec)
        cloud_batch_job_url = f'https://workflowexecutions.googleapis.com/v1/projects/{config.gcp_project_id}/locations/{config.scheduler_location}/workflows/{config.cloud_workflow_id}/executions'
        req = cloud_scheduler.cloud_batch_job_request(
            absolute_import_name, schedule, cloud_batch_job_url,
            json_encoded_body.encode('utf-8'),
            scheduler_config_dict[_GKE_SERVICE_ACCOUNT_KEY])
        logging.info('Setting up a cloud batch job with config:')
        logging.info(req)
    else:
        raise Exception(
            f"Invalid executor_type {config.executor_type}, expects one of ('CLOUD_RUN', 'CLOUD_BATCH')"
        )

    return cloud_scheduler.create_or_update_job(config.gcp_project_id,
                                                config.scheduler_location, req)
