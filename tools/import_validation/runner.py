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
import json
import sys
from typing import Tuple

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from validation_config import ValidationConfig
from report_generator import ReportGenerator
from validator import Validator
from result import ValidationResult, ValidationStatus
from util import filter_dataframe

_FLAGS = flags.FLAGS


class ValidationRunner:
    """
  Orchestrates the validation process based on the new schema.
  """

    def __init__(self, validation_config_path: str, differ_output: str,
                 stats_summary: str, lint_report: str, validation_output: str):
        self.config = ValidationConfig(validation_config_path)
        self.validation_output = validation_output
        self.validator = Validator()
        self.validation_results = []
        self.data_sources = {
            'stats': pd.DataFrame(),
            'differ': pd.DataFrame(),
            'lint': {}
        }

        self.validation_dispatch = {
            'SQL_VALIDATOR': (self.validator.validate_sql, 'sql'),
            'MAX_DATE_LATEST':
                (self.validator.validate_max_date_latest, 'stats'),
            'MAX_DATE_CONSISTENT':
                (self.validator.validate_max_date_consistent, 'stats'),
            'DELETED_RECORDS_COUNT':
                (self.validator.validate_deleted_records_count, 'differ'),
            'MISSING_REFS_COUNT':
                (self.validator.validate_missing_refs_count, 'lint'),
            'LINT_ERROR_COUNT':
                (self.validator.validate_lint_error_count, 'lint'),
            'MODIFIED_RECORDS_COUNT':
                (self.validator.validate_modified_records_count, 'differ'),
            'ADDED_RECORDS_COUNT':
                (self.validator.validate_added_records_count, 'differ'),
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

        self._initialize_data_sources(stats_summary, lint_report, differ_output)

    def _initialize_data_sources(self, stats_summary: str, lint_report: str,
                                 differ_output: str):
        """
    Checks for and loads the required data sources based on the config.
    """
        req_sources = self._determine_required_sources()

        if 'stats' in req_sources and (not stats_summary or
                                       not os.path.exists(stats_summary)):
            raise ValueError(
                f"A validation rule requires the 'stats' data source, but the --stats_summary file was not provided or does not exist. Path: {stats_summary}"
            )

        if 'differ' in req_sources:
            if not differ_output or not os.path.exists(differ_output):
                logging.warning(
                    f"A validation rule requires the 'differ' data source, but the --differ_output file was not provided or does not exist. Path: {differ_output}"
                )

        if 'lint' in req_sources and (not lint_report or
                                      not os.path.exists(lint_report)):
            raise ValueError(
                f"A validation rule requires the 'lint' data source, but the --lint_report file was not provided or does not exist. Path: {lint_report}"
            )

        if stats_summary and os.path.exists(stats_summary) and os.path.getsize(
                stats_summary) > 0:
            self.data_sources['stats'] = pd.read_csv(stats_summary)
        elif stats_summary and os.path.exists(stats_summary):
            logging.warning("stats_summary file exists but is empty: %s",
                            stats_summary)

        if differ_output and os.path.exists(differ_output) and os.path.getsize(
                differ_output) > 0:
            self.data_sources['differ'] = pd.read_csv(differ_output)
        elif differ_output and os.path.exists(differ_output):
            logging.warning("differ_output file exists but is empty: %s",
                            differ_output)

        if lint_report and os.path.exists(lint_report) and os.path.getsize(
                lint_report) > 0:
            try:
                with open(lint_report, 'r') as f:
                    self.data_sources['lint'] = json.load(f)
            except Exception as e:
                logging.error(
                    "JSON parse error while reading lint report at {lint_report}: {e}"
                )
        elif lint_report and os.path.exists(lint_report):
            logging.warning("lint_report file exists but is empty: %s",
                            lint_report)

    def _determine_required_sources(self) -> set[str]:
        """
    Parses the validation config to determine which data sources are required.
    """
        req_sources = set()
        for rule in self.config.rules:
            if not rule.get('enabled', True):
                continue

            validator_name = rule.get('validator')
            if validator_name in self.validation_dispatch:
                req_sources.add(self.validation_dispatch[validator_name][1])
        return req_sources

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

            validation_func, data_source_key = self.validation_dispatch[
                validator_name]

            if validator_name == 'SQL_VALIDATOR':
                result = validation_func(self.data_sources['stats'],
                                         self.data_sources['differ'],
                                         rule['params'])
            else:
                scope = rule.get('scope', {})
                if isinstance(scope, str):
                    scope = self.config.get_scope(scope)

                df = self.data_sources[data_source_key]

                if 'variables' in scope:
                    variables_config = scope['variables']
                    df = filter_dataframe(
                        df,
                        dcids=variables_config.get('dcids'),
                        regex_patterns=variables_config.get('regex'),
                        contains_all=variables_config.get('contains_all'))

                result = validation_func(df, rule['params'])

            result.name = rule['rule_id']
            result.validation_params = rule.get('params', {})

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
        report_generator.generate_report(self.validation_output)

        return overall_status, self.validation_results


def main(_):
    try:
        config_path = _FLAGS.validation_config
        runner = ValidationRunner(validation_config_path=config_path,
                                  differ_output=_FLAGS.differ_output,
                                  stats_summary=_FLAGS.stats_summary,
                                  lint_report=_FLAGS.lint_report,
                                  validation_output=_FLAGS.validation_output)
        overall_status, _ = runner.run_validations()
        if not overall_status:
            sys.exit(1)
    except ValueError as e:
        logging.error(e)
        sys.exit(1)


if __name__ == '__main__':
    flags.DEFINE_string('validation_config', 'validation_config.json',
                        'Path to the validation config file.')
    flags.DEFINE_string('differ_output', None,
                        'Path to the differ output data file.')
    flags.DEFINE_string('stats_summary', None,
                        'Path to the stats summary report file.')
    flags.DEFINE_string('lint_report', None,
                        'Path to the mcf lint report file.')
    flags.DEFINE_string('validation_output', None,
                        'Path to the validation output file.')
    flags.mark_flag_as_required('validation_output')
    app.run(main)
