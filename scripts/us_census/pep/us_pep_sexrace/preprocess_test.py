# Copyright 2024 Google LLC
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
Script to automate the testing for USA Population by Sex Race preprocess script.
"""

import os
import shutil
import unittest
from unittest import mock
import sys

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)
sys.path.insert(0, module_dir_)
import common
import preprocess
from preprocess import process
from preprocess import add_future_year_urls

expected_data_folder = os.path.join(module_dir_,
                                    "test_data/expected_output_files")
actual_data_folder = os.path.join(module_dir_, "output_files/final")
test_data_folder = os.path.join(module_dir_, "test_data")


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing
    """

    @classmethod
    def setUpClass(cls):
        ip_config_files = test_data_folder + os.sep + "config_files"
        ip_files = os.listdir(ip_config_files)
        config_files = []
        for file in ip_files:
            config_files.append(ip_config_files + os.sep + file)
        mock_resp = mock.MagicMock(status_code=503)
        with mock.patch("preprocess._head_with_html_retry",
                        return_value=mock_resp):
            add_future_year_urls()
        process(config_files, test=True)

    @classmethod
    def tearDownClass(cls):
        for folder in ["output_files", "input_files"]:
            folder_path = os.path.join(module_dir_, folder)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF and TMCF File.
        """
        mcf_files = [
            "state_county_after_2000.mcf", "state_county_before_2000.mcf",
            "national_after_2000.mcf", "national_before_2000.mcf"
        ]

        for mcf_file in mcf_files:
            expected_mcf_file_path = os.path.join(expected_data_folder,
                                                  mcf_file)
            with open(expected_mcf_file_path,
                      encoding="UTF-8") as expected_mcf_file:
                expected_mcf_data = expected_mcf_file.read()

            actual_mcf_file_path = os.path.join(actual_data_folder, mcf_file)
            with open(actual_mcf_file_path,
                      encoding="UTF-8") as actual_mcf_file:
                actual_mcf_data = actual_mcf_file.read()

            self.assertEqual(expected_mcf_data.strip(), actual_mcf_data.strip())

        tmcf_files = [
            "state_county_after_2000.tmcf", "state_county_before_2000.tmcf",
            "national_after_2000.tmcf", "national_before_2000.tmcf"
        ]

        for tmcf_file in tmcf_files:
            expected_tmcf_file_path = os.path.join(expected_data_folder,
                                                   tmcf_file)
            with open(expected_tmcf_file_path,
                      encoding="UTF-8") as expected_tmcf_file:
                expected_tmcf_data = expected_tmcf_file.read()

            actual_tmcf_file_path = os.path.join(actual_data_folder, tmcf_file)
            with open(actual_tmcf_file_path,
                      encoding="UTF-8") as actual_tmcf_file:
                actual_tmcf_data = actual_tmcf_file.read()
            self.assertEqual(expected_tmcf_data.strip(),
                             actual_tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        # self.maxDiff = None
        output_csv_files = [
            "state_county_after_2000.csv", "state_county_before_2000.csv",
            "national_after_2000.csv", "national_before_2000.csv"
        ]

        for output_csv_file in output_csv_files:
            expected_csv_file_path = os.path.join(expected_data_folder,
                                                  output_csv_file)
            with open(expected_csv_file_path,
                      encoding="utf-8-sig") as expected_csv_file:
                expected_csv_data = expected_csv_file.read()

            actual_csv_file_path = os.path.join(actual_data_folder,
                                                output_csv_file)
            with open(actual_csv_file_path,
                      encoding="utf-8-sig") as actual_csv_file:
                actual_csv_data = actual_csv_file.read()

            self.assertEqual(expected_csv_data.strip(), actual_csv_data.strip())

    def test_retry_session_configuration(self):
        session = preprocess._create_retry_session()
        try:
            self.assertIn("Mozilla/5.0", session.headers.get("User-Agent", ""))
            adapter = session.get_adapter("https://www2.census.gov/")
            self.assertEqual(adapter.max_retries.total, 5)
            self.assertIn(429, adapter.max_retries.status_forcelist)
            self.assertIn(503, adapter.max_retries.status_forcelist)
            self.assertIn(520, adapter.max_retries.status_forcelist)
        finally:
            session.close()

    def test_is_html_response(self):
        resp = mock.MagicMock()
        resp.headers = {"Content-Type": "text/html"}
        self.assertTrue(preprocess._is_html_response(resp))

        resp_csv = mock.MagicMock()
        resp_csv.headers = {"Content-Type": "text/csv"}
        self.assertFalse(
            preprocess._is_html_response(resp_csv, b"YEAR,STATE,COUNTY\n"))
        self.assertTrue(
            preprocess._is_html_response(
                resp_csv, b"<!DOCTYPE html><html>blocked</html>"))

    def test_load_url_or_path_caches_repeated_url(self):
        orig_cache = preprocess._LAST_FETCHED_URL
        self.addCleanup(setattr, preprocess, '_LAST_FETCHED_URL', orig_cache)
        preprocess._LAST_FETCHED_URL = (None, None)
        url = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/asrh/cc-est2025-alldata.csv"
        with mock.patch("preprocess._fetch_url_bytes",
                        return_value=b"col1,col2\n1,2\n") as mock_fetch:
            buf1 = preprocess.load_url_or_path(url)
            buf2 = preprocess.load_url_or_path(url)
            self.assertEqual(mock_fetch.call_count, 1)
            self.assertEqual(buf1.read(), b"col1,col2\n1,2\n")
            self.assertEqual(buf2.read(), b"col1,col2\n1,2\n")

    @mock.patch.object(preprocess,
                       "_head_with_html_retry",
                       return_value=mock.MagicMock(status_code=503))
    def test_add_future_year_urls_fallback_to_baseline(self, mock_head):
        orig_files = list(preprocess._FILES_TO_DOWNLOAD
                         ) if preprocess._FILES_TO_DOWNLOAD else None
        self.addCleanup(setattr, preprocess, '_FILES_TO_DOWNLOAD', orig_files)
        add_future_year_urls()
        self.assertEqual(len(preprocess._FILES_TO_DOWNLOAD), 1)
        self.assertIn("2025", preprocess._FILES_TO_DOWNLOAD[0]["download_path"])
