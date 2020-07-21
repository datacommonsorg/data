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

import unittest
from unittest import mock

from requests import exceptions

from test import utils
from app.service import dashboard_api


@mock.patch('app.utils.utctime', lambda: '2020-07-15T12:07:17.365264+00:00')
class DashboardAPITest(unittest.TestCase):

    def setUp(self):
        self.dashboard = dashboard_api.DashboardAPI('client-id')

    @mock.patch('app.service.iap_request.IAPRequest.post')
    def test_log_helper(self, post):
        args = {
            'message': 'message',
            'level': 'level',
            'run_id': 'run',
            'attempt_id': 'attempt',
            'time_logged': 'time'
        }
        expected = {
            'message': 'message',
            'level': 'level',
            'run_id': 'run',
            'attempt_id': 'attempt',
            'time_logged': 'time',
            'log_id': 'random-id'
        }
        post.return_value = utils.ResponseMock(200, expected)
        self.assertEqual(expected, self.dashboard._log_helper(**args))
        post.assert_called_once_with(
            'https://datcom-data.uc.r.appspot.com/logs', json=args)

    @mock.patch('app.service.iap_request.IAPRequest.post')
    def test_log_helper_time(self, post):
        """Tests that time_logged is generated if not supplied."""
        args = {
            'message': 'message',
            'level': 'level',
            'run_id': 'run'
        }
        expected = {
            'message': 'message',
            'level': 'level',
            'run_id': 'run',
            'time_logged': '2020-07-15T12:07:17.365264+00:00',
            'log_id': 'random-id'
        }
        post.return_value = utils.ResponseMock(200, expected)
        self.assertEqual(expected, self.dashboard._log_helper(**args))

    def test_log_helper_id(self):
        """Tests that at least one of run_id and attempt_id
        need to be specified."""
        self.assertRaises(ValueError,
                          self.dashboard._log_helper, 'message', 'level')

    @mock.patch('app.service.iap_request.IAPRequest.post')
    def test_log_helper_http(self, post):
        """Tests that an exception is thrown is the HTTP request fails."""
        post.return_value = utils.ResponseMock(400)
        self.assertRaises(exceptions.HTTPError,
                          self.dashboard._log_helper,
                          'message', 'level', 'attempt')

    @mock.patch('app.service.iap_request.IAPRequest.patch')
    def test_update_attempt(self, patch):
        attempt = {'import_name': 'treasury'}
        patch.return_value = utils.ResponseMock(200, {})
        self.assertEqual({}, self.dashboard.update_attempt(attempt, 'id'))
        patch.assert_called_with(
            'https://datcom-data.uc.r.appspot.com/import_attempts/id',
            json=attempt)

    @mock.patch('app.service.iap_request.IAPRequest.patch')
    def test_update_attempt_id(self, patch):
        """Tests that attempt_id can be found in the attempt body
        if not supplied as an argument."""
        attempt = {'import_name': 'treasury', 'attempt_id': 'idd'}
        patch.return_value = utils.ResponseMock(200, {})
        self.assertEqual({}, self.dashboard.update_attempt(attempt, 'idd'))
        self.dashboard.iap.patch.assert_called_with(
            'https://datcom-data.uc.r.appspot.com/import_attempts/idd',
            json={'import_name': 'treasury', 'attempt_id': 'idd'})

    def test_update_attempt_no_id(self):
        """Tests that an exception is raised if attempt_id is not found."""
        attempt = {'import_name': 'treasury'}
        self.assertRaises(ValueError, self.dashboard.update_attempt, attempt)

    @mock.patch('app.service.iap_request.IAPRequest.patch')
    def test_update_run(self, patch):
        run = {'commit_sha': 'commit-sha'}
        patch.return_value = utils.ResponseMock(200, {})
        self.assertEqual({}, self.dashboard.update_run(run, 'id'))
        patch.assert_called_with(
            'https://datcom-data.uc.r.appspot.com/system_runs/id',
            json=run)

    @mock.patch('app.service.iap_request.IAPRequest.patch')
    def test_update_run_id(self, patch):
        """Tests that run_id can be found in the run body
        if not supplied as an argument."""
        run = {'commit_sha': 'commit-sha', 'attempt_id': 'idddd'}
        patch.return_value = utils.ResponseMock(200, {})
        self.assertEqual({}, self.dashboard.update_attempt(run))
        self.dashboard.iap.patch.assert_called_with(
            'https://datcom-data.uc.r.appspot.com/import_attempts/idddd',
            json={'commit_sha': 'commit-sha', 'attempt_id': 'idddd'})

    def test_update_run_no_id(self):
        """Tests that an exception is raised if run_id is not found."""
        run = {'commit_sha': 'commit-sha'}
        self.assertRaises(ValueError, self.dashboard.update_run, run)

    @mock.patch('app.service.iap_request.IAPRequest.post',
                lambda self, url, json=None: utils.ResponseMock(200, json))
    def test_levels(self):
        """Tests that the convenient logging functions set the right
        logging levels.  """
        args = {
            'message': 'message',
            'time_logged': 'time',
            'run_id': 'run'
        }
        funcs = [
            (self.dashboard.critical, 'critical'),
            (self.dashboard.error, 'error'),
            (self.dashboard.warning, 'warning'),
            (self.dashboard.info, 'info'),
            (self.dashboard.debug, 'debug')
        ]
        for func, level in funcs:
            self.assertEqual(level, func(**args)['level'])
