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
Tests for import_attempt_database.py.
"""

import unittest
from unittest import mock

import test.datastore_mocks as datastore_mocks
from app.service import import_attempt_database


@mock.patch('google.cloud.datastore.Client',
            datastore_mocks.DatastoreClientMock)
@mock.patch('google.cloud.datastore.Entity',
            datastore_mocks.DatastoreEntityMock)
@mock.patch('google.cloud.datastore.Query',
            datastore_mocks.DatastoreQueryMock)
class ImportAttemptDatabaseTest(unittest.TestCase):
    """Tests for ImportAttemptDatabase."""

    def test_save_then_get(self):
        """Tests that an import attempt can be saved and then retrieved."""
        database = import_attempt_database.ImportAttemptDatabase()
        attempt = {'attempt_id': '0', 'import_name': 'name'}
        database.save(attempt)
        self.assertEqual(attempt, database.get_by_id(attempt['attempt_id']))

    def test_make_new(self):
        """Tests that get_by_id returns a new import attempt when
        make_new is True."""
        database = import_attempt_database.ImportAttemptDatabase()
        attempt_id = 'noooo'
        self.assertEqual({'attempt_id': attempt_id},
                         database.get_by_id(attempt_id, make_new=True))

    def test_filter(self):
        """Tests that filtering by fields works."""
        database = import_attempt_database.ImportAttemptDatabase()
        attempt_0 = {
            'attempt_id': '0',
            'import_name': 'name',
            'provenance_url': 'google.com',
            'pr_number': 0
        }
        attempt_1 = {
            'attempt_id': '1',
            'import_name': 'name',
            'provenance_url': 'google.com',
            'pr_number': 1
        }
        attempt_2 = {
            'attempt_id': '2',
            'import_name': 'name',
            'provenance_url': 'apple.com',
            'pr_number': 1
        }
        attempt_3 = {
            'attempt_id': '3',
            'import_name': 'name',
            'pr_number': 2
        }
        attempts = [attempt_0, attempt_1, attempt_2, attempt_3]
        for attempt in attempts:
            database.save(attempt)

        filters = {
            'import_name': 'name',
            'pr_number': 1
        }
        expected = [attempt_1, attempt_2]
        self.assertEqual(expected, database.filter(filters))
