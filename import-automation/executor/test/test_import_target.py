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
Tests for import_target.py.
"""

import unittest

from app.executor import import_target


class ImportTargetTest(unittest.TestCase):

    def test_absolute_import_name(self):
        self.assertTrue(
            import_target.is_absolute_import_name('scripts/us_fed:treasury'))
        self.assertTrue(
            import_target.is_absolute_import_name('us_fed:treasury'))
        self.assertFalse(
            import_target.is_absolute_import_name(
                'scripts/us_fed:treasury/data'))
        self.assertFalse(import_target.is_absolute_import_name(':treasury'))
        self.assertFalse(
            import_target.is_absolute_import_name('scripts/us_fed:'))
        self.assertFalse(
            import_target.is_absolute_import_name('scripts/us_fed/treasury'))
        self.assertFalse(
            import_target.is_absolute_import_name(' scripts/us_fed:treasury'))
        self.assertFalse(import_target.is_absolute_import_name(''))

    def test_parse_commit_message_targets(self):
        self.assertEqual([], import_target.parse_commit_message_targets(''))
        self.assertEqual([],
                         import_target.parse_commit_message_targets('IMPORTS='))
        self.assertEqual(
            [], import_target.parse_commit_message_targets('imports=treasury'))
        self.assertRaises(ValueError,
                          import_target.parse_commit_message_targets,
                          'IMPORTS=scripts/us_fed/treasury')
        self.assertRaises(
            ValueError, import_target.parse_commit_message_targets,
            'abc IMPORTS=scripts/us_fed:treasury, scripts/us_bls:cpi')
        self.assertEqual(['scripts/us_fed:treasury'],
                         import_target.parse_commit_message_targets(
                             'IMPORTS=scripts/us_fed:treasury'))
        self.assertEqual(
            ['scripts/us_fed:treasury'],
            import_target.parse_commit_message_targets(
                'IMPORTS=scripts/us_fed:treasury,scripts/us_fed:treasury'))
        self.assertCountEqual(
            ['scripts/us_fed:treasury', 'scripts/us_bls:cpi', 'all'],
            import_target.parse_commit_message_targets(
                'ab IMPORTS=scripts/us_fed:treasury,scripts/us_bls:cpi,all cc'))

    def test_is_import_targetted_by_commit(self):
        self.assertTrue(
            import_target.is_import_targetted_by_commit(
                'scripts/us_fed', 'treasury', ['scripts/us_fed:treasury']))
        self.assertTrue(
            import_target.is_import_targetted_by_commit('scripts/us_fed',
                                                        'treasury', ['all']))
        self.assertTrue(
            import_target.is_import_targetted_by_commit('scripts/us_fed',
                                                        'treasury',
                                                        ['scripts/us_fed:all']))
        self.assertTrue(
            import_target.is_import_targetted_by_commit(
                'scripts/us_fed', 'treasury',
                ['scripts/us_fed:all', 'scripts/us_fed:else']))
        self.assertFalse(
            import_target.is_import_targetted_by_commit('scripts/us_fed',
                                                        'treasury', []))
        self.assertFalse(
            import_target.is_import_targetted_by_commit(
                'scripts/us_fed', 'treasury', ['scripts/us_fed:else']))
