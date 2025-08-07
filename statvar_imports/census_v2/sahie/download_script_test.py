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

import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys
import tempfile
import json
import datetime

# Allows the test to find the module under test
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_PATH)
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util'))

import download_script
from absl import flags

FLAGS = flags.FLAGS

class DownloadScriptTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.input_files_dir = os.path.join(self.test_dir.name, "input_files")
        os.makedirs(self.input_files_dir, exist_ok=True)
        # Parse flags for each test
        FLAGS(sys.argv)


    def tearDown(self):
        self.test_dir.cleanup()

    def test_clean_csv_file(self):
        # Create a dummy CSV with header lines to be removed
        csv_content = (
            "Some descriptive line 1\n"
            "Some descriptive line 2\n"
            "year,version,statefips,countyfips,geocat,agecat,racecat,sexcat,iprcat,NIPR\n"
            "2022,1,01,001,40,0,0,0,0,12345\n"
        )
        csv_path = os.path.join(self.test_dir.name, "test.csv")
        with open(csv_path, "w", encoding="latin-1") as f:
            f.write(csv_content)

        download_script.clean_csv_file(csv_path)

        with open(csv_path, "r", encoding="latin-1") as f:
            cleaned_content = f.read()

        expected_content = (
            "year,version,statefips,countyfips,geocat,agecat,racecat,sexcat,iprcat,NIPR\n"
            "2022,1,01,001,40,0,0,0,0,12345\n"
        )
        self.assertEqual(cleaned_content, expected_content)

    @patch('download_script.storage.Client')
    @patch('download_script.download_file')
    @patch('download_script.datetime')
    @patch('absl.logging.fatal')
    def test_main_gcs_config_success(self, mock_logging_fatal, mock_datetime, mock_download_file, mock_storage_client):
        # Mock datetime to control the year range
        mock_datetime.datetime.now.return_value = datetime.datetime(2020, 1, 1)
        
        # Mock GCS client
        mock_blob = MagicMock()
        mock_blob.download_as_string.return_value = json.dumps({
            "CensusSAHIE": {
                "source_url": "http://fake.url/sahie-{year}.zip"
            }
        })
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        # Mock download_file to simulate success
        mock_download_file.return_value = True

        # Mock os.path.exists to simulate the unzipped file is present
        with patch('os.path.exists', return_value=True):
            # Mock clean_csv_file since it's tested separately
            with patch('download_script.clean_csv_file') as mock_clean_csv:
                # Run main with a GCS path
                FLAGS.config_file_path = 'gs://fake-bucket/config.json'
                download_script.main(None)


        # Assertions
        self.assertEqual(mock_download_file.call_count, 3) # 2018, 2019, 2020
        mock_download_file.assert_any_call(url='http://fake.url/sahie-2018.zip', output_folder='input_files', unzip=True, tries=5, delay=10)
        mock_download_file.assert_any_call(url='http://fake.url/sahie-2020.zip', output_folder='input_files', unzip=True, tries=5, delay=10)
        self.assertEqual(mock_clean_csv.call_count, 3)
        mock_logging_fatal.assert_not_called()

    @patch('download_script.download_file')
    @patch('download_script.datetime')
    @patch('absl.logging.fatal')
    def test_main_local_config_download_failure(self, mock_logging_fatal, mock_datetime, mock_download_file):
        # Mock datetime
        mock_datetime.datetime.now.return_value = datetime.datetime(2019, 1, 1)

        # Mock download_file to simulate failure on the second year
        mock_download_file.side_effect = [True, False]

        # Create a fake local config file
        config_content = json.dumps({
            "CensusSAHIE": {
                "source_url": "http://fake.url/sahie-{year}.zip"
            }
        })
        config_path = os.path.join(self.test_dir.name, 'config.json')
        with open(config_path, 'w') as f:
            f.write(config_content)

        with patch('os.path.exists', return_value=True):
            with patch('download_script.clean_csv_file'):
                FLAGS.config_file_path = config_path
                download_script.main(None)

        # Assertions
        self.assertEqual(mock_download_file.call_count, 2) # 2018 (success), 2019 (failure)
        mock_logging_fatal.assert_called_once_with("Failed to download data for the following years: [2019]")

    @patch('absl.logging.fatal')
    def test_main_local_config_not_found(self, mock_logging_fatal):
        # Run main with a non-existent local path
        FLAGS.config_file_path = '/no/such/file.json'
        download_script.main(None)
        
        mock_logging_fatal.assert_called_once_with("Config file not found at local path: /no/such/file.json")

if __name__ == '__main__':
    unittest.main()
