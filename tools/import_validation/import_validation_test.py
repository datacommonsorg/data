# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pandas as pd
import unittest
from datetime import datetime

from tools.import_validation import import_validation


class TestMaxDateLatestValidation(unittest.TestCase):
    '''Test Class for the MAX_DATE_LATEST validation rule.'''

    def setUp(self):
        self.validator = import_validation.Validator()

    def test_max_date_latest_fails_on_old_date(self):
        old_year = datetime.now().year - 2
        test_df = pd.DataFrame({'MaxDate': [f'{old_year}-01-01']})
        result = self.validator.validate_max_date_latest(test_df)
        self.assertEqual(result.status, 'FAILED')
        self.assertIn('Latest date found was', result.message)
        self.assertEqual(result.details['latest_date_found'], old_year)

    def test_max_date_latest_passes_on_current_date(self):
        current_year = datetime.now().year
        test_df = pd.DataFrame({'MaxDate': [f'{current_year}-01-01']})
        result = self.validator.validate_max_date_latest(test_df)
        self.assertEqual(result.status, 'PASSED')


class TestDeletedCountValidation(unittest.TestCase):
    '''Test Class for the DELETED_COUNT validation rule.'''

    def setUp(self):
        self.validator = import_validation.Validator()

    def test_deleted_count_fails_when_over_threshold(self):
        test_df = pd.DataFrame({'DELETED': [1, 1]})  # Total deleted = 2
        config = {'threshold': 1}
        result = self.validator.validate_deleted_count(test_df, config)
        self.assertEqual(result.status, 'FAILED')
        self.assertEqual(result.details['deleted_count'], 2)
        self.assertEqual(result.details['threshold'], 1)

    def test_deleted_count_passes_when_at_threshold(self):
        test_df = pd.DataFrame({'DELETED': [1, 1]})  # Total deleted = 2
        config = {'threshold': 2}
        result = self.validator.validate_deleted_count(test_df, config)
        self.assertEqual(result.status, 'PASSED')


class TestModifiedCountValidation(unittest.TestCase):
    '''Test Class for the MODIFIED_COUNT validation rule.'''

    def setUp(self):
        self.validator = import_validation.Validator()

    def test_modified_count_fails_on_inconsistent_counts(self):
        test_df = pd.DataFrame({'MODIFIED': [1, 2]})  # Inconsistent
        result = self.validator.validate_modified_count(test_df)
        self.assertEqual(result.status, 'FAILED')
        self.assertEqual(sorted(result.details['unique_counts']), [1, 2])

    def test_modified_count_passes_on_consistent_counts(self):
        test_df = pd.DataFrame({'MODIFIED': [2, 2]})  # Consistent
        result = self.validator.validate_modified_count(test_df)
        self.assertEqual(result.status, 'PASSED')


class TestAddedCountValidation(unittest.TestCase):
    '''Test Class for the ADDED_COUNT validation rule.'''

    def setUp(self):
        self.validator = import_validation.Validator()

    def test_added_count_fails_on_inconsistent_counts(self):
        test_df = pd.DataFrame({'ADDED': [1, 2]})  # Inconsistent
        result = self.validator.validate_added_count(test_df)
        self.assertEqual(result.status, 'FAILED')
        self.assertEqual(sorted(result.details['unique_counts']), [1, 2])

    def test_added_count_passes_on_consistent_counts(self):
        test_df = pd.DataFrame({'ADDED': [1, 1]})  # Consistent
        result = self.validator.validate_added_count(test_df)
        self.assertEqual(result.status, 'PASSED')


class TestUnmodifiedCountValidation(unittest.TestCase):
    '''Test Class for the UNMODIFIED_COUNT validation rule.'''

    def setUp(self):
        self.validator = import_validation.Validator()

    def test_unmodified_count_is_always_successful(self):
        test_df = pd.DataFrame({'UNMODIFIED': [1, 2]})  # Inconsistent
        result = self.validator.validate_unmodified_count(test_df)
        self.assertEqual(result.status, 'PASSED')


class TestNumPlacesConsistentValidation(unittest.TestCase):
    '''Test Class for the NUM_PLACES_CONSISTENT validation rule.'''

    def setUp(self):
        self.validator = import_validation.Validator()

    def test_num_places_consistent_fails_on_inconsistent_counts(self):
        test_df = pd.DataFrame({'NumPlaces': [1, 2]})  # Inconsistent
        result = self.validator.validate_num_places_consistent(test_df)
        self.assertEqual(result.status, 'FAILED')
        self.assertEqual(sorted(result.details['unique_counts']), [1, 2])

    def test_num_places_consistent_passes_on_consistent_counts(self):
        test_df = pd.DataFrame({'NumPlaces': [2, 2]})  # Consistent
        result = self.validator.validate_num_places_consistent(test_df)
        self.assertEqual(result.status, 'PASSED')


class TestNumPlacesCountValidation(unittest.TestCase):
    '''Test Class for the NUM_PLACES_COUNT validation rule.'''

    def setUp(self):
        self.validator = import_validation.Validator()

    def test_num_places_count_fails_below_minimum(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumPlaces': [5]})
        config = {'minimum': 10}
        result = self.validator.validate_num_places_count(test_df, config)
        self.assertEqual(result.status, 'FAILED')
        self.assertEqual(result.details['actual_count'], 5)

    def test_num_places_count_fails_above_maximum(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumPlaces': [15]})
        config = {'maximum': 10}
        result = self.validator.validate_num_places_count(test_df, config)
        self.assertEqual(result.status, 'FAILED')
        self.assertEqual(result.details['actual_count'], 15)

    def test_num_places_count_fails_on_exact_mismatch(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumPlaces': [10]})
        config = {'value': 11}
        result = self.validator.validate_num_places_count(test_df, config)
        self.assertEqual(result.status, 'FAILED')
        self.assertEqual(result.details['actual_count'], 10)

    def test_num_places_count_passes_within_range(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumPlaces': [10]})
        config = {'minimum': 5, 'maximum': 15}
        result = self.validator.validate_num_places_count(test_df, config)
        self.assertEqual(result.status, 'PASSED')

    def test_num_places_count_passes_on_exact_match(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumPlaces': [10]})
        config = {'value': 10}
        result = self.validator.validate_num_places_count(test_df, config)
        self.assertEqual(result.status, 'PASSED')


if __name__ == '__main__':
    unittest.main()
