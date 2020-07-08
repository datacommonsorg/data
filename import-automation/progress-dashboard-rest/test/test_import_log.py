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
Tests for log.py.
"""

import unittest
from unittest import mock

from app.resource import import_attempt, log
from app.service import import_attempt_database_dict
from app import utils


PARSE_ARGS = 'flask_restful.reqparse.RequestParser.parse_args'
IMPORT_ATTEMPT_DATABASE = 'app.resource.import_attempt' \
                          '.import_attempt_database.ImportAttemptDatabase'


@mock.patch(IMPORT_ATTEMPT_DATABASE,
            import_attempt_database_dict.ImportAttemptDatabaseDict)
class ImportLogTest(unittest.TestCase):
    """Tests for ImportLog."""

    def setUp(self):
        """Clears the database before every test."""
        import_attempt_database_dict.ImportAttemptDatabaseDict.reset()

    @mock.patch(PARSE_ARGS)
    def test_post_then_get(self, parse_args):
        """Tests that POST adds a log to an attempt."""
        log_0 = {'level': 'info', 'message': 'first'}
        log_1 = {
            'level': 'info', 'message': 'second', 'time_logged': utils.utctime()
        }
        parse_args.side_effect = [
            {'import_name': 'name'}, log_0, log_1
        ]
        attempt_api = import_attempt.ImportAttemptByID()
        attempt_id = '0'
        attempt_api.put(attempt_id)

        log_api = log.ImportLogByAttemptID()
        log_api.post(attempt_id)
        log_api.post(attempt_id)

        logs = log_api.get(attempt_id)
        self.assertEqual(2, len(logs))
        self.assertIn(log_0, logs)
        self.assertIn(log_1, logs)

    @mock.patch(PARSE_ARGS)
    def test_log_level_not_allowed(self, parse_args):
        """Tests that POST returns FORBIDDEN if the level of the log
        is not supported by the API."""
        log = {'level': 'nooooo', 'message': 'message'}
        parse_args.side_effect = [{'import_name': 'name'}, log]
        attempt_api = import_attempt.ImportAttemptByID()
        attempt_api.put('0')
        log_api = log.ImportLogByAttemptID()
        _, err = log_api.post(log)
        self.assertEqual(403, err)

    def test_not_found(self):
        """Tests that querying the logs of an attempt that does not exist
        returns NOT FOUND."""
        log_api = log.ImportLogByAttemptID()
        _, err = log_api.get('9999')
        self.assertEqual(404, err)

    @mock.patch(PARSE_ARGS, lambda self: {'import_name': 'name'})
    def test_get_empty(self):
        """Tests that querying the logs of an attempt that does not have any
        log returns an empty list."""
        attempt_api = import_attempt.ImportAttemptByID()
        attempt_id = '0'
        attempt_api.put(attempt_id)
        log_api = log.ImportLogByAttemptID()
        logs = log_api.get(attempt_id)
        self.assertEqual([], logs)
