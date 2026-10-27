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

# Allows the unittest to access table directories in relative path. Also used to
# import modules for generating cleaned CSV, MCF and Column Map
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '..'))

from s2409.process import set_column_map
from s2409.data_loader import process_subject_tables

table_dir_path = os.path.join(_SCRIPT_PATH, '.')


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
                - test zip file

    Returns:
        A tuple of the paths to the spec, CSV, Stat Var MCF, column map and test
        zip file.
    """
    paths = {}

    # Find spec, Expects spec to be in table_dir
    for filename in os.listdir(table_dir):
        if 'spec.json' in filename:
            paths['spec'] = os.path.join(table_dir, filename)

    # Expects StatVar MCF, Column Map, CSV and test zip to be in testdata folder
    testdata_path = os.path.join(table_dir, 'testdata')
    for filename in os.listdir(testdata_path):
        if 'cleaned.csv' in filename:
            paths['csv'] = os.path.join(testdata_path, filename)
        elif 'output.mcf' in filename:
            paths['mcf'] = os.path.join(testdata_path, filename)
        elif 'column_map.json' in filename:
            paths['cmap'] = os.path.join(testdata_path, filename)
        elif filename.endswith('.zip'):
            paths['zip'] = os.path.join(testdata_path, filename)

    return paths


def _read_files(test_path, expected_path):
    with open(test_path, 'r') as test_f:
        test_result = test_f.read()
    with open(expected_path, 'r') as expected_f:
        expected_result = expected_f.read()
    return test_result, expected_result


class TestSubjectTableS2409(unittest.TestCase):

    def test_csv_mcf_column_map(self):

        paths = _get_paths(table_dir_path)

        # Check if all required files exist
        expected_keys = ['spec', 'csv', 'mcf', 'cmap', 'zip']
        for file_key in expected_keys:
            with self.subTest(table=table_dir_path, file_key=file_key):
                self.assertTrue(file_key in paths)

        # TODO: Look into speeding up this section of the code
        with tempfile.TemporaryDirectory() as tmp_dir:
            # generate CSV, MCF and Column Map
            set_column_map(paths['zip'], paths['spec'], tmp_dir)
            process_subject_tables(table_prefix='test',
                                   input_path=paths['zip'],
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
                test_mcf, expected_mcf = _read_files(test_mcf_path,
                                                     paths['mcf'])
                self.assertEqual(test_mcf, expected_mcf)

                # Test Column Map
                test_cmap, expected_cmap = _read_files(test_cmap_path,
                                                       paths['cmap'])
                self.assertEqual(test_cmap, expected_cmap)

                # Test CSV
                test_csv, expected_csv = _read_files(test_csv_path,
                                                     paths['csv'])
                self.assertEqual(test_csv, expected_csv)

    def test_quantity_cleaning(self):
        paths = _get_paths(table_dir_path)
        col_name = ('Median earnings (dollars)!!Estimate!!Full-time, year-round'
                    ' civilian employed population 16 years and over')

        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_input_path = os.path.join(
                tmp_dir, 'ACSST5Y2010.S2409_data_with_overlays_test.csv')
            rows = [
                ['GEO_ID', 'NAME', 'S2409_C04_001E'],
                ['id', 'Geographic Area Name', col_name],
                ['0400000US01', 'Alabama', '2,500-'],
                ['0400000US02', 'Alaska', '250,000+'],
                ['0400000US04', 'Arizona', '45,678'],
                ['0400000US05', 'Arkansas', '1.25e-02'],
                ['0400000US06', 'California', '-'],
                ['0400000US08', 'Colorado', 'N'],
                ['0400000US09', 'Connecticut', 'unparseable_val'],
            ]
            pd.DataFrame(rows).to_csv(csv_input_path, header=False, index=False)

            process_subject_tables(table_prefix='clean_test',
                                   input_path=csv_input_path,
                                   output_dir=tmp_dir,
                                   column_map_path=paths['cmap'],
                                   spec_path=paths['spec'],
                                   debug=False,
                                   delimiter='!!',
                                   has_percent=False)

            cleaned_df = pd.read_csv(
                os.path.join(tmp_dir, 'clean_test_cleaned.csv'))
            self.assertEqual(cleaned_df['Place'].tolist(),
                             ['geoId/01', 'geoId/02', 'geoId/04', 'geoId/05'])
            self.assertEqual(cleaned_df['Quantity'].tolist(),
                             [2500.0, 250000.0, 45678.0, 0.0125])
