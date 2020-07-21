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

from app.model import import_attempt_model
from app.resource import import_attempt
from app.resource import import_attempt_list
from app.resource import system_run_list
from test import utils

_ATTEMPT = import_attempt_model.ImportAttemptModel


class ImportAttemptByIDTest(unittest.TestCase):
    """Tests for ImportAttemptByID."""

    @classmethod
    def setUpClass(cls):
        cls.emulator = utils.start_emulator()

    @classmethod
    def tearDownClass(cls):
        utils.terminate_emulator(cls.emulator)

    @mock.patch('app.utils.create_datastore_client',
                utils.create_test_datastore_client)
    def setUp(self):
        """Injects a system run and several import attempts to the database."""
        self.resource = import_attempt.ImportAttemptByID()
        list_resource = import_attempt_list.ImportAttemptList()
        run_list_resource = system_run_list.SystemRunList()
        run_list_resource.database.client = self.resource.client
        list_resource.database.client = self.resource.client
        list_resource.run_database.client = self.resource.client
        attempts = [{
            _ATTEMPT.csv_url: 'google.com'
        }, {
            _ATTEMPT.node_mcf_url: 'facebook.com'
        }, {
            _ATTEMPT.template_mcf_url: 'bing.com'
        }]
        self.attempts = utils.ingest_import_attempts(run_list_resource,
                                                     list_resource, attempts)

    def test_get(self):
        """Tests that querying by attempt_id returns the correct
        import attempt."""
        self.assertEqual(
            self.attempts[0],
            self.resource.get(self.attempts[0][_ATTEMPT.attempt_id]))

    def test_default_values_set(self):
        """Tests that default values for certain fields of newly created
        import attempts are set."""
        for attempt in self.attempts:
            retrieved = self.resource.get(attempt[_ATTEMPT.attempt_id])
            self.assertIn(_ATTEMPT.logs, retrieved)
            self.assertIn(_ATTEMPT.time_created, retrieved)
            self.assertIn(_ATTEMPT.status, retrieved)

    def test_get_not_exist(self):
        """Tests that GET returns NOT FOUND if the attempt_id does not exist."""
        attempt_id = 9999
        _, err = self.resource.get(attempt_id)
        self.assertEqual(404, err)

    @mock.patch(utils.PARSE_ARGS,
                lambda self: {_ATTEMPT.csv_url: 'facebook.com'})
    def test_patch(self):
        """Tests that patching a field succeeds."""
        attempt_id = self.attempts[0][_ATTEMPT.attempt_id]
        before = self.resource.get(attempt_id)
        self.assertEqual('google.com', before[_ATTEMPT.csv_url])
        self.resource.patch(attempt_id)
        after = self.resource.get(attempt_id)
        self.assertEqual('facebook.com', after[_ATTEMPT.csv_url])

    @mock.patch(utils.PARSE_ARGS)
    def test_patch_not_allowed(self, parse_args):
        """Tests that patching attempt_id or run_id fails and
        returns FORBIDDEN."""
        parse_args.side_effect = [{
            _ATTEMPT.attempt_id: 'forbidden'
        }, {
            _ATTEMPT.run_id: 'forbidden'
        }]
        _, err = self.resource.patch(self.attempts[1][_ATTEMPT.attempt_id])
        self.assertEqual(403, err)
