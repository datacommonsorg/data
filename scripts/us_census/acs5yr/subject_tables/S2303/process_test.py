"""Tests for process.py for S2303"""

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import sys
import tempfile
import unittest
import json

#pylint: disable=wrong-import-position
#pylint: disable=import-error
_CODEDIR = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, _CODEDIR)
sys.path.insert(1, os.path.join(_CODEDIR, '..', 'common'))
from generate_col_map import process_zip_file
try:
    from .process import S2303SubjectTableDataLoader, process_subject_tables, set_column_map
except ImportError:
    from process import S2303SubjectTableDataLoader, process_subject_tables, set_column_map
#pylint: enable=wrong-import-position
#pylint: enable=import-error

_TEST_DIR = os.path.join(_CODEDIR, 'testdata')
_TEST_DATA_ZIP = os.path.join(_TEST_DIR, 'alabama.zip')
_CONFIG_PATH = os.path.join(_CODEDIR, 'S2303_spec.json')
_EXPECTED_TMCF = os.path.join(_TEST_DIR, 'output.tmcf')
_EXPECTED_MCF = os.path.join(_TEST_DIR, 'output.mcf')
_EXPECTED_CSV = os.path.join(_TEST_DIR, 'expected.csv')


class ProcessTest(unittest.TestCase):

    def test_create_csv_mcf_tmcf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            column_map_path = set_column_map(_TEST_DATA_ZIP,
                                             _CONFIG_PATH,
                                             tmp_dir,
                                             table_prefix='S2303')
            process_subject_tables(table_prefix='S2303',
                                   input_path=_TEST_DATA_ZIP,
                                   output_dir=tmp_dir,
                                   column_map_path=column_map_path,
                                   spec_path=_CONFIG_PATH,
                                   debug=False,
                                   delimiter='!!',
                                   has_percent=True,
                                   decimal_places=3,
                                   estimate_period=5,
                                   header_row=1)

            mcf_file_path = os.path.join(tmp_dir, 'S2303_output.mcf')
            tmcf_file_path = os.path.join(tmp_dir, 'S2303_output.tmcf')
            csv_file_path = os.path.join(tmp_dir, 'S2303_cleaned.csv')

            with open(mcf_file_path) as mcf_f:
                mcf_result = mcf_f.read()
                with open(_EXPECTED_MCF) as expected_mcf_f:
                    expected_mcf_result = expected_mcf_f.read()
                    self.assertEqual(mcf_result, expected_mcf_result)

            with open(tmcf_file_path) as tmcf_f:
                tmcf_result = tmcf_f.read()
                with open(_EXPECTED_TMCF) as expected_tmcf_f:
                    expected_tmcf_result = expected_tmcf_f.read()
                    self.assertEqual(tmcf_result, expected_tmcf_result)

            with open(csv_file_path) as csv_f:
                csv_result = csv_f.read()
                with open(_EXPECTED_CSV) as expected_csv_f:
                    expected_csv_result = expected_csv_f.read()
                    self.assertEqual(csv_result, expected_csv_result)
