# Copyright 2026 Google LLC
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
"""Tests for download.py of the CDC Natality import automation."""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_PATH not in sys.path:
    sys.path.append(_SCRIPT_PATH)

import download


class DownloadTest(unittest.TestCase):

    def test_chrome_options_configuration(self):
        """Verifies Chrome options include headless, sandbox, and download prefs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch('download.webdriver.Chrome') as mock_chrome:
                mock_driver = MagicMock()
                mock_chrome.return_value = mock_driver

                driver = download.create_chrome_driver(tmp_dir, headless=True)
                mock_chrome.assert_called_once()
                call_kwargs = mock_chrome.call_args[1]
                options = call_kwargs['options']
                self.assertIn('--headless=new', options.arguments)
                self.assertIn('--no-sandbox', options.arguments)
                self.assertIn('--disable-dev-shm-usage', options.arguments)
                mock_driver.execute_cdp_cmd.assert_called_once_with(
                    'Page.setDownloadBehavior', {
                        'behavior': 'allow',
                        'downloadPath': tmp_dir
                    })

    @patch('download.time.sleep', return_value=None)
    def test_download_natality_dataset_timeout(self, _):
        """Verifies TimeoutError is raised when file download does not complete."""
        mock_driver = MagicMock()
        mock_element = MagicMock()
        mock_element.tag_name = 'select'
        mock_option = MagicMock()
        mock_element.find_elements.return_value = [mock_option]
        mock_driver.find_element.return_value = mock_element
        mock_driver.find_elements.return_value = [mock_element]

        with tempfile.TemporaryDirectory() as tmp_dl_dir:
            dest_file = os.path.join(tmp_dl_dir, 'out.tsv')
            with self.assertRaises(TimeoutError):
                download.download_natality_dataset(mock_driver,
                                                   geo_level='state',
                                                   download_tmp_dir=tmp_dl_dir,
                                                   dest_path=dest_file,
                                                   timeout=0.1)

    @patch('download.time.sleep', return_value=None)
    def test_download_natality_dataset_success(self, _):
        """Verifies successful download copies file to destination path."""
        mock_driver = MagicMock()
        mock_element = MagicMock()
        mock_element.tag_name = 'select'
        mock_option = MagicMock()
        mock_element.find_elements.return_value = [mock_option]
        mock_driver.find_element.return_value = mock_element
        mock_driver.find_elements.return_value = [mock_element]

        with tempfile.TemporaryDirectory() as tmp_dl_dir:
            dest_dir = os.path.join(tmp_dl_dir, 'dest')
            dest_file = os.path.join(dest_dir, 'state_raw.tsv')

            # Create mock downloaded file in download directory
            simulated_file = os.path.join(tmp_dl_dir, 'downloaded.tsv')
            with open(simulated_file, 'w', encoding='utf-8') as f:
                f.write(
                    '"Notes"\t"State"\t"Year"\tBirths\n\t"01"\t"2024"\t50000\n')

            # Patch os.remove to prevent removing the simulated downloaded file
            with patch('os.remove', side_effect=lambda p: None):
                download.download_natality_dataset(mock_driver,
                                                   geo_level='state',
                                                   download_tmp_dir=tmp_dl_dir,
                                                   dest_path=dest_file,
                                                   timeout=5)

            self.assertTrue(os.path.exists(dest_file))
            self.assertGreater(os.path.getsize(dest_file), 0)

    @patch('download.subprocess.run')
    @patch('download.shutil.which', return_value='/usr/bin/gcloud')
    def test_download_historical_baseline(self, mock_which, mock_run):
        """Verifies download_historical_baseline queries snapshots and calls gcloud cp."""
        mock_res_ls = MagicMock()
        mock_res_ls.stdout = 'gs://unresolved_mcf/cdc/wonder/natality/country/20231215/\n'
        mock_res_cp = MagicMock()
        mock_run.side_effect = [
            mock_res_ls, mock_res_cp, mock_res_ls, mock_res_cp, mock_res_ls,
            mock_res_cp
        ]

        with tempfile.TemporaryDirectory() as tmp_out:
            download.download_historical_baseline(tmp_out)
            self.assertEqual(mock_run.call_count, 6)

    @patch('download.shutil.which', return_value='/usr/bin/gcloud')
    def test_download_historical_baseline_idempotent_prefix(self, mock_which):
        """Verifies idempotent prefixing in download_historical_baseline."""
        mock_res_ls = MagicMock()
        mock_res_ls.stdout = 'gs://unresolved_mcf/cdc/wonder/natality/country/20231215/\n'

        def fake_run(cmd, **kwargs):
            if 'ls' in cmd:
                return mock_res_ls
            if 'cp' in cmd:
                dest_dir = cmd[-1]
                with open(os.path.join(dest_dir, 'country_baseline.csv'),
                          'w') as f:
                    f.write('Year,StatVar,Quantity\n')
                return MagicMock()
            return MagicMock()

        with tempfile.TemporaryDirectory() as tmp_out:
            with patch('download.subprocess.run', side_effect=fake_run):
                download.download_historical_baseline(tmp_out)
            self.assertTrue(
                os.path.exists(os.path.join(tmp_out, 'country_baseline.csv')))
            self.assertFalse(
                os.path.exists(
                    os.path.join(tmp_out, 'country_country_baseline.csv')))

    @patch('download.shutil.which', return_value=None)
    @patch('download.logging.fatal')
    def test_download_historical_baseline_missing_gcloud(
            self, mock_fatal, mock_which):
        """Verifies fatal error when gcloud CLI is missing."""
        with tempfile.TemporaryDirectory() as tmp_out:
            download.download_historical_baseline(tmp_out)
            mock_fatal.assert_called_once()
            self.assertIn('gcloud CLI not found', mock_fatal.call_args[0][0])

    @patch('download.download_historical_baseline')
    @patch('download.create_chrome_driver')
    @patch('download.download_natality_dataset')
    @patch('download.logging.fatal')
    @patch('download.time.sleep', return_value=None)
    def test_download_all_retries_and_fatal_failure(self, mock_sleep,
                                                    mock_fatal, mock_download,
                                                    mock_driver, mock_baseline):
        """Verifies download_all retries up to max_retries before logging fatal."""
        mock_download.side_effect = RuntimeError('Download connection error')
        with tempfile.TemporaryDirectory() as tmp_out:
            download.download_all(tmp_out, max_retries=3, timeout=1)
            self.assertEqual(mock_download.call_count, 3)
            mock_fatal.assert_called_once()


if __name__ == '__main__':
    unittest.main()
