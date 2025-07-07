# Copyright 2025 Google LLC
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
"""Unit tests for download_and_convert.py script."""

import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import download_and_convert


class DownloadAndConvertTest(unittest.TestCase):

    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'testdata')
        self.temp_dir = tempfile.mkdtemp()
        self.test_json_path = os.path.join(self.test_data_dir, 'financial_incentives_prod_data.json')
        self.test_csv_path = os.path.join(self.temp_dir, 'test_output.csv')
        
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_find_latest_dated_folder(self):
        """Test finding the latest dated folder from GCS."""
        # Mock the storage client and bucket
        with patch('download_and_convert.storage.Client') as mock_client:
            mock_bucket = MagicMock()
            mock_client.return_value.bucket.return_value = mock_bucket
            
            # Mock blobs with different date patterns - fix name attribute
            mock_blobs = []
            blob_names = [
                'source_csv/sustainability_financial_incentives/2025_06_30/file.json',
                'source_csv/sustainability_financial_incentives/2025_07_01/file.json', 
                'source_csv/sustainability_financial_incentives/2025_06_29/file.json',
                'source_csv/sustainability_financial_incentives/invalid_folder/file.json',
            ]
            for name in blob_names:
                mock_blob = MagicMock()
                mock_blob.name = name
                mock_blobs.append(mock_blob)
            
            mock_bucket.list_blobs.return_value = mock_blobs
            
            result = download_and_convert.find_latest_dated_folder('test_bucket', 'source_csv/sustainability_financial_incentives')
            
            self.assertEqual(result, '2025_07_01')
            mock_client.assert_called_once()
            mock_bucket.list_blobs.assert_called_once_with(prefix='source_csv/sustainability_financial_incentives/')

    def test_find_latest_dated_folder_no_folders(self):
        """Test finding latest dated folder when no valid folders exist."""
        with patch('download_and_convert.storage.Client') as mock_client:
            mock_bucket = MagicMock()
            mock_client.return_value.bucket.return_value = mock_bucket
            mock_bucket.list_blobs.return_value = []
            
            result = download_and_convert.find_latest_dated_folder('test_bucket', 'source_csv/sustainability_financial_incentives')
            
            self.assertIsNone(result)


    def test_download_json_file(self):
        """Test downloading JSON file from GCS."""
        with patch('download_and_convert.storage.Client') as mock_client:
            mock_bucket = MagicMock()
            mock_blob = MagicMock()
            mock_client.return_value.bucket.return_value = mock_bucket
            mock_bucket.blob.return_value = mock_blob
            
            local_path = os.path.join(self.temp_dir, 'test_file.json')
            
            result = download_and_convert.download_json_file('test_bucket', 'test/path/file.json', local_path)
            
            self.assertTrue(result)
            mock_client.assert_called_once()
            mock_bucket.blob.assert_called_once_with('test/path/file.json')
            mock_blob.download_to_filename.assert_called_once_with(local_path)


    def test_download_json_file_error(self):
        """Test download JSON file with error."""
        with patch('download_and_convert.storage.Client') as mock_client:
            mock_client.side_effect = Exception("GCS error")
            
            local_path = os.path.join(self.temp_dir, 'test_file.json')
            
            result = download_and_convert.download_json_file('test_bucket', 'test/path/file.json', local_path)
            
            self.assertFalse(result)



    def test_convert_json_to_csv(self):
        """Test converting JSON to CSV and compare with expected output."""
        expected_csv_path = os.path.join(self.test_data_dir, 'expected_output.csv')
        
        result = download_and_convert.convert_json_to_csv(self.test_json_path, self.test_csv_path)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.test_csv_path))
        
        # Compare actual output with expected output
        with open(self.test_csv_path, 'r') as actual_file, \
             open(expected_csv_path, 'r') as expected_file:
            actual_content = actual_file.read().strip()
            expected_content = expected_file.read().strip()
            self.assertEqual(actual_content, expected_content)

    def test_convert_json_to_csv_error(self):
        """Test converting JSON to CSV with error."""
        with patch('download_and_convert.file_json_to_csv') as mock_convert:
            mock_convert.side_effect = Exception("Conversion failed")
            
            result = download_and_convert.convert_json_to_csv(self.test_json_path, self.test_csv_path)
            
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()