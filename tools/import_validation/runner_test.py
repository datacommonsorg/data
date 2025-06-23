# Copyright 2025 Google LLC
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
"""Tests for the ValidationRunner."""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import os
import json
import tempfile

from tools.import_validation.runner import ValidationRunner
from tools.import_validation.result import ValidationResult, ValidationStatus


class TestValidationRunner(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.test_dir.name, 'config.json')
        self.stats_path = os.path.join(self.test_dir.name, 'stats.csv')
        self.differ_path = os.path.join(self.test_dir.name, 'differ.csv')
        self.output_path = os.path.join(self.test_dir.name, 'output.csv')

    def tearDown(self):
        # Clean up the temporary directory
        self.test_dir.cleanup()

    @patch('tools.import_validation.runner.Validator')
    def test_runner_calls_correct_validator_function(self, MockValidator):
        # 1. Setup the mock
        mock_validator_instance = MockValidator.return_value
        mock_validator_instance.validate_max_date_latest.return_value = ValidationResult(
            ValidationStatus.PASSED, 'MAX_DATE_LATEST')

        # 2. Create test files
        with open(self.config_path, 'w') as f:
            json.dump(
                {
                    'rules': [{
                        'rule_id': 'test_max_date',
                        'validator': 'MAX_DATE_LATEST',
                        'scope': {
                            'data_source': 'stats'
                        },
                        'params': {}
                    }]
                }, f)
        pd.DataFrame({
            'StatVar': ['sv1'],
            'MaxDate': ['2024-01-01']
        }).to_csv(self.stats_path, index=False)

        # 3. Run the runner
        runner = ValidationRunner(
            validation_config_path=self.config_path,
            stats_summary=self.stats_path,
            differ_output=self.differ_path,  # Will be empty
            validation_output=self.output_path)
        runner.run_validations()

        # 4. Assert that the correct method was called on the mock
        mock_validator_instance.validate_max_date_latest.assert_called_once()
        # Ensure other methods were NOT called
        mock_validator_instance.validate_deleted_count.assert_not_called()

    @unittest.skip("Variable filtering not yet implemented in new runner.")
    @patch('tools.import_validation.runner.filter_dataframe')
    @patch('tools.import_validation.runner.Validator')
    def test_runner_applies_filters_correctly(self, MockValidator,
                                              mock_filter_dataframe):
        # 1. Setup mocks
        mock_validator_instance = MockValidator.return_value
        mock_validator_instance.validate_num_places_consistent.return_value = ValidationResult(
            ValidationStatus.PASSED, 'NUM_PLACES_CONSISTENT')
        # Make the mock filter function return a specific dummy dataframe
        mock_filter_dataframe.return_value = pd.DataFrame(
            {'StatVar': ['filtered_sv']})

        # 2. Create test files
        config = {
            'rules': [{
                'rule_id': 'test_places_consistent',
                'validator': 'NUM_PLACES_CONSISTENT',
                'scope': {
                    'data_source': 'stats',
                    'variables': {
                        'dcids': ['Count_Person_Male']
                    }
                },
                'params': {}
            }]
        }
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
        original_df = pd.DataFrame({
            'StatVar': ['sv1', 'sv2'],
            'NumPlaces': [10, 20]
        })
        original_df.to_csv(self.stats_path, index=False)

        # 3. Run the runner
        runner = ValidationRunner(validation_config_path=self.config_path,
                                  stats_summary=self.stats_path,
                                  differ_output=self.differ_path,
                                  validation_output=self.output_path)
        runner.run_validations()

        # 4. Assert that the filter function was called correctly
        mock_filter_dataframe.assert_called_once()
        # Check that the validator was called with the *filtered* dataframe
        call_args, _ = mock_validator_instance.validate_num_places_consistent.call_args
        filtered_df_arg = call_args[0]
        self.assertEqual(filtered_df_arg.iloc[0]['StatVar'], 'filtered_sv')

    @patch('tools.import_validation.runner.Validator')
    def test_runner_handles_failed_validation(self, MockValidator):
        # 1. Setup the mock to return a FAILED result
        mock_validator_instance = MockValidator.return_value
        mock_validator_instance.validate_max_date_latest.return_value = ValidationResult(
            ValidationStatus.FAILED, 'MAX_DATE_LATEST', 'It failed')

        # 2. Create test files
        with open(self.config_path, 'w') as f:
            json.dump(
                {
                    'rules': [{
                        'rule_id': 'test_max_date',
                        'validator': 'MAX_DATE_LATEST',
                        'scope': {
                            'data_source': 'stats'
                        },
                        'params': {}
                    }]
                }, f)
        pd.DataFrame({
            'StatVar': ['sv1'],
            'MaxDate': ['2024-01-01']
        }).to_csv(self.stats_path, index=False)

        # 3. Run the runner
        runner = ValidationRunner(validation_config_path=self.config_path,
                                  stats_summary=self.stats_path,
                                  differ_output=self.differ_path,
                                  validation_output=self.output_path)
        overall_status, _ = runner.run_validations()

        # 4. Assert that the overall status is False
        self.assertFalse(overall_status)

    @patch('tools.import_validation.runner.Validator')
    def test_runner_writes_correct_output(self, MockValidator):
        # 1. Setup the mock to return a specific result
        mock_validator_instance = MockValidator.return_value
        expected_result = ValidationResult(
            ValidationStatus.FAILED,
            'DELETED_COUNT',
            message='Too many deletions, found 100',
            details={'deleted_count': 100},
            rows_processed=1,
            rows_succeeded=0,
            rows_failed=1)
        mock_validator_instance.validate_deleted_count.return_value = expected_result

        # 2. Create test files
        with open(self.config_path, 'w') as f:
            json.dump(
                {
                    'rules': [{
                        'rule_id': 'check_deleted_count',
                        'validator': 'DELETED_COUNT',
                        'scope': {
                            'data_source': 'differ'
                        },
                        'params': {
                            'threshold': 10
                        }
                    }]
                }, f)
        pd.DataFrame({'DELETED': [100]}).to_csv(self.differ_path, index=False)

        # 3. Run the runner
        runner = ValidationRunner(validation_config_path=self.config_path,
                                  stats_summary=self.stats_path,
                                  differ_output=self.differ_path,
                                  validation_output=self.output_path)
        runner.run_validations()

        # 4. Read the output file and assert its contents
        output_df = pd.read_csv(self.output_path)
        self.assertEqual(len(output_df), 1)
        self.assertEqual(output_df.iloc[0]['ValidationName'],
                         'check_deleted_count')
        self.assertEqual(output_df.iloc[0]['Status'], 'FAILED')
        self.assertEqual(output_df.iloc[0]['Message'],
                         'Too many deletions, found 100')
        self.assertEqual(
            json.loads(output_df.iloc[0]['Details']), {'deleted_count': 100})
        self.assertEqual(output_df.iloc[0]['RowsProcessed'], 1)
        self.assertEqual(output_df.iloc[0]['RowsSucceeded'], 0)
        self.assertEqual(output_df.iloc[0]['RowsFailed'], 1)

    @patch('tools.import_validation.runner.Validator')
    def test_runner_uses_custom_name(self, MockValidator):
        # This test is less relevant with rule_id, but we can keep it
        # to ensure the output uses the rule_id.
        mock_validator_instance = MockValidator.return_value
        mock_validator_instance.validate_max_date_latest.return_value = ValidationResult(
            ValidationStatus.PASSED, 'MAX_DATE_LATEST')

        with open(self.config_path, 'w') as f:
            json.dump(
                {
                    'rules': [{
                        'rule_id': 'My_Custom_Test_Name',
                        'validator': 'MAX_DATE_LATEST',
                        'scope': {
                            'data_source': 'stats'
                        },
                        'params': {}
                    }]
                }, f)
        pd.DataFrame({
            'StatVar': ['sv1'],
            'MaxDate': ['2025-01-01']
        }).to_csv(self.stats_path, index=False)

        runner = ValidationRunner(validation_config_path=self.config_path,
                                  stats_summary=self.stats_path,
                                  differ_output=self.differ_path,
                                  validation_output=self.output_path)
        runner.run_validations()

        output_df = pd.read_csv(self.output_path)
        self.assertEqual(len(output_df), 1)
        self.assertEqual(output_df.iloc[0]['ValidationName'],
                         'My_Custom_Test_Name')

    @patch('tools.import_validation.runner.logging')
    @patch('tools.import_validation.runner.Validator')
    def test_runner_handles_unknown_validation(self, MockValidator,
                                               mock_logging):
        with open(self.config_path, 'w') as f:
            json.dump(
                {
                    'rules': [{
                        'rule_id': 'test_fake',
                        'validator': 'FAKE_VALIDATION',
                        'scope': {
                            'data_source': 'stats'
                        },
                        'params': {}
                    }]
                }, f)
        pd.DataFrame({'StatVar': ['sv1']}).to_csv(self.stats_path,
                                                  index=False)

        runner = ValidationRunner(validation_config_path=self.config_path,
                                  stats_summary=self.stats_path,
                                  differ_output=self.differ_path,
                                  validation_output=self.output_path)
        runner.run_validations()

        mock_logging.warning.assert_called_with('Unknown validator: %s',
                                                'FAKE_VALIDATION')
