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
Tests for validation.py.
"""

import unittest

from app.service import validation


class ValidationTest(unittest.TestCase):
    """Tests for validation.py."""

    def test_is_iso_utc(self):
        """Tests _is_iso_utc."""
        # Not UTC
        self.assertFalse(
            validation._is_iso_utc('2020-07-28T13:21:50.665294-07:00'))
        # Without timezone info
        self.assertFalse(validation._is_iso_utc('2020-07-28T13:21:50.665294'))

        self.assertTrue(
            validation._is_iso_utc('2020-07-28T20:22:18.311294+00:00'))

    def test_is_field_iso_utc(self):
        """Tests _is_field_iso_utc."""
        entity = {'abc': '2020-07-28T20:22:18.311294+00:00'}
        valid, _, _ = validation._is_field_iso_utc(entity, 'abc')
        self.assertTrue(valid)

        # Field does not exist. Vacuously true.
        entity = {}
        valid, _, _ = validation._is_field_iso_utc(entity, 'not-exist')
        self.assertTrue(valid)

        # Not UTC
        entity = {'abc': '2020-07-28T13:21:50.665294-07:00'}
        valid, err, code = validation._is_field_iso_utc(entity, 'abc')
        self.assertFalse(valid)
        self.assertIn('ISO', err)
        self.assertEqual(403, code)

    def test_is_value_defined(self):
        """Tests _is_value_defined."""
        # Not defined
        entity = {'cba': 'not-defined'}
        valid, err, code = validation._is_value_defined(entity, 'cba',
                                                        ('defined', 'definedd'))
        self.assertFalse(valid)
        self.assertIn('not-defined', err)
        self.assertEqual(403, code)

        entity = {'cba': 'defined'}
        valid, _, _ = validation._is_value_defined(entity, 'cba',
                                                   ('defined', 'definedd'))
        self.assertTrue(valid)

        # Vacuously true
        entity = {'cba': 'not-defined'}
        valid, _, _ = validation._is_value_defined(entity, 'not-exist',
                                                   ('defined', 'definedd'))
        self.assertTrue(valid)

    def test_id_matches(self):
        """Tests _id_matches."""
        entity = {'id-field': 'some-id'}
        valid, _, _ = validation._id_matches(entity, 'id-field', 'some-id')
        self.assertTrue(valid)

        # Vacuously true
        entity = {'id-field': 'some-id'}
        valid, _, _ = validation._id_matches(entity, 'id-field', None)
        self.assertTrue(valid)

        entity = {'id-field': 'some-id'}
        valid, err, code = validation._id_matches(entity, 'id-field',
                                                  'not-match')
        self.assertFalse(valid)
        self.assertIn('not match', err)
        self.assertEqual(409, code)

    def test_get_patch_forbidden_error(self):
        """Tests _get_patch_forbidden_error."""
        err, code = validation.get_patch_forbidden_error(('field1', 'field2'))
        self.assertEqual(err, f'It is not allowed to patch field1, field2')
        self.assertEqual(403, code)

    def test_get_not_found_error(self):
        """Tests get_not_found_error."""
        err, code = validation.get_not_found_error('fielddd', 'idddd')
        self.assertEqual('fielddd idddd not found', err)
        self.assertEqual(404, code)

    def test_required_fields_present(self):
        """Tests required_fields_present."""
        fields = ('field1', 'field2', 'field3')
        entity = {'field1': '1', 'field2': '2', 'field3': '3'}
        valid, _, _ = validation.required_fields_present(fields, entity)
        self.assertTrue(valid)

        # Some not present
        fields = ('field1', 'field2', 'field3')
        entity = {'field1': '1'}
        valid, err, code = validation.required_fields_present(fields, entity)
        self.assertFalse(valid)
        self.assertIn('field2, field3', err)
        self.assertEqual(403, code)

        # Some not present but allowed
        fields = ('field1', 'field2', 'field3')
        entity = {'field1': '1'}
        valid, _, _ = validation.required_fields_present(fields,
                                                         entity,
                                                         all_present=False)
        self.assertTrue(valid)

        # None present
        fields = ('field1', 'field2', 'field3')
        entity = {'field4': '1'}
        valid, _, _ = validation.required_fields_present(fields,
                                                         entity,
                                                         all_present=False)
        valid, err, code = validation.required_fields_present(fields, entity)
        self.assertFalse(valid)
        self.assertIn('field1, field2, field3', err)
        self.assertEqual(403, code)

    def test_is_import_attempt_valid(self):
        """Tests is_import_attempt_valid."""
        attempt = {
            'attempt_id': 'attempt',
            'status': 'created',
            'time_created': '2020-07-28T20:22:18.311294+00:00',
            'time_completed': '2020-07-28T20:22:18.311294+00:00'
        }
        valid, _, _ = validation.is_import_attempt_valid(attempt, 'attempt')
        self.assertTrue(valid)

        # Not UTC
        attempt = {
            'attempt_id': 'attempt',
            'status': 'created',
            'time_created': '2020-07-28T13:21:50.665294-07:00',
            'time_completed': '2020-07-28T20:22:18.311294+00:00'
        }
        valid, _, _ = validation.is_import_attempt_valid(attempt, 'attempt')
        self.assertFalse(valid)

        # status not defined
        attempt = {
            'attempt_id': 'attempt',
            'status': 'not-defined',
            'time_created': '2020-07-28T20:22:18.311294+00:00',
            'time_completed': '2020-07-28T20:22:18.311294+00:00'
        }
        valid, _, _ = validation.is_import_attempt_valid(attempt, 'attempt')
        self.assertFalse(valid)

        # attempt_id not match
        attempt = {
            'attempt_id': 'attempt',
            'status': 'created',
            'time_created': '2020-07-28T20:22:18.311294+00:00',
            'time_completed': '2020-07-28T20:22:18.311294+00:00'
        }
        valid, _, _ = validation.is_import_attempt_valid(attempt, 'not-match')
        self.assertFalse(valid)

    def test_is_system_run_valid(self):
        """Tests is_system_run_valid."""
        run = {
            'run_id': 'run',
            'status': 'created',
            'time_created': '2020-07-28T20:22:18.311294+00:00',
            'time_completed': '2020-07-28T20:22:18.311294+00:00'
        }
        valid, _, _ = validation.is_system_run_valid(run, 'run')
        self.assertTrue(valid)

        # Not UTC
        run = {
            'run_id': 'run',
            'status': 'created',
            'time_created': '2020-07-28T13:21:50.665294-07:00',
            'time_completed': '2020-07-28T20:22:18.311294+00:00'
        }
        valid, _, _ = validation.is_system_run_valid(run, 'run')
        self.assertFalse(valid)

        # status not defined
        run = {
            'run_id': 'run',
            'status': 'not-defined',
            'time_created': '2020-07-28T20:22:18.311294+00:00',
            'time_completed': '2020-07-28T20:22:18.311294+00:00'
        }
        valid, _, _ = validation.is_system_run_valid(run, 'run')
        self.assertFalse(valid)

        # run_id not match
        run = {
            'run_id': 'run',
            'status': 'created',
            'time_created': '2020-07-28T20:22:18.311294+00:00',
            'time_completed': '2020-07-28T20:22:18.311294+00:00'
        }
        valid, _, _ = validation.is_system_run_valid(run, 'not-match')
        self.assertFalse(valid)

    def test_is_progress_log_valid(self):
        log = {
            'log_id': 'log',
            'time_logged': '2020-07-28T20:22:18.311294+00:00',
            'level': 'info'
        }
        valid, _, _ = validation.is_progress_log_valid(log, 'log')
        self.assertTrue(valid)

        # log_id not match
        log = {
            'log_id': 'log',
            'time_logged': '2020-07-28T20:22:18.311294+00:00',
            'level': 'info'
        }
        valid, _, _ = validation.is_progress_log_valid(log, 'not-match')
        self.assertFalse(valid)

        # Level not defined
        log = {
            'log_id': 'log',
            'time_logged': '2020-07-28T20:22:18.311294+00:00',
            'level': 'infoooooo'
        }
        valid, _, _ = validation.is_progress_log_valid(log, 'log')
        self.assertFalse(valid)

        # Not UTC
        log = {
            'log_id': 'log',
            'time_logged': '2020-07-28T20:22:18.311294-07:00',
            'level': 'info'
        }
        valid, _, _ = validation.is_progress_log_valid(log, 'log')
        self.assertFalse(valid)
