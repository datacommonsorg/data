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
flags.DEFINE_string('validation_config_file', 'validation_config.json',
                    'Path to the validation config file.')
flags.DEFINE_string('differ_output_location', '.',
                    'Path to the differ output data folder.')
flags.DEFINE_string('stats_summary_location', '.',
                    'Path to the stats summary report folder.')
flags.DEFINE_string('validation_output_location', '.',
                    'Path to the validation output folder.')

_POINT_ANALAYSIS_FILE = 'point_analysis_summary.csv'
_STATS_SUMMARY_FILE = 'summary_report.csv'
_VALIDATION_OUTPUT_FILE = 'validation_output.csv'

Validation = Enum('Validation', [
    ('MODIFIED_COUNT', 1),
    ('UNMODIFIED_COUNT', 2),
    ('ADDED_COUNT', 3),
    ('DELETED_COUNT', 4),
    ('LATEST_DATA', 5),
])


class ValidationResult:
    """Describes the result of the validaiton of an import."""

    def __init__(self, status, name, message):
        # Status of the execution: PASSED OR FAILED
        self.status = status
        # Name of the validaiton executed
        self.name = name
        # Description of the result/error message
        self.message = message


class ImportValidation:
    """
  Class to perform validations for import automation.

  Usage:
  $ python import_validation.py --validation_config_file=<path> \
    --differ_output_location=<path> --stats_summary_location=<path>

  Each import can provide configuration (JSON) to select which validation
  checks are performed. Validation results are written to an output file.
  Sample config and output files can be found in test folder.
  """

    def __init__(self, config_file: str, differ_output: str, stats_summary: str,
                 validation_output: str):
        logging.info('Reading config from %s', config_file)
        self.differ_results = pd.read_csv(differ_output)
        self.validation_map = {
            Validation.MODIFIED_COUNT: self._modified_count_validation,
            Validation.ADDED_COUNT: self._added_count_validation,
            Validation.DELETED_COUNT: self._deleted_count_validation,
            Validation.UNMODIFIED_COUNT: self._unmodified_count_validation
        }
        self.validation_output = validation_output
        self.validation_result = []
        with open(config_file, encoding='utf-8') as fd:
            self.validation_config = json.load(fd)

    def _latest_data_validation(self, config: dict):
        logging.info('Not yet implemented')

    # Checks if the number of deleted data points are below a threshold.
    def _deleted_count_validation(self, config: dict):
        if self.differ_results.empty:
            return
        if self.differ_results['deleted'].sum() > config['threshold']:
            raise AssertionError(f'Validation failed: {config["validation"]}')

    # Checks if number of modified points for each stat var are same.
    def _modified_count_validation(self, config: dict):
        if self.differ_results.empty:
            return
        if self.differ_results['modified'].nunique() > 1:
            raise AssertionError(f'Validation failed: {config["validation"]}')

    # Checks if number of added points for each stat var are same.
    def _added_count_validation(self, config: dict):
        if self.differ_results.empty:
            return
        if self.differ_results['added'].nunique() > 1:
            raise AssertionError(f'Validation failed: {config["validation"]}')

    # Checks if number of unmodified points for each stat var are same.
    def _unmodified_count_validation(self, config: dict):
        if self.differ_results.empty:
            return
        if self.differ_results['same'].nunique() > 1:
            raise AssertionError(f'Validation failed: {config["validation"]}')

    def _run_validation(self, config) -> ValidationResult:
        try:
            self.validation_map[Validation[config['validation']]](config)
            logging.info('Validation passed: %s', config['validation'])
            return ValidationResult('PASSED', config['validation'], '')
        except AssertionError as exc:
            logging.error(repr(exc))
            return ValidationResult('FAILED', config['validation'], repr(exc))

    def run_validations(self) -> bool:
        # Returns false if any validation fails.
        status = True
        with open(self.validation_output, mode='w',
                  encoding='utf-8') as output_file:
            output_file.write('test,status,message\n')
            for config in self.validation_config:
                result = self._run_validation(config)
                # TODO: use CSV writer libs
                output_file.write(
                    f'{result.name},{result.status},{result.message}\n')
                self.validation_result.append(result)
                if result.status == 'FAILED':
                    status = False
        return status


def main(_):
    validation = ImportValidation(
        _FLAGS.validation_config_file,
        os.path.join(_FLAGS.differ_output_location, _POINT_ANALAYSIS_FILE),
        os.path.join(_FLAGS.stats_summary_location, _STATS_SUMMARY_FILE),
        os.paht.join(_FLAGS.validation_output_location,
                     _VALIDATION_OUTPUT_FILE))
    validation.run_validations()


if __name__ == '__main__':
    app.run(main)
