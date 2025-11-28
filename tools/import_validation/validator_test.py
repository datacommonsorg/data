# Copyright 2025 Google LLC
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

import os
import sys
import pandas as pd
import unittest
from datetime import datetime

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from validator import Validator
from result import ValidationStatus


class TestMaxDateLatestValidation(unittest.TestCase):
    '''Test Class for the MAX_DATE_LATEST validation rule.'''

    def setUp(self):
        self.validator = Validator()

    def test_max_date_latest_fails_on_old_date(self):
        old_year = datetime.now().year - 2
        test_df = pd.DataFrame(
            {'MaxDate': [f'{old_year}-01-01', f'{old_year-1}-01-01']})
        result = self.validator.validate_max_date_latest(test_df, {})
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertIn('Latest date found was', result.message)
        self.assertEqual(result.details['latest_date_found'], old_year)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 2)

    def test_max_date_latest_passes_on_current_date(self):
        current_year = datetime.now().year
        test_df = pd.DataFrame({'MaxDate': [f'{current_year}-01-01']})
        result = self.validator.validate_max_date_latest(test_df, {})
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 1)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_max_date_latest_passes_on_empty_dataframe(self):
        test_df = pd.DataFrame({'MaxDate': []})
        result = self.validator.validate_max_date_latest(test_df, {})
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 0)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_max_date_latest_fails_on_missing_column(self):
        test_df = pd.DataFrame({'StatVar': ['sv1']})  # Missing 'MaxDate'
        result = self.validator.validate_max_date_latest(test_df, {})
        self.assertEqual(result.status, ValidationStatus.DATA_ERROR)
        self.assertIn('missing required column', result.message)


class TestDeletedCountValidation(unittest.TestCase):
    '''Test Class for the DELETED_COUNT validation rule.'''

    def setUp(self):
        self.validator = Validator()

    def test_deleted_count_fails_when_over_threshold(self):
        test_df = pd.DataFrame({'DELETED': [1, 1]})  # Total deleted = 2
        params = {'threshold': 1}
        result = self.validator.validate_deleted_count(test_df, params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.details['deleted_count'], 2)
        self.assertEqual(result.details['threshold'], 1)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 2)

    def test_deleted_count_passes_when_at_threshold(self):
        test_df = pd.DataFrame({'DELETED': [1, 1]})  # Total deleted = 2
        params = {'threshold': 2}
        result = self.validator.validate_deleted_count(test_df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 2)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_deleted_count_passes_on_empty_dataframe(self):
        test_df = pd.DataFrame({'DELETED': []})
        params = {'threshold': 0}
        result = self.validator.validate_deleted_count(test_df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 0)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_deleted_count_fails_on_missing_column(self):
        test_df = pd.DataFrame({'StatVar': ['sv1']})  # Missing 'DELETED'
        params = {'threshold': 1}
        result = self.validator.validate_deleted_count(test_df, params)
        self.assertEqual(result.status, ValidationStatus.DATA_ERROR)
        self.assertIn('missing required column', result.message)


class TestMissingRefsCountValidation(unittest.TestCase):
    '''Test Class for the MISSING_REFS_COUNT validation rule.'''

    def setUp(self):
        self.validator = Validator()

    def test_missing_refs_count_fails_when_over_threshold(self):
        report = {
            'levelSummary': {
                'LEVEL_WARNING': {
                    'counters': {
                        'Existence_MissingReference': 5
                    }
                }
            }
        }
        params = {'threshold': 4}
        result = self.validator.validate_missing_refs_count(report, params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.details['missing_refs_count'], 5)


class TestModifiedCountValidation(unittest.TestCase):
    '''Test Class for the MODIFIED_COUNT validation rule.'''

    def setUp(self):
        self.validator = Validator()

    def test_modified_count_fails_on_inconsistent_counts(self):
        test_df = pd.DataFrame({
            'StatVar': ['sv1', 'sv2'],
            'MODIFIED': [1, 2]
        })  # Inconsistent
        result = self.validator.validate_modified_count(test_df, {})
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.details['distinct_statvar_count'], 2)
        self.assertEqual(result.details['distinct_modified_counts'], 2)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 2)

    def test_modified_count_passes_on_consistent_counts(self):
        test_df = pd.DataFrame({'MODIFIED': [2, 2]})  # Consistent
        result = self.validator.validate_modified_count(test_df, {})
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 2)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_modified_count_passes_on_empty_dataframe(self):
        test_df = pd.DataFrame({'MODIFIED': []})
        result = self.validator.validate_modified_count(test_df, {})
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 0)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_modified_count_fails_on_missing_column(self):
        test_df = pd.DataFrame({'StatVar': ['sv1']})  # Missing 'MODIFIED'
        result = self.validator.validate_modified_count(test_df, {})
        self.assertEqual(result.status, ValidationStatus.DATA_ERROR)
        self.assertIn('missing required column', result.message)


class TestAddedCountValidation(unittest.TestCase):
    '''Test Class for the ADDED_COUNT validation rule.'''

    def setUp(self):
        self.validator = Validator()

    def test_added_count_fails_on_inconsistent_counts(self):
        test_df = pd.DataFrame({
            'StatVar': ['sv1', 'sv2'],
            'ADDED': [1, 2]
        })  # Inconsistent
        result = self.validator.validate_added_count(test_df, {})
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.details['distinct_statvar_count'], 2)
        self.assertEqual(result.details['distinct_added_counts'], 2)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 2)

    def test_added_count_passes_on_consistent_counts(self):
        test_df = pd.DataFrame({'ADDED': [1, 1]})  # Consistent
        result = self.validator.validate_added_count(test_df, {})
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 2)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_added_count_passes_on_empty_dataframe(self):
        test_df = pd.DataFrame({'ADDED': []})
        result = self.validator.validate_added_count(test_df, {})
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 0)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_added_count_fails_on_missing_column(self):
        test_df = pd.DataFrame({'StatVar': ['sv1']})  # Missing 'ADDED'
        result = self.validator.validate_added_count(test_df, {})
        self.assertEqual(result.status, ValidationStatus.DATA_ERROR)
        self.assertIn('missing required column', result.message)


class TestNumPlacesConsistentValidation(unittest.TestCase):
    '''Test Class for the NUM_PLACES_CONSISTENT validation rule.'''

    def setUp(self):
        self.validator = Validator()

    def test_num_places_consistent_fails_on_inconsistent_counts(self):
        test_df = pd.DataFrame({
            'StatVar': ['sv1', 'sv2'],
            'NumPlaces': [1, 2]
        })  # Inconsistent
        result = self.validator.validate_num_places_consistent(test_df, {})
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(
            result.message,
            "The number of places is not consistent across all StatVars.")
        self.assertEqual(result.details['distinct_statvar_count'], 2)
        self.assertEqual(result.details['distinct_place_counts'], 2)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 2)

    def test_num_places_consistent_passes_on_consistent_counts(self):
        test_df = pd.DataFrame({'NumPlaces': [2, 2]})  # Consistent
        result = self.validator.validate_num_places_consistent(test_df, {})
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 2)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_num_places_consistent_passes_on_empty_dataframe(self):
        test_df = pd.DataFrame({'NumPlaces': []})
        result = self.validator.validate_num_places_consistent(test_df, {})
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 0)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_num_places_consistent_fails_on_missing_column(self):
        test_df = pd.DataFrame({'StatVar': ['sv1']})  # Missing 'NumPlaces'
        result = self.validator.validate_num_places_consistent(test_df, {})
        self.assertEqual(result.status, ValidationStatus.DATA_ERROR)
        self.assertIn('missing required column', result.message)


class TestNumPlacesCountValidation(unittest.TestCase):
    '''Test Class for the NUM_PLACES_COUNT validation rule.'''

    def setUp(self):
        self.validator = Validator()

    def test_num_places_count_fails_below_minimum(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumPlaces': [5]})
        params = {'minimum': 10}
        result = self.validator.validate_num_places_count(test_df, params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 1)
        self.assertEqual(result.details['failed_rows'][0]['actual_value'], 5)

    def test_num_places_count_fails_above_maximum(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumPlaces': [15]})
        params = {'maximum': 10}
        result = self.validator.validate_num_places_count(test_df, params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 1)
        self.assertEqual(result.details['failed_rows'][0]['actual_value'], 15)

    def test_num_places_count_fails_on_exact_mismatch(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumPlaces': [10]})
        params = {'value': 11}
        result = self.validator.validate_num_places_count(test_df, params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 1)
        self.assertEqual(result.details['failed_rows'][0]['actual_value'], 10)

    def test_num_places_count_passes_within_range(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumPlaces': [10]})
        params = {'minimum': 5, 'maximum': 15}
        result = self.validator.validate_num_places_count(test_df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 1)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_num_places_count_passes_on_exact_match(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumPlaces': [10]})
        params = {'value': 10}
        result = self.validator.validate_num_places_count(test_df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 1)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_num_places_count_passes_on_empty_dataframe(self):
        test_df = pd.DataFrame({'StatVar': [], 'NumPlaces': []})
        params = {'minimum': 1}
        result = self.validator.validate_num_places_count(test_df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 0)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_num_places_count_fails_on_missing_column(self):
        test_df = pd.DataFrame({'StatVar': ['sv1']})  # Missing 'NumPlaces'
        params = {'value': 10}
        result = self.validator.validate_num_places_count(test_df, params)
        self.assertEqual(result.status, ValidationStatus.DATA_ERROR)
        self.assertIn('missing required column', result.message)


class TestMinValueCheckValidation(unittest.TestCase):
    '''Test Class for the MIN_VALUE_CHECK validation rule.'''

    def setUp(self):
        self.validator = Validator()

    def test_min_value_check_fails_below_minimum(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'MinValue': [5]})
        params = {'minimum': 10}
        result = self.validator.validate_min_value_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 1)
        self.assertEqual(result.details['failed_rows'][0]['actual_min_value'],
                         5)

    def test_min_value_check_passes_at_minimum(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'MinValue': [10]})
        params = {'minimum': 10}
        result = self.validator.validate_min_value_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 1)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_min_value_check_passes_on_empty_dataframe(self):
        test_df = pd.DataFrame({'StatVar': [], 'MinValue': []})
        params = {'minimum': 1}
        result = self.validator.validate_min_value_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 0)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_min_value_check_fails_on_missing_config(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'MinValue': [10]})
        params = {}  # Missing 'minimum'
        result = self.validator.validate_min_value_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.CONFIG_ERROR)
        self.assertIn('Configuration error', result.message)

    def test_min_value_check_fails_on_missing_column(self):
        test_df = pd.DataFrame({'StatVar': ['sv1']})  # Missing 'MinValue'
        params = {'minimum': 10}
        result = self.validator.validate_min_value_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.DATA_ERROR)
        self.assertIn('missing required column', result.message)


class TestMaxDateConsistentValidation(unittest.TestCase):
    '''Test Class for the MAX_DATE_CONSISTENT validation rule.'''

    def setUp(self):
        self.validator = Validator()

    def test_max_date_consistent_fails_on_inconsistent_dates(self):
        test_df = pd.DataFrame({
            'StatVar': ['sv1', 'sv2'],
            'MaxDate': ['2024-01-01', '2024-01-02']
        })  # Inconsistent
        result = self.validator.validate_max_date_consistent(test_df, {})
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.message,
                         "The MaxDate is not consistent across all StatVars.")
        self.assertEqual(result.details['distinct_statvar_count'], 2)
        self.assertEqual(result.details['distinct_max_date_counts'], 2)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 2)

    def test_max_date_consistent_passes_on_consistent_dates(self):
        test_df = pd.DataFrame({'MaxDate': ['2024-01-01',
                                            '2024-01-01']})  # Consistent
        result = self.validator.validate_max_date_consistent(test_df, {})
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 2)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_max_date_consistent_passes_on_empty_dataframe(self):
        test_df = pd.DataFrame({'MaxDate': []})
        result = self.validator.validate_max_date_consistent(test_df, {})
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 0)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_max_date_consistent_fails_on_missing_column(self):
        test_df = pd.DataFrame({'StatVar': ['sv1']})  # Missing 'MaxDate'
        result = self.validator.validate_max_date_consistent(test_df, {})
        self.assertEqual(result.status, ValidationStatus.DATA_ERROR)
        self.assertIn('missing required column', result.message)


