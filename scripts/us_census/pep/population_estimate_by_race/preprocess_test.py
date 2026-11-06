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
Script to automate the testing for USA Population by Race preprocess script.
"""

import os
import sys
import tempfile
import unittest
import shutil
from os import path

# module_dir is the path to where this test is running from.
module_dir = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(module_dir, '../../../'))
for path_entry in (_SCRIPTS_DIR, module_dir):
    if path_entry not in sys.path:
        sys.path.append(path_entry)

# pylint: disable=wrong-import-position
from us_census.pep.population_estimate_by_race.preprocess import CensusUSAPopulationByRace
# pylint: enable=wrong-import-position
TEST_DATA_FOLDER = os.path.join(module_dir, "test_data")


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inheriting unittest class
    properties which further required for unit testing
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir_obj = tempfile.TemporaryDirectory()
        cls.cleaned_csv_file_path = cls.tmp_dir_obj.name
        cls.mcf_file_path = cls.tmp_dir_obj.name
        cls.tmcf_file_path = cls.tmp_dir_obj.name

        cls.ip_files = os.path.join(TEST_DATA_FOLDER, "test_files")

        base = CensusUSAPopulationByRace(cls.ip_files,
                                         cls.cleaned_csv_file_path,
                                         cls.mcf_file_path, cls.tmcf_file_path)
        base.process()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        files = [
            "USA_Population_Count_by_Race_before_2000",
            "USA_Population_Count_by_Race_county_after_2000",
            "USA_Population_Count_by_Race_National_state_2000"
        ]
        for file in files:
            temp_mcf_file = file + ".mcf"
            expected_mcf_file_path = os.path.join(TEST_DATA_FOLDER,
                                                  "expected_files",
                                                  temp_mcf_file)

            with open(expected_mcf_file_path,
                      encoding="UTF-8") as expected_mcf_file:
                expected_mcf_data = expected_mcf_file.read()

            temp_tmcf_file = file + ".tmcf"
            expected_tmcf_file_path = os.path.join(TEST_DATA_FOLDER,
                                                   "expected_files",
                                                   temp_tmcf_file)
            with open(expected_tmcf_file_path,
                      encoding="UTF-8") as expected_tmcf_file:
                expected_tmcf_data = expected_tmcf_file.read()

            with open(os.path.join(self.mcf_file_path, temp_mcf_file),
                      encoding="UTF-8") as mcf_file:
                mcf_data = mcf_file.read()

            with open(os.path.join(self.tmcf_file_path, temp_tmcf_file),
                      encoding="UTF-8") as tmcf_file:
                tmcf_data = tmcf_file.read()

            self.assertEqual(expected_mcf_data.strip(), mcf_data.strip())
            self.assertEqual(expected_tmcf_data.strip(), tmcf_data.strip())

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir_obj.cleanup()

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(
            TEST_DATA_FOLDER, "expected_USA_Population_Count_by_Race.csv")

        expected_csv_data = ""
        files = [
            "USA_Population_Count_by_Race_before_2000",
            "USA_Population_Count_by_Race_county_after_2000",
            "USA_Population_Count_by_Race_National_state_2000"
        ]
        for file in files:
            temp_csv_file = file + ".csv"
            expected_csv_file_path = os.path.join(TEST_DATA_FOLDER,
                                                  "expected_files",
                                                  temp_csv_file)
            with open(expected_csv_file_path,
                      encoding="utf-8-sig") as expected_csv_file:
                expected_csv_data = expected_csv_file.read()
            with open(os.path.join(self.cleaned_csv_file_path, temp_csv_file),
                      encoding="UTF-8") as csv_file:
                csv_data = csv_file.read()

            self.assertEqual(expected_csv_data.strip(), csv_data.strip())

    def test_create_retry_session(self):
        """Tests that _create_retry_session sets user agent and retry adapter."""
        from us_census.pep.population_estimate_by_race.preprocess import _create_retry_session
        session = _create_retry_session()
        self.assertIn('User-Agent', session.headers)
        self.assertIn('DataCommonsImport', session.headers['User-Agent'])

    def test_is_html_response(self):
        """Tests HTML error page detection."""
        from us_census.pep.population_estimate_by_race.preprocess import _is_html_response
        self.assertTrue(_is_html_response('text/html'))
        self.assertTrue(_is_html_response('text/html; charset=utf-8'))
        self.assertTrue(
            _is_html_response('application/json',
                              b'<html><body>Error</body></html>'))
        self.assertTrue(
            _is_html_response('', b'<title>Request Rejected</title>'))
        self.assertFalse(_is_html_response('text/plain', b'1990  1  248709873'))

    def test_srh_txt_parser_with_bad_lines(self):
        """Tests that multi-whitespace table parsing with extra fields in footnotes skips notes cleanly."""
        from us_census.pep.population_estimate_by_race.preprocess import parse_srh_txt
        sample_srh = (
            "ALABAMA   100  200  300  400  500  600  700  800  900  1000\n"
            "ALASKA    110  210  310  410  510  610  710  810  910  1010\n"
            "Note: This file contains estimates produced by Population Division with 17 extra fields saw here\n"
        )
        df = parse_srh_txt(sample_srh, skiprows=0)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['Area'], 'ALABAMA')


if __name__ == "__main__":
    unittest.main()
