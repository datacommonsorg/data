# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import requests

import fema_download


class FemaDownloadTest(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Remove the temporary directory after tests."""
        shutil.rmtree(self.test_dir)

    @patch('fema_download.requests.get')
    def test_get_total_records_success(self, mock_get):
        """Test successful retrieval of total records."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'metadata': {'count': 12345}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        total = fema_download.get_total_records('http://fake-api.com')
        self.assertEqual(total, 12345)
        mock_get.assert_called_once_with('http://fake-api.com?$count=true',
                                         timeout=30)

    @patch('fema_download.requests.get')
    def test_get_total_records_request_fails(self, mock_get):
        """Test failure due to a request exception."""
        mock_get.side_effect = requests.exceptions.RequestException
        with self.assertRaisesRegex(RuntimeError,
                                    'Failed to get total record count.'):
            fema_download.get_total_records('http://fake-api.com')

    @patch('fema_download.requests.get')
    def test_get_total_records_parsing_fails(self, mock_get):
        """Test failure due to parsing a malformed response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'metadata': {}}  # Missing 'count'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        with self.assertRaisesRegex(
                RuntimeError,
                'Failed to parse the total record count from the response.'):
            fema_download.get_total_records('http://fake-api.com')

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_integration(self, mock_get_total_records,
                                       mock_download_file, mock_rmtree):
        """
        Test the integrated logic of downloading, merging, and cleaning up.
        """
        # Temporarily change the PAGE_SIZE for this test to a small value
        # to control the pagination logic without creating massive dummy files.
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2

        try:
            mock_get_total_records.return_value = 3  # Total records to download

            # Chunk 1 is a "full page" with 2 records.
            chunk1_content = b"headerA,headerB\n1,A\n2,B"
            # Chunk 2 has the remaining 1 record.
            chunk2_content = b"headerA,headerB\n3,C"

            # This side effect simulates the download_file utility's behavior
            def download_side_effect(url, output_folder, **kwargs):
                util_output_path = os.path.join(output_folder,
                                                "FimaNfipClaims.xlsx")
                # The skip_count in the URL should correspond to the test's PAGE_SIZE
                if "$skip=0" in url:
                    with open(util_output_path, 'wb') as f:
                        f.write(chunk1_content)
                elif f"$skip={fema_download.PAGE_SIZE}" in url:  # e.g., $skip=2
                    with open(util_output_path, 'wb') as f:
                        f.write(chunk2_content)
                else:
                    return False  # Fail for any unexpected URL
                return True

            mock_download_file.side_effect = download_side_effect

            # The function writes to directories relative to the current working directory.
            # We change into our temporary test directory to isolate file operations.
            original_cwd = os.getcwd()
            os.chdir(self.test_dir)

            try:
                fema_download.download_data('http://fake-api.com',
                                            'temp_fema_data')

                # Verify the final merged file exists and has the correct content
                final_filepath = os.path.join('input_file',
                                              'fema_nfip_claims.csv')
                self.assertTrue(os.path.exists(final_filepath))

                with open(final_filepath, 'rb') as f:
                    content = f.read()

                # Should contain the header from the first chunk and data from both
                expected_content = b"headerA,headerB\n1,A\n2,B\n3,C"
                self.assertEqual(content.strip(), expected_content)

                # Verify that download_file was called twice
                self.assertEqual(mock_download_file.call_count, 2)

                # Verify the temporary directory was removed
                mock_rmtree.assert_called_with('temp_fema_data')

            finally:
                # Restore the original working directory
                os.chdir(original_cwd)
        finally:
            # Restore the original PAGE_SIZE to avoid side effects in other tests
            fema_download.PAGE_SIZE = original_page_size


if __name__ == '__main__':
    unittest.main()
