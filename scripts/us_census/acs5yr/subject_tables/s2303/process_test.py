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

sys.path.insert(1, os.path.join(_CODEDIR, '..', 'common'))
from generate_col_map import process_zip_file
from process import S2303SubjectTableDataLoader
#pylint: enable=wrong-import-position
#pylint: enable=import-error

_TEST_DIR = os.path.join(_CODEDIR, 'testdata')
_TEST_DATA_ZIP = os.path.join(_TEST_DIR, 'alabama.zip')
_CONFIG_PATH = os.path.join(_CODEDIR, 'config.json')
_EXPECTED_TMCF = os.path.join(_CODEDIR, 'output.tmcf')
_EXPECTED_MCF = os.path.join(_CODEDIR, 'output.mcf')
_EXPECTED_CSV = os.path.join(_TEST_DIR, 'expected.csv')


def set_column_map(input_path, spec_path, output_dir):
    generated_col_map = process_zip_file(input_path,
                                         spec_path,
                                         write_output=False)
    f = open(os.path.join(output_dir, 'column_map.json'), 'w')
    json.dump(generated_col_map, f, indent=4)
    f.close()


class ProcessTest(unittest.TestCase):

    def test_create_csv_mcf_tmcf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            set_column_map(_TEST_DATA_ZIP, _CONFIG_PATH, tmp_dir)
            column_map_path = os.path.join(tmp_dir, 'column_map.json')
            data_loader = S2303SubjectTableDataLoader(
                table_id='S2303',
                col_delimiter='!!',
                has_percent=True,
                debug=False,
                output_path_dir=tmp_dir,
                json_spec=_CONFIG_PATH,
                column_map_path=column_map_path,
                decimal_places=3,
                estimate_period=5,
                header_row=1)
            data_loader._process_zip_file(_TEST_DATA_ZIP)

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
