# Copyright 2023 Google LLC
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
"""Test for events_pipeline.py"""

import os
import pandas as pd
import shutil
import sys
import tempfile
import unittest

from absl import logging

# Allows the following module imports to work when running as a script
_MODULE_DIR = os.path.dirname(__file__)
sys.path.append(_MODULE_DIR)
sys.path.append(os.path.dirname(_MODULE_DIR))
sys.path.append(os.path.dirname(os.path.dirname((_MODULE_DIR))))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname((_MODULE_DIR))), 'util'))

import file_util
import utils
import download_util

from events_pipeline import EventPipeline
from config_map import ConfigMap

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')


class EventsPipelineTest(unittest.TestCase):

    def compare_files(self, expected: str, actual: str):
        '''Compare lines in files after sorting.'''
        logging.info(f'Comparing files: expected:{expected}, actual: {actual}')
        file, ext = os.path.splitext(expected)
        if ext == '.csv':
            self.compare_csv_files(expected, actual)
        with file_util.FileIO(expected, 'r') as exp:
            with file_util.FileIO(actual, 'r') as act:
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

    def setUp(self):
        self.maxDiff = None
        self._config = ConfigMap(filename=os.path.join(
            _TESTDIR, 'sample_fires_event_pipeline_config.py'))

        # Setup download URL response to the test input.
        self.test_input_file = os.path.join(_TESTDIR, 'sample_fires_input.csv')
        self.test_url = 'http://sample_test.com/data/2023'
        with open(self.test_input_file, mode='r') as test_input:
            download_util._PREFILLED_RESPONSE[self.test_url] = test_input.read()

        # Set temp dir in the config
        self._tmp_dir = tempfile.gettempdir()
        if not self._config.get('defaults', {}).get('tmp_dir'):
            self._tmp_dir = tempfile.mkdtemp()
            self._config.get_configs()['defaults']['tmp_dir'] = self._tmp_dir

        # Set place property cache file.
        self._config.get_configs(
        )['defaults']['place_property_cache_file'] = os.path.join(
            _TESTDIR, 'test_s2_cells_properties.pkl')

        self._config.set_config(
            'pipeline_state_file',
            os.path.join(self._tmp_dir, 'test_pipeline_state.py'))

        # Create an events pipeline for the config.
        self.events_pipeline = EventPipeline(config=self._config)

    def tearDown(self):
        # Delete the tmp directory
        if self._tmp_dir and self._tmp_dir != tempfile.gettempdir():
            logging.info(f'Deleting tmp dir: {self._tmp_dir}')
            shutil.rmtree(self._tmp_dir)

    def test_pipeline_stage_download(self):
        # Run the download stage of the event pipeline.
        output_files = self.events_pipeline.run_stage('download')
        self.assertEqual(1, len(output_files))
        self.compare_files(self.test_input_file, output_files[0])

        # Running download again should not return any output
        output_files = self.events_pipeline.run_stage('download')
        self.assertEqual(0, len(output_files))

    def test_events_pipeline_run(self):
        # Run all stages in the events pipeline.
        output_files = self.events_pipeline.run()

        # Check outputs
        logging.info(f'Comparing file: {output_files}')
        self.assertEqual(5, len(output_files))
        self.compare_files(
            os.path.join(_TESTDIR, 'sample_fires_events.csv'),
            _get_matching_in_list(output_files, 'sample_fires_events.csv'))

        for file in ['place_svobs', 'svobs']:
            for ext in ['.csv', '.tmcf']:
                filename = f'sample_fires_{file}{ext}'
                output_file = _get_matching_in_list(output_files, filename)
                expected_output = os.path.join(_TESTDIR, filename)
                self.compare_files(expected_output, output_file)


def _get_matching_in_list(items: list, pat: str) -> str:
    '''Returns the element matching the pat in the items list.'''
    for item in items:
        if pat in item:
            return item
    return ''
