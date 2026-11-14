# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#             https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock
from unittest.mock import patch

# Adjust the path to import the script under test
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_PATH)
sys.modules.pop('download_script', None)
import download_script


class DownloadScriptTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.raw_files_dir = os.path.join(self.test_dir.name, "raw_files")
        self.input_files_dir = os.path.join(self.test_dir.name, "input_files")
        os.makedirs(self.raw_files_dir, exist_ok=True)
        os.makedirs(self.input_files_dir, exist_ok=True)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_clean_csv_file(self):
        dummy_content = (
            "This is a description line to be removed.\n"
            "Fields year, version, statefips, countyfips, geocat are documented below.\n"
            "Year,Version,Statefips,Countyfips,Geocat\n"
            "2022,1,01,001,County\n")
        dummy_content_encoded = dummy_content.encode('utf-8')

        raw_path = os.path.join(self.raw_files_dir, "sahie-2022.csv")
        out_path = os.path.join(self.input_files_dir, "sahie-2022.csv")
        with open(raw_path, 'wb') as f:
            f.write(dummy_content_encoded)

        download_script.clean_csv_file(raw_path, out_path)

        with open(out_path, 'r', encoding='utf-8') as f:
            cleaned_content = f.read()
        with open(raw_path, 'r', encoding='utf-8') as f:
            preserved_raw = f.read()

        expected_content = ("Year,Version,Statefips,Countyfips,Geocat\n"
                            "2022,1,01,001,County\n")
        self.assertEqual(cleaned_content, expected_content)
        self.assertEqual(preserved_raw, dummy_content)

    def test_clean_csv_file_latin1_encoding(self):
        dummy_content = (
            "SAHIE preamble note - Doña Ana County.\n"
            "year,version,statefips,countyfips,geocat,county_name\n"
            "2022,1,35,013,50,Doña Ana County\n")
        dummy_content_encoded = dummy_content.encode('latin-1')

        with tempfile.NamedTemporaryFile(mode='wb',
                                         delete=False,
                                         dir=self.test_dir.name) as tmp:
            tmp.write(dummy_content_encoded)
            tmp_path = tmp.name

        download_script.clean_csv_file(tmp_path)

        with open(tmp_path, 'r', encoding='utf-8') as f:
            cleaned_content = f.read()

        expected_content = (
            "year,version,statefips,countyfips,geocat,county_name\n"
            "2022,1,35,013,50,Doña Ana County\n")
        self.assertEqual(cleaned_content, expected_content)

    def test_clean_csv_file_missing_header_raises(self):
        dummy_content = "Invalid file content without required header columns\n"
        with tempfile.NamedTemporaryFile(mode='w',
                                         encoding='utf-8',
                                         delete=False,
                                         dir=self.test_dir.name) as tmp:
            tmp.write(dummy_content)
            tmp_path = tmp.name

        with self.assertRaises(RuntimeError):
            download_script.clean_csv_file(tmp_path)

    def test_is_year_url_available_404_returns_false_immediately(self):
        mock_session = Mock()
        mock_response = Mock(status_code=404)
        mock_session.head.return_value = mock_response

        available = download_script._is_year_url_available(
            "https://example.com/sahie-2025-csv.zip",
            session=mock_session,
            tries=3,
            delay=0)

        self.assertFalse(available)
        self.assertEqual(mock_session.head.call_count, 1)

    def test_is_year_url_available_retries_transient_503_then_succeeds(self):
        mock_session = Mock()
        resp_503 = Mock(status_code=503)
        resp_200 = Mock(status_code=200)
        resp_200.raise_for_status.return_value = None
        mock_session.head.side_effect = [resp_503, resp_200]

        available = download_script._is_year_url_available(
            "https://example.com/sahie-2023-csv.zip",
            session=mock_session,
            tries=3,
            delay=0,
            backoff=1)

        self.assertTrue(available)
        self.assertEqual(mock_session.head.call_count, 2)

    def test_is_year_url_available_raises_on_persistent_server_error(self):
        mock_session = Mock()
        resp_503 = Mock(status_code=503)
        mock_session.head.return_value = resp_503

        with self.assertRaises(RuntimeError):
            download_script._is_year_url_available(
                "https://example.com/sahie-2023-csv.zip",
                session=mock_session,
                tries=2,
                delay=0,
                backoff=1)

        self.assertEqual(mock_session.head.call_count, 2)

    @patch.object(download_script, '_is_year_url_available', return_value=True)
    @patch.object(download_script, 'download_file')
    @patch.object(download_script,
                  'clean_csv_file',
                  wraps=download_script.clean_csv_file)
    def test_main_success(self, mock_clean, mock_download, mock_available):

        def side_effect_download(url, output_folder, **kwargs):
            year = url.split('/')[-1].replace('.zip', '').split('-')[1]
            dummy_csv_path = os.path.join(output_folder, f"sahie-{year}.csv")
            dummy_zip_path = os.path.join(output_folder,
                                          f"sahie-{year}-csv.zip")
            with open(dummy_csv_path, 'w') as f:
                f.write("Preamble\nyear,version,statefips,countyfips,geocat\n"
                        f"{year},1,01,000,40\n")
            with open(dummy_zip_path, 'w') as f:
                f.write("dummy_zip")
            return True

        mock_download.side_effect = side_effect_download

        with patch.object(download_script, '_RAW_DIRECTORY',
                          self.raw_files_dir), patch.object(
                              download_script, '_OUTPUT_DIRECTORY',
                              self.input_files_dir), patch.object(
                                  download_script, 'datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value.year = 2023
            download_script.main(None)

        # START_YEAR = 2018, current_year = 2023 -> 6 years (2018..2023).
        self.assertEqual(mock_download.call_count, 6)
        self.assertEqual(mock_clean.call_count, 6)
        # Verify input_files contains only cleaned .csv files and no .zip/.tmp files.
        remaining_files = os.listdir(self.input_files_dir)
        self.assertTrue(
            all(f.endswith('.csv') for f in remaining_files),
            f"Expected only .csv files in input_files, found: {remaining_files}"
        )
        self.assertEqual(len(remaining_files), 6)

    @patch.object(download_script, '_is_year_url_available')
    @patch.object(download_script, 'download_file')
    @patch.object(download_script, 'clean_csv_file')
    @patch('absl.logging.warning')
    def test_main_unpublished_recent_year_stops_gracefully(
            self, mock_logging_warning, mock_clean, mock_download,
            mock_available):

        def side_effect_available(url, **kwargs):
            year = int(url.split('/')[-1].replace('.zip', '').split('-')[1])
            return year <= 2021

        def side_effect_download(url, output_folder, **kwargs):
            year = int(url.split('/')[-1].replace('.zip', '').split('-')[1])
            dummy_csv_path = os.path.join(output_folder, f"sahie-{year}.csv")
            with open(dummy_csv_path, 'w') as f:
                f.write("dummy_data")
            return True

        mock_available.side_effect = side_effect_available
        mock_download.side_effect = side_effect_download

        with patch.object(download_script, '_RAW_DIRECTORY',
                          self.raw_files_dir), patch.object(
                              download_script, '_OUTPUT_DIRECTORY',
                              self.input_files_dir), patch.object(
                                  download_script, 'datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value.year = 2023
            download_script.main(None)

        # 2018..2020 are required (<= 2023 - 3 = 2020), 2021 is available,
        # 2022 returns False from _is_year_url_available and stops before download_file.
        self.assertEqual(mock_download.call_count, 4)
        self.assertEqual(mock_clean.call_count, 4)
        self.assertTrue(mock_logging_warning.called)

    @patch.object(download_script, '_is_year_url_available', return_value=True)
    @patch.object(download_script, 'download_file')
    def test_main_published_recent_year_download_failure_raises_and_cleans_up(
            self, mock_download, mock_available):

        def side_effect_download(url, output_folder, **kwargs):
            year = int(url.split('/')[-1].replace('.zip', '').split('-')[1])
            if year <= 2021:
                with open(os.path.join(output_folder, f"sahie-{year}.csv"),
                          'w') as f:
                    f.write("uncleaned_preamble_data")
                return True
            return False

        mock_download.side_effect = side_effect_download

        with patch.object(download_script, '_RAW_DIRECTORY',
                          self.raw_files_dir), patch.object(
                              download_script, '_OUTPUT_DIRECTORY',
                              self.input_files_dir), patch.object(
                                  download_script, 'datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value.year = 2023
            with self.assertRaises(RuntimeError):
                download_script.main(None)

        # Verify no uncleaned .csv files are written to input_files on failed run.
        self.assertEqual(os.listdir(self.input_files_dir), [])

    @patch.object(download_script, 'download_file', return_value=False)
    @patch('absl.logging.error')
    def test_main_download_failure_on_required_year_raises(
            self, mock_logging_error, mock_download):
        with patch.object(download_script, '_RAW_DIRECTORY',
                          self.raw_files_dir), patch.object(
                              download_script, '_OUTPUT_DIRECTORY',
                              self.input_files_dir), patch.object(
                                  download_script, 'datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value.year = 2021
            with self.assertRaises(RuntimeError):
                download_script.main(None)

        self.assertEqual(mock_download.call_count, 1)
        self.assertTrue(mock_logging_error.called)

    @patch.object(download_script, '_is_year_url_available', return_value=True)
    @patch.object(download_script, 'download_file', return_value=True)
    def test_main_no_csv_files_raises(self, mock_download, mock_available):
        with patch.object(download_script, '_RAW_DIRECTORY',
                          self.raw_files_dir), patch.object(
                              download_script, '_OUTPUT_DIRECTORY',
                              self.input_files_dir), patch.object(
                                  download_script, 'datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value.year = 2018
            with self.assertRaises(RuntimeError):
                download_script.main(None)


if __name__ == '__main__':
    unittest.main()
