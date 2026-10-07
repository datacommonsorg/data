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
Script to automate the testing for EuroStat Physical Activity process script.
"""

import os
import unittest
import sys
import tempfile
import json
import shutil
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
from absl import flags

# module_dir is the path to where this test is running from.
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(MODULE_DIR, '../../../'))
for path in (_SCRIPTS_DIR, MODULE_DIR):
    if path not in sys.path:
        sys.path.append(path)

# pylint: disable=wrong-import-position
from us_census.pep.us_pep_sex.process import (
    PopulationEstimateBySex,
    _state_latest,
    _download_single_file,
    _create_retry_session,
    add_future_year_urls,
    download_files,
)
import us_census.pep.us_pep_sex.process as sex_proc
# pylint: enable=wrong-import-position

TEST_DATASET_DIR = os.path.join(MODULE_DIR, "test_data", "datasets")
EXPECTED_FILES_DIR = os.path.join(MODULE_DIR, "test_data", "expected_files")


class TestProcess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing.
    The test will be conducted for EuroStat Physical Activity Sample Datasets,
    It will be generating CSV, MCF and TMCF files based on the sample input.
    Comparing the data with the expected files.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir_obj = tempfile.TemporaryDirectory()
        tmp_dir = cls.tmp_dir_obj.name
        cleaned_csv_file_path = os.path.join(tmp_dir, "data.csv")
        mcf_file_path = os.path.join(tmp_dir, "test_census.mcf")
        tmcf_file_path = os.path.join(tmp_dir, "test_census.tmcf")

        base = PopulationEstimateBySex(TEST_DATASET_DIR, cleaned_csv_file_path,
                                       mcf_file_path, tmcf_file_path)
        base.process()

        with open(mcf_file_path, mode='r', encoding="UTF-8") as mcf_file:
            cls.actual_mcf_data = mcf_file.read()

        with open(tmcf_file_path, mode='r', encoding="UTF-8") as tmcf_file:
            cls.actual_tmcf_data = tmcf_file.read()

        with open(cleaned_csv_file_path, mode='r',
                  encoding="utf-8-sig") as csv_file:
            cls.actual_csv_data = csv_file.read()

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir_obj.cleanup()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and expected output files like MCF File
        """
        expected_mcf_file_path = os.path.join(EXPECTED_FILES_DIR,
                                              "population_estimate_sex.mcf")

        expected_tmcf_file_path = os.path.join(EXPECTED_FILES_DIR,
                                               "population_estimate_sex.tmcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        self.assertEqual(expected_mcf_data.strip(),
                         self.actual_mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(),
                         self.actual_tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and expected output files like CSV
        """
        expected_csv_file_path = os.path.join(EXPECTED_FILES_DIR,
                                              "population_estimate_sex.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()
            self.assertEqual(expected_csv_data.strip(),
                             self.actual_csv_data.strip())


class TestStateLatestVintageBoundary(unittest.TestCase):
    """Tests vintage boundary logic in _state_latest."""

    def test_state_latest_boundary_2029(self):
        """Verifies that max_year 2029 (current_year=2030) appends columns up to 2029 without being dropped."""
        header_df = pd.DataFrame(
            [['dummy'] * 34, ['dummy'] * 34,
             [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan] +
             [2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029] +
             [np.nan] * 18])
        data_row = ['Total'] + [1000] * 33
        data_df = pd.DataFrame([data_row])

        with patch('pandas.read_excel', side_effect=[header_df, data_df]):
            res = _state_latest('dummy_sc-est2029-syasex-01.xlsx')

        self.assertIn('Year', res.columns)
        years = res['Year'].unique().tolist()
        self.assertIn('2029', years)
        self.assertIn('geo_ID', res.columns)
        self.assertEqual(res['geo_ID'].iloc[0], 'geoId/01')


class TestDynamicFunctionMapping(unittest.TestCase):
    """Tests dynamic registration of file-to-function mappings up to year 2029."""

    def test_file_to_function_mapping_years_2023_to_2029(self):
        """Tests that national, state, and county future year files (e.g. 2024, 2029) are dispatched correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            for yr in [2024, 2029]:
                open(os.path.join(tmp_dir, f"nc-est{yr}-agesex-res.csv"),
                     'w').close()
                open(os.path.join(tmp_dir, f"sc-est{yr}-syasex-01.xlsx"),
                     'w').close()
                open(os.path.join(tmp_dir, f"cc-est{yr}-agesex-all.csv"),
                     'w').close()

            mock_df = pd.DataFrame({
                'Year': ['2024'],
                'geo_ID': ['geoId/01'],
                'Count_Person_Male': [10],
                'Count_Person_Female': [10],
                'Measurement_Method': ['CensusPEPSurvey']
            })

            with patch('us_census.pep.us_pep_sex.process._national_latest',
                       return_value=mock_df) as mock_nat, \
                 patch('us_census.pep.us_pep_sex.process._state_latest',
                       return_value=mock_df) as mock_st, \
                 patch('us_census.pep.us_pep_sex.process._county_latest',
                       return_value=mock_df) as mock_co:
                loader = PopulationEstimateBySex(
                    tmp_dir, os.path.join(tmp_dir, 'out.csv'),
                    os.path.join(tmp_dir, 'out.mcf'),
                    os.path.join(tmp_dir, 'out.tmcf'))
                loader.process()
                self.assertEqual(mock_nat.call_count, 2)
                self.assertEqual(mock_st.call_count, 2)
                self.assertEqual(mock_co.call_count, 2)


class TestDownloadAndCacheLifecycle(unittest.TestCase):
    """Tests for streaming downloads, temp file cleanup, and cache fallback."""

    def test_download_single_file_success(self):
        """Tests that _download_single_file streams chunks to temp file."""
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'Content-Type': 'application/vnd.ms-excel'}
        mock_resp.iter_content.return_value = [b'data1', b'data2']
        mock_resp.__enter__.return_value = mock_resp
        session.get.return_value = mock_resp

        tmp_path = _download_single_file.__wrapped__(
            session, 'https://census.gov/test.xlsx')
        self.assertTrue(os.path.exists(tmp_path))
        with open(tmp_path, 'rb') as f:
            self.assertEqual(f.read(), b'data1data2')
        os.remove(tmp_path)

    def test_download_single_file_html_error(self):
        """Tests that _download_single_file raises ValueError on HTML error response."""
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'Content-Type': 'text/html; charset=UTF-8'}
        mock_resp.__enter__.return_value = mock_resp
        session.get.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            _download_single_file.__wrapped__(session,
                                              'https://census.gov/test.xlsx')
        self.assertIn('HTML error page', str(ctx.exception))

    def test_download_single_file_cleanup_on_exception(self):
        """Tests that temporary files are deleted if an error occurs mid-stream."""
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.headers = {'Content-Type': 'application/octet-stream'}
        mock_resp.__enter__.return_value = mock_resp

        created_files = []
        original_named_temp = tempfile.NamedTemporaryFile

        def track_temp(*args, **kwargs):
            tf = original_named_temp(*args, **kwargs)
            created_files.append(tf.name)
            return tf

        def failing_iter(*args, **kwargs):
            yield b'chunk1'
            raise IOError('Connection aborted')

        mock_resp.iter_content = failing_iter
        session.get.return_value = mock_resp

        with patch('tempfile.NamedTemporaryFile', side_effect=track_temp):
            with self.assertRaises(IOError):
                _download_single_file.__wrapped__(session,
                                                  'https://census.gov/broken')

        self.assertEqual(len(created_files), 1)
        self.assertFalse(os.path.exists(created_files[0]))

    def test_download_files_cache_fallback(self):
        """Tests that download_files falls back to cached persistent file if network download fails."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            gcs_persistent = os.path.join(tmp_dir, 'gcs_persistent')
            input_dir = os.path.join(tmp_dir, 'input_files')
            os.makedirs(gcs_persistent)
            os.makedirs(input_dir)

            cached_file = os.path.join(gcs_persistent,
                                       'nc-est2024-agesex-res.csv')
            with open(cached_file, 'w') as f:
                f.write('cached_content')

            # Force file to appear expired to trigger download attempt
            os.utime(cached_file, (0, 0))

            files_to_download = [{
                'download_path':
                'https://census.gov/nc-est2024-agesex-res.csv'
            }]

            with patch.object(sex_proc, '_GCS_FOLDER_PERSISTENT_PATH', gcs_persistent), \
                 patch.object(sex_proc, '_INPUT_FILE_PATH', input_dir), \
                 patch.object(sex_proc, '_FILES_TO_DOWNLOAD', files_to_download), \
                 patch.object(sex_proc, '_download_single_file', side_effect=IOError('Network error')), \
                 patch('time.sleep'):
                sex_proc.download_files.__wrapped__()

            dest_file = os.path.join(input_dir, 'nc-est2024-agesex-res.csv')
            self.assertTrue(os.path.exists(dest_file))
            with open(dest_file) as f:
                self.assertEqual(f.read(), 'cached_content')
            self.assertTrue(files_to_download[0]['is_downloaded'])

    def test_add_future_year_urls_gatekeeper_break(self):
        """Tests that add_future_year_urls gatekeeper loop breaks immediately upon finding the first valid year."""
        session = MagicMock()
        head_calls = []

        def mock_head(url, *args, **kwargs):
            head_calls.append(url)
            resp = MagicMock()
            if '2024' in url:
                resp.status_code = 200
                resp.headers = {'Content-Type': 'text/csv'}
            else:
                resp.status_code = 404
                resp.headers = {'Content-Type': 'text/html'}
            return resp

        session.head = mock_head

        with patch.object(sex_proc, 'extract_gcs_info', return_value=('bucket', 'path')), \
             patch.object(sex_proc, 'fetch_skip_urls_from_gcs', return_value=set()), \
             patch.object(sex_proc, '_create_retry_session', return_value=session), \
             patch('time.sleep'):
            sex_proc.add_future_year_urls()

        self.assertTrue(any('2024' in url for url in head_calls))
        self.assertFalse(any('2023' in url for url in head_calls))


if __name__ == "__main__":
    unittest.main()
