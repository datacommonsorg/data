# Copyright 2022 Google LLC
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
"""
Script to automate the testing for USA Population preprocess script.
"""
import os
import sys
import unittest
from os import path
from absl import flags

# module_dir_ is the path to where this test is running from.
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_MODULE_DIR, '../../../'))
for path_entry in (_SCRIPTS_DIR, _MODULE_DIR):
    if path_entry not in sys.path:
        sys.path.append(path_entry)

# pylint: disable=wrong-import-position
from us_census.pep.monthly_population_estimate.preprocess import CensusUSACountryPopulation
# pylint: enable=wrong-import-position
_INPUT_FILE_PATH = os.path.join(_MODULE_DIR, "test_data", "input_files")
test_output_folder = os.path.join(_MODULE_DIR, "test_data", "output_data")
expected_op_folder = os.path.join(_MODULE_DIR, "test_data", "expected_output")


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing
    """

    cleaned_csv_file_path = os.path.join(test_output_folder, "data.csv")
    mcf_file_path = os.path.join(test_output_folder, "test_census.mcf")
    tmcf_file_path = os.path.join(test_output_folder, "test_census.tmcf")

    base = CensusUSACountryPopulation(_INPUT_FILE_PATH, cleaned_csv_file_path,
                                      mcf_file_path, tmcf_file_path)
    base.process()

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(test_output_folder, ignore_errors=True)

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        expected_mcf_file_path = os.path.join(expected_op_folder,
                                              "USA_Population_Count.mcf")

        expected_tmcf_file_path = os.path.join(expected_op_folder,
                                               "USA_Population_Count.tmcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        with open(self.mcf_file_path, encoding="UTF-8") as mcf_file:
            mcf_data = mcf_file.read()

        with open(self.tmcf_file_path, encoding="UTF-8") as tmcf_file:
            tmcf_data = tmcf_file.read()

        if path.exists(self.mcf_file_path):
            os.remove(self.mcf_file_path)
        if path.exists(self.tmcf_file_path):
            os.remove(self.tmcf_file_path)

        self.assertEqual(expected_mcf_data.strip(), mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(), tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(expected_op_folder,
                                              "USA_Population_Count.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8-sig") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        with open(self.cleaned_csv_file_path, encoding="utf-8-sig") as csv_file:
            csv_data = csv_file.read()

        if path.exists(self.cleaned_csv_file_path):
            os.remove(self.cleaned_csv_file_path)

        self.assertEqual(expected_csv_data.strip(), csv_data.strip())

    def test_create_retry_session(self):
        """Tests that _create_retry_session sets user agent and retry adapter."""
        from us_census.pep.monthly_population_estimate.preprocess import _create_retry_session
        session = _create_retry_session()
        self.assertIn('User-Agent', session.headers)
        self.assertIn('DataCommonsImport', session.headers['User-Agent'])

    def test_is_html_response(self):
        """Tests HTML error page detection."""
        from us_census.pep.monthly_population_estimate.preprocess import _is_html_response
        self.assertTrue(_is_html_response('text/html'))
        self.assertTrue(_is_html_response('text/html; charset=utf-8'))
        self.assertTrue(
            _is_html_response('application/json',
                              b'<html><body>Error</body></html>'))
        self.assertTrue(
            _is_html_response('', b'<title>Request Rejected</title>'))
        self.assertFalse(
            _is_html_response('application/octet-stream', b'PK\x03\x04'))
        self.assertFalse(_is_html_response('text/plain', b'1990  1  248709873'))

    def test_txt_parser_with_bad_lines(self):
        """Tests that multi-whitespace table parsing with bad lines (e.g. notes) does not fail."""
        import io
        import pandas as pd
        cols = [
            "Year and Month", "Date", "Resident Population",
            "Resident Population Plus Armed Forces Overseas",
            "Civilian Population", "Civilian NonInstitutionalized Population"
        ]
        sample_txt = (
            "1990  April 1   248709873 249622814 247051785 242952865\n"
            "1990  May 1     248769873 249682814 247111785 243012865\n"
            "Source: U.S. Census Bureau, Population Division. Note with many extra words here\n"
        )
        df = pd.read_table(io.StringIO(sample_txt),
                           index_col=False,
                           sep=r'\s+',
                           engine='python',
                           names=cols,
                           on_bad_lines=lambda line: line[:len(cols)])
        self.assertEqual(len(df), 3)
        self.assertEqual(df.iloc[0]['Year and Month'], '1990')


if __name__ == "__main__":
    unittest.main()