class TestNumObservationsCheckValidation(unittest.TestCase):
    '''Test Class for the NUM_OBSERVATIONS_CHECK validation rule.'''

    def setUp(self):
        self.validator = Validator()

    def test_num_observations_check_fails_below_minimum(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumObservations': [5]})
        params = {'minimum': 10}
        result = self.validator.validate_num_observations_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 1)
        self.assertEqual(result.details['failed_rows'][0]['actual_value'], 5)

    def test_num_observations_check_fails_above_maximum(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumObservations': [15]})
        params = {'maximum': 10}
        result = self.validator.validate_num_observations_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 1)
        self.assertEqual(result.details['failed_rows'][0]['actual_value'], 15)

    def test_num_observations_check_fails_on_exact_mismatch(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumObservations': [10]})
        params = {'value': 11}
        result = self.validator.validate_num_observations_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 1)
        self.assertEqual(result.details['failed_rows'][0]['actual_value'], 10)

    def test_num_observations_check_passes_within_range(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumObservations': [10]})
        params = {'minimum': 5, 'maximum': 15}
        result = self.validator.validate_num_observations_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 1)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_num_observations_check_passes_on_exact_match(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'NumObservations': [10]})
        params = {'value': 10}
        result = self.validator.validate_num_observations_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 1)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_num_observations_check_passes_on_empty_dataframe(self):
        test_df = pd.DataFrame({'StatVar': [], 'NumObservations': []})
        params = {'minimum': 1}
        result = self.validator.validate_num_observations_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 0)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_num_observations_check_fails_on_missing_column(self):
        test_df = pd.DataFrame({'StatVar': ['sv1']
                               })  # Missing 'NumObservations'
        params = {'value': 10}
        result = self.validator.validate_num_observations_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.DATA_ERROR)
        self.assertIn('missing required column', result.message)


class TestUnitConsistencyValidation(unittest.TestCase):
    '''Test Class for the UNIT_CONSISTENCY_CHECK validation rule.'''

    def setUp(self):
        self.validator = Validator()

    def test_unit_consistency_fails_on_inconsistent_units(self):
        test_df = pd.DataFrame({
            'StatVar': ['sv1', 'sv2'],
            'Units': ['USD', 'Percent']
        })  # Inconsistent
        result = self.validator.validate_unit_consistency(test_df, {})
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.message,
                         "The unit is not consistent across all StatVars.")
        self.assertEqual(result.details['distinct_statvar_count'], 2)
        self.assertEqual(result.details['distinct_unit_counts'], 2)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 2)

    def test_unit_consistency_passes_on_consistent_units(self):
        test_df = pd.DataFrame({'Units': ['USD', 'USD']})  # Consistent
        result = self.validator.validate_unit_consistency(test_df, {})
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 2)
        self.assertEqual(result.details['rows_succeeded'], 2)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_unit_consistency_passes_on_empty_dataframe(self):
        test_df = pd.DataFrame({'Units': []})
        result = self.validator.validate_unit_consistency(test_df, {})
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 0)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_unit_consistency_fails_on_missing_column(self):
        test_df = pd.DataFrame({'StatVar': ['sv1']})  # Missing 'Units'
        result = self.validator.validate_unit_consistency(test_df, {})
        self.assertEqual(result.status, ValidationStatus.DATA_ERROR)
        self.assertIn('missing required column', result.message)


