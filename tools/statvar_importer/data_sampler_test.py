# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for data_sampler.py"""

import os
import shutil
import sys
import tempfile
import unittest

from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

_TEST_DIR = os.path.join(_SCRIPT_DIR, 'test_data')

import data_sampler

from counters import Counters
from mcf_file_util import load_mcf_nodes, write_mcf_nodes


class DataSamplerTest(unittest.TestCase):

    def setUp(self):
        # Create a temp directory
        self._tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the temp directory
        shutil.rmtree(self._tmp_dir)

    def test_sample_csv_file(self):
        input_file = os.path.join(_TEST_DIR, 'india_census_sample_input.csv')
        sample_output_file = os.path.join(self._tmp_dir, 'sample_output.csv')
        data_sampler.sample_csv_file(input_file, sample_output_file)

        input_lines = []
        with open(input_file) as file:
            input_lines = file.read()

        output_lines = []
        with open(sample_output_file) as file:
            output_lines = file.read()

        self.assertGreater(len(input_lines), 0)
        self.assertGreater(len(output_lines), 0)
        self.assertGreater(len(input_lines), len(output_lines))
        print(output_lines)

        # Check header is copied
        self.assertEqual(input_lines[0], output_lines[0])
        # Check all output lines are in input in same order
        prev_index = 0
        for index in range(1, len(output_lines)):
            output_line = output_lines[index]
            input_index = prev_index + input_lines[prev_index:].index(
                output_line)
            self.assertGreaterEqual(
                input_index, prev_index,
                f'sample line: {index}:{output_line} expected after input line {prev_index}'
            )
            prev_index = input_index
            index += 1
