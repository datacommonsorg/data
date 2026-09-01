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
        self.test_input_dir = os.path.join(self.test_dir, 'input_file')
        self.test_temp_dir = os.path.join(self.test_dir, 'temp_fema_data')

    def tearDown(self):
        """Remove the temporary directory after tests."""
        if os.path.exists(self.test_dir):
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

    @patch('fema_download.get_total_records')
    def test_download_data_zero_records_fails(self, mock_get_total_records):
        """Test failure when total record count is 0."""
        mock_get_total_records.return_value = 0
        with self.assertRaisesRegex(
                RuntimeError,
                'Download failed: API metadata reported 0 records.'):
            fema_download.download_data(api_url='http://fake-api.com',
                                        temp_dir=self.test_temp_dir,
                                        output_dir=self.test_input_dir)

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_integration(self, mock_get_total_records,
                                       mock_download_file, mock_rmtree):
        """
        Test the integrated logic of downloading, merging, and cleaning up.
        """
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2

        try:
            mock_get_total_records.return_value = 3  # Total records to download

            # Chunk 1 is a "full page" with 2 records.
            chunk1_content = b"headerA,headerB\n1,A\n2,B"
            # Chunk 2 has the remaining 1 record.
            chunk2_content = b"headerA,headerB\n3,C"

            def download_side_effect(url, output_folder, **kwargs):
                util_output_path = os.path.join(output_folder,
                                                "FimaNfipClaims.xlsx")
                if "$skip=0" in url:
                    with open(util_output_path, 'wb') as f:
                        f.write(chunk1_content)
                elif f"$skip={fema_download.PAGE_SIZE}" in url:
                    with open(util_output_path, 'wb') as f:
                        f.write(chunk2_content)
                else:
                    return False
                return True

            mock_download_file.side_effect = download_side_effect

            fema_download.download_data('http://fake-api.com',
                                        self.test_temp_dir,
                                        output_dir=self.test_input_dir)

            final_filepath = os.path.join(self.test_input_dir,
                                          'fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(final_filepath))

            with open(final_filepath, 'rb') as f:
                content = f.read()

            expected_content = b"headerA,headerB\n1,A\n2,B\n3,C"
            self.assertEqual(content.strip(), expected_content)
            self.assertEqual(mock_download_file.call_count, 2)
            mock_rmtree.assert_called_with(self.test_temp_dir)
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    def test_download_data_bulk_success(self, mock_download_file, mock_rmtree):
        """Test successful direct bulk download."""

        def download_side_effect(url, output_folder, **kwargs):
            os.makedirs(output_folder, exist_ok=True)
            with open(os.path.join(output_folder, "FimaNfipClaims.csv"),
                      'wb') as f:
                f.write(b"policyCount,dateOfLoss\n1,2020-01-01\n2,2020-01-02\n")
            return True

        mock_download_file.side_effect = download_side_effect

        fema_download.download_data(
            'http://fake-api.com',
            self.test_temp_dir,
            bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
            output_dir=self.test_input_dir)

        final_filepath = os.path.join(self.test_input_dir,
                                      'fema_nfip_claims.csv')
        self.assertTrue(os.path.exists(final_filepath))
        with open(final_filepath, 'rb') as f:
            content = f.read()
        self.assertEqual(
            content.strip(),
            b"policyCount,dateOfLoss\n1,2020-01-01\n2,2020-01-02")
        mock_download_file.assert_called_once()
        mock_rmtree.assert_called_with(self.test_temp_dir)

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_bulk_failure_fallback(self, mock_get_total_records,
                                                 mock_download_file,
                                                 mock_rmtree):
        """Test fallback to pagination when direct bulk download fails."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 2

            def download_side_effect(url, output_folder, **kwargs):
                if url == 'http://fake-bulk.com/FimaNfipClaims.csv':
                    return False
                util_output_path = os.path.join(output_folder,
                                                "FimaNfipClaims.xlsx")
                with open(util_output_path, 'wb') as f:
                    f.write(b"headerA,headerB\n1,A\n2,B")
                return True

            mock_download_file.side_effect = download_side_effect

            fema_download.download_data(
                'http://fake-api.com',
                self.test_temp_dir,
                bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
                output_dir=self.test_input_dir)

            final_filepath = os.path.join(self.test_input_dir,
                                          'fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(final_filepath))
            with open(final_filepath, 'rb') as f:
                content = f.read()
            self.assertEqual(content.strip(), b"headerA,headerB\n1,A\n2,B")
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_bulk_empty_file_fallback(self,
                                                    mock_get_total_records,
                                                    mock_download_file,
                                                    mock_rmtree):
        """Test fallback to pagination when direct bulk download produces an empty 0-byte file."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 2

            def download_side_effect(url, output_folder, **kwargs):
                if url == 'http://fake-bulk.com/FimaNfipClaims.csv':
                    os.makedirs(output_folder, exist_ok=True)
                    # Write an empty 0-byte file
                    open(os.path.join(output_folder, "FimaNfipClaims.csv"),
                         'wb').close()
                    return True
                util_output_path = os.path.join(output_folder,
                                                "FimaNfipClaims.xlsx")
                with open(util_output_path, 'wb') as f:
                    f.write(b"headerA,headerB\n1,A\n2,B")
                return True

            mock_download_file.side_effect = download_side_effect

            fema_download.download_data(
                'http://fake-api.com',
                self.test_temp_dir,
                bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
                output_dir=self.test_input_dir)

            final_filepath = os.path.join(self.test_input_dir,
                                          'fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(final_filepath))
            with open(final_filepath, 'rb') as f:
                content = f.read()
            self.assertEqual(content.strip(), b"headerA,headerB\n1,A\n2,B")
            self.assertEqual(mock_download_file.call_count, 2)
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_header_only_chunk_no_blank_lines(
            self, mock_get_total_records, mock_download_file, mock_rmtree):
        """Test that a chunk containing only the header does not introduce blank lines and terminates cleanly."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 3

            def download_side_effect(url, output_folder, **kwargs):
                util_output_path = os.path.join(output_folder,
                                                "FimaNfipClaims.xlsx")
                if "$skip=0" in url:
                    with open(util_output_path, 'wb') as f:
                        f.write(b"headerA,headerB\n1,A\n2,B\n")
                else:
                    # Second chunk contains only header
                    with open(util_output_path, 'wb') as f:
                        f.write(b"headerA,headerB\n")
                return True

            mock_download_file.side_effect = download_side_effect

            with self.assertRaisesRegex(
                    RuntimeError,
                    r"Download incomplete: only 2 of 3 records downloaded\."):
                fema_download.download_data('http://fake-api.com',
                                            self.test_temp_dir,
                                            output_dir=self.test_input_dir)

            self.assertEqual(mock_download_file.call_count, 2)

            # Staging merged file should only contain chunk 1 data without extra blank lines
            temp_merged_filepath = os.path.join(self.test_temp_dir,
                                                'merged_fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(temp_merged_filepath))
            with open(temp_merged_filepath, 'rb') as f:
                content = f.read()
            self.assertEqual(content, b"headerA,headerB\n1,A\n2,B\n")
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_bulk_html_fallback(self, mock_get_total_records,
                                              mock_download_file, mock_rmtree):
        """Test fallback to pagination when direct bulk download returns an HTML error page."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 2

            def download_side_effect(url, output_folder, **kwargs):
                if url == 'http://fake-bulk.com/FimaNfipClaims.csv':
                    os.makedirs(output_folder, exist_ok=True)
                    with open(os.path.join(output_folder, "FimaNfipClaims.csv"),
                              'wb') as f:
                        f.write(
                            b"<!DOCTYPE html><html><body>Error 503</body></html>\n"
                        )
                    return True
                util_output_path = os.path.join(output_folder,
                                                "FimaNfipClaims.xlsx")
                with open(util_output_path, 'wb') as f:
                    f.write(b"headerA,headerB\n1,A\n2,B")
                return True

            mock_download_file.side_effect = download_side_effect

            fema_download.download_data(
                'http://fake-api.com',
                self.test_temp_dir,
                bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
                output_dir=self.test_input_dir)

            final_filepath = os.path.join(self.test_input_dir,
                                          'fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(final_filepath))
            with open(final_filepath, 'rb') as f:
                content = f.read()
            self.assertEqual(content.strip(), b"headerA,headerB\n1,A\n2,B")
            self.assertEqual(mock_download_file.call_count, 2)
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_bulk_missing_header_fallback(
            self, mock_get_total_records, mock_download_file, mock_rmtree):
        """Test fallback to pagination when direct bulk download lacks expected CSV headers."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 2

            def download_side_effect(url, output_folder, **kwargs):
                if url == 'http://fake-bulk.com/FimaNfipClaims.csv':
                    os.makedirs(output_folder, exist_ok=True)
                    with open(os.path.join(output_folder, "FimaNfipClaims.csv"),
                              'wb') as f:
                        f.write(b"randomCol1,randomCol2\n1,X\n2,Y\n")
                    return True
                util_output_path = os.path.join(output_folder,
                                                "FimaNfipClaims.xlsx")
                with open(util_output_path, 'wb') as f:
                    f.write(b"headerA,headerB\n1,A\n2,B")
                return True

            mock_download_file.side_effect = download_side_effect

            fema_download.download_data(
                'http://fake-api.com',
                self.test_temp_dir,
                bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
                output_dir=self.test_input_dir)

            final_filepath = os.path.join(self.test_input_dir,
                                          'fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(final_filepath))
            with open(final_filepath, 'rb') as f:
                content = f.read()
            self.assertEqual(content.strip(), b"headerA,headerB\n1,A\n2,B")
            self.assertEqual(mock_download_file.call_count, 2)
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_chunk_different_filename(self, mock_get_total_records,
                                                    mock_download_file,
                                                    mock_rmtree):
        """Test dynamic chunk detection when download utility saves under an arbitrary filename."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 2

            def download_side_effect(url, output_folder, **kwargs):
                # Save under a non-standard filename (not FimaNfipClaims.xlsx)
                custom_output_path = os.path.join(output_folder,
                                                  "custom_chunk_name.csv")
                with open(custom_output_path, 'wb') as f:
                    f.write(b"headerA,headerB\n1,A\n2,B")
                return True

            mock_download_file.side_effect = download_side_effect

            fema_download.download_data('http://fake-api.com',
                                        self.test_temp_dir,
                                        output_dir=self.test_input_dir)

            final_filepath = os.path.join(self.test_input_dir,
                                          'fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(final_filepath))
            with open(final_filepath, 'rb') as f:
                content = f.read()
            self.assertEqual(content.strip(), b"headerA,headerB\n1,A\n2,B")
            self.assertEqual(mock_download_file.call_count, 1)
        finally:
            fema_download.PAGE_SIZE = original_page_size


if __name__ == '__main__':
    unittest.main()
