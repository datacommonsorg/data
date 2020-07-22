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
Tests for base_database.py.

TODO(intrepiditee): Decide later whether test filenames start with
test_ or end with _test or use a pattern that supports both.
"""

import unittest
from unittest import mock

from google.cloud import datastore

from app.service import base_database
from test import utils


def setUpModule():
    utils.EMULATOR.start_emulator()


class BaseDatabaseTest(unittest.TestCase):
    """Tests for BaseDatabase."""

    @mock.patch('app.utils.create_datastore_client',
                utils.create_test_datastore_client)
    def setUp(self):
        """Test setup that runs before every test."""
        self.id_field = 'entity_id'
        self.database = base_database.BaseDatabase(
            kind='kind', id_field=self.id_field)

    def test_make_new(self):
        """Tests that get returns a new import attempt when
        make_new is True."""
        entity_id = 'does-not-exist'
        new_entity = self.database.get(entity_id, True)
        self.assertIn('entity_id', new_entity)
        self.assertNotEqual(entity_id, new_entity[self.id_field])
        self.assertEqual(1, len(new_entity))

    def test_save_then_get(self):
        """Tests that a new entity can be saved and then retrieved."""
        entity = self.database.get(make_new=True)
        entity['foo'] = 'bar'
        self.database.save(entity)
        self.assertIn(self.id_field, entity)
        self.assertEqual('bar', entity['foo'])
        self.assertEqual(2, len(entity))

    def test_save_partial_key(self):
        """Tests that attempting to save an entity with a partial key throws
        an exeception."""
        key = datastore.Key('namespace', project='project')
        entity = datastore.Entity(key)
        self.assertRaises(ValueError, self.database.save, entity)

    def test_filter(self):
        """Tests that filtering by fields works."""
        entity_0 = self.database.get(make_new=True)
        entity_1 = self.database.get(make_new=True)
        entity_2 = self.database.get(make_new=True)
        entity_3 = self.database.get(make_new=True)

        entity_0.update({
            'import_name': 'name',
            'provenance_url': 'google.com',
            'pr_number': 0
        })
        entity_1.update({
            'attempt_id': '1',
            'import_name': 'name',
            'provenance_url': 'google.com',
            'pr_number': 1
        })
        entity_2.update({
            'attempt_id': '2',
            'import_name': 'name',
            'provenance_url': 'apple.com',
            'pr_number': 1
        })
        entity_3.update({
            'attempt_id': '3',
            'import_name': 'name',
            'pr_number': 2
        })
        entities = [entity_0, entity_1, entity_2, entity_3]
        for entity in entities:
            self.database.save(entity)

        filters = {
            'import_name': 'name',
            'pr_number': 1
        }

        retrieved = self.database.filter(filters)
        self.assertIn(entity_1, retrieved)
        self.assertIn(entity_2, retrieved)
        self.assertEqual(2, len(retrieved))
