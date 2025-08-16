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
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json
import sys

# Adjust the path to import the script under test
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_PATH)
import download_script

class DownloadScriptTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.input_files_dir = os.path.join(self.test_dir.name, "input_files")
        os.makedirs(self.input_files_dir, exist_ok=True)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_clean_csv_file(self):
        dummy_content = (
            "This is a description line to be removed.\n"
            "Another line of metadata.\n"
            "year,version,statefips,countyfips,geocat\n"
            "2022,1,01,001,County\n"
        )
        dummy_content_encoded = dummy_content.encode('latin-1')

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, dir=self.test_dir.name) as tmp:
            tmp.write(dummy_content_encoded)
            tmp_path = tmp.name

        download_script.clean_csv_file(tmp_path)

        with open(tmp_path, 'r', encoding='latin-1') as f:
            cleaned_content = f.read()

        expected_content = (
            "year,version,statefips,countyfips,geocat\n"
            "2022,1,01,001,County\n"
        )
        self.assertEqual(cleaned_content, expected_content)

    @patch('download_script.storage.Client')
    @patch('download_script.download_file')
    @patch('download_script.datetime')
    @patch('download_script.clean_csv_file')
    def test_main_success(self, mock_clean, mock_datetime, mock_download, mock_storage_client):
        mock_datetime.datetime.now.return_value.year = 2020

        def side_effect_download(url, output_folder, **kwargs):
            year = url.split('/')[-1].replace('.zip', '')
            dummy_csv_path = os.path.join(output_folder, f"sahie_{year}.csv")
            with open(dummy_csv_path, 'w') as f:
                f.write("dummy_data")
            return True
        
        mock_download.side_effect = side_effect_download

        mock_blob = MagicMock()
        config_data = {"CensusSAHIE": {"source_url": "gs://fake-bucket/data/{year}.zip"}}
        mock_blob.download_as_string.return_value = json.dumps(config_data)
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        with patch('os.getcwd', return_value=self.test_dir.name):
            os.chdir(self.test_dir.name)
            download_script.main(None)
            os.chdir(_SCRIPT_PATH)

        self.assertEqual(mock_download.call_count, 3)
        self.assertEqual(mock_clean.call_count, 3)

    @patch('download_script.storage.Client')
    @patch('download_script.download_file', return_value=False)
    @patch('download_script.datetime')
    @patch('absl.logging.fatal')
    def test_main_download_failure(self, mock_logging_fatal, mock_datetime, mock_download, mock_storage_client):
        mock_datetime.datetime.now.return_value.year = 2020

        mock_blob = MagicMock()
        config_data = {"CensusSAHIE": {"source_url": "http://fake.url/{year}.zip"}}
        mock_blob.download_as_string.return_value = json.dumps(config_data)
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        with self.assertRaises(SystemExit) as cm:
            with patch('os.getcwd', return_value=self.test_dir.name):
                os.chdir(self.test_dir.name)
                download_script.main(None)
                os.chdir(_SCRIPT_PATH)
        
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(mock_download.call_count, 1)
        mock_logging_fatal.assert_called_with("Failed to download data for the following years: [2018]")

if __name__ == '__main__':
    unittest.main()
