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
  $ python import_validation.py --validation_config=<path> \
    --differ_output=<path> --stats_summary=<path> --validation_output=<path>

  Each import can provide configuration (JSON) to select which validation
  checks are performed. Validation results are written to an output file.
  Sample config and output files can be found in test folder.
  """

    def __init__(self, validation_config: str, differ_output: str,
                 stats_summary: str, validation_output: str):
        logging.info('Reading config from %s', validation_config)
        self.differ_results = pd.read_csv(differ_output)
        print(self.differ_results)
        self.validation_map = {
            Validation.MODIFIED_COUNT: self._modified_count_validation,
            Validation.ADDED_COUNT: self._added_count_validation,
            Validation.DELETED_COUNT: self._deleted_count_validation,
            Validation.UNMODIFIED_COUNT: self._unmodified_count_validation
        }
        self.validation_output = validation_output
        self.validation_result = []
        with open(validation_config, encoding='utf-8') as fd:
            self.validation_config = json.load(fd)

    def _latest_data_validation(self, config: dict):
        logging.info('Not yet implemented')

    # Checks if the number of deleted data points are below a threshold.
    def _deleted_count_validation(self, config: dict):
        if self.differ_results.empty:
            return
        if self.differ_results['DELETED'].sum() > config['threshold']:
            raise AssertionError(f'Validation failed: {config["validation"]}')

    # Checks if number of modified points for each stat var are same.
    def _modified_count_validation(self, config: dict):
        if self.differ_results.empty:
            return
        if self.differ_results['MODIFIED'].nunique() > 1:
            raise AssertionError(f'Validation failed: {config["validation"]}')

    # Checks if number of added points for each stat var are same.
    def _added_count_validation(self, config: dict):
        if self.differ_results.empty:
            return
        if self.differ_results['ADDED'].nunique() > 1:
            raise AssertionError(f'Validation failed: {config["validation"]}')

    # Checks if number of unmodified points for each stat var are same.
    def _unmodified_count_validation(self, config: dict):
        if self.differ_results.empty:
            return
        # if self.differ_results['UNMODIFIED'].nunique() > 1:
        #    raise AssertionError(f'Validation failed: {config["validation"]}')

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
    validation = ImportValidation(_FLAGS.validation_config,
                                  _FLAGS.differ_output, _FLAGS.stats_summary,
                                  _FLAGS.validation_output)
    validation.run_validations()


if __name__ == '__main__':
    app.run(main)
