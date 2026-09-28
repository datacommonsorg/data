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
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import fema_download


class FemaDownloadTest(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Remove the temporary directory after tests."""
        shutil.rmtree(self.test_dir)

    @patch('fema_download._retry_method')
    def test_get_total_records_success(self, mock_retry_method):
        """Test successful retrieval of total records with retries and top=1."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'metadata': {'count': 12345}}
        mock_retry_method.return_value = mock_response

        total = fema_download.get_total_records('http://fake-api.com')
        self.assertEqual(total, 12345)
        mock_retry_method.assert_called_once_with(
            'http://fake-api.com?$top=1&$count=true',
            headers=None,
            tries=5,
            delay=5,
            backoff=2)

    @patch('fema_download._retry_method')
    def test_get_total_records_request_fails(self, mock_retry_method):
        """Test failure due to a request exception after retries exhausted."""
        mock_retry_method.side_effect = requests.exceptions.RequestException
        with self.assertRaisesRegex(RuntimeError,
                                    'Failed to get total record count.'):
            fema_download.get_total_records('http://fake-api.com')

    @patch('fema_download._retry_method')
    def test_get_total_records_parsing_fails(self, mock_retry_method):
        """Test failure due to parsing a malformed response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'metadata': {}}  # Missing 'count'
        mock_retry_method.return_value = mock_response
        with self.assertRaisesRegex(
                RuntimeError,
                'Failed to parse the total record count from the response.'):
            fema_download.get_total_records('http://fake-api.com')

    @patch('fema_download._retry_method')
    def test_get_total_records_zero_raises(self, mock_retry_method):
        """Test failure when API returns zero total records."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'metadata': {'count': 0}}
        mock_retry_method.return_value = mock_response
        with self.assertRaisesRegex(RuntimeError,
                                    'Invalid total record count from API: 0'):
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

            # Chunk 1 is a "full page" with 2 records, ending in trailing newline.
            chunk1_content = b"headerA,headerB\n1,A\n2,B\n"
            # Chunk 2 has the remaining 1 record, ending in trailing newline.
            chunk2_content = b"headerA,headerB\n3,C\n"

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
            output_dir = os.path.join(self.test_dir, 'input_file')
            temp_dir = os.path.join(self.test_dir, 'temp_fema_data')
            try:
                fema_download.download_data('http://fake-api.com',
                                            temp_dir,
                                            output_dir=output_dir)

                # Verify the final merged file exists and has the correct content
                final_filepath = os.path.join(output_dir,
                                              'fema_nfip_claims.csv')
                self.assertTrue(os.path.exists(final_filepath))

                with open(final_filepath, 'rb') as f:
                    content = f.read()

                # Should contain clean concatenated records without double newlines
                expected_content = b"headerA,headerB\n1,A\n2,B\n3,C\n"
                self.assertEqual(content, expected_content)
                self.assertNotIn(b"\n\n", content)

                # Verify that download_file was called twice
                self.assertEqual(mock_download_file.call_count, 2)

                # Verify the temporary directory was removed
                mock_rmtree.assert_called_with(temp_dir)

            finally:
                # Restore the original working directory
                os.chdir(original_cwd)
        finally:
            # Restore the original PAGE_SIZE to avoid side effects in other tests
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_bulk_success(self, mock_get_total_records,
                                        mock_download_file, mock_rmtree):
        """Test successful direct bulk download bypassing pagination."""
        mock_get_total_records.return_value = 1

        def mock_download(url, output_folder, **kwargs):
            out_file = os.path.join(output_folder, "FimaNfipClaims.csv")
            with open(out_file, "w", encoding="utf-8") as f:
                f.write("dateOfLoss,yearOfLoss,state\n2020-05-10,2020,CA\n")
            return True

        mock_download_file.side_effect = mock_download
        output_dir = os.path.join(self.test_dir, 'input_file')
        temp_dir = os.path.join(self.test_dir, 'temp_fema_data')
        fema_download.download_data(
            api_url='http://fake-api.com',
            temp_dir=temp_dir,
            bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
            output_dir=output_dir,
            min_bulk_size=10)
        final_filepath = os.path.join(output_dir, 'fema_nfip_claims.csv')
        self.assertTrue(os.path.exists(final_filepath))
        with open(final_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content.strip(),
                         "dateOfLoss,yearOfLoss,state\n2020-05-10,2020,CA")
        mock_download_file.assert_called_once()
        mock_get_total_records.assert_called_once()

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_bulk_failure_falls_back_to_pagination(
            self, mock_get_total_records, mock_download_file, mock_rmtree):
        """Test that bulk download failure falls back to API pagination."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 2

            def side_effect(url, output_folder, **kwargs):
                if url.startswith("http://fake-bulk.com/"):
                    return False
                if "$skip=0" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n1,A\n2,B")
                    return True
                elif "$skip=" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n")
                    return True
                return False

            mock_download_file.side_effect = side_effect
            output_dir = os.path.join(self.test_dir, 'input_file')
            temp_dir = os.path.join(self.test_dir, 'temp_fema_data')

            fema_download.download_data(
                api_url='http://fake-api.com',
                temp_dir=temp_dir,
                bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
                output_dir=output_dir)

            final_filepath = os.path.join(output_dir, 'fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(final_filepath))
            with open(final_filepath, 'rb') as f:
                content = f.read()
            self.assertEqual(content.strip(), b"headerA,headerB\n1,A\n2,B")
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_bulk_zero_bytes_fallback(self,
                                                    mock_get_total_records,
                                                    mock_download_file,
                                                    mock_rmtree):
        """Test that 0-byte bulk download falls back to API pagination."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 2

            def side_effect(url, output_folder, **kwargs):
                if url.startswith("http://fake-bulk.com/"):
                    with open(os.path.join(output_folder, "empty.csv"),
                              'wb') as f:
                        pass
                    return True
                if "$skip=0" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n1,A\n2,B")
                    return True
                elif "$skip=" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n")
                    return True
                return False

            mock_download_file.side_effect = side_effect
            output_dir = os.path.join(self.test_dir, 'input_file')
            temp_dir = os.path.join(self.test_dir, 'temp_fema_data')

            fema_download.download_data(
                api_url='http://fake-api.com',
                temp_dir=temp_dir,
                bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
                output_dir=output_dir)

            final_filepath = os.path.join(output_dir, 'fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(final_filepath))
            with open(final_filepath, 'rb') as f:
                content = f.read()
            self.assertEqual(content.strip(), b"headerA,headerB\n1,A\n2,B")
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_bulk_missing_header_fallback(
            self, mock_get_total_records, mock_download_file, mock_rmtree):
        """Test that bulk download missing expected header falls back to pagination."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 2

            def side_effect(url, output_folder, **kwargs):
                if url.startswith("http://fake-bulk.com/"):
                    with open(os.path.join(output_folder, "html_error.csv"),
                              'w') as f:
                        f.write(
                            "<html><body>500 Internal Error</body></html>\n" *
                            100)
                    return True
                if "$skip=0" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n1,A\n2,B")
                    return True
                elif "$skip=" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n")
                    return True
                return False

            mock_download_file.side_effect = side_effect
            output_dir = os.path.join(self.test_dir, 'input_file')
            temp_dir = os.path.join(self.test_dir, 'temp_fema_data')

            fema_download.download_data(
                api_url='http://fake-api.com',
                temp_dir=temp_dir,
                bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
                output_dir=output_dir,
                min_bulk_size=10)

            final_filepath = os.path.join(output_dir, 'fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(final_filepath))
            with open(final_filepath, 'rb') as f:
                content = f.read()
            self.assertEqual(content.strip(), b"headerA,headerB\n1,A\n2,B")
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_bulk_too_small_fallback(self,
                                                   mock_get_total_records,
                                                   mock_download_file,
                                                   mock_rmtree):
        """Test that bulk download below min_size threshold falls back to pagination."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 2

            def side_effect(url, output_folder, **kwargs):
                if url.startswith("http://fake-bulk.com/"):
                    with open(os.path.join(output_folder, "small.csv"),
                              'w') as f:
                        f.write("dateOfLoss\n2020\n")  # Only ~16 bytes
                    return True
                if "$skip=0" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n1,A\n2,B")
                    return True
                elif "$skip=" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n")
                    return True
                return False

            mock_download_file.side_effect = side_effect
            output_dir = os.path.join(self.test_dir, 'input_file')
            temp_dir = os.path.join(self.test_dir, 'temp_fema_data')

            fema_download.download_data(
                api_url='http://fake-api.com',
                temp_dir=temp_dir,
                bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
                output_dir=output_dir,
                min_bulk_size=1024)  # requires >= 1 KB

            final_filepath = os.path.join(output_dir, 'fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(final_filepath))
            with open(final_filepath, 'rb') as f:
                content = f.read()
            self.assertEqual(content.strip(), b"headerA,headerB\n1,A\n2,B")
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_bulk_truncated_falls_back_to_pagination(
            self, mock_get_total_records, mock_download_file, mock_rmtree):
        """Test that bulk download with fewer rows than expected falls back to pagination."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 2

            def side_effect(url, output_folder, **kwargs):
                if url.startswith("http://fake-bulk.com/"):
                    with open(os.path.join(output_folder, "truncated.csv"),
                              'w') as f:
                        f.write(
                            "dateOfLoss,yearOfLoss,state\n2020-05-10,2020,CA\n"
                        )
                    return True
                if "$skip=0" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n1,A\n2,B")
                    return True
                elif "$skip=" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n")
                    return True
                return False

            mock_download_file.side_effect = side_effect
            output_dir = os.path.join(self.test_dir, 'input_file')
            temp_dir = os.path.join(self.test_dir, 'temp_fema_data')

            fema_download.download_data(
                api_url='http://fake-api.com',
                temp_dir=temp_dir,
                bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
                output_dir=output_dir,
                min_bulk_size=10)

            final_filepath = os.path.join(output_dir, 'fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(final_filepath))
            with open(final_filepath, 'rb') as f:
                content = f.read()
            self.assertEqual(content.strip(), b"headerA,headerB\n1,A\n2,B")
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_pagination_incomplete_raises_error(
            self, mock_get_total_records, mock_download_file, mock_rmtree):
        """Test that incomplete download (fewer records than total) raises RuntimeError."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 10
        try:
            mock_get_total_records.return_value = 100

            def side_effect(url, output_folder, **kwargs):
                util_out = os.path.join(output_folder, "FimaNfipClaims.xlsx")
                with open(util_out, 'wb') as f:
                    f.write(b"headerA,headerB\n1,A\n2,B")
                return True

            mock_download_file.side_effect = side_effect
            output_dir = os.path.join(self.test_dir, 'input_file')
            temp_dir = os.path.join(self.test_dir, 'temp_fema_data')

            with self.assertRaises(RuntimeError):
                fema_download.download_data(api_url='http://fake-api.com',
                                            temp_dir=temp_dir,
                                            output_dir=output_dir)
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_ioerror_raises(self, mock_get_total_records,
                                          mock_download_file, mock_rmtree):
        """Test that IOError during chunk writing is re-raised."""
        mock_get_total_records.return_value = 2

        def side_effect(url, output_folder, **kwargs):
            util_out = os.path.join(output_folder, "FimaNfipClaims.xlsx")
            with open(util_out, 'wb') as f:
                f.write(b"headerA,headerB\n1,A\n2,B")
            return True

        mock_download_file.side_effect = side_effect
        output_dir = os.path.join(self.test_dir, 'input_file')
        temp_dir = os.path.join(self.test_dir, 'temp_fema_data')

        real_open = open

        def open_side_effect(path, mode='r', *args, **kwargs):
            if 'staging_fema_nfip_claims.csv' in str(path):
                raise IOError("Disk write error")
            return real_open(path, mode, *args, **kwargs)

        with patch('builtins.open', side_effect=open_side_effect):
            with self.assertRaises(IOError):
                fema_download.download_data(api_url='http://fake-api.com',
                                            temp_dir=temp_dir,
                                            output_dir=output_dir)

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.get_total_records')
    def test_download_data_zero_total_records_raises_error(
            self, mock_get_total_records, mock_rmtree):
        """Test that get_total_records returning 0 causes download_data to fail fast."""
        mock_get_total_records.return_value = 0
        output_dir = os.path.join(self.test_dir, 'input_file')
        temp_dir = os.path.join(self.test_dir, 'temp_fema_data')
        with self.assertRaises(RuntimeError):
            fema_download.download_data(api_url='http://fake-api.com',
                                        temp_dir=temp_dir,
                                        output_dir=output_dir)

    def test_is_valid_bulk_file_within_tolerance(self):
        """Test that bulk files within 2% tolerance margin are accepted."""
        test_file = os.path.join(self.test_dir, 'tolerance_test.csv')
        # Create CSV with header + 99 data rows
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("dateOfLoss,yearOfLoss,state\n")
            for i in range(99):
                f.write(f"2020-05-10,2020,CA\n")

        # When expecting 100 records, 99 is >= 98 (98%), so it should be valid
        self.assertTrue(
            fema_download._is_valid_bulk_file(test_file,
                                              min_size=10,
                                              expected_records=100))

        # When expecting 105 records, 99 is < 102.9, so it should be rejected
        self.assertFalse(
            fema_download._is_valid_bulk_file(test_file,
                                              min_size=10,
                                              expected_records=105))

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_bulk_failure_reuses_total_records_without_second_call(
            self, mock_get_total_records, mock_download_file, mock_rmtree):
        """Test that get_total_records is called only once when falling back from bulk to pagination."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 2

            def side_effect(url, output_folder, **kwargs):
                if url.startswith("http://fake-bulk.com/"):
                    # Bulk file downloads but has 0 data rows (fails tolerance against expected 2)
                    out_file = os.path.join(output_folder,
                                            "FimaNfipClaims.csv")
                    with open(out_file, "w", encoding="utf-8") as f:
                        f.write("dateOfLoss,yearOfLoss,state\n")
                    return True
                if "$skip=0" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n1,A\n2,B")
                    return True
                elif "$skip=" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n")
                    return True
                return False

            mock_download_file.side_effect = side_effect
            output_dir = os.path.join(self.test_dir, 'input_file')
            temp_dir = os.path.join(self.test_dir, 'temp_fema_data')

            fema_download.download_data(
                api_url='http://fake-api.com',
                temp_dir=temp_dir,
                bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
                output_dir=output_dir,
                min_bulk_size=10)

            # mock_get_total_records should only have been called ONCE (during bulk validation and reused in pagination)
            self.assertEqual(mock_get_total_records.call_count, 1)
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_bulk_count_api_failure_falls_back_to_pagination(
            self, mock_get_total_records, mock_download_file, mock_rmtree):
        """Test that failure to get total_records during bulk validation triggers fallback to pagination."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            # First call (during bulk) fails; second call (during pagination) succeeds
            mock_get_total_records.side_effect = [
                RuntimeError("Transient API count error"), 2
            ]

            def side_effect(url, output_folder, **kwargs):
                if url.startswith("http://fake-bulk.com/"):
                    out_file = os.path.join(output_folder,
                                            "FimaNfipClaims.csv")
                    with open(out_file, "w", encoding="utf-8") as f:
                        f.write(
                            "dateOfLoss,yearOfLoss,state\n2020-05-10,2020,CA\n"
                        )
                    return True
                if "$skip=0" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n1,A\n2,B")
                    return True
                elif "$skip=" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n")
                    return True
                return False

            mock_download_file.side_effect = side_effect
            output_dir = os.path.join(self.test_dir, 'input_file')
            temp_dir = os.path.join(self.test_dir, 'temp_fema_data')

            fema_download.download_data(
                api_url='http://fake-api.com',
                temp_dir=temp_dir,
                bulk_url='http://fake-bulk.com/FimaNfipClaims.csv',
                output_dir=output_dir,
                min_bulk_size=10)

            # Verify it fell back to pagination and queried get_total_records twice
            self.assertEqual(mock_get_total_records.call_count, 2)
            final_filepath = os.path.join(output_dir, 'fema_nfip_claims.csv')
            self.assertTrue(os.path.exists(final_filepath))
            with open(final_filepath, 'rb') as f:
                content = f.read()
            self.assertEqual(content, b"headerA,headerB\n1,A\n2,B\n")
        finally:
            fema_download.PAGE_SIZE = original_page_size

    @patch('fema_download.shutil.rmtree')
    @patch('fema_download.download_file')
    @patch('fema_download.get_total_records')
    def test_download_data_pagination_deletes_chunk_files(
            self, mock_get_total_records, mock_download_file, mock_rmtree):
        """Test that chunk files are deleted immediately after appending during pagination."""
        original_page_size = fema_download.PAGE_SIZE
        fema_download.PAGE_SIZE = 2
        try:
            mock_get_total_records.return_value = 2

            def side_effect(url, output_folder, **kwargs):
                if "$skip=0" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n1,A\n2,B")
                    return True
                elif "$skip=" in url:
                    util_out = os.path.join(output_folder,
                                            "FimaNfipClaims.xlsx")
                    with open(util_out, 'wb') as f:
                        f.write(b"headerA,headerB\n")
                    return True
                return False

            mock_download_file.side_effect = side_effect
            output_dir = os.path.join(self.test_dir, 'input_file')
            temp_dir = os.path.join(self.test_dir, 'temp_fema_data')

            # Prevent rmtree so we can verify chunk files were deleted mid-loop
            mock_rmtree.side_effect = lambda path: None

            fema_download.download_data(api_url='http://fake-api.com',
                                        temp_dir=temp_dir,
                                        output_dir=output_dir)

            if os.path.exists(temp_dir):
                chunk_files = [
                    f for f in os.listdir(temp_dir)
                    if f.startswith("FimaNfipClaims_")
                ]
                self.assertEqual(chunk_files, [])
        finally:
            fema_download.PAGE_SIZE = original_page_size


if __name__ == '__main__':
    unittest.main()
