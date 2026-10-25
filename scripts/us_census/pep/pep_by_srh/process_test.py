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
Script to automate the testing for USA Census Population Estimate's (by SRH)
process, generate_mcf and generate_tmcf scripts.
"""

import os
import shutil
import tempfile
import unittest
from unittest import mock
from mcf_generator import generate_mcf
from tmcf_generator import generate_tmcf

import process as process_module
from process import (
    _BASELINE_YEAR,
    _create_retry_session,
    _head_with_html_retry,
    add_future_year_urls,
    download_with_retry,
    process,
)
from constants import OUTPUT_DIR

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_ACTUAL_RESULTS_DIR = os.path.join(_CODEDIR, "testdata", "actual_results")


class ProcessTest(unittest.TestCase):
    """
    This class defines unit test cases for automated testing of generation of
    MCF, tMCF and DC import CSV files for US Census Estimates by SRH data.
    """

    def setUp(self):
        os.makedirs(_ACTUAL_RESULTS_DIR, exist_ok=True)

    def tearDown(self):
        if os.path.exists(_ACTUAL_RESULTS_DIR):
            shutil.rmtree(_ACTUAL_RESULTS_DIR)
        for folder in ["output_files", "process_files"]:
            folder_path = os.path.join(_CODEDIR, folder)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

    def test_Mcf(self):
        """
        This method runs generate_mcf method, which generates MCF files for
        as-is and aggregate import and compares expected mcf files with actual
        (generated) files
        """
        generate_mcf('/testdata/actual_results/')
        with open(_CODEDIR +
                  '/testdata/expected_results/population_estimate_by_srh.mcf',
                  'r',
                  encoding='utf-8') as expected_mcf_file:
            expected_mcf = expected_mcf_file.read()

        with open(_CODEDIR +
                  '/testdata/actual_results/population_estimate_by_srh.mcf',
                  'r',
                  encoding='utf-8') as actual_mcf_file:
            actual_mcf = actual_mcf_file.read()

        with open(
                _CODEDIR +
                '/testdata/expected_results/population_estimate_by_srh_agg.mcf',
                'r',
                encoding='utf-8') as expected_agg_mcf_file:
            expected_agg_mcf = expected_agg_mcf_file.read()

        with open(_CODEDIR +
                  '/testdata/actual_results/population_estimate_by_srh_agg.mcf',
                  'r',
                  encoding='utf-8') as actual_agg_mcf_file:
            actual_agg_mcf = actual_agg_mcf_file.read()

        expected_agg_mcf_file.close()
        actual_agg_mcf_file.close()

        self.assertEqual(expected_mcf, actual_mcf)
        self.assertEqual(expected_agg_mcf, actual_agg_mcf)

    def test_Tmcf(self):
        """
        This method runs generate_tmcf method, which generates tMCF files for
        as-is and aggregate import and compares expected tmcf files with actual
        (generated) files.
        """

        generate_tmcf('/testdata/actual_results/')
        with open(_CODEDIR +
                  '/testdata/expected_results/population_estimate_by_srh.tmcf',
                  'r',
                  encoding='utf-8') as expected_tmcf_file:
            expected_tmcf = expected_tmcf_file.read()
        with open(_CODEDIR +
                  '/testdata/actual_results/population_estimate_by_srh.tmcf',
                  'r',
                  encoding='utf-8') as actual_tmcf_file:
            actual_tmcf = actual_tmcf_file.read()

        with open(
                _CODEDIR +
                '/testdata/expected_results/population_estimate_by_srh_agg.tmcf',
                'r',
                encoding='utf-8') as expected_agg_tmcf_file:
            expected_agg_tmcf = expected_agg_tmcf_file.read()
        with open(
                _CODEDIR +
                '/testdata/actual_results/population_estimate_by_srh_agg.tmcf',
                'r',
                encoding='utf-8') as actual_agg_tmcf_file:
            actual_agg_tmcf = actual_agg_tmcf_file.read()

        self.assertEqual(expected_tmcf, actual_tmcf)
        self.assertEqual(expected_agg_tmcf, actual_agg_tmcf)

    def test_Csv(self):
        """
        This method runs process script, which generates csv files for
        as-is and aggregate imports to dc. It compares expected files with 
        actual files.
        """

        process('/testdata/input_files/', '/testdata/actual_results/')
        with open(_CODEDIR +
                  '/testdata/expected_results/population_estimate_by_srh.csv',
                  'r',
                  encoding='utf-8') as expected_csv_file:
            expected_csv = expected_csv_file.read()
        with open(_CODEDIR +
                  '/testdata/actual_results/population_estimate_by_srh.csv',
                  'r',
                  encoding='utf-8') as actual_csv_file:
            actual_csv = actual_csv_file.read()

        with open(
                _CODEDIR +
                '/testdata/expected_results/population_estimate_by_srh_agg.csv',
                'r',
                encoding='utf-8') as expected_agg_csv_file:
            expected_agg_csv = expected_agg_csv_file.read()
        with open(_CODEDIR +
                  '/testdata/actual_results/population_estimate_by_srh_agg.csv',
                  'r',
                  encoding='utf-8') as actual_agg_csv_file:
            actual_agg_csv = actual_agg_csv_file.read()

        self.assertEqual(expected_csv, actual_csv)
        self.assertEqual(expected_agg_csv, actual_agg_csv)

    def test_create_retry_session(self):
        session = _create_retry_session()
        self.assertIn('DataCommonsImport',
                      session.headers.get('User-Agent', ''))
        adapter = session.get_adapter('https://www2.census.gov')
        self.assertEqual(adapter.max_retries.total, 5)
        self.assertIn(429, adapter.max_retries.status_forcelist)
        self.assertIn(503, adapter.max_retries.status_forcelist)
        session.close()

    def test_download_with_retry_rejects_waf_html(self):
        mock_response = mock.MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/octet-stream'}
        mock_response.iter_content.return_value = [
            b'<html><head><title>Request Rejected</title></head><body>The requested URL was rejected.</body></html>'
        ]
        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_path = os.path.join(tmp_dir, 'test.csv')
            with self.assertRaises(ValueError):
                download_with_retry.__wrapped__(
                    mock_session,
                    'https://www2.census.gov/test.csv',
                    dest_path,
                )
            self.assertFalse(os.path.exists(dest_path))

    @mock.patch('process._head_with_html_retry')
    def test_add_future_year_urls_fallback_to_baseline(self, mock_head):
        mock_head.side_effect = Exception('Connection reset')
        add_future_year_urls()
        expected_url = (
            f'https://www2.census.gov/programs-surveys/popest/datasets/'
            f'2020-{_BASELINE_YEAR}/counties/asrh/cc-est{_BASELINE_YEAR}-alldata.csv'
        )
        downloaded_urls = [
            item['download_path'] for item in process_module._FILES_TO_DOWNLOAD
        ]
        self.assertIn(expected_url, downloaded_urls)


if __name__ == "__main__":
    unittest.main()
