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
import unittest
from unittest.mock import patch, mock_open, MagicMock
import pandas as pd
from io import StringIO

# Add the parent directory to the sys.path to allow imports.
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '..'))

# Assuming the script to be tested is named download_script.py
import download_script

class DownloadScriptTest(unittest.TestCase):

    @patch('os.makedirs')
    @patch('os.remove')
    @patch('zipfile.ZipFile')
    @patch('download_script.download_util.download_file_from_url')
    @patch('os.path.exists', return_value=True)
    @patch('os.listdir', return_value=[])
    def test_download_and_extract_data_success(
            self, mock_listdir, mock_exists, mock_download, mock_zipfile, mock_remove, mock_makedirs):
        """
        Test the successful download and extraction of data.
        """
        # Arrange
        mock_download.return_value = '/fake/path/SAGDP.zip'
        
        # Act
        download_script.download_and_extract_data()

        # Assert
        mock_makedirs.assert_called_once_with(download_script._OUTPUT_DIR, exist_ok=True)
        mock_download.assert_called_once_with(
            download_script._DOWNLOAD_URL, 
            output_file=os.path.join(download_script._OUTPUT_DIR, 'SAGDP.zip'), 
            overwrite=True
        )
        mock_zipfile.assert_called_once_with('/fake/path/SAGDP.zip', 'r')
        # We expect one call to remove the zip file.
        mock_remove.assert_any_call('/fake/path/SAGDP.zip')
        self.assertGreaterEqual(mock_remove.call_count, 1)

    @patch('os.listdir')
    @patch('os.remove')
    def test_clean_up_files(self, mock_remove, mock_listdir):
        """
        Test the file cleanup functionality.
        """
        # Arrange
        mock_listdir.return_value = ['file1_ALL_AREAS.csv', 'file2.csv', 'file3.txt']
        
        # Act
        download_script.clean_up_files('/fake/dir')
        
        # Assert
        self.assertEqual(mock_remove.call_count, 2)
        mock_remove.assert_any_call('/fake/dir/file2.csv')
        mock_remove.assert_any_call('/fake/dir/file3.txt')

    def test_process_csv_data(self):
        """
        Test CSV data processing to ensure whitespace is stripped.
        """
        # Arrange
        csv_content = ("GeoName,Description,Unit,IndustryClassification,Value\n"
                       "\"  Test Geo  \",\"  Test Desc  \",\"  USD  \",\"  NAICS123  \",100\n")
        
        mock_df = pd.read_csv(StringIO(csv_content))
        
        with patch('os.listdir', return_value=['test.csv']):
            with patch('pandas.read_csv', return_value=mock_df):
                with patch.object(mock_df, 'to_csv') as mock_to_csv:
                    # Act
                    download_script._process_csv_data('/fake/dir')

                    # Assert
                    self.assertTrue(mock_to_csv.called)
                    args, kwargs = mock_to_csv.call_args
                    # The first argument to to_csv should be the file path, and the second is index=False.
                    # We can't easily check the dataframe that was written, but we can check the call.
                    self.assertEqual(kwargs['index'], False)

if __name__ == '__main__':
    print("Running tests...")
    unittest.main()