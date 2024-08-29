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
Tests for cloud_scheduler.py.
"""

import os
import unittest
from deepdiff.diff import DeepDiff

from app.executor import cloud_scheduler


class CloudSchedulerTest(unittest.TestCase):

    def test_appengine_job_request(self):
        absolute_import_name = "scripts/preprocess:A"
        schedule = "0 5 * * *"
        json_encoded_job_body = '{"k":"v"}'

        got = cloud_scheduler.appengine_job_request(absolute_import_name,
                                                    schedule,
                                                    json_encoded_job_body)
        want = {
            'name': 'scripts_preprocess_A_GAE',
            'description': 'scripts/preprocess:A',
            'schedule': "0 5 * * *",
            'time_zone': 'Etc/UTC',
            'retry_config': {
                'retry_count': 2,
                'min_backoff_duration': {
                    'seconds': 60 * 60
                }
            },
            'attempt_deadline': {
                'seconds': 60 * 30
            },
            'app_engine_http_target': {
                'http_method': 'POST',
                'app_engine_routing': {
                    'service': 'default',
                },
                'relative_uri': '/update',
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': '{"k":"v"}'
            }
        }
        assert DeepDiff(got, want) == {}

    def test_http_job_request(self):
        absolute_import_name = "scripts/preprocess:A"
        schedule = "0 5 * * *"
        json_encoded_job_body = '{"k":"v"}'
        cloud_scheduler.GKE_CALLER_SERVICE_ACCOUNT = 'account'
        cloud_scheduler.GKE_OAUTH_AUDIENCE = 'audience'

        got = cloud_scheduler.http_job_request(absolute_import_name, schedule,
                                               json_encoded_job_body)
        want = {
            'name': 'scripts_preprocess_A_GKE',
            'description': 'scripts/preprocess:A',
            'schedule': "0 5 * * *",
            'time_zone': 'Etc/UTC',
            'retry_config': {
                'retry_count': 2,
                'min_backoff_duration': {
                    'seconds': 60 * 60
                }
            },
            'attempt_deadline': {
                'seconds': 60 * 30
            },
            'http_target': {
                'uri': 'https://importautomation.datacommons.org/update',
                'http_method': 'POST',
                'headers': {
                    'Content-Type': 'application/json',
                },
                'body': '{"k":"v"}',
                'oidc_token': {
                    'service_account_email': 'account',
                    'audience': 'audience',
                }
            }
        }
        assert DeepDiff(got, want) == {}
