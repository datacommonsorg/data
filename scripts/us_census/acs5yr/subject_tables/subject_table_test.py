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

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import sys
import tempfile
import unittest
import subprocess

# Allows the unittest to access table directories in relative path
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '.'))

# These directories are excluded from testing
_EXCLUDE_DIRS = ['common', 's2201', '__pycache__']


def get_paths(table_dir):
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
    spec_path = None
    statvar_mcf_path = None
    csv_path = None
    column_map_path = None
    zip_path = None

    # Find spec, Expects spec to be in table_dir
    for filename in os.listdir(table_dir):
        if '_spec.json' in filename:
            spec_path = os.path.join(table_dir, filename)

    # Expects StatVar MCF, Column Map, CSV and test zip to be in testdata folder
    testdata_path = os.path.join(table_dir, 'testdata')
    for filename in os.listdir(testdata_path):
        if '_cleaned.csv' in filename:
            csv_path = os.path.join(testdata_path, filename)
        elif '_output.mcf' in filename:
            statvar_mcf_path = os.path.join(testdata_path, filename)
        elif 'column_map.json' in filename:
            column_map_path = os.path.join(testdata_path, filename)
        elif filename.endswith('.zip'):
            zip_path = os.path.join(testdata_path, filename)

    return spec_path, csv_path, statvar_mcf_path, column_map_path, zip_path


class TestSubjectTable(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # A list of all directories to be tested
        cls.test_dirs = []
        for table_dir in os.listdir(_SCRIPT_PATH):
            table_dir_path = os.path.join(_SCRIPT_PATH, table_dir)
            process_path = os.path.join(_SCRIPT_PATH, table_dir, 'process.py')

            # Run test only if table_dir is not in _EXCLUDE_DIRS and process.py
            # is not in table_dir and table_dir is a directory
            if table_dir not in _EXCLUDE_DIRS and os.path.isdir(
                    table_dir_path) and not os.path.isfile(process_path):
                cls.test_dirs.append(table_dir_path)

    def test_csv_mcf_column_map(self):

        for table_dir_path in self.test_dirs:
            with self.subTest(table_dir_path=table_dir_path):
                spec_path, csv_path, statvar_mcf_path, column_map_path, \
                    zip_path = get_paths(table_dir_path)

                # Check if all required files exist
                self.assertTrue(spec_path is not None)
                self.assertTrue(csv_path is not None)
                self.assertTrue(statvar_mcf_path is not None)
                self.assertTrue(column_map_path is not None)
                self.assertTrue(zip_path is not None)

                # TODO: Look into speeding up this section of the code
                with tempfile.TemporaryDirectory() as tmp_dir:
                    # Run scripts/us_census/acs5yr/subject_tables/process.py
                    process_arg = ['python']
                    process_arg.append(os.path.join(_SCRIPT_PATH, 'process.py'))
                    process_arg.append('--table_prefix=test')
                    process_arg.append(f'--spec_path={spec_path}')
                    process_arg.append(f'--input_path={zip_path}')
                    process_arg.append(f'--output_dir={tmp_dir}')
                    process_arg.append('--has_percent=True')
                    process_arg.append('--debug=False')

                    subprocess.run(process_arg, check=True)

                    test_mcf_path = os.path.join(tmp_dir, 'test_output.mcf')
                    test_column_map_path = os.path.join(tmp_dir,
                                                        'column_map.json')
                    test_csv_path = os.path.join(tmp_dir, 'test_cleaned.csv')

                    # Test StatVar MCF
                    with open(test_mcf_path, 'r') as mcf_f:
                        mcf_result = mcf_f.read()
                        with open(statvar_mcf_path, 'r') as expected_mcf_f:
                            expected_mcf_result = expected_mcf_f.read()
                            self.assertEqual(mcf_result, expected_mcf_result)

                    # Test Column Map
                    with open(test_column_map_path, 'r') as cmap_f:
                        cmap_result = cmap_f.read()
                        with open(column_map_path, 'r') as expected_cmap_f:
                            expected_cmap_result = expected_cmap_f.read()
                            self.assertEqual(cmap_result, expected_cmap_result)

                    # Test CSV
                    with open(test_csv_path, 'r') as csv_f:
                        csv_result = csv_f.read()
                        with open(csv_path, 'r') as expected_csv_f:
                            expected_csv_result = expected_csv_f.read()
                            self.assertEqual(csv_result, expected_csv_result)
