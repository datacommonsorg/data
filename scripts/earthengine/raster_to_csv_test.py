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
"""Tests for raster_to_csv.py"""

import os
import tempfile
import sys
import unittest

from absl import logging

# Allows the following module imports to work when running as a script
_SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))

import raster_to_csv as r2c

from util.config_map import ConfigMap
from util.counters import Counters

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')


class RasterToCsvTest(unittest.TestCase):

    def setUp(self):
        logging.set_verbosity(2)
        # Display longer diff string on error.
        self.maxDiff = None
        return

    def compare_files(self, expected: str, actual: str):
        '''Compare lines in files after sorting.'''
        logging.info(f'Comparing files: expected:{expected}, actual: {actual}')
        with open(expected, 'r') as exp:
            with open(actual, 'r') as act:
                exp_lines = sorted(exp.readlines())
                act_lines = sorted(act.readlines())
                self.assertEqual(exp_lines, act_lines)

    def test_process_geotiff(self):
        '''Verify generation of place and data CSVs.'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_geotiff = os.path.join(_TESTDIR, 'sample_floods.tif')
            place_output_prefix = os.path.join(tmp_dir, 'sample_flood_place')
            process_config = ConfigMap(
                config_dict={
                    's2_level': 13,
                    'aggregate_s2_level': 10,
                    'contained_in_s2_level': 10,
                    'aggregate': 'sum',
                    'rename_columns': {
                        'band:0': 'water'
                    },
                    'output_date': '2022-10',
                    'output_s2_place': place_output_prefix,
                })
            output_csv = os.path.join(tmp_dir, 'sample_floods_output.csv')
            counter = Counters()
            # Process raster into csv data points.
            r2c.process(input_geotiff=input_geotiff,
                        input_csv=None,
                        output_csv=output_csv,
                        config=process_config,
                        counter=counter)
            self.compare_files(
                os.path.join(_TESTDIR, 'sample_floods_output.csv'), output_csv)
            self.compare_files(
                os.path.join(_TESTDIR, 'sample_floods_output_places.csv'),
                f'{place_output_prefix}.csv')
            self.compare_files(
                os.path.join(_TESTDIR, 'sample_floods_output_places.tmcf'),
                f'{place_output_prefix}.tmcf')

    def test_process_csv(self):
        '''Verify re-processing of CSV file.'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_csv = os.path.join(_TESTDIR, 'sample_floods_output.csv')
            process_config = ConfigMap(
                config_dict={
                    's2_level': 13,
                    'aggregate': 'sum',
                    'input_data_filter': {
                        'area': {
                            'min': 1.0
                        },
                        # Use only level-13 from csv and aggregate
                        's2Level': {
                            'eq': 13,
                        }
                    },
                    'aggregate_s2_level': 5,
                })
            output_csv = os.path.join(tmp_dir,
                                      'sample_flood_output_filtered.csv')
            counter = Counters()
            # Process raster into csv data points.
            r2c.process(input_geotiff=None,
                        input_csv=input_csv,
                        output_csv=output_csv,
                        config=process_config,
                        counter=counter)
            self.compare_files(
                os.path.join(_TESTDIR, 'sample_floods_output_filtered.csv'),
                output_csv)
