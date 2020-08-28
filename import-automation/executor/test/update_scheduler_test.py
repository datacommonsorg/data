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

import google.api_core.exceptions

from app import configs
from app.executor import update_scheduler
from test import utils


@mock.patch('google.protobuf.json_format.MessageToDict',
            lambda job, preserving_proto_field_name=False: dict(job))
class UpdateSchedulerTest(unittest.TestCase):
    """Tests for create_schedule and delete_schedule. schedule_on_commit is
    tested in test_integration.py."""

    def setUp(self):
        config = configs.ExecutorConfig(gcp_project_id='google.com:datcom-data',
                                        scheduler_location='us-central1',
                                        github_auth_username='username',
                                        github_auth_access_token='access-token',
                                        dashboard_oauth_client_id='dashboard',
                                        importer_oauth_client_id='importer',
                                        email_account='@google',
                                        email_token='token')
        self.scheduler = update_scheduler.UpdateScheduler(
            utils.SchedulerClientMock(), None, config, None)

    @mock.patch('app.utils.utctime', lambda: '2020-07-24T16:27:22.609304+00:00')
    def test_create_schedule(self):
        job = self.scheduler.create_schedule('scripts/us_fed:treasury',
                                             '5 4 * * *')
        expected_name = ('projects/google.com:datcom-data/locations/'
                         'us-central1/jobs/scripts_us_fed_treasury')
        self.assertEqual(expected_name, job['name'])
        self.assertEqual('scripts/us_fed:treasury', job['description'])
        expected_body = {
            'absolute_import_name': 'scripts/us_fed:treasury',
            'configs': {
                'github_repo_name': 'data',
                'github_repo_owner_username': 'datacommonsorg',
                'github_auth_username': 'username',
                'github_auth_access_token': 'access-token',
                'dashboard_oauth_client_id': 'dashboard',
                'importer_oauth_client_id': 'importer',
                'email_account': '@google',
                'email_token': 'token'
            }
        }
        self.assertEqual(expected_body, job['app_engine_http_target']['body'])

    def test_delete_schedule(self):
        self.scheduler.create_schedule('foo/bar:import', '5 4 * * *')
        self.scheduler.delete_schedule('foo/bar:import')
        self.assertRaises(google.api_core.exceptions.GoogleAPICallError,
                          self.scheduler.delete_schedule, 'foo/bar:import')
