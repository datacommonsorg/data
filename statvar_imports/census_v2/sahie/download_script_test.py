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
from unittest.mock import patch, MagicMock, mock_open
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
        """
        Tests the clean_csv_file function to ensure it correctly
        removes the pre-header lines from a CSV file.
        """
        # Create a dummy CSV file with a pre-header
        dummy_content = (
            "This is a description line to be removed.\n"
            "Another line of metadata.\n"
            "year,version,statefips,countyfips,geocat\n"
            "2022,1,01,001,County\n"
            "2022,1,01,003,County\n"
        )
        
        # Use latin-1 encoding as in the original script
        dummy_content_encoded = dummy_content.encode('latin-1')

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, dir=self.test_dir.name) as tmp:
            tmp.write(dummy_content_encoded)
            tmp_path = tmp.name

        # Run the function
        download_script.clean_csv_file(tmp_path)

        # Read the cleaned file and assert its content
        with open(tmp_path, 'r', encoding='latin-1') as f:
            cleaned_content = f.read()

        expected_content = (
            "year,version,statefips,countyfips,geocat\n"
            "2022,1,01,001,County\n"
            "2022,1,01,003,County\n"
        )
        self.assertEqual(cleaned_content, expected_content)

    @patch('download_script.download_file')
    @patch('download_script.datetime')
    @patch('download_script.clean_csv_file')
    @patch('os.makedirs')
    def test_main_local_config(self, mock_makedirs, mock_clean, mock_datetime, mock_download):
        """
        Tests the main function with a local configuration file.
        """
        # Mock datetime to control the year range
        mock_datetime.datetime.now.return_value.year = 2020
        
        # Mock download_file to simulate success and create a dummy file
        def side_effect_download(url, output_folder, **kwargs):
            year = url.split('/')[-1].replace('.zip', '')
            # Create a dummy CSV file that would have been unzipped
            dummy_csv_path = os.path.join(output_folder, f"sahie_{year}.csv")
            with open(dummy_csv_path, 'w') as f:
                f.write("dummy_data")
            # Create a dummy zip file to test cleanup
            dummy_zip_path = os.path.join(output_folder, f"{year}.zip")
            with open(dummy_zip_path, 'w') as f:
                f.write("zip_data")
            return True
        
        mock_download.side_effect = side_effect_download

        # Create a temporary config file
        config_data = {
            "CensusSAHIE": {
                "source_url": "http://fake.census.gov/{year}.zip"
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=self.test_dir.name, suffix=".json") as tmp:
            json.dump(config_data, tmp)
            config_path = tmp.name

        # Run the main function, overriding the config path and working directory
        with patch('sys.argv', ['download_script.py', f'--config_file_path={config_path}']):
            download_script.FLAGS(sys.argv)
            with patch('os.getcwd', return_value=self.test_dir.name):
                 # Change CWD for the scope of this test
                os.chdir(self.test_dir.name)
                download_script.main(None)
                # Revert CWD
                os.chdir(_SCRIPT_PATH)


        # Assertions
        self.assertEqual(mock_download.call_count, 3) # 2018, 2019, 2020
        mock_download.assert_any_call(url='http://fake.census.gov/2018.zip', output_folder='input_files', unzip=True, tries=5, delay=10)
        mock_download.assert_any_call(url='http://fake.census.gov/2020.zip', output_folder='input_files', unzip=True, tries=5, delay=10)
        
        self.assertEqual(mock_clean.call_count, 3)
        mock_clean.assert_any_call(os.path.join('input_files', 'sahie_2018.csv'))
        mock_clean.assert_any_call(os.path.join('input_files', 'sahie_2020.csv'))

        # Check that zip files were removed
        self.assertFalse(os.path.exists(os.path.join(self.input_files_dir, "2018.zip")))
        self.assertFalse(os.path.exists(os.path.join(self.input_files_dir, "2020.zip")))


    @patch('download_script.storage.Client')
    @patch('download_script.download_file')
    @patch('download_script.datetime')
    @patch('download_script.clean_csv_file')
    def test_main_gcs_config(self, mock_clean, mock_datetime, mock_download, mock_storage_client):
        """
        Tests the main function with a GCS configuration path.
        """
        # Mock datetime
        mock_datetime.datetime.now.return_value.year = 2019

        # Mock download_file to simulate success and create a dummy file
        def side_effect_download(url, output_folder, **kwargs):
            year = url.split('/')[-1].replace('.zip', '')
            # Create a dummy CSV file that would have been unzipped
            dummy_csv_path = os.path.join(output_folder, f"sahie_{year}.csv")
            with open(dummy_csv_path, 'w') as f:
                f.write("dummy_data")
            return True
        
        mock_download.side_effect = side_effect_download

        # Mock GCS client
        mock_blob = MagicMock()
        config_data = {
            "CensusSAHIE": {
                "source_url": "gs://fake-bucket/data/{year}.zip"
            }
        }
        mock_blob.download_as_string.return_value = json.dumps(config_data)
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        # Run main with a GCS path
        with patch('sys.argv', ['download_script.py', '--config_file_path=gs://test-bucket/config.json']):
             download_script.FLAGS(sys.argv)
             with patch('os.getcwd', return_value=self.test_dir.name):
                os.chdir(self.test_dir.name)
                download_script.main(None)
                os.chdir(_SCRIPT_PATH)

        # Assertions
        self.assertEqual(mock_download.call_count, 2) # 2018, 2019
        mock_download.assert_any_call(url='gs://fake-bucket/data/2018.zip', output_folder='input_files', unzip=True, tries=5, delay=10)
        mock_download.assert_any_call(url='gs://fake-bucket/data/2019.zip', output_folder='input_files', unzip=True, tries=5, delay=10)
        self.assertEqual(mock_clean.call_count, 2)

    @patch('download_script.download_file', return_value=False)
    @patch('download_script.datetime')
    @patch('absl.logging.warning')
    def test_main_download_failure(self, mock_logging_warning, mock_datetime, mock_download):
        """
        Tests that the script stops if a download fails.
        """
        mock_datetime.datetime.now.return_value.year = 2020
        
        # Create a dummy local config
        config_data = {"CensusSAHIE": {"source_url": "http://fake.url/{year}.zip"}}
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=self.test_dir.name, suffix=".json") as tmp:
            json.dump(config_data, tmp)
            config_path = tmp.name

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', ['download_script.py', f'--config_file_path={config_path}']):
                download_script.FLAGS(sys.argv)
                with patch('os.getcwd', return_value=self.test_dir.name):
                    os.chdir(self.test_dir.name)
                    download_script.main(None)
                    os.chdir(_SCRIPT_PATH)
        self.assertEqual(cm.exception.code, 1)
        # Assert that download was only attempted once and a warning was logged
        self.assertEqual(mock_download.call_count, 1)
        mock_logging_warning.assert_called_with("Failed to download or process data for year 2018. Stopping further downloads.")

if __name__ == '__main__':
    unittest.main()
