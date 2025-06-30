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
    """Tests for the DataSampler class."""

    def setUp(self):
        """Sets up the test environment."""
        # Create a temp directory
        self._tmp_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(_TEST_DIR,
                                       'india_census_sample_input.csv')
        self.output_file = os.path.join(self._tmp_dir, 'sample_output.csv')

    def tearDown(self):
        """Tears down the test environment."""
        # Remove the temp directory
        shutil.rmtree(self._tmp_dir)

    def test_sample_csv_file_creates_output(self):
        """Tests that the sample_csv_file function creates an output file."""
        data_sampler.sample_csv_file(self.input_file, self.output_file)
        self.assertTrue(os.path.exists(self.output_file))

    def test_sample_csv_file_output_is_smaller_than_input(self):
        """Tests that the output file is smaller than the input file."""
        data_sampler.sample_csv_file(self.input_file, self.output_file)
        input_size = os.path.getsize(self.input_file)
        output_size = os.path.getsize(self.output_file)
        self.assertLess(output_size, input_size)

    def test_header_is_copied_correctly(self):
        """Tests that the header is copied correctly from the input file."""
        data_sampler.sample_csv_file(self.input_file, self.output_file)
        with open(self.input_file) as f_in, open(self.output_file) as f_out:
            input_header = f_in.readline()
            output_header = f_out.readline()
            self.assertEqual(input_header, output_header)

    def test_all_output_lines_are_in_input(self):
        """Tests that all output lines are present in the input file."""
        data_sampler.sample_csv_file(self.input_file, self.output_file)
        with open(self.input_file) as f_in, open(self.output_file) as f_out:
            input_lines = f_in.readlines()
            output_lines = f_out.readlines()
            for output_line in output_lines[1:]:
                self.assertIn(output_line, input_lines)

    def test_different_delimiter(self):
        """Tests that the sampler works with a different delimiter."""
        input_file = os.path.join(self._tmp_dir, 'sample_input_semicolon.csv')
        with open(input_file, 'w') as f:
            f.write('a;b;c\n')
            f.write('1;2;3\n')
            f.write('4;5;6\n')
            f.write('7;8;9\n')
        output_file = os.path.join(self._tmp_dir, 'sample_output_semicolon.csv')
        config = {'input_delimiter': ';'}
        data_sampler.sample_csv_file(input_file, output_file, config)
        self.assertTrue(os.path.exists(output_file))
        with open(output_file) as f:
            lines = f.readlines()
            self.assertIn('a;b;c\n', lines)

    def test_different_header_row_count(self):
        """Tests that the sampler works with a different header row count."""
        config = {'header_rows': 2}
        data_sampler.sample_csv_file(self.input_file, self.output_file, config)
        with open(self.input_file) as f_in, open(self.output_file) as f_out:
            input_lines = f_in.readlines()
            output_lines = f_out.readlines()
            self.assertEqual(input_lines[0], output_lines[0])
            self.assertEqual(input_lines[1], output_lines[1])

    def test_sampling_rate(self):
        """Tests that the sampling rate is respected."""
        config = {'sampler_rate': 0.1, 'sampler_output_rows': -1}
        data_sampler.sample_csv_file(self.input_file, self.output_file, config)
        with open(self.input_file) as f_in, open(self.output_file) as f_out:
            input_lines = f_in.readlines()
            output_lines = f_out.readlines()
            # The number of output lines should be greater than the header and
            # less than the input lines.
            self.assertLess(len(output_lines), len(input_lines))
            self.assertGreater(len(output_lines), 1)

    @unittest.skip("TODO: Implement unique column selection in DataSampler.")
    def test_unique_columns(self):
        """Tests that the sampler selects unique values from a column."""
        config = {'sampler_unique_columns': 'State'}
        data_sampler.sample_csv_file(self.input_file, self.output_file, config)
        with open(self.output_file) as f:
            lines = f.readlines()
            # The number of unique states in the input file is 3, so the output
            # should have 3 data rows + 1 header row.
            self.assertEqual(len(lines), 4)

    @unittest.skip("TODO: Implement rows per key in DataSampler.")
    def test_rows_per_key(self):
        """Tests that the sampler respects the sampler_rows_per_key config."""
        config = {'sampler_rows_per_key': 2}
        data_sampler.sample_csv_file(self.input_file, self.output_file, config)
        with open(self.output_file) as f:
            lines = f.readlines()
            # The input file has 3 unique states. With sampler_rows_per_key=2,
            # we expect 2 rows for each state, plus the header.
            self.assertLessEqual(len(lines), 3 * 2 + 1)

    @unittest.skip("TODO: Implement column regex in DataSampler.")
    def test_column_regex(self):
        """Tests that the sampler respects the sampler_column_regex config."""
        config = {'sampler_column_regex': r'^State_1$'}
        data_sampler.sample_csv_file(self.input_file, self.output_file, config)
        with open(self.output_file) as f:
            lines = f.readlines()
            # The regex only matches 'State_1', so we expect only rows with that
            # value to be sampled.
            self.assertEqual(len(lines), 2)
            self.assertIn('State_1', lines[1])

    def test_non_existent_input_file(self):
        """Tests that the sampler handles a non-existent input file."""
        input_file = os.path.join(_TEST_DIR, 'non_existent_file.csv')
        output_file = data_sampler.sample_csv_file(input_file, self.output_file)
        self.assertIsNone(output_file)

    def test_empty_input_file(self):
        """Tests that the sampler handles an empty input file."""
        input_file = os.path.join(self._tmp_dir, 'empty.csv')
        with open(input_file, 'w') as f:
            pass
        output_file = data_sampler.sample_csv_file(input_file, self.output_file)
        self.assertTrue(os.path.exists(output_file))
        with open(output_file) as f:
            self.assertEqual(len(f.readlines()), 0)

    def test_input_file_with_only_header(self):
        """Tests that the sampler handles an input file with only a header."""
        input_file = os.path.join(self._tmp_dir, 'header_only.csv')
        with open(input_file, 'w') as f:
            f.write('header1,header2,header3\n')
        output_file = data_sampler.sample_csv_file(input_file, self.output_file)
        self.assertTrue(os.path.exists(output_file))
        with open(output_file) as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(lines[0], 'header1,header2,header3\n')
