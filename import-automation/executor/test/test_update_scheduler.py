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
Tests for update_scheduler.py.
"""

import json
import unittest
from unittest import mock

from app.executor import update_scheduler


class UpdateSchedulerTest(unittest.TestCase):

    def setUp(self):
        config = mock.MagicMock()
        config.gcp_project_id = 'google.com:datcom-data'
        config.scheduler_location = 'us-central1'
        config.github_auth_username = 'username'
        config.github_auth_access_token = 'access-token'
        config.dashboard_oauth_client_id = 'client-id'
        self.client = mock.MagicMock()
        self.scheduler = update_scheduler.UpdateScheduler(self.client, config)

    def test_create_schedule(self):
        self.scheduler.create_schedule('scripts/us_fed:treasury', '5 4 * * *')
        self.client.location_path.assert_called_once_with(
            'google.com/datcom-data', 'us-central1')
        args, _ = self.client.create_job.call_args
        job = args[1]
        self.assertEqual('scripts_us_fed_treasury', job['name'])
        self.assertEqual('scripts/us_fed:treasury', job['description'])
        expected_body = {
            'absolute_import_name': 'scripts/us_fed:treasury',
            'configs': {
                'github_auth_username': 'username',
                'github_auth_access_token': 'access-token',
                'dashboard_oauth_client_id': 'client-id'
            }
        }
        self.assertEqual(expected_body,
                         json.loads(job['app_engine_http_target']['body']))

    def test_delete_schedule(self):
        self.scheduler.delete_schedule('foo/bar:import')
        self.client.job_path.assert_called_once_with('google.com/datcom-data',
                                                     'us-central1',
                                                     'foo_bar_import')
