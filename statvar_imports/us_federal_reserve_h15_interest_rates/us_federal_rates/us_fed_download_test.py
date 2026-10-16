# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
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

import us_fed_download

VALID_CSV_CONTENT = (
    b"Series Description,Federal funds effective rate\n"
    b"Unit:,Percent:_Per_Year\n"
    b"Multiplier:,1\n"
    b"Currency:,NA\n"
    b"Unique Identifier: ,H15/H15/RIFSPFF_N.WW\n"
    b"Time Period,RIFSPFF_N.WW\n"
    b"1970-01-07,8.45\n"
    b"1970-01-14,8.96\n"
)

HEADER_ONLY_CSV_CONTENT = (
    b"Series Description,Federal funds effective rate\n"
    b"Unit:,Percent:_Per_Year\n"
    b"Multiplier:,1\n"
    b"Currency:,NA\n"
    b"Unique Identifier: ,H15/H15/RIFSPFF_N.WW\n"
    b"Time Period,RIFSPFF_N.WW\n"
)


class UsFedDownloadTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_input_dir = us_fed_download.INPUT_DIR
        us_fed_download.INPUT_DIR = os.path.join(self.test_dir, "input_files")

    def tearDown(self):
        us_fed_download.INPUT_DIR = self.original_input_dir
        shutil.rmtree(self.test_dir)

    @patch("retry.api.time.sleep")
    @patch("us_fed_download.requests.get")
    def test_retry_method_valid_csv_succeeds(self, mock_get, mock_sleep):
        mock_response = MagicMock()
        mock_response.content = VALID_CSV_CONTENT
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = us_fed_download.retry_method("https://example.com/data.csv")

        self.assertEqual(response.content, VALID_CSV_CONTENT)
        mock_get.assert_called_once_with(
            "https://example.com/data.csv", headers=None, timeout=30
        )
        mock_sleep.assert_not_called()

    @patch("retry.api.time.sleep")
    @patch("us_fed_download.requests.get")
    def test_retry_method_retries_on_empty_or_invalid_content(
        self, mock_get, mock_sleep
    ):
        empty_response = MagicMock()
        empty_response.content = b""
        empty_response.raise_for_status.return_value = None

        html_response = MagicMock()
        html_response.content = b"<html><body>Error</body></html>"
        html_response.raise_for_status.return_value = None

        header_only_response = MagicMock()
        header_only_response.content = HEADER_ONLY_CSV_CONTENT
        header_only_response.raise_for_status.return_value = None

        valid_response = MagicMock()
        valid_response.content = VALID_CSV_CONTENT
        valid_response.raise_for_status.return_value = None

        mock_get.side_effect = [
            empty_response,
            html_response,
            header_only_response,
            valid_response,
        ]

        response = us_fed_download.retry_method("https://example.com/data.csv")

        self.assertEqual(response.content, VALID_CSV_CONTENT)
        self.assertEqual(mock_get.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 3)

    @patch("retry.api.time.sleep")
    @patch("us_fed_download.requests.get")
    def test_retry_method_exhausted_raises_request_exception(
        self, mock_get, mock_sleep
    ):
        empty_response = MagicMock()
        empty_response.content = b""
        empty_response.raise_for_status.return_value = None
        mock_get.return_value = empty_response

        with self.assertRaises(requests.exceptions.RequestException):
            us_fed_download.retry_method("https://example.com/data.csv")

        self.assertEqual(mock_get.call_count, 5)
        self.assertEqual(mock_sleep.call_count, 4)

    @patch("us_fed_download.requests.get")
    def test_download_files_creates_dir_and_writes_files(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = VALID_CSV_CONTENT
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        self.assertFalse(os.path.exists(us_fed_download.INPUT_DIR))
        us_fed_download.download_files(
            ["https://example.com/1?to={}", "https://example.com/2?to={}"]
        )
        self.assertTrue(os.path.exists(us_fed_download.INPUT_DIR))

        file1 = os.path.join(us_fed_download.INPUT_DIR, "us_fed_input_1.csv")
        file2 = os.path.join(us_fed_download.INPUT_DIR, "us_fed_input_2.csv")
        self.assertTrue(os.path.exists(file1))
        self.assertTrue(os.path.exists(file2))
        with open(file1, "rb") as f:
            self.assertEqual(f.read(), VALID_CSV_CONTENT)

    @patch("us_fed_download.logging.fatal")
    @patch("retry.api.time.sleep")
    @patch("us_fed_download.requests.get")
    def test_download_files_exhausted_retries_calls_logging_fatal(
        self, mock_get, mock_sleep, mock_fatal
    ):
        empty_response = MagicMock()
        empty_response.content = b""
        empty_response.raise_for_status.return_value = None
        mock_get.return_value = empty_response

        us_fed_download.download_files(["https://example.com/1?to={}"])

        self.assertEqual(mock_get.call_count, 5)
        mock_fatal.assert_called_once()


if __name__ == "__main__":
    unittest.main()
