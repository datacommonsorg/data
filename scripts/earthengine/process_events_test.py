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
"""Test for process_events.py"""

import math
import os
import s2sphere
import shapely
import sys
import tempfile
import unittest

from absl import logging

# Allows the following module imports to work when running as a script
_MODULE_DIR = os.path.dirname(__file__)
sys.path.append(_MODULE_DIR)
sys.path.append(os.path.dirname(_MODULE_DIR))
sys.path.append(os.path.dirname(os.path.dirname((_MODULE_DIR))))

import utils

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')

from process_events import process_csv

from util.config_map import ConfigMap


class ProcessEventsTest(unittest.TestCase):

    def compare_files(self, expected: str, actual: str):
        '''Compare lines in files after sorting.'''
        logging.info(f'Comparing files: expected:{expected}, actual: {actual}')
        with open(expected, 'r') as exp:
            with open(actual, 'r') as act:
                exp_lines = exp.readlines().sort()
                act_lines = act.readlines().sort()
                self.assertEqual(exp_lines, act_lines)

    def test_process(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_prefix = os.path.join(tmp_dir, 'events_test_')
            test_prefix = os.path.join(_TESTDIR, 'sample_floods_')
            # Process flood s2 cells into events.
            process_csv(
                csv_files='sample_flood_output_filtered.csv',
                output_path=output_prefix,
                config=ConfigMap(
                    filename=os.path.join(_MODULE_DIR, 'event_config.py')))
            # Verify generated events.
            for file in [
                    'events.csv', 'events.tmcf', 'svobs.csv', 'svobs.tmcf'
            ]:
                self.compare_files(test_prefix + file, output_prefix + file)
