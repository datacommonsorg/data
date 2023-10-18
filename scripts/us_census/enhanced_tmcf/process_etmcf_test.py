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
"""Tests for process_etmcf.py"""

import os
import tempfile
import unittest
from .process_etmcf import *

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_INPUT_DIR = os.path.join(_CODEDIR, 'testdata', 'input')
_EXPECTED_DIR = os.path.join(_CODEDIR, 'testdata', 'expected')


def compare_files(t, output_path, expected_path):
    with open(output_path) as gotf:
        got = gotf.read()
        with open(expected_path) as wantf:
            want = wantf.read()
            t.assertEqual(got, want)


class Process_ETMCF_Test(unittest.TestCase):

    def test_simple_success(self):
        self.maxDiff = None
        input_etmcf = 'simple'
        input_csv = 'simple'

        output_tmcf = "simple_processed"
        output_csv = "simple_processed"
        with tempfile.TemporaryDirectory() as tmp_dir:
            process_enhanced_tmcf(_INPUT_DIR, tmp_dir, input_etmcf, input_csv,
                                  output_tmcf, output_csv)
            for fname in [output_tmcf + ".tmcf", output_csv + ".csv"]:
                output_path = os.path.join(tmp_dir, fname)
                expected_path = os.path.join(_EXPECTED_DIR, fname)
                compare_files(self, output_path, expected_path)

    def test_simple_opaque_success(self):
        self.maxDiff = None
        input_etmcf = 'simple_opaque'
        input_csv = 'simple_opaque'

        output_tmcf = "simple_opaque_processed"
        output_csv = "simple_opaque_processed"
        with tempfile.TemporaryDirectory() as tmp_dir:
            process_enhanced_tmcf(_INPUT_DIR, tmp_dir, input_etmcf, input_csv,
                                  output_tmcf, output_csv)
            for fname in [output_tmcf + ".tmcf", output_csv + ".csv"]:
                output_path = os.path.join(tmp_dir, fname)
                expected_path = os.path.join(_EXPECTED_DIR, fname)
                compare_files(self, output_path, expected_path)

    def test_process_enhanced_tmcf_medium_success(self):
        self.maxDiff = None
        input_etmcf = 'ECNBASIC2012.EC1200A1'
        input_csv = 'ECNBASIC2012.EC1200A1-Data'

        output_tmcf = "ECNBASIC2012.EC1200A1_processed"
        output_csv = "ECNBASIC2012.EC1200A1_processed"
        with tempfile.TemporaryDirectory() as tmp_dir:
            process_enhanced_tmcf(_INPUT_DIR, tmp_dir, input_etmcf, input_csv,
                                  output_tmcf, output_csv)
            for fname in [output_tmcf + ".tmcf", output_csv + ".csv"]:
                output_path = os.path.join(tmp_dir, fname)
                expected_path = os.path.join(_EXPECTED_DIR, fname)
                compare_files(self, output_path, expected_path)

    def test_tmcf_file_not_found_exception(self):
        self.maxDiff = None
        input_etmcf = 'nonexistent_tmcf'
        input_csv = 'ECNBASIC2012.EC1200A1-Data'

        output_tmcf = "no_output"
        output_csv = "no_output"
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(Exception):
                process_enhanced_tmcf(_INPUT_DIR, tmp_dir, input_etmcf,
                                      input_csv, output_tmcf, output_csv)

    def test_csv_file_not_found_exception(self):
        self.maxDiff = None
        input_etmcf = 'ECNBASIC2012.EC1200A1'
        input_csv = 'nonexistent_csv'

        output_tmcf = "no_output"
        output_csv = "no_output"
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(Exception):
                process_enhanced_tmcf(_INPUT_DIR, tmp_dir, input_etmcf,
                                      input_csv, output_tmcf, output_csv)

    def test_bad_tmcf_variable_measured_two_question_marks_exception(self):
        self.maxDiff = None
        input_etmcf = 'bad_varMeasured_question_marks'
        input_csv = 'ECNBASIC2012.EC1200A1-Data'

        output_tmcf = "no_output"
        output_csv = "no_output"
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(
                    Exception,
                    "Exactly one '\?' expected in variableMeasured*"):
                process_enhanced_tmcf(_INPUT_DIR, tmp_dir, input_etmcf,
                                      input_csv, output_tmcf, output_csv)

    def test_bad_tmcf_variable_measured_two_equals_exception(self):
        self.maxDiff = None
        input_etmcf = 'bad_varMeasured_equals'
        input_csv = 'ECNBASIC2012.EC1200A1-Data'

        output_tmcf = "no_output"
        output_csv = "no_output"
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(
                    Exception,
                    "Exactly one '=' expected in the key/val opaque mapping*"):
                process_enhanced_tmcf(_INPUT_DIR, tmp_dir, input_etmcf,
                                      input_csv, output_tmcf, output_csv)


if __name__ == '__main__':
    unittest.main()
