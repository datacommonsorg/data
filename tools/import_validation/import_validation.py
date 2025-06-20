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
import pandas as pd
import csv
import json
import os
import sys

from .validator import Validator
from .util import filter_dataframe
from .result import ValidationResult, ValidationStatus

_FLAGS = flags.FLAGS
flags.DEFINE_string('validation_config', 'validation_config.json',
                    'Path to the validation config file.')
flags.DEFINE_string('differ_output', None,
                    'Path to the differ output data file.')
flags.DEFINE_string('stats_summary', None,
                    'Path to the stats summary report file.')
flags.DEFINE_string('validation_output', None,
                    'Path to the validation output file.')
flags.mark_flag_as_required('differ_output')
flags.mark_flag_as_required('stats_summary')
flags.mark_flag_as_required('validation_output')


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

        self.dataframes = {
            'stats':
                pd.read_csv(stats_summary)
                if os.path.exists(stats_summary) else pd.DataFrame(),
            'differ':
                pd.read_csv(differ_output)
                if os.path.exists(differ_output) else pd.DataFrame()
        }

        # This dispatch map links a validation name to its function and the
        # dataframe it requires.
        self.validation_dispatch = {
            'MAX_DATE_LATEST':
                (self.validator.validate_max_date_latest, 'stats'),
            'MAX_DATE_CONSISTENT':
                (self.validator.validate_max_date_consistent, 'stats'),
            'DELETED_COUNT': (self.validator.validate_deleted_count, 'differ'),
            'MODIFIED_COUNT':
                (self.validator.validate_modified_count, 'differ'),
            'ADDED_COUNT': (self.validator.validate_added_count, 'differ'),
            'UNMODIFIED_COUNT':
                (self.validator.validate_unmodified_count, 'differ'),
            'NUM_PLACES_CONSISTENT':
                (self.validator.validate_num_places_consistent, 'stats'),
            'NUM_PLACES_COUNT':
                (self.validator.validate_num_places_count, 'stats'),
            'NUM_OBSERVATIONS_CHECK':
                (self.validator.validate_num_observations_check, 'stats'),
            'UNIT_CONSISTENCY_CHECK':
                (self.validator.validate_unit_consistency, 'stats'),
            'MIN_VALUE_CHECK':
                (self.validator.validate_min_value_check, 'stats'),
            'MAX_VALUE_CHECK':
                (self.validator.validate_max_value_check, 'stats'),
        }

    def run_validations(self) -> bool:
        """
    Runs all validations specified in the config and returns the overall status.
    """
        overall_status = True
        for config in self.validation_config:
            validation_name = config['validation']
            if validation_name not in self.validation_dispatch:
                logging.warning('Unknown validation: %s', validation_name)
                continue

            validation_func, df_key = self.validation_dispatch[validation_name]
            df = self.dataframes[df_key]

            # Apply filters if they are defined in the config
            if 'variableMeasured' in config:
                df = filter_dataframe(df, config['variableMeasured'])

            # Pass config to the validation function if it's needed
            if validation_name in [
                    'DELETED_COUNT', 'NUM_PLACES_COUNT',
                    'NUM_OBSERVATIONS_CHECK', 'MIN_VALUE_CHECK',
                    'MAX_VALUE_CHECK'
            ]:
                result = validation_func(df, config)
            else:
                result = validation_func(df)

            self.validation_results.append(result)
            if result.status != ValidationStatus.PASSED:
                overall_status = False
                if result.status == ValidationStatus.FAILED:
                    logging.error(result.message)
                else:
                    logging.warning(result.message)
            else:
                logging.info('Validation passed: %s', result.name)

        self._write_results_to_file()
        return overall_status

    def _write_results_to_file(self):
        with open(self.validation_output,
                  mode='w',
                  encoding='utf-8',
                  newline='') as output_file:
            writer = csv.writer(output_file)
            writer.writerow(['test', 'status', 'message', 'details'])
            for result in self.validation_results:
                details_str = json.dumps(
                    result.details) if result.details else ''
                writer.writerow([
                    result.name, result.status.value, result.message,
                    details_str
                ])


def main(_):
    runner = ValidationRunner(_FLAGS.validation_config, _FLAGS.differ_output,
                              _FLAGS.stats_summary, _FLAGS.validation_output)
    if not runner.run_validations():
        sys.exit(1)


if __name__ == '__main__':
    app.run(main)
