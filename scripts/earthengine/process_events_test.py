# Copyright 2022 Google LLC
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
"""Test for events_processor.py"""

import math
import os
import s2sphere
import shapely
import sys
import tempfile
import unittest
import pandas as pd

from absl import logging

# Allows the following module imports to work when running as a script
_MODULE_DIR = os.path.dirname(__file__)
sys.path.append(_MODULE_DIR)
sys.path.append(os.path.dirname(_MODULE_DIR))
sys.path.append(os.path.dirname(os.path.dirname((_MODULE_DIR))))

import utils

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')

from process_events import process

from util.config_map import ConfigMap


class ProcessEventsTest(unittest.TestCase):

    def compare_files(self, expected: str, actual: str):
        '''Compare lines in files after sorting.'''
        logging.info(f'Comparing files: expected:{expected}, actual: {actual}')
        file, ext = os.path.splitext(expected)
        if ext == '.csv':
            self.compare_csv_files(expected, actual)
        with open(expected, 'r') as exp:
            with open(actual, 'r') as act:
                exp_lines = sorted(exp.readlines())
                act_lines = sorted(act.readlines())
                self.assertEqual(exp_lines, act_lines)

    def compare_csv_files(self,
                          expected_file: str,
                          actual_file: str,
                          ignore_columns: list = []):
        '''Compare CSV files with statvar obsevration data.'''
        # Sort files by columns.
        df_expected = pd.read_csv(expected_file)
        df_actual = pd.read_csv(actual_file)
        self.assertEqual(
            df_expected.columns.to_list(), df_actual.columns.to_list(),
            f'Found different columns in CSV files:' +
            f'expected:{expected_file}:{df_expected.columns.to_list()}, ' +
            f'actual:{actual_file}:{df_actual.columns.to_list()}, ')
        if ignore_columns:
            df_expected.drop(
                columns=df_expected.columns.difference(ignore_columns),
                inplace=True)
            df_actual.drop(columns=df_actual.columns.difference(ignore_columns),
                           inplace=True)
        df_expected.sort_values(by=df_expected.columns.to_list(),
                                inplace=True,
                                ignore_index=True)
        df_actual.sort_values(by=df_expected.columns.to_list(),
                              inplace=True,
                              ignore_index=True)
        self.assertTrue(
            df_expected.equals(df_actual), f'Found diffs in CSV rows:' +
            f'"{actual_file}" vs "{expected_file}":')

    def test_process(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = '/tmp'
            output_prefix = os.path.join(tmp_dir, 'events_test_')
            test_prefix = os.path.join(_TESTDIR, 'sample_floods_')
            # Process flood s2 cells into events.
            process(
                csv_files=[os.path.join(_TESTDIR, 'sample_floods_output.csv')],
                output_path=output_prefix,
                config=ConfigMap(
                    filename=os.path.join(_TESTDIR, 'event_config.py')))
            # Verify generated events.
            for file in [
                    'events.csv', 'events.tmcf', 'svobs.csv', 'svobs.tmcf'
            ]:
                if file.endswith('.csv'):
                    # compare csv output without geoJson that is not deterministic
                    self.compare_csv_files(test_prefix + file,
                                           output_prefix + file,
                                           ['geoJsonCoordinatesDP1'])
                else:
                    self.compare_files(test_prefix + file, output_prefix + file)
