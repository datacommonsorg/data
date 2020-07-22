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
"""
Class for scheduling import updates using Google Cloud Scheduler.
"""

import json
from typing import Dict

from google.cloud import scheduler

from app import configs


class UpdateScheduler:
    """Class for scheduling import updates using Google Cloud Scheduler.

    Attributes:
        client: CloudSchedulerClient object for managing Google Cloud
            Scheduler jobs.
        config: ExecutorConfig object containing configurations for
            Cloud Scheduler.

    Returns:
        Created job as a dict.
    """

    def __init__(self, client: scheduler.CloudSchedulerClient,
                 config: configs.ExecutorConfig):
        self.client = client
        self.config = config

    def create_schedule(self, absolute_import_name: str, schedule: str) -> Dict:
        """Schedules periodic updates for an import.

        Attributes:
            absolute_import_name: Absolute import name of the import to be
                updated. This is used as the name of the job.
            schedule: Cron schedule for the updates as a string. See
                https://en.wikipedia.org/wiki/Cron.

        Returns:
            Created job as a dict.

        Raises:
            Same exceptions as CloudSchedulerClient.create_job.
        """
        location_path = self.client.location_path(
            _fix_project_id(self.config.gcp_project_id),
            self.config.scheduler_location)
        return dict(
            self.client.create_job(
                location_path, _create_job_body(absolute_import_name,
                                                schedule)))

    def delete_schedule(self, absolute_import_name):
        """Deletes an update schedule for an import.

        Args:
            absolute_import_name: Absolute import name of the import
                as a string.

        Raises:
            Same exceptions as CloudSchedulerClient.delete_job.
        """
        job_path = self.client.job_path(
            _fix_project_id(self.config.gcp_project_id),
            self.config.scheduler_location, absolute_import_name)
        self.client.delete_job(job_path)


def _create_job_body(absolute_import_name: str, schedule: str) -> Dict:
    """Creates the body of a Cloud Scheduler job for updating an import.

    This function does not schedule any jobs.

    Args:
        absolute_import_name: Absolute import name of the import as a string.
        schedule: Cron schedule for the updates as a string.

    Returns:
        The body of a Cloud Scheduler job as a dict that is ready to be used
        as an argument to CloudSchedulerClient.create_job.
    """
    return {
        'name': absolute_import_name,
        'schedule': schedule,
        'time_zone': 'utc',
        'app_engine_http_target': {
            'http_method':
                'POST',
            'app_engine_routing': {
                'service': 'default',
            },
            'relative_uri':
                '/update',
            'headers': {
                'Content-Type': 'application/json'
            },
            'body':
                json.dumps({
                    'absolute_import_name': absolute_import_name
                }).encode()
        },
        'retry_config': {
            'retry_count': 2
        },
        'attempt_deadline': {
            # 24h
            'seconds': 86400
        }
    }


def _fix_project_id(project_id: str) -> str:
    """Converts Google Cloud project ID from the form <organization>:<project>
    to <organization>/<project>."""
    sep = ':'
    if sep in project_id:
        organization, project = project_id.split(sep)
        return f'{organization}/{project}'
    return project_id
