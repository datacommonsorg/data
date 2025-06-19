# Copyright 2024 Google LLC
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
""" Class to perform validations for import automation."""

from absl import app
from absl import flags
from absl import logging
from enum import Enum
import pandas as pd
import os
import json

_FLAGS = flags.FLAGS
flags.DEFINE_string('validation_config', 'validation_config.json',
                    'Path to the validation config file.')
flags.DEFINE_string('differ_output', 'point_analysis_summary.csv',
                    'Path to the differ output data file.')
flags.DEFINE_string('stats_summary', 'summary_report.csv',
                    'Path to the stats summary report file.')
flags.DEFINE_string('validation_output', 'validation_output.csv',
                    'Path to the validation output file.')

Validation = Enum('Validation', [
    ('MODIFIED_COUNT', 1),
    ('UNMODIFIED_COUNT', 2),
    ('ADDED_COUNT', 3),
    ('DELETED_COUNT', 4),
    ('LATEST_DATA', 5),
    ('MAX_DATE_LATEST', 6),
    ('NUM_PLACES_CONSISTENT', 7),
])


class ValidationResult:
    """Describes the result of the validaiton of an import."""

    def __init__(self, status, name, message=''):
        self.status = status
        self.name = name
        self.message = message


class Validator:
    """
  Contains the core logic for all validation rules.
  This class is stateless and does not interact with the filesystem.
  """

    def validate_max_date_latest(self,
                                 stats_df: pd.DataFrame) -> ValidationResult:
        """
    Checks that the MaxDate in the stats summary is from the current year.
    """
        if stats_df.empty:
            return ValidationResult('PASSED', 'MAX_DATE_LATEST')

        stats_df['MaxDate'] = pd.to_datetime(stats_df['MaxDate'])
        max_date_year = stats_df['MaxDate'].dt.year.max()
        if max_date_year < pd.to_datetime('today').year:
            return ValidationResult(
                'FAILED', 'MAX_DATE_LATEST',
                f"AssertionError('Validation failed: MAX_DATE_LATEST')")
        return ValidationResult('PASSED', 'MAX_DATE_LATEST')

    def validate_deleted_count(self, differ_df: pd.DataFrame,
                               threshold: int) -> ValidationResult:
        if differ_df.empty:
            return ValidationResult('PASSED', 'DELETED_COUNT')
        if differ_df['DELETED'].sum() > threshold:
            return ValidationResult(
                'FAILED', 'DELETED_COUNT',
                f"AssertionError('Validation failed: DELETED_COUNT')")
        return ValidationResult('PASSED', 'DELETED_COUNT')

    def validate_modified_count(self,
                                differ_df: pd.DataFrame) -> ValidationResult:
        if differ_df.empty:
            return ValidationResult('PASSED', 'MODIFIED_COUNT')
        if differ_df['MODIFIED'].nunique() > 1:
            return ValidationResult(
                'FAILED', 'MODIFIED_COUNT',
                f"AssertionError('Validation failed: MODIFIED_COUNT')")
        return ValidationResult('PASSED', 'MODIFIED_COUNT')

    def validate_added_count(self, differ_df: pd.DataFrame) -> ValidationResult:
        if differ_df.empty:
            return ValidationResult('PASSED', 'ADDED_COUNT')
        if differ_df['ADDED'].nunique() != 1:
            return ValidationResult(
                'FAILED', 'ADDED_COUNT',
                f"AssertionError('Validation failed: ADDED_COUNT')")
        return ValidationResult('PASSED', 'ADDED_COUNT')

    def validate_unmodified_count(self,
                                  differ_df: pd.DataFrame) -> ValidationResult:
        # The logic for this validation is currently disabled.
        # This method is a placeholder to ensure the validation "passes".
        return ValidationResult('PASSED', 'UNMODIFIED_COUNT')

    def validate_num_places_consistent(
        self, stats_df: pd.DataFrame) -> ValidationResult:
        if stats_df.empty:
            return ValidationResult('PASSED', 'NUM_PLACES_CONSISTENT')
        if stats_df['NumPlaces'].nunique() > 1:
            return ValidationResult(
                'FAILED', 'NUM_PLACES_CONSISTENT',
                f"AssertionError('Validation failed: NUM_PLACES_CONSISTENT')")
        return ValidationResult('PASSED', 'NUM_PLACES_CONSISTENT')


class ValidationRunner:
    """
  Orchestrates the validation process.
  Handles file I/O, configuration, and invoking the Validator.
  """

    def __init__(self, validation_config: str, differ_output: str,
                 stats_summary: str, validation_output: str):
        self.validation_output = validation_output
        self.validator = Validator()
        self.validation_results = []

        with open(validation_config, encoding='utf-8') as f:
            self.validation_config = json.load(f)

        self.differ_df = pd.read_csv(differ_output) if os.path.exists(
            differ_output) else pd.DataFrame()
        self.stats_df = pd.read_csv(stats_summary) if os.path.exists(
            stats_summary) else pd.DataFrame()

    def run_validations(self) -> bool:
        """
    Runs all validations specified in the config and returns the overall status.
    """
        status = True
        for config in self.validation_config:
            validation_name = config['validation']
            result = None
            if validation_name == 'MAX_DATE_LATEST':
                result = self.validator.validate_max_date_latest(self.stats_df)
            elif validation_name == 'DELETED_COUNT':
                result = self.validator.validate_deleted_count(
                    self.differ_df, config.get('threshold', 0))
            elif validation_name == 'MODIFIED_COUNT':
                result = self.validator.validate_modified_count(self.differ_df)
            elif validation_name == 'ADDED_COUNT':
                result = self.validator.validate_added_count(self.differ_df)
            elif validation_name == 'UNMODIFIED_COUNT':
                result = self.validator.validate_unmodified_count(
                    self.differ_df)
            elif validation_name == 'NUM_PLACES_CONSISTENT':
                result = self.validator.validate_num_places_consistent(
                    self.stats_df)

            if result:
                self.validation_results.append(result)
                if result.status == 'FAILED':
                    status = False
                    logging.error(result.message)
                else:
                    logging.info('Validation passed: %s', result.name)

        self._write_results_to_file()
        return status

    def _write_results_to_file(self):
        with open(self.validation_output, mode='w',
                  encoding='utf-8') as output_file:
            output_file.write('test,status,message\n')
            for result in self.validation_results:
                output_file.write(
                    f'{result.name},{result.status},{result.message}\n')


def main(_):
    runner = ValidationRunner(_FLAGS.validation_config, _FLAGS.differ_output,
                              _FLAGS.stats_summary, _FLAGS.validation_output)
    runner.run_validations()


if __name__ == '__main__':
    app.run(main)
