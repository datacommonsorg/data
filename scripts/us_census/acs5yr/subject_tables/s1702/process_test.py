"""Tests for process.py for S1702"""

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import sys
import tempfile
import unittest

_CODEDIR = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.join(_CODEDIR, '..'))
from process import S1702TableDataLoader

_TEST_DIR = os.path.join(_CODEDIR, 'testdata')
_TEST_DATA_ZIP = os.path.join(_TEST_DIR, 'alabama.zip')
_CONFIG_PATH = os.path.join(_CODEDIR, 'config.json')
_EXPECTED_TMCF = os.path.join(_CODEDIR, 'output.tmcf')
_EXPECTED_MCF = os.path.join(_CODEDIR, 'output.mcf')
_EXPECTED_CSV = os.path.join(_TEST_DIR, 'expected.csv')


class ProcessTest(unittest.TestCase):

    def test_create_csv_mcf_tmcf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_loader_obj = S1702TableDataLoader(table_id='S1702',
                                                   estimate_period=5,
                                                   json_spec_path=_CONFIG_PATH,
                                                   output_dir_path=tmp_dir,
                                                   zip_file_path=_TEST_DATA_ZIP,
                                                   debug=True)

            mcf_file_path = os.path.join(tmp_dir, 'S1702_output.mcf')
            tmcf_file_path = os.path.join(tmp_dir, 'S1702_output.tmcf')
            csv_file_path = os.path.join(tmp_dir, 'S1702_cleaned.csv')

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
