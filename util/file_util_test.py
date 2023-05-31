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

_TEST_DIR = os.path.join(
    os.path.join(os.path.join(os.path.dirname(_SCRIPTS_DIR), 'scripts'),
                 'earthengine'), 'test_data')

import file_util


class FileIOTest(unittest.TestCase):

    def test_read_write(self):
        filename = file_util.file_get_matching(
            os.path.join(_TEST_DIR, 'sample*.csv'))[0]
        # Create a copy in a new directory
        dirname = tempfile.mkdtemp()
        copy_filename = file_util.file_get_name(file_path=os.path.join(
            os.path.join(dirname, 'test'), 'copy'),
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


class FileUtilsTest(unittest.TestCase):

    def test_file_get_matching(self):
        files = file_util.file_get_matching(
            os.path.join(_TEST_DIR, 'sample*.csv'))
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
            os.path.join(_TEST_DIR, 'sample*.csv'))
        for file in files:
            estimate_rows = file_util.file_estimate_num_rows(file)
            with file_util.FileIO(file, 'r') as fp:
                num_lines = len(fp.readlines())
                self.assertTrue(
                    math.isclose(num_lines, estimate_rows, rel_tol=1))

    def test_file_load_csv_dict(self):
        csv_dict = file_util.file_load_csv_dict(
            os.path.join(_TEST_DIR, 'sample_output.csv'), 's2CellId')
        self.assertTrue(len(csv_dict) > 0)
        test_key = 'dcid:s2CellId/0x39925b1c00000000'
        self.assertTrue(test_key in csv_dict)
        self.assertEqual('1', csv_dict[test_key]['water'])
        self.assertEqual('13', csv_dict[test_key]['s2Level'])

    def test_file_write_load_py_dict(self):
        test_dict = {'test_key': 'test_value', 'int_key': 10, 'list': [1, 2, 3]}
        # read/write dict as a py file
        fd, tmp_py_filename = tempfile.mkstemp(suffix='.py')
        file_util.file_write_py_dict(test_dict, tmp_py_filename)
        self.assertTrue(os.path.getsize(tmp_py_filename) > 10)
        read_dict = file_util.file_load_py_dict(tmp_py_filename)
        self.assertEqual(test_dict, read_dict)
        # Repeat test with pkl file.
        fd, tmp_pkl_filename = tempfile.mkstemp(suffix='.pkl')
        file_util.file_write_py_dict(test_dict, tmp_pkl_filename)
        self.assertTrue(os.path.getsize(tmp_pkl_filename) > 10)
        read_pkl_dict = file_util.file_load_py_dict(tmp_pkl_filename)
        self.assertEqual(test_dict, read_pkl_dict)
        # check pkl and py files are different.
        self.assertTrue(
            file_util.file_get_size(tmp_pkl_filename) !=
            file_util.file_get_size(tmp_py_filename))
