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

import os
import pandas as pd
import unittest
import json
from datetime import datetime

from tools.import_validation import import_validation

module_dir = os.path.dirname(__file__)


class TestMaxDateLatestValidation(unittest.TestCase):
    '''Test Class for the MAX_DATE_LATEST validation rule.'''

    def setUp(self):
        self.test_data_dir = os.path.join(module_dir, 'test_data',
                                          'max_date_latest')
        os.makedirs(self.test_data_dir, exist_ok=True)
        # Clean up previous test files
        for f in os.listdir(self.test_data_dir):
            os.remove(os.path.join(self.test_data_dir, f))

    def test_max_date_latest_fails_on_old_date(self):
        config_path = os.path.join(self.test_data_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump([{'validation': 'MAX_DATE_LATEST'}], f)

        stats_path = os.path.join(self.test_data_dir, 'stats.csv')
        old_year = datetime.now().year - 2
        pd.DataFrame({
            'MaxDate': [f'{old_year}-01-01']
        }).to_csv(stats_path, index=False)

        validator = import_validation.ImportValidation(
            validation_config=config_path,
            stats_summary=stats_path,
            differ_output='',
            validation_output=os.path.join(self.test_data_dir, 'output.csv'))
        validator.run_validations()

        result = validator.validation_result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, 'FAILED')
        self.assertEqual(result[0].name, 'MAX_DATE_LATEST')

    def test_max_date_latest_passes_on_current_date(self):
        config_path = os.path.join(self.test_data_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump([{'validation': 'MAX_DATE_LATEST'}], f)

        stats_path = os.path.join(self.test_data_dir, 'stats.csv')
        current_year = datetime.now().year
        pd.DataFrame({
            'MaxDate': [f'{current_year}-01-01']
        }).to_csv(stats_path, index=False)

        validator = import_validation.ImportValidation(
            validation_config=config_path,
            stats_summary=stats_path,
            differ_output='',
            validation_output=os.path.join(self.test_data_dir, 'output.csv'))
        validator.run_validations()

        result = validator.validation_result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, 'PASSED')
        self.assertEqual(result[0].name, 'MAX_DATE_LATEST')


class TestDeletedCountValidation(unittest.TestCase):
    '''Test Class for the DELETED_COUNT validation rule.'''

    def setUp(self):
        self.test_data_dir = os.path.join(module_dir, 'test_data',
                                          'deleted_count')
        os.makedirs(self.test_data_dir, exist_ok=True)
        # Clean up previous test files
        for f in os.listdir(self.test_data_dir):
            os.remove(os.path.join(self.test_data_dir, f))

    def test_deleted_count_fails_when_over_threshold(self):
        config_path = os.path.join(self.test_data_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(
                [{
                    'validation': 'DELETED_COUNT',
                    'threshold': 1
                }], f)

        differ_path = os.path.join(self.test_data_dir, 'differ.csv')
        pd.DataFrame({
            'DELETED': [1, 1]
        }).to_csv(differ_path, index=False) # Total deleted = 2

        validator = import_validation.ImportValidation(
            validation_config=config_path,
            stats_summary='',
            differ_output=differ_path,
            validation_output=os.path.join(self.test_data_dir, 'output.csv'))
        validator.run_validations()

        result = validator.validation_result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, 'FAILED')
        self.assertEqual(result[0].name, 'DELETED_COUNT')

    def test_deleted_count_passes_when_at_threshold(self):
        config_path = os.path.join(self.test_data_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(
                [{
                    'validation': 'DELETED_COUNT',
                    'threshold': 2
                }], f)

        differ_path = os.path.join(self.test_data_dir, 'differ.csv')
        pd.DataFrame({
            'DELETED': [1, 1]
        }).to_csv(differ_path, index=False) # Total deleted = 2

        validator = import_validation.ImportValidation(
            validation_config=config_path,
            stats_summary='',
            differ_output=differ_path,
            validation_output=os.path.join(self.test_data_dir, 'output.csv'))
        validator.run_validations()

        result = validator.validation_result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, 'PASSED')
        self.assertEqual(result[0].name, 'DELETED_COUNT')


