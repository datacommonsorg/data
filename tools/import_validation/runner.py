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
"""Module for the ValidationRunner class."""

import os
from absl import app
from absl import flags
from absl import logging
import pandas as pd
import sys

from .config import Config
from .report_generator import ReportGenerator
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
  Orchestrates the validation process based on the new schema.
  """

    def __init__(self, validation_config_path: str, differ_output: str,
                 stats_summary: str, validation_output: str):
        self.config = Config(validation_config_path)
        self.validation_output = validation_output
        self.validator = Validator()
        self.validation_results = []

        stats_exists = os.path.exists(stats_summary)
        differ_exists = os.path.exists(differ_output)

        if not stats_exists and not differ_exists:
            logging.error(
                "Fatal: Neither stats_summary (%s) nor differ_output (%s) file found. Aborting.",
                stats_summary, differ_output)
            sys.exit(1)

        self.dataframes = {
            'stats': pd.DataFrame(),
            'differ': pd.DataFrame()
        }

        if stats_exists:
            self.dataframes['stats'] = pd.read_csv(stats_summary)
        else:
            logging.warning(
                "Warning: stats_summary file not found at %s. Proceeding without it.",
                stats_summary)

        if differ_exists:
            self.dataframes['differ'] = pd.read_csv(differ_output)
        else:
            logging.warning(
                "Warning: differ_output file not found at %s. Proceeding without it.",
                differ_output)

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

    def run_validations(self) -> tuple[bool, list[ValidationResult]]:
        """Runs all validations specified in the config.

    Returns:
        A tuple containing:
        - A boolean representing the overall status (True if all passed).
        - A list of ValidationResult objects.
    """
        overall_status = True
        for rule in self.config.rules:
            if not rule.get('enabled', True):
                continue

            validator_name = rule['validator']
            if validator_name not in self.validation_dispatch:
                logging.warning('Unknown validator: %s', validator_name)
                continue

            validation_func, _ = self.validation_dispatch[validator_name]

            scope = rule['scope']
            if isinstance(scope, str):
                scope = self.config.get_scope(scope)

            df = self.dataframes[scope['data_source']]

            # TODO: Implement variable filtering and groupBy
            # if 'variables' in scope:
            #     ...
            # if 'groupBy' in scope:
            #     ...

            result = validation_func(df, rule['params'])
            result.name = rule['rule_id']

            self.validation_results.append(result)
            if result.status != ValidationStatus.PASSED:
                overall_status = False
                if result.status == ValidationStatus.FAILED:
                    logging.error(result.message)
                else:
                    logging.warning(result.message)
            else:
                logging.info('Validation passed: %s', result.name)

        report_generator = ReportGenerator(self.validation_results)
        report_generator.generate_detailed_report(self.validation_output)

        return overall_status, self.validation_results


def main(_):
    runner = ValidationRunner(_FLAGS.validation_config, _FLAGS.differ_output,
                              _FLAGS.stats_summary, _FLAGS.validation_output)
    overall_status, _ = runner.run_validations()
    if not overall_status:
        sys.exit(1)


if __name__ == '__main__':
    app.run(main)