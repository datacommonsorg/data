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
"""Tests for file_util.py"""

import math
import os
import sys
import tempfile
import unittest

from absl import logging

# Allows the following module imports to work when running as a script
_SCRIPTS_DIR = os.path.dirname(__file__)
if _SCRIPTS_DIR not in sys.path:
    sys.path.append(_SCRIPTS_DIR)

import file_util

_SAMPLE_CSV_HEADER = 'area,latitude,longitude,s2CellId,s2Level,water\n'
_SAMPLE_CSV_ROWS = [
    '0.894664,26.055635,84.131718,dcid:s2CellId/0x39925b1c00000000,13,1\n',
    '0.894664,26.055635,84.967151,dcid:s2CellId/0x39ed336400000000,13,1\n',
    '0.894731,26.046652,84.958168,dcid:s2CellId/0x39ed34a400000000,13,1\n',
]


def _create_sample_csv_files(test_dir: str):
    file_row_multipliers = {
        'sample_output.csv': 1,
        'sample_1.csv': 10,
        # ~10KB (>4KB sample window in file_estimate_num_rows)
        'sample_2.csv': 50,
    }
    for name, multiplier in file_row_multipliers.items():
        path = os.path.join(test_dir, name)
        with open(path, 'w') as f:
            f.write(_SAMPLE_CSV_HEADER)
            f.writelines(_SAMPLE_CSV_ROWS * multiplier)


class FileIOTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self._temp_dir = tempfile.TemporaryDirectory()
        self._test_dir = self._temp_dir.name
        _create_sample_csv_files(self._test_dir)

    def tearDown(self):
        self._temp_dir.cleanup()
        super().tearDown()

    def test_read_write(self):
        filename = file_util.file_get_matching(
            os.path.join(self._test_dir, 'sample*.csv'))[0]
        # Create a copy in a new directory
        copy_filename = file_util.file_get_name(file_path=os.path.join(
            os.path.join(self._test_dir, 'test'), 'copy'),
                                                suffix='temp')

        # Read from file and write to a copy.
        with file_util.FileIO(filename, mode='r') as input_file:
            with file_util.FileIO(copy_filename, mode='w',
                                  use_tempfile=True) as output_file:
                file_content = input_file.read()
                output_file.write(file_content)
                # Verify target file is empty until file is closed.
                self.assertEqual(0, file_util.file_get_size(copy_filename))

        # Output file should exists after file is closed.
        self.assertTrue(file_util.file_get_size(copy_filename) > 0)

        # Compare files.
        with open(filename) as expected_input:
            with open(copy_filename) as expected_output:
                self.assertEqual(expected_input.read(), expected_output.read())

    def test_write_exception_preserves_existing_file(self):
        target = os.path.join(self._test_dir, 'atomic_output.txt')
        with file_util.FileIO(target, mode='w') as f:
            f.write('original content')

        with self.assertRaises(RuntimeError):
            with file_util.FileIO(target, mode='w') as f:
                f.write('partial corrupt content')
                raise RuntimeError('simulated write failure')

        with file_util.FileIO(target, mode='r') as f:
            self.assertEqual('original content', f.read())


class FileUtilsTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self._temp_dir = tempfile.TemporaryDirectory()
        self._test_dir = self._temp_dir.name
        _create_sample_csv_files(self._test_dir)

    def tearDown(self):
        self._temp_dir.cleanup()
        super().tearDown()

    def test_file_get_matching(self):
        files = file_util.file_get_matching(
            os.path.join(self._test_dir, 'sample*.csv'))
        self.assertTrue(len(files) > 2)
        for file in files:
            self.assertTrue(os.path.exists(file))

    def test_file_type(self):
        self.assertTrue(file_util.file_is_local('/abc/def.csv'))
        self.assertFalse(file_util.file_is_local('https://abc/def.csv'))
        self.assertFalse(
            file_util.file_is_local('gs://gcs_bucket/gcs_path/file.csv'))

        self.assertTrue(file_util.file_is_gcs('gs://some_bucket/some_path'))
        self.assertFalse(file_util.file_is_gcs('https://some_bucket/some_path'))
        self.assertFalse(file_util.file_is_gcs('/dir/some_path'))

        self.assertTrue(
            file_util.file_is_google_spreadsheet(
                'https://docs.google.com/spreadsheets/d/some-sheet-id/edit#gid=12345'
            ))
        self.assertFalse(
            file_util.file_is_google_spreadsheet('gs://folders/some-path'))
        self.assertFalse(
            file_util.file_is_google_spreadsheet(
                'http://drive.google.com/folders/some-path'))
        self.assertFalse(
            file_util.file_is_google_spreadsheet('/folders/some-path'))

    def test_file_get_estimate_num_rows(self):
        files = file_util.file_get_matching(
            os.path.join(self._test_dir, 'sample*.csv'))
        for file in files:
            estimate_rows = file_util.file_estimate_num_rows(file)
            with file_util.FileIO(file, 'r') as fp:
                num_lines = len(fp.readlines())
                self.assertTrue(
                    math.isclose(num_lines, estimate_rows, rel_tol=1))

    def test_file_load_csv_dict(self):
        csv_dict = file_util.file_load_csv_dict(
            os.path.join(self._test_dir, 'sample_output.csv'), 's2CellId')
        self.assertTrue(len(csv_dict) > 0)
        test_key = 'dcid:s2CellId/0x39925b1c00000000'
        self.assertTrue(test_key in csv_dict)
        self.assertEqual('1', csv_dict[test_key]['water'])
        self.assertEqual('13', csv_dict[test_key]['s2Level'])

    def test_file_write_load_py_dict(self):
        test_dict = {'test_key': 'test_value', 'int_key': 10, 'list': [1, 2, 3]}
        # read/write dict as a py file
        tmp_py_filename = os.path.join(self._test_dir, 'test_dict.py')
        file_util.file_write_py_dict(test_dict, tmp_py_filename)
        self.assertTrue(os.path.getsize(tmp_py_filename) > 10)
        read_dict = file_util.file_load_py_dict(tmp_py_filename)
        self.assertEqual(test_dict, read_dict)
        # Repeat test with pkl file.
        tmp_pkl_filename = os.path.join(self._test_dir, 'test_dict.pkl')
        file_util.file_write_py_dict(test_dict, tmp_pkl_filename)
        self.assertTrue(os.path.getsize(tmp_pkl_filename) > 10)
        read_pkl_dict = file_util.file_load_py_dict(tmp_pkl_filename)
        self.assertEqual(test_dict, read_pkl_dict)
        # check pkl and py files are different.
        self.assertTrue(
            file_util.file_get_size(tmp_pkl_filename) !=
            file_util.file_get_size(tmp_py_filename))


if __name__ == '__main__':
    unittest.main()