class TestMaxValueCheckValidation(unittest.TestCase):
    '''Test Class for the MAX_VALUE_CHECK validation rule.'''

    def setUp(self):
        self.validator = Validator()

    def test_max_value_check_fails_above_maximum(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'MaxValue': [15]})
        params = {'maximum': 10}
        result = self.validator.validate_max_value_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 1)
        self.assertEqual(result.details['failed_rows'][0]['actual_max_value'],
                         15)

    def test_max_value_check_passes_at_maximum(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'MaxValue': [10]})
        params = {'maximum': 10}
        result = self.validator.validate_max_value_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 1)
        self.assertEqual(result.details['rows_succeeded'], 1)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_max_value_check_passes_on_empty_dataframe(self):
        test_df = pd.DataFrame({'StatVar': [], 'MaxValue': []})
        params = {'maximum': 1}
        result = self.validator.validate_max_value_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.details['rows_processed'], 0)
        self.assertEqual(result.details['rows_succeeded'], 0)
        self.assertEqual(result.details['rows_failed'], 0)

    def test_max_value_check_fails_on_missing_config(self):
        test_df = pd.DataFrame({'StatVar': ['sv1'], 'MaxValue': [10]})
        params = {}  # Missing 'maximum'
        result = self.validator.validate_max_value_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.CONFIG_ERROR)
        self.assertIn('Configuration error', result.message)

    def test_max_value_check_fails_on_missing_column(self):
        test_df = pd.DataFrame({'StatVar': ['sv1']})  # Missing 'MaxValue'
        params = {'maximum': 10}
        result = self.validator.validate_max_value_check(test_df, params)
        self.assertEqual(result.status, ValidationStatus.DATA_ERROR)
        self.assertIn('missing required column', result.message)


class TestSQLValidator(unittest.TestCase):
    '''Test Class for the SQL_VALIDATOR validation rule.'''

    def setUp(self):
        self.validator = Validator()
        self.stats_df = pd.DataFrame({
            'StatVar': ['sv1', 'sv2', 'sv3'],
            'MaxValue': [100, 101, 99],
            'NumPlaces': [10, 10, 20]
        })
        self.differ_df = pd.DataFrame({
            'StatVar': ['sv1', 'sv2', 'sv3'],
            'ADDED': [5, 0, 5]
        })

    def test_sql_validator_passes(self):
        params = {
            'query': 'SELECT StatVar, MaxValue FROM stats',
            'condition': 'MaxValue <= 101'
        }
        result = self.validator.validate_sql(self.stats_df, self.differ_df,
                                             params)
        self.assertEqual(result.status, ValidationStatus.PASSED)

    def test_sql_validator_fails(self):
        params = {
            'query': 'SELECT StatVar, MaxValue FROM stats',
            'condition': 'MaxValue <= 100'
        }
        result = self.validator.validate_sql(self.stats_df, self.differ_df,
                                             params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(len(result.details['failing_rows']), 1)
        self.assertEqual(result.details['failing_rows'][0]['StatVar'], 'sv2')

    def test_sql_validator_aggregation_passes(self):
        params = {
            'query':
                'SELECT NumPlaces, COUNT(StatVar) as sv_count FROM stats GROUP BY NumPlaces',
            'condition':
                'sv_count >= 1'
        }
        result = self.validator.validate_sql(self.stats_df, self.differ_df,
                                             params)
        self.assertEqual(result.status, ValidationStatus.PASSED)

    def test_sql_validator_aggregation_fails(self):
        params = {
            'query':
                'SELECT NumPlaces, COUNT(StatVar) as sv_count FROM stats GROUP BY NumPlaces',
            'condition':
                'sv_count > 1'
        }
        result = self.validator.validate_sql(self.stats_df, self.differ_df,
                                             params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(len(result.details['failing_rows']), 1)
        self.assertEqual(result.details['failing_rows'][0]['NumPlaces'], 20)

    def test_sql_validator_join_fails(self):
        params = {
            'query':
                'SELECT s.StatVar as statvar, s.MaxValue as max_val, d.ADDED as added_val FROM stats s JOIN differ d ON s.StatVar = d.StatVar',
            'condition':
                "statvar = 'sv1'"
        }
        result = self.validator.validate_sql(self.stats_df, self.differ_df,
                                             params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(len(result.details['failing_rows']), 2)

    def test_sql_validator_invalid_sql(self):
        params = {'query': 'SELEC * FROM stats', 'condition': 'MaxValue <= 100'}
        result = self.validator.validate_sql(self.stats_df, self.differ_df,
                                             params)
        self.assertEqual(result.status, ValidationStatus.CONFIG_ERROR)
        self.assertIn('SQL Error', result.message)

    def test_sql_validator_missing_params(self):
        params = {'query': 'SELECT * FROM stats'}
        result = self.validator.validate_sql(self.stats_df, self.differ_df,
                                             params)
        self.assertEqual(result.status, ValidationStatus.CONFIG_ERROR)
        self.assertIn('must be specified', result.message)


if __name__ == '__main__':
    unittest.main()
