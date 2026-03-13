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

import csv
import os
import shutil
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

_TEST_DIR = os.path.join(_SCRIPT_DIR, 'test_data')

import data_sampler


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

    def test_unique_columns(self):
        """Tests that the sampler selects unique values from specified columns."""
        config = {
            'sampler_unique_columns': 'Table',
            'sampler_rows_per_key': 1,
            'sampler_output_rows': -1,
            'header_rows': 3,
        }
        data_sampler.sample_csv_file(self.input_file, self.output_file, config)

        with open(self.output_file, newline='') as f:
            rows = list(csv.reader(f))

        header_rows = config['header_rows']
        self.assertGreater(len(rows), header_rows,
                           'Expected at least one sampled data row.')
        sampled_values = {
            row[0] for row in rows[header_rows:] if row and row[0].strip()
        }
        # The fixture contains only C0402 Table rows; ensure exactly one unique
        # data row was emitted and that it corresponds to the configured column.
        self.assertEqual(sampled_values, {'C0402'})

    def test_unique_columns_with_regex(self):
        """Tests unique columns combined with regex filtering."""
        config = {
            'sampler_unique_columns': 'Table',
            'sampler_column_regex': r'^C',  # Only values starting with 'C'
            'sampler_rows_per_key': 1,
            'sampler_output_rows': -1,
            'header_rows': 3,
        }
        data_sampler.sample_csv_file(self.input_file, self.output_file, config)

        with open(self.output_file, newline='') as f:
            rows = list(csv.reader(f))

        header_rows = config['header_rows']
        data_rows = [
            row for row in rows[header_rows:]
            if row and row[0].strip() and row[0] not in ('Name', 'Table')
        ]
        self.assertGreater(len(data_rows), 0,
                           'Expected at least one sampled data row.')
        sampled_values = {row[0] for row in data_rows}
        self.assertTrue(all(value.startswith('C') for value in sampled_values))
        self.assertEqual(len(sampled_values), len(data_rows),
                         'Expected unique Table values after filtering.')

    def test_unique_columns_selects_rows_from_header_defined_columns(self):
        """Ensures that header processing builds column indices before sampling."""
        input_file = os.path.join(self._tmp_dir, 'unique_header.csv')
        with open(input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Key', 'Value'])
            writer.writerow(['A', 'first'])
            writer.writerow(['B', 'second'])
            writer.writerow(['A', 'third'])

        config = {
            'sampler_unique_columns': 'Key',
            'sampler_rows_per_key': 1,
            'sampler_output_rows': -1,
            'header_rows': 1,
        }
        data_sampler.sample_csv_file(input_file, self.output_file, config)

        with open(self.output_file, newline='') as f:
            rows = list(csv.reader(f))

        self.assertEqual(rows[0], ['Key', 'Value'])
        data_rows = rows[1:]
        self.assertEqual(len(data_rows), 2,
                         'Expected one row per unique Key value.')
        sampled_keys = {row[0] for row in data_rows}
        self.assertEqual(sampled_keys, {'A', 'B'})

    def test_unique_columns_partial_match_raises_error(self):
        """Tests that partial matches of unique columns raises ValueError."""
        input_file = os.path.join(self._tmp_dir, 'test_partial_match.csv')
        with open(input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Age', 'City'])
            writer.writerow(['Alice', '30', 'NYC'])
            writer.writerow(['Bob', '25', 'LA'])

        config = {
            'sampler_unique_columns':
                'Name,Country',  # Name exists, Country doesn't
            'header_rows': 1,
        }

        with self.assertRaises(ValueError) as context:
            data_sampler.sample_csv_file(input_file, self.output_file, config)

        error_msg = str(context.exception)
        self.assertIn('Country', error_msg)
        self.assertNotIn('Name',
                         error_msg)  # Name should be found, not in error

    def test_rows_per_key(self):
        """Tests that the sampler respects the sampler_rows_per_key config."""
        # Use a controlled input
        input_file = os.path.join(self._tmp_dir, 'rows_per_key.csv')
        with open(input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Key', 'Value'])
            writer.writerow(['A', 'v1'])
            writer.writerow(['A', 'v2'])
            writer.writerow(['A', 'v3'])
            writer.writerow(['B', 'v4'])

        config = {
            'sampler_rows_per_key': 2,
            'sampler_unique_columns': 'Key',
            'sampler_output_rows': -1,
            'header_rows': 1,
        }
        data_sampler.sample_csv_file(input_file, self.output_file, config)
        with open(self.output_file) as f:
            lines = f.readlines()
            # 2 rows for 'A', 1 row for 'B' + 1 header = 4 lines
            self.assertEqual(len(lines), 4)

    def test_cell_value_regex(self):
        """Tests that sampler_column_regex filters based on cell values."""
        input_file = os.path.join(self._tmp_dir, 'regex_test.csv')
        with open(input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Key', 'Value'])
            writer.writerow(['2021', 'v1'])
            writer.writerow(['2022', 'v2'])
            writer.writerow(['abc', 'v3'])
            writer.writerow(['123', 'v4'])

        config = {
            'sampler_column_regex': r'^\d{4}$',
            'sampler_output_rows': -1,
            'header_rows': 1,
        }
        data_sampler.sample_csv_file(input_file, self.output_file, config)
        with open(self.output_file) as f:
            lines = f.readlines()
            # Header + 2021 + 2022 = 3 lines. '123' is only 3 digits.
            self.assertEqual(len(lines), 3)
            self.assertIn('2021,v1\n', lines)
            self.assertIn('2022,v2\n', lines)

    def test_exhaustive_mode(self):
        """Tests that exhaustive mode captures all unique values."""
        input_file = os.path.join(self._tmp_dir, 'exhaustive.csv')
        with open(input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Key', 'Value'])
            for i in range(150):
                writer.writerow([f'Key{i}', f'Value{i}'])

        # Default max rows is 100. Exhaustive should take all 150.
        config = {
            'sampler_exhaustive': True,
            'sampler_unique_columns': 'Key',
            'header_rows': 1,
        }
        data_sampler.sample_csv_file(input_file, self.output_file, config)
        with open(self.output_file) as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 151)

    def test_must_include_values(self):
        """Tests that the sampler always includes must-include values."""
        input_file = os.path.join(self._tmp_dir, 'must_include.csv')
        with open(input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Key', 'Value'])
            writer.writerow(['A', 'v1'])
            writer.writerow(['B', 'v2'])
            writer.writerow(['C', 'v3'])

        # Include list for column 'Key'
        include_file = os.path.join(self._tmp_dir, 'include.txt')
        with open(include_file, 'w') as f:
            f.write('Key\n')  # Add header
            f.write('C\n')

        config = {
            'sampler_column_keys': [f'Key:{include_file}'],
            'sampler_rate': 0,  # Disable random sampling
            'sampler_unique_columns':
                'Value',  # Track Value for unique sampling
            'sampler_uniques_per_column':
                1,  # Only first row ('A', 'v1') will be unique
            'sampler_output_rows': 10,
            'header_rows': 1,
        }

        data_sampler.sample_csv_file(input_file, self.output_file, config)
        with open(self.output_file) as f:
            lines = f.readlines()
            # Header + 'A' (unique) + 'C' (must-include) = 3 lines
            # 'B' is skipped because it's not unique enough for 'Value' column
            # (since v1 was already taken) and not in must-include.
            self.assertEqual(len(lines), 3)
            self.assertIn('A,v1\n', lines)
            self.assertIn('C,v3\n', lines)
            self.assertNotIn('B,v2\n', lines)

    def test_uniques_per_column(self):
        """Tests that the sampler respects sampler_uniques_per_column."""
        input_file = os.path.join(self._tmp_dir, 'uniques_per_col.csv')
        with open(input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Key', 'Value'])
            writer.writerow(['A', 'v1'])
            writer.writerow(['B', 'v2'])
            writer.writerow(['C', 'v3'])
            writer.writerow(['D', 'v4'])

        config = {
            'sampler_uniques_per_column': 2,
            'sampler_unique_columns': 'Key',
            'sampler_output_rows': -1,
            'header_rows': 1,
        }
        data_sampler.sample_csv_file(input_file, self.output_file, config)
        with open(self.output_file) as f:
            lines = f.readlines()
            # Header + 2 unique values = 3 lines
            self.assertEqual(len(lines), 3)

    def test_load_column_keys(self):
        """Tests that load_column_keys correctly parses the include list."""
        file1 = os.path.join(self._tmp_dir, 'file1.csv')
        with open(file1, 'w') as f:
            f.write('col1\nval1\nval2\n')

        file2 = os.path.join(self._tmp_dir, 'file2.csv')
        with open(file2, 'w') as f:
            f.write('col2\nval3\n')

        column_keys = [f'col1:{file1}', f'col2:{file2}']
        result = data_sampler.load_column_keys(column_keys)

        self.assertEqual(result, {'col1': {'val1', 'val2'}, 'col2': {'val3'}})

    def test_get_default_config(self):
        """Tests that get_default_config returns the expected dictionary."""
        config = data_sampler.get_default_config()
        self.assertIn('sampler_rate', config)
        self.assertIn('sampler_output_rows', config)
        self.assertEqual(config['sampler_output_rows'],
                         100)  # Default flag value

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
