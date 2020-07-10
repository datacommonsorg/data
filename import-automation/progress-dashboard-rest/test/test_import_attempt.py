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

The Datastore emulator must be running for these tests to run.
In a different terminal, run
'gcloud beta emulators datastore start --no-store-on-disk'.
In the terminal where the tests will be run, run
'$(gcloud beta emulators datastore env-init)' and proceed to run the tests.

See https://cloud.google.com/datastore/docs/tools/datastore-emulator.
"""

import unittest
from unittest import mock

from app.resource import import_attempt
from app.resource import import_attempt_list
from test import utils


class ImportAttemptByIDTest(unittest.TestCase):
    """Tests for ImportAttemptByID."""

    @mock.patch('app.utils.create_datastore_client',
                utils.create_test_datastore_client)
    def setUp(self):
        self.resource = import_attempt.ImportAttemptByID()

    def test_get_not_exist(self):
        """Tests that GET returns NOT FOUND if the attempt_id does not exist."""
        attempt_id = 9999
        _, err = self.resource.get(attempt_id)
        self.assertEqual(404, err)

    @mock.patch(utils.PARSE_ARGS,
                side_effect=(utils.EXAMPLE_ATTEMPT, {'pr_number': 9999}))
    def test_patch(self, _):
        """Tests that patching a field succeeds."""
        attempt_id = utils.EXAMPLE_ATTEMPT['attempt_id']
        self.resource.put(attempt_id)
        self.resource.patch(attempt_id)
        retrieved_attempt = self.resource.get(attempt_id)
        self.assertEqual(9999, retrieved_attempt['pr_number'])

    @mock.patch(utils.PARSE_ARGS,
                side_effect=(utils.EXAMPLE_ATTEMPT, {'attempt_id': '?'}))
    def test_patch_id_not_allowed(self, _):
        """Tests that patching attempt_id or run_id fails and
        returns FORBIDDEN."""
        attempt_id = utils.EXAMPLE_ATTEMPT['attempt_id']
        self.resource.put(attempt_id)
        _, err = self.resource.patch(attempt_id)
        self.assertEqual(403, err)
