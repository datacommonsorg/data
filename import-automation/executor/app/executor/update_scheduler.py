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
    def __init__(self,
                client: scheduler.CloudSchedulerClient,
                config: configs.ExecutorConfig):
        self.client = client
        self.config = config

    def schedule_update(self, absolute_import_name: str, schedule: str) -> Dict:
        """Schedules periodic updates for an import.

        Attributes:
            absolute_import_name: Absolute import name of the import to be
                updated. This is used as the name of the job.
            schedule: Cron schedule for the updates. See
                https://en.wikipedia.org/wiki/Cron.

        Returns:
            Created job as a dict.

        Raises:
            See CloudSchedulerClient.create_job.
        """
        job = {
            'name': absolute_import_name,
            'schedule': schedule,
            'time_zone': 'utc',
            'app_engine_http_target': {
                'http_method': 'POST',
                'app_engine_routing': {
                    'service': 'default',
                    'relative_uri': '/update',
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'absolute_import_name': absolute_import_name
                    }).encode()
                }
            },
            'retry_config': {
                'retry_count': 2
            },
            'attempt_deadline': {
                # 24h
                'seconds': 86400
            }
        }
        location_path = self.client.location_path(
            self.config.gcp_project_id,
            self.config.scheduler_location)
        return dict(self.client.create_job(location_path, job))