class TestModifiedCountValidation(unittest.TestCase):
    '''Test Class for the MODIFIED_COUNT validation rule.'''

    def setUp(self):
        self.test_data_dir = os.path.join(module_dir, 'test_data',
                                          'modified_count')
        os.makedirs(self.test_data_dir, exist_ok=True)
        for f in os.listdir(self.test_data_dir):
            os.remove(os.path.join(self.test_data_dir, f))

    def test_modified_count_fails_on_inconsistent_counts(self):
        config_path = os.path.join(self.test_data_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump([{'validation': 'MODIFIED_COUNT'}], f)

        differ_path = os.path.join(self.test_data_dir, 'differ.csv')
        pd.DataFrame({
            'MODIFIED': [1, 2]
        }).to_csv(differ_path, index=False) # Inconsistent counts

        validator = import_validation.ImportValidation(
            validation_config=config_path,
            stats_summary='',
            differ_output=differ_path,
            validation_output=os.path.join(self.test_data_dir, 'output.csv'))
        validator.run_validations()

        result = validator.validation_result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, 'FAILED')
        self.assertEqual(result[0].name, 'MODIFIED_COUNT')

    def test_modified_count_passes_on_consistent_counts(self):
        config_path = os.path.join(self.test_data_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump([{'validation': 'MODIFIED_COUNT'}], f)

        differ_path = os.path.join(self.test_data_dir, 'differ.csv')
        pd.DataFrame({
            'MODIFIED': [2, 2]
        }).to_csv(differ_path, index=False) # Consistent counts

        validator = import_validation.ImportValidation(
            validation_config=config_path,
            stats_summary='',
            differ_output=differ_path,
            validation_output=os.path.join(self.test_data_dir, 'output.csv'))
        validator.run_validations()

        result = validator.validation_result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, 'PASSED')
        self.assertEqual(result[0].name, 'MODIFIED_COUNT')


class TestAddedCountValidation(unittest.TestCase):
    '''Test Class for the ADDED_COUNT validation rule.'''

    def setUp(self):
        self.test_data_dir = os.path.join(module_dir, 'test_data',
                                          'added_count')
        os.makedirs(self.test_data_dir, exist_ok=True)
        for f in os.listdir(self.test_data_dir):
            os.remove(os.path.join(self.test_data_dir, f))

    def test_added_count_fails_on_inconsistent_counts(self):
        config_path = os.path.join(self.test_data_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump([{'validation': 'ADDED_COUNT'}], f)

        differ_path = os.path.join(self.test_data_dir, 'differ.csv')
        pd.DataFrame({
            'ADDED': [1, 2]
        }).to_csv(differ_path, index=False) # Inconsistent counts

        validator = import_validation.ImportValidation(
            validation_config=config_path,
            stats_summary='',
            differ_output=differ_path,
            validation_output=os.path.join(self.test_data_dir, 'output.csv'))
        validator.run_validations()

        result = validator.validation_result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, 'FAILED')
        self.assertEqual(result[0].name, 'ADDED_COUNT')

    def test_added_count_passes_on_consistent_counts(self):
        config_path = os.path.join(self.test_data_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump([{'validation': 'ADDED_COUNT'}], f)

        differ_path = os.path.join(self.test_data_dir, 'differ.csv')
        pd.DataFrame({
            'ADDED': [1, 1]
        }).to_csv(differ_path, index=False) # Consistent counts

        validator = import_validation.ImportValidation(
            validation_config=config_path,
            stats_summary='',
            differ_output=differ_path,
            validation_output=os.path.join(self.test_data_dir, 'output.csv'))
        validator.run_validations()

        result = validator.validation_result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, 'PASSED')
        self.assertEqual(result[0].name, 'ADDED_COUNT')


class TestUnmodifiedCountValidation(unittest.TestCase):
    '''Test Class for the UNMODIFIED_COUNT validation rule.'''

    def setUp(self):
        self.test_data_dir = os.path.join(module_dir, 'test_data',
                                          'unmodified_count')
        os.makedirs(self.test_data_dir, exist_ok=True)
        for f in os.listdir(self.test_data_dir):
            os.remove(os.path.join(self.test_data_dir, f))

    def test_unmodified_count_is_always_successful(self):
        # This test is here to ensure the validation runs without error.
        # The validation logic is currently commented out in the source.
        config_path = os.path.join(self.test_data_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump([{'validation': 'UNMODIFIED_COUNT'}], f)

        differ_path = os.path.join(self.test_data_dir, 'differ.csv')
        pd.DataFrame({
            'UNMODIFIED': [1, 2]
        }).to_csv(differ_path, index=False)

        validator = import_validation.ImportValidation(
            validation_config=config_path,
            stats_summary='',
            differ_output=differ_path,
            validation_output=os.path.join(self.test_data_dir, 'output.csv'))
        validator.run_validations()

        result = validator.validation_result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, 'PASSED')
        self.assertEqual(result[0].name, 'UNMODIFIED_COUNT')


if __name__ == '__main__':
    unittest.main()
