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
import tempfile
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
from us_census.pep.monthly_population_estimate.preprocess import (
    CensusUSACountryPopulation,
    parse_nat_total_txt,
)
# pylint: enable=wrong-import-position
_INPUT_FILE_PATH = os.path.join(_MODULE_DIR, "test_data", "input_files")
expected_op_folder = os.path.join(_MODULE_DIR, "test_data", "expected_output")


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inheriting unittest class
    properties which further required for unit testing
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir_obj = tempfile.TemporaryDirectory()
        cls.cleaned_csv_file_path = os.path.join(cls.tmp_dir_obj.name,
                                                 "data.csv")
        cls.mcf_file_path = os.path.join(cls.tmp_dir_obj.name,
                                         "test_census.mcf")
        cls.tmcf_file_path = os.path.join(cls.tmp_dir_obj.name,
                                          "test_census.tmcf")

        base = CensusUSACountryPopulation(_INPUT_FILE_PATH,
                                          cls.cleaned_csv_file_path,
                                          cls.mcf_file_path, cls.tmcf_file_path)
        base.process()

        with open(cls.mcf_file_path, encoding="UTF-8") as mcf_file:
            cls.mcf_data = mcf_file.read()

        with open(cls.tmcf_file_path, encoding="UTF-8") as tmcf_file:
            cls.tmcf_data = tmcf_file.read()

        with open(cls.cleaned_csv_file_path, encoding="utf-8-sig") as csv_file:
            cls.csv_data = csv_file.read()

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir_obj.cleanup()

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

        self.assertEqual(expected_mcf_data.strip(), self.mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(), self.tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(expected_op_folder,
                                              "USA_Population_Count.csv")

        with open(expected_csv_file_path,
                  encoding="utf-8-sig") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(), self.csv_data.strip())

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

    def test_txt_parser_filters_non_data_lines(self):
        """Tests that text table parsing filters out notes/headers and keeps valid data rows."""
        sample_txt = (
            "Monthly Estimates of the United States Population: April 1, 1980 to\n"
            "July 1, 1999, with Short-Term Projections to November 1, 2000.\n"
            "1990\n"
            "April 1   248,709 249,622 247,051 242,952\n"
            "May 1     248,769 249,682 247,111 243,012\n"
            "April 1 (census) 226,546 227,061 224,968\n"
            "Note: The estimates base population of April 1, 1990 is 248,790,925.\n"
            "Source: U.S. Census Bureau, Population Division. Note with many extra words here\n"
        )
        df = parse_nat_total_txt(sample_txt)
        self.assertEqual(len(df), 4)
        self.assertEqual(df.iloc[0]["Year and Month"], '1990')
        self.assertEqual(df.iloc[1]["Year and Month"], 'April')
        self.assertEqual(df.iloc[1]["Date"], '1')
        self.assertEqual(df.iloc[2]["Year and Month"], 'May')
        self.assertEqual(df.iloc[3]["Year and Month"], 'April')
        self.assertEqual(df.iloc[3]["Date"], '1')
        self.assertEqual(df.iloc[3]["Resident Population"], '226546')


if __name__ == "__main__":
    unittest.main()
