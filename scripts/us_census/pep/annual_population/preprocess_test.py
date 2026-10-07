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
import tempfile
# _MODULE_DIR is the path to where this test is running from.
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_MODULE_DIR, '../../../'))
for path in (_SCRIPTS_DIR, _MODULE_DIR):
    if path not in sys.path:
        sys.path.append(path)

import json
import re
from unittest.mock import MagicMock, patch
import pandas as pd

# pylint: disable=wrong-import-position
# pylint: disable=import-error
from us_census.pep.annual_population.preprocess import (
    process,
    _process_nationals_2029,
    download_with_retry,
    _create_retry_session,
    add_future_year_urls,
    USA,
)
from us_census.pep.annual_population.constants import TEST_DATA_DIR
# pylint: enable=import-error
# pylint: enable=wrong-import-position


class TestPreprocess(unittest.TestCase):
    """
    This module is used to test USCensus PEP_Annual_Population data processing.
    It will generate and test CSV, MCF and TMCF files for given test input files
    and compare it with expected results.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir_obj = tempfile.TemporaryDirectory()
        tmp_dir = cls.tmp_dir_obj.name
        files_dir = os.path.join(_MODULE_DIR, TEST_DATA_DIR, "datasets")

        cleaned_csv_path = os.path.join(tmp_dir, "usa_annual_population.csv")
        mcf_path = os.path.join(tmp_dir, "usa_annual_population.mcf")
        tmcf_path = os.path.join(tmp_dir, "usa_annual_population.tmcf")

        process(files_dir, cleaned_csv_path, mcf_path, tmcf_path, False)

        with open(mcf_path, encoding="UTF-8") as mcf_file:
            cls._actual_mcf_data = mcf_file.read()

        with open(tmcf_path, encoding="UTF-8") as tmcf_file:
            cls._actual_tmcf_data = tmcf_file.read()

        with open(cleaned_csv_path, encoding="utf-8") as csv_file:
            cls._actual_csv_data = csv_file.read()

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir_obj.cleanup()

    def test_mcf_tmcf_files(self):
        """
        This method tests MCF, tMCF files generated using process module against
        expected results.
        """
        expected_mcf_file_path = os.path.join(_MODULE_DIR, TEST_DATA_DIR,
                                              "expected_files",
                                              "usa_annual_population.mcf")

        expected_tmcf_file_path = os.path.join(_MODULE_DIR, TEST_DATA_DIR,
                                               "expected_files",
                                               "usa_annual_population.tmcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        self.assertEqual(expected_mcf_data.strip(),
                         self._actual_mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(),
                         self._actual_tmcf_data.strip())

    def test_create_csv(self):
        """
        This method tests CSV file generated using process module against
        expected CSV result.
        """
        expected_csv_file_path = os.path.join(_MODULE_DIR, TEST_DATA_DIR,
                                              "expected_files",
                                              "usa_annual_population.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()
        self.assertEqual(expected_csv_data.strip(),
                         self._actual_csv_data.strip())


class TestProcessExcel2029(unittest.TestCase):
    """Tests for dynamic future year processing in Excel files and POPCHG regex."""

    def test_process_nationals_2029_float_and_int_headers(self):
        """Tests that _process_nationals_2029 correctly parses float and int headers for future years."""
        mock_df = pd.DataFrame({
            'Geographic Area': [USA, 'Northeast'],
            'April 1, 2020': [331449281, 57000000],
            '2020': [331511512, 57100000],
            '2021': [332031554, 57200000],
            '2022': [333287557, 57300000],
            '2023': [334914895, 57400000],
            2024.0: [336000000,
                     57500000],  # parsed as float by pandas read_excel
            2025: [337000000, 57600000],  # parsed as int
        })
        with patch('us_census.pep.annual_population.preprocess._load_data_df',
                   return_value=mock_df):
            result = _process_nationals_2029('dummy_path.xlsx')

        self.assertIn('Year', result.columns)
        self.assertIn('Count_Person', result.columns)
        self.assertIn('Location', result.columns)
        years = result['Year'].tolist()
        self.assertIn('2024', years)
        self.assertIn('2025', years)
        self.assertEqual(
            result[result['Year'] == '2024']['Count_Person'].iloc[0],
            336000000)
        self.assertEqual(
            result[result['Year'] == '2025']['Count_Person'].iloc[0],
            337000000)

    def test_popchg_regex_matches_various_years(self):
        """Tests that regex pattern matches NST-EST<year>-POPCHG2020_<year>.csv for various years."""
        pattern = r"NST-EST\d{4}-POPCHG2020_\d{4}\.csv"
        for year in [2023, 2024, 2025, 2026, 2029]:
            filename = f"NST-EST{year}-POPCHG2020_{year}.csv"
            self.assertIsNotNone(re.search(pattern, filename),
                                 f"Failed to match {filename}")

        self.assertIsNone(re.search(pattern, "NST-EST2024-POP.csv"))
        self.assertIsNone(re.search(pattern, "NST-EST-POPCHG2020.csv"))


class TestDownloadAndUrlProbing(unittest.TestCase):
    """Tests for download session, retries, HTML error detection, and URL probing."""

    def test_create_retry_session(self):
        """Tests that retry session is properly configured with status codes and backoff."""
        session = _create_retry_session()
        self.assertIn('User-Agent', session.headers)
        adapter = session.adapters.get('https://')
        self.assertIsNotNone(adapter)
        self.assertIsNotNone(adapter.max_retries)
        self.assertIn(429, adapter.max_retries.status_forcelist)
        self.assertIn(500, adapter.max_retries.status_forcelist)
        self.assertIn(503, adapter.max_retries.status_forcelist)

    def test_download_with_retry_raises_on_html_error(self):
        """Tests that download_with_retry raises ValueError on HTML error page (soft-404)."""
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'Content-Type': 'text/html; charset=UTF-8'}
        mock_resp.__enter__.return_value = mock_resp
        session.get.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_file = os.path.join(tmp_dir, 'test.xlsx')
            with self.assertRaises(ValueError) as ctx:
                download_with_retry.__wrapped__(
                    session, 'https://census.gov/test.xlsx', dest_file)
            self.assertIn('HTML error page', str(ctx.exception))

    def test_download_with_retry_writes_binary_file(self):
        """Tests that download_with_retry writes binary data chunks successfully."""
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {
            'Content-Type':
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        mock_resp.iter_content.return_value = [b'chunk1', b'chunk2']
        mock_resp.__enter__.return_value = mock_resp
        session.get.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_file = os.path.join(tmp_dir, 'test.xlsx')
            download_with_retry.__wrapped__(session,
                                            'https://census.gov/test.xlsx',
                                            dest_file)
            self.assertTrue(os.path.exists(dest_file))
            with open(dest_file, 'rb') as f:
                self.assertEqual(f.read(), b'chunk1chunk2')

    def test_add_future_year_urls_gatekeeper_break(self):
        """Tests that add_future_year_urls stops scanning when gatekeeper year is found."""
        session = MagicMock()
        head_calls = []

        def mock_head(url, *args, **kwargs):
            head_calls.append(url)
            resp = MagicMock()
            if '2024' in url:
                resp.status_code = 200
                resp.headers = {'Content-Type': 'application/vnd.ms-excel'}
            else:
                resp.status_code = 404
                resp.headers = {'Content-Type': 'text/html'}
            return resp

        session.head = mock_head

        with patch(
                'us_census.pep.annual_population.preprocess._create_retry_session',
                return_value=session), patch('time.sleep'):
            add_future_year_urls()

        years_probed = [url for url in head_calls if '2024' in url]
        self.assertTrue(len(years_probed) > 0)
        years_2023 = [url for url in head_calls if '2023' in url]
        self.assertEqual(len(years_2023), 0)

    def test_add_future_year_urls_fallback_to_baseline(self):
        """Tests that add_future_year_urls falls back to baseline year when all future years 404."""
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.headers = {'Content-Type': 'text/html'}
        session.head.return_value = mock_resp

        import us_census.pep.annual_population.preprocess as prep
        with patch(
                'us_census.pep.annual_population.preprocess._create_retry_session',
                return_value=session), patch('time.sleep'):
            prep.add_future_year_urls()

        download_urls = [
            entry['download_path'] for entry in prep._FILES_TO_DOWNLOAD
        ]
        self.assertTrue(
            any('2020-2025' in url or '2020-2023' in url
                for url in download_urls))


if __name__ == '__main__':
    unittest.main()
