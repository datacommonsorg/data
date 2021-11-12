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
_EXCLUDE_DIRS = ['common', 's2201']

def get_paths(table_dir):
    spec_path = None
    statvar_mcf_path = None
    csv_path = None
    column_map_path = None
    zip_path = None

    # Find spec, Expects spec to be in table_dir
    for filename in os.listdir(table_dir):
        if '_spec.json' in filename:
            spec_path = os.path.join(table_dir, filename)

    # Expect statvar MCF, column map, csv and zip to be in testdata folder
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
        cls.test_dirs = list()
        for table_dir in os.listdir(_SCRIPT_PATH):
            table_dir_path = os.path.join(_SCRIPT_PATH, table_dir)
            process_path = os.path.join(_SCRIPT_PATH, table_dir, 'process.py')
            
            # Run test only if table_dir is not in _EXCLUDE_DIRS and process.py 
            # is not in table_dir and table_dir is a directory 
            if table_dir not in _EXCLUDE_DIRS and os.path.isdir(table_dir_path) and not os.path.isfile(process_path):
                cls.test_dirs.append(table_dir_path)
    
    def test_csv_mcf_column_map(self):
        
        for table_dir_path in self.test_dirs:    
            with self.subTest(table_dir_path=table_dir_path):
                spec_path, csv_path, statvar_mcf_path, column_map_path, \
                    zip_path = get_paths(table_dir_path)

                self.assertTrue(spec_path is not None)
                self.assertTrue(csv_path is not None)
                self.assertTrue(statvar_mcf_path is not None)
                self.assertTrue(column_map_path is not None)
                self.assertTrue(zip_path is not None)

                # TODO: Look into speeding up this section of the code
                with tempfile.TemporaryDirectory() as tmp_dir:
                    pass_arg = ['python']
                    pass_arg.append(os.path.join(_SCRIPT_PATH, 'process.py'))
                    pass_arg.append('--table_prefix=test')
                    pass_arg.append(f'--spec_path={spec_path}')
                    pass_arg.append(f'--input_path={zip_path}')
                    pass_arg.append(f'--output_dir={tmp_dir}')
                    pass_arg.append('--has_percent=True')
                    pass_arg.append('--debug=False')

                    subprocess.run(pass_arg)
                    
                    test_mcf_path = os.path.join(tmp_dir, 'test_output.mcf')
                    test_column_map_path = os.path.join(tmp_dir, 'column_map.json')
                    test_csv_path = os.path.join(tmp_dir, 'test_cleaned.csv')

                    with open(test_mcf_path) as mcf_f:
                        mcf_result = mcf_f.read()
                        with open(statvar_mcf_path) as expected_mcf_f:
                            expected_mcf_result = expected_mcf_f.read()
                            self.assertEqual(mcf_result, expected_mcf_result)

                    with open(test_column_map_path) as cmap_f:
                        cmap_result = cmap_f.read()
                        with open(column_map_path) as expected_cmap_f:
                            expected_cmap_result = expected_cmap_f.read()
                            self.assertEqual(cmap_result, expected_cmap_result)

                    with open(test_csv_path) as csv_f:
                        csv_result = csv_f.read()
                        with open(csv_path) as expected_csv_f:
                            expected_csv_result = expected_csv_f.read()
                            self.assertEqual(csv_result, expected_csv_result)