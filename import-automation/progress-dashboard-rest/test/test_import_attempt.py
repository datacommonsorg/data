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
Tests for import_attempt.py.
"""

import unittest
from unittest import mock

from context import app
from app.resource import import_attempt
from app.service import import_attempt_database_dict


PARSE_ARGS = 'flask_restful.reqparse.RequestParser.parse_args'
IMPORT_ATTEMPT_DATABASE = 'app.resource.import_attempt' \
                          '.import_attempt_database.ImportAttemptDatabase'
EXAMPLE_ATTEMPT = {
    'attempt_id': '0',
    'branch_name': 'branch',
    'repo_name': 'repo',
    'import_name': 'name',
    'time_created': '2020-06-30T04:28:53.717569+00:00',
    'logs': [],
    'status': 'created',
    'pr_number': 0
}


@mock.patch(IMPORT_ATTEMPT_DATABASE,
            import_attempt_database_dict.ImportAttemptDatabaseDict)
class ImportAttemptByIDTest(unittest.TestCase):
    """Tests for ImportAttemptByID."""

    def test_get_not_exist(self):
        """Tests that GET returns NOT FOUND if the attempt_id does not exist."""
        attempt_api = import_attempt.ImportAttemptByID()
        attempt_id = 9999
        _, err = attempt_api.get(attempt_id)
        self.assertEqual(404, err)

    @mock.patch(PARSE_ARGS, lambda self: {'status': 'noooo'})
    def test_put_status_not_allowed(self):
        """Tests that PUT returns FORBIDDEN for disallowed status."""
        attempt_api = import_attempt.ImportAttemptByID()
        _, err = attempt_api.put('0')
        self.assertEqual(403, err)

    @mock.patch(PARSE_ARGS, lambda self: EXAMPLE_ATTEMPT)
    def test_put_then_get(self):
        """Tests that GET after PUT returns the same attempt."""
        attempt_api = import_attempt.ImportAttemptByID()
        attempt_id = EXAMPLE_ATTEMPT['attempt_id']
        attempt_api.put(attempt_id)
        retrieved_attempt = attempt_api.get(attempt_id)
        self.assertEqual(EXAMPLE_ATTEMPT, retrieved_attempt)

    @mock.patch(PARSE_ARGS, lambda self: EXAMPLE_ATTEMPT)
    def test_put_id_not_match(self):
        """Tests that PUT returns CONFLICT if the attempt_id in the url does
        not match the attempt_id in the request body."""
        attempt_api = import_attempt.ImportAttemptByID()
        attempt_id = EXAMPLE_ATTEMPT['attempt_id']
        EXAMPLE_ATTEMPT['attempt_id'] = 'wrong'
        _, err = attempt_api.put(attempt_id)
        self.assertEqual(409, err)

    @mock.patch(PARSE_ARGS, side_effect=(EXAMPLE_ATTEMPT, {'pr_number': 9999}))
    def test_patch(self, _):
        """Tests that patching a field succeeds."""
        attempt_api = import_attempt.ImportAttemptByID()
        attempt_id = EXAMPLE_ATTEMPT['attempt_id']
        attempt_api.put(attempt_id)
        attempt_api.patch(attempt_id)
        retrieved_attempt = attempt_api.get(attempt_id)
        self.assertEqual(9999, retrieved_attempt['pr_number'])

    @mock.patch(PARSE_ARGS, side_effect=(EXAMPLE_ATTEMPT, {'attempt_id': '?'}))
    def test_patch_id_not_allowed(self, _):
        """Tests that patching the attempt_id fails and returns FORBIDDEN."""
        attempt_api = import_attempt.ImportAttemptByID()
        attempt_id = EXAMPLE_ATTEMPT['attempt_id']
        attempt_api.put(attempt_id)
        _, err = attempt_api.patch(attempt_id)
        self.assertEqual(403, err)


@mock.patch(IMPORT_ATTEMPT_DATABASE,
            import_attempt_database_dict.ImportAttemptDatabaseDict)
class ImportAttemptListTest(unittest.TestCase):
    """Tests for ImportAttemptList."""

    @mock.patch(IMPORT_ATTEMPT_DATABASE,
                import_attempt_database_dict.ImportAttemptDatabaseDict)
    def setUp(self):
        """Injects several attempts to the database."""
        import_attempt_database_dict.ImportAttemptDatabaseDict.reset()

        attempt_0 = EXAMPLE_ATTEMPT
        attempt_1 = {'attempt_id': '1', 'import_name': 'name', 'pr_number': 1}
        attempt_2 = {'attempt_id': '2', 'import_name': 'name', 'pr_number': 1}
        attempt_3 = {'attempt_id': '3', 'import_name': 'nameeeee'}
        returns = [attempt_0, attempt_1, attempt_2, attempt_3]
        with mock.patch(PARSE_ARGS) as parse_args:
            parse_args.side_effect = returns
            self.attempts = returns

            attempt_api = import_attempt.ImportAttemptByID()
            attempt_api.put(attempt_0['attempt_id'])
            attempt_api.put(attempt_1['attempt_id'])
            attempt_api.put(attempt_2['attempt_id'])
            attempt_api.put(attempt_3['attempt_id'])
            self.attempt_api = attempt_api

    @mock.patch(PARSE_ARGS, lambda self: {'import_name': 'name'})
    def test_get_by_name(self):
        """Tests filtering by import_name returns the correct attempts."""
        attempt_list = import_attempt.ImportAttemptList()
        attempts = attempt_list.get()
        self.assertEqual(3, len(attempts))
        self.assertIn(self.attempts[0], attempts)
        self.assertIn(self.attempts[1], attempts)
        self.assertIn(self.attempts[2], attempts)

    @mock.patch(PARSE_ARGS, lambda self: {'attempt_id': '1'})
    def test_get_by_id(self):
        """Tests filtering by attempt_id returns the only correct attempt."""
        attempt_list = import_attempt.ImportAttemptList()
        attempts = attempt_list.get()
        self.assertEqual(1, len(attempts))
        self.assertIn(self.attempts[1], attempts)

    @mock.patch(PARSE_ARGS,
                lambda self: {'import_name': 'name', 'pr_number': 1})
    def test_get_by_name_and_repo_num(self):
        """Tests filtering by import_name and pr_number returns
        the correct attempts."""
        attempt_list = import_attempt.ImportAttemptList()
        attempts = attempt_list.get()
        self.assertEqual(2, len(attempts))
        self.assertIn(self.attempts[1], attempts)
        self.assertIn(self.attempts[2], attempts)

    @mock.patch(PARSE_ARGS, lambda self: {'import_name': 'noooo'})
    def test_get_not_exist(self):
        """Tests empty result."""
        attempt_list = import_attempt.ImportAttemptList()
        attempts = attempt_list.get()
        self.assertEqual([], attempts)
