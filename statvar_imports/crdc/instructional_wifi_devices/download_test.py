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
"""Unit tests for CRDC instructional wifi devices download.py."""

import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import pandas as pd
import requests

try:
    from statvar_imports.crdc.instructional_wifi_devices import download
except ImportError:
    import download


class DownloadTest(unittest.TestCase):

    def test_get_full_year_valid(self):
        self.assertEqual(download.get_full_year("2020-21"), 2021)
        self.assertEqual(download.get_full_year("2023-24"), 2024)

    def test_get_full_year_invalid(self):
        with self.assertRaises(ValueError):
            download.get_full_year("2024")
        with self.assertRaises(ValueError):
            download.get_full_year("2023-2024")

    def test_generate_year_strings(self):
        years = download.generate_year_strings(start_year=2020)
        self.assertIn("2020-21", years)
        self.assertIn("2023-24", years)
        self.assertEqual(years[0], "2020-21")

    def _create_mock_zip(self, csv_filename: str, csv_content: str) -> bytes:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(csv_filename, csv_content)
        return zip_buffer.getvalue()

    def test_process_crdc_data_success_and_nullifies_reserve_codes(self):
        csv_content = ("COMBOKEY,SCH_JUST,SCH_INTERNET_WIFIENDEV\n"
                       "010000201705,Yes,25\n"
                       "010000500870,No,-11\n"
                       "010000500871,No,-5\n"
                       "010000500872,No,120\n")
        zip_bytes = self._create_mock_zip("Internet Access and Devices.csv",
                                          csv_content)

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [zip_bytes]
        mock_response.raise_for_status.return_value = None

        mock_session = mock.Mock()
        mock_session.get.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)
            with mock.patch.object(download, "OUTPUT_DIR", temp_output_dir):
                result = download.process_crdc_data(mock_session, "2023-24")
                self.assertTrue(result)

                expected_file = temp_output_dir / "Internet_Access_and_Devices_2024.csv"
                self.assertTrue(expected_file.exists())

                df = pd.read_csv(expected_file,
                                 dtype=str,
                                 keep_default_na=False)
                self.assertEqual(df["YEAR"].iloc[0], "2024")
                # Positive values preserved
                self.assertEqual(df["SCH_INTERNET_WIFIENDEV"].iloc[0], "25")
                self.assertEqual(df["SCH_INTERNET_WIFIENDEV"].iloc[3], "120")
                # Negative reserve codes (-11, -5) nullified to empty string
                self.assertEqual(df["SCH_INTERNET_WIFIENDEV"].iloc[1], "")
                self.assertEqual(df["SCH_INTERNET_WIFIENDEV"].iloc[2], "")

    def test_process_crdc_data_404_closes_response(self):
        mock_response = mock.Mock()
        mock_response.status_code = 404

        mock_session = mock.Mock()
        mock_session.get.return_value = mock_response

        result = download.process_crdc_data(mock_session, "2028-29")
        self.assertFalse(result)
        mock_response.close.assert_called_once()

    def test_process_crdc_data_http_500_raises(self):
        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "500 Server Error")

        mock_session = mock.Mock()
        mock_session.get.return_value = mock_response

        with self.assertRaises(requests.exceptions.HTTPError):
            download.process_crdc_data(mock_session, "2023-24")

    def test_process_crdc_data_soft_404_html_skipped(self):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_response.raise_for_status.return_value = None

        mock_session = mock.Mock()
        mock_session.get.return_value = mock_response

        result = download.process_crdc_data(mock_session, "2022-23")
        self.assertFalse(result)
        mock_response.close.assert_called_once()

    def test_process_crdc_data_soft_404_non_zip_payload_skipped(self):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "binary/octet-stream"}
        mock_response.iter_content.return_value = [
            b"<!DOCTYPE html><html><body>404 Not Found</body></html>"
        ]
        mock_response.raise_for_status.return_value = None

        mock_session = mock.Mock()
        mock_session.get.return_value = mock_response

        result = download.process_crdc_data(mock_session, "2022-23")
        self.assertFalse(result)
        mock_response.close.assert_called_once()

    def test_process_crdc_data_bad_zip_raises(self):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/zip"}
        mock_response.iter_content.return_value = [
            b"PK\x03\x04CORRUPTED_ZIP_ARCHIVE_DATA"
        ]
        mock_response.raise_for_status.return_value = None

        mock_session = mock.Mock()
        mock_session.get.return_value = mock_response

        with self.assertRaises(zipfile.BadZipFile):
            download.process_crdc_data(mock_session, "2023-24")

    def test_process_crdc_data_missing_csv_raises(self):
        zip_bytes = self._create_mock_zip("Some Other File.csv",
                                          "a,b,c\n1,2,3\n")

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [zip_bytes]
        mock_response.raise_for_status.return_value = None

        mock_session = mock.Mock()
        mock_session.get.return_value = mock_response

        with self.assertRaises(FileNotFoundError):
            download.process_crdc_data(mock_session, "2023-24")

    @mock.patch.object(download, "process_crdc_data")
    @mock.patch.object(download, "generate_year_strings")
    @mock.patch.object(download, "create_session")
    def test_main_terminates_on_exception(self, mock_create_session,
                                          mock_generate_years, mock_process):
        mock_generate_years.return_value = ["2020-21", "2023-24"]
        # First year succeeds, second year throws network/unhandled exception
        mock_process.side_effect = [
            True,
            requests.exceptions.ConnectionError("Connection timed out")
        ]

        with self.assertRaises(SystemExit) as cm:
            download.main()
        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
