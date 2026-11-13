# Copyright 2021 Google LLC
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
"""Generic test for subject tables"""

import os
import sys
import tempfile
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

# Allows the unittest to access table directories in relative path. Also used to
# import modules for generating cleaned CSV, MCF and Column Map
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_PATH)

from common.data_loader import process_subject_tables

from .process import set_column_map

# These directories are excluded from testing
_EXCLUDE_DIRS = ['common', 's2201', '__pycache__', '~']


def _get_paths(table_dir):
    """Gets paths to the spec, CSV, StatVar MCF, Column Map and test zip file.
    Args:
        table_dir: Path to the subject table directory.
          Expected directory structure is (<code> refers to subject table code)
          table_dir
            - <code>_spec.json
            - testdata
                - <code>_output.mcf
                - <code>_cleaned.csv
                - column_map.json
                - test zip file or raw data_with_overlays CSV file(s)

    Returns:
        A dict of the paths to the spec, CSV, Stat Var MCF, column map and test
        zip file (or raw_csvs list).
    """
    paths = {}

    # Find spec, Expects spec to be in table_dir
    for filename in os.listdir(table_dir):
        if 'spec.json' in filename:
            paths['spec'] = os.path.join(table_dir, filename)

    # Expects StatVar MCF, Column Map, CSV and test zip (or raw overlay CSVs)
    # to be in testdata folder
    testdata_path = os.path.join(table_dir, 'testdata')
    raw_csvs = []
    for filename in sorted(os.listdir(testdata_path)):
        if 'cleaned.csv' in filename:
            paths['csv'] = os.path.join(testdata_path, filename)
        elif 'output.mcf' in filename:
            paths['mcf'] = os.path.join(testdata_path, filename)
        elif 'column_map.json' in filename:
            paths['cmap'] = os.path.join(testdata_path, filename)
        elif filename.endswith('.zip'):
            paths['zip'] = os.path.join(testdata_path, filename)
        elif 'data_with_overlays' in filename and filename.endswith('.csv'):
            raw_csvs.append(os.path.join(testdata_path, filename))
    if raw_csvs:
        paths['raw_csvs'] = raw_csvs

    return paths


def _read_files(test_path, expected_path):
    with open(test_path, 'r') as test_f:
        test_result = test_f.read()
    with open(expected_path, 'r') as expected_f:
        expected_result = expected_f.read()
    return test_result, expected_result


def _read_csv_files(test_path, expected_path, precision=3):
    test_df = pd.read_csv(test_path).round(precision)
    expected_df = pd.read_csv(expected_path).round(precision)

    return test_df, expected_df


class TestSubjectTable(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dirs = []  # A list of all directories to be tested
        for table_dir in sorted(os.listdir(_SCRIPT_PATH)):
            table_dir_path = os.path.join(_SCRIPT_PATH, table_dir)
            process_path = os.path.join(_SCRIPT_PATH, table_dir, 'process.py')

            testdata_path = os.path.join(table_dir_path, 'testdata')

            # Run test only if table_dir is not in _EXCLUDE_DIRS and process.py
            # is not in table_dir and table_dir has a testdata directory
            if (table_dir not in _EXCLUDE_DIRS and
                    os.path.isdir(table_dir_path) and
                    os.path.isdir(testdata_path) and
                    not os.path.isfile(process_path)):
                cls.test_dirs.append(table_dir_path)

    def test_csv_mcf_column_map(self):

        for table_dir_path in self.test_dirs:
            paths = _get_paths(table_dir_path)

            # Check if all required files exist
            expected_keys = ['spec', 'csv', 'mcf', 'cmap']
            for file_key in expected_keys:
                with self.subTest(table=table_dir_path, file_key=file_key):
                    self.assertTrue(file_key in paths)
            with self.subTest(table=table_dir_path, file_key='zip'):
                self.assertTrue('zip' in paths or 'raw_csvs' in paths)
            if not all(k in paths for k in expected_keys) or (
                    'zip' not in paths and 'raw_csvs' not in paths):
                continue

            with tempfile.TemporaryDirectory() as tmp_dir:
                zip_path = paths.get('zip')
                if not zip_path:
                    zip_path = os.path.join(tmp_dir, 'test_input.zip')
                    with zipfile.ZipFile(zip_path, 'w') as zf:
                        for raw_csv in paths['raw_csvs']:
                            zf.write(raw_csv, arcname=os.path.basename(raw_csv))
                # generate CSV, MCF and Column Map
                set_column_map(zip_path, paths['spec'], tmp_dir)
                process_subject_tables(table_prefix='test',
                                       input_path=zip_path,
                                       output_dir=tmp_dir,
                                       column_map_path=os.path.join(
                                           tmp_dir, 'column_map.json'),
                                       spec_path=paths['spec'],
                                       debug=False,
                                       delimiter='!!',
                                       has_percent=True)

                test_mcf_path = os.path.join(tmp_dir, 'test_output.mcf')
                test_cmap_path = os.path.join(tmp_dir, 'column_map.json')
                test_csv_path = os.path.join(tmp_dir, 'test_cleaned.csv')

                with self.subTest(table=table_dir_path):
                    # Test StatVar MCF
                    test_mcf, expected_mcf = _read_files(
                        test_mcf_path, paths['mcf'])
                    self.assertEqual(test_mcf, expected_mcf)

                    # Test Column Map
                    test_cmap, expected_cmap = _read_files(
                        test_cmap_path, paths['cmap'])
                    self.assertEqual(test_cmap, expected_cmap)

                    # Test CSV
                    test_csv, expected_csv = _read_files(
                        test_csv_path, paths['csv'])
                    self.assertEqual(test_csv.rstrip('\n'),
                                     expected_csv.rstrip('\n'))
                    test_df, expected_df = _read_csv_files(
                        test_csv_path, paths['csv'])
                    assert_frame_equal(test_df, expected_df)


if __name__ == "__main__":
    unittest.main(verbosity=2)
