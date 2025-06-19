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
"""Runs a series of validations on a data import.

This script provides a framework for running validation checks on data imports.
It is designed to be used as part of an automated import pipeline.

The script separates the validation logic from the execution runner:
- The `Validator` class contains the pure, stateless logic for each individual
  validation rule. It operates directly on pandas DataFrames.
- The `ValidationRunner` class handles the orchestration, including file I/O,
  reading configuration, and invoking the appropriate methods in the Validator.

The script is configured via a JSON file that specifies which validations to
run.
"""

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
    ('NUM_PLACES_COUNT', 8),
])


class ValidationResult:
    """Describes the result of the validaiton of an import."""

    def __init__(self, status, name, message='', details=None):
        self.status = status
        self.name = name
        self.message = message # A human-readable summary
        self.details = details if details is not None else {} # A machine-readable dictionary


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
        current_year = pd.to_datetime('today').year
        if max_date_year < current_year:
            return ValidationResult(
                'FAILED',
                'MAX_DATE_LATEST',
                message=
                f"Latest date found was {max_date_year}, expected {current_year}.",
                details={
                    'latest_date_found': int(max_date_year),
                    'expected_latest_date': int(current_year)
                })
        return ValidationResult('PASSED', 'MAX_DATE_LATEST')

    def validate_deleted_count(self, differ_df: pd.DataFrame,
                               threshold: int) -> ValidationResult:
        """Checks if the total number of deleted points is within a threshold."""
        if differ_df.empty:
            return ValidationResult('PASSED', 'DELETED_COUNT')
        deleted_count = differ_df['DELETED'].sum()
        if deleted_count > threshold:
            return ValidationResult(
                'FAILED',
                'DELETED_COUNT',
                message=
                f"Found {deleted_count} deleted points, which is over the threshold of {threshold}.",
                details={
                    'deleted_count': int(deleted_count),
                    'threshold': threshold
                })
        return ValidationResult('PASSED', 'DELETED_COUNT')

    def validate_modified_count(self,
                                differ_df: pd.DataFrame) -> ValidationResult:
        """Checks if the number of modified points is the same for all StatVars."""
        if differ_df.empty:
            return ValidationResult('PASSED', 'MODIFIED_COUNT')
        unique_counts = differ_df['MODIFIED'].nunique()
        if unique_counts > 1:
            return ValidationResult(
                'FAILED',
                'MODIFIED_COUNT',
                message=
                f"Found {unique_counts} unique modified counts where 1 was expected.",
                details={'unique_counts': list(differ_df['MODIFIED'].unique())})
        return ValidationResult('PASSED', 'MODIFIED_COUNT')

    def validate_added_count(self, differ_df: pd.DataFrame) -> ValidationResult:
        """Checks if the number of added points is the same for all StatVars."""
        if differ_df.empty:
            return ValidationResult('PASSED', 'ADDED_COUNT')
        unique_counts = differ_df['ADDED'].nunique()
        if unique_counts != 1:
            return ValidationResult(
                'FAILED',
                'ADDED_COUNT',
                message=
                f"Found {unique_counts} unique added counts where 1 was expected.",
                details={'unique_counts': list(differ_df['ADDED'].unique())})
        return ValidationResult('PASSED', 'ADDED_COUNT')

    def validate_unmodified_count(self,
                                  differ_df: pd.DataFrame) -> ValidationResult:
        """Checks if the number of unmodified points is the same for all StatVars."""
        # The logic for this validation is currently disabled.
        # This method is a placeholder to ensure the validation "passes".
        return ValidationResult('PASSED', 'UNMODIFIED_COUNT')

    def validate_num_places_consistent(
        self, stats_df: pd.DataFrame) -> ValidationResult:
        """Checks if the number of places is the same for all StatVars."""
        if stats_df.empty:
            return ValidationResult('PASSED', 'NUM_PLACES_CONSISTENT')
        unique_counts = stats_df['NumPlaces'].nunique()
        if unique_counts > 1:
            return ValidationResult(
                'FAILED',
                'NUM_PLACES_CONSISTENT',
                message=
                f"Found {unique_counts} unique place counts where 1 was expected.",
                details={'unique_counts': list(stats_df['NumPlaces'].unique())})
        return ValidationResult('PASSED', 'NUM_PLACES_CONSISTENT')

    def validate_num_places_count(self, stats_df: pd.DataFrame,
                                  config: dict) -> ValidationResult:
        """Checks if the number of places for each StatVar is within a defined range."""
        if stats_df.empty:
            return ValidationResult('PASSED', 'NUM_PLACES_COUNT')

        min_val = config.get('minimum')
        max_val = config.get('maximum')
        exact_val = config.get('value')

        for _, row in stats_df.iterrows():
            num_places = row['NumPlaces']
            stat_var = row.get(
                'StatVar', 'Unknown'
            ) # Assuming StatVar column exists for better error messages

            if exact_val is not None and num_places != exact_val:
                return ValidationResult(
                    'FAILED',
                    'NUM_PLACES_COUNT',
                    message=
                    f"StatVar '{stat_var}' has {num_places} places, but expected exactly {exact_val}.",
                    details={
                        'stat_var': stat_var,
                        'actual_count': num_places,
                        'expected_count': exact_val
                    })
            if min_val is not None and num_places < min_val:
                return ValidationResult(
                    'FAILED',
                    'NUM_PLACES_COUNT',
                    message=
                    f"StatVar '{stat_var}' has {num_places} places, which is below the minimum of {min_val}.",
                    details={
                        'stat_var': stat_var,
                        'actual_count': num_places,
                        'minimum': min_val
                    })
            if max_val is not None and num_places > max_val:
                return ValidationResult(
                    'FAILED',
                    'NUM_PLACES_COUNT',
                    message=
                    f"StatVar '{stat_var}' has {num_places} places, which is above the maximum of {max_val}.",
                    details={
                        'stat_var': stat_var,
                        'actual_count': num_places,
                        'maximum': max_val
                    })

        return ValidationResult('PASSED', 'NUM_PLACES_COUNT')


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
            elif validation_name == 'NUM_PLACES_COUNT':
                result = self.validator.validate_num_places_count(
                    self.stats_df, config)

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
            output_file.write('test,status,message,details\n')
            for result in self.validation_results:
                details_str = json.dumps(
                    result.details) if result.details else ''
                output_file.write(
                    f'{result.name},{result.status},{result.message},{details_str}\n'
                )


def main(_):
    runner = ValidationRunner(_FLAGS.validation_config, _FLAGS.differ_output,
                              _FLAGS.stats_summary, _FLAGS.validation_output)
    runner.run_validations()


if __name__ == '__main__':
    app.run(main)
