# Copyright 2026 Google LLC
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

import io
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import zipfile
import pandas as pd
import requests
import download_and_segregate_by_gas


class DownloadAndSegregateByGasTest(unittest.TestCase):

    def test_format_emission(self):
        self.assertEqual(download_and_segregate_by_gas._format_emission(0.0),
                         '0')
        self.assertEqual(download_and_segregate_by_gas._format_emission(-0.0),
                         '0')
        self.assertEqual(download_and_segregate_by_gas._format_emission('0'),
                         '0')
        self.assertEqual(download_and_segregate_by_gas._format_emission(1e-7),
                         '0.0000001')
        self.assertEqual(
            download_and_segregate_by_gas._format_emission(123.4500), '123.45')
        self.assertEqual(download_and_segregate_by_gas._format_emission(None),
                         '')
        self.assertEqual(
            download_and_segregate_by_gas._format_emission(float('nan')), '')
        self.assertEqual(download_and_segregate_by_gas._format_emission(''), '')
        self.assertEqual(download_and_segregate_by_gas._format_emission('   '),
                         '')
        self.assertEqual(download_and_segregate_by_gas._format_emission('N/A'),
                         '')
        self.assertEqual(download_and_segregate_by_gas._format_emission('null'),
                         '')

    @patch('download_and_segregate_by_gas.get_retry_session')
    def test_country_list_api_failure_raises_exception(self,
                                                       mock_get_retry_session):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.exceptions.RequestException(
            "API failure")
        mock_get_retry_session.return_value = mock_session

        with self.assertRaises(requests.exceptions.RequestException):
            download_and_segregate_by_gas.download_and_segregate_by_gas()
        mock_session.close.assert_called_once()

    @patch('builtins.open', side_effect=FileNotFoundError())
    @patch('download_and_segregate_by_gas.download_and_process_zip')
    @patch('download_and_segregate_by_gas.get_retry_session')
    def test_empty_gas_dataframes_raises_runtime_error(self,
                                                       mock_get_retry_session,
                                                       mock_download_zip,
                                                       mock_open):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'id': 'USA'}, {'id': 'IND'}]
        mock_session.get.return_value = mock_response
        mock_get_retry_session.return_value = mock_session

        # Simulate all downloads returning None (e.g., HTTP 404 or no relevant CSVs)
        mock_download_zip.return_value = None

        with self.assertRaisesRegex(RuntimeError,
                                    "No data was downloaded for gas: co2"):
            download_and_segregate_by_gas.download_and_segregate_by_gas()
        self.assertEqual(mock_download_zip.call_count, 2)
        mock_session.close.assert_called_once()

    def test_download_and_process_zip_404_returns_none(self):
        mock_session = MagicMock()
        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        mock_response_404.raise_for_status.side_effect = (
            requests.exceptions.HTTPError(response=mock_response_404))
        mock_session.get.return_value = mock_response_404

        result = download_and_segregate_by_gas.download_and_process_zip(
            "http://example.com/test.zip", "USA", "co2", session=mock_session)
        self.assertIsNone(result)

    def test_download_and_process_zip_non_404_raises(self):
        mock_session = MagicMock()
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("500 Server Error",
                                          response=mock_response_500))
        mock_session.get.return_value = mock_response_500

        with self.assertRaises(requests.exceptions.HTTPError):
            download_and_segregate_by_gas.download_and_process_zip(
                "http://example.com/test.zip",
                "USA",
                "co2",
                session=mock_session)

    def test_download_and_process_zip_bad_zip_raises(self):
        mock_session = MagicMock()
        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.content = b"not a valid zip payload"
        mock_session.get.return_value = mock_response_ok

        with self.assertRaises(zipfile.BadZipFile):
            download_and_segregate_by_gas.download_and_process_zip(
                "http://example.com/test.zip",
                "USA",
                "co2",
                session=mock_session)

    def test_download_and_process_zip_valid_zip(self):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("country_agriculture_emissions.csv",
                        "iso3_country,gas,emissions_quantity\nUSA,co2,100.5\n")
            zf.writestr("other_metadata.csv", "col1,col2\n1,2\n")
            zf.writestr("readme.txt", "ignore me")

        mock_session = MagicMock()
        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.content = zip_buffer.getvalue()
        mock_session.get.return_value = mock_response_ok

        df = download_and_segregate_by_gas.download_and_process_zip(
            "http://example.com/USA.zip", "USA", "co2", session=mock_session)
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.loc[0, 'iso3_country'], 'USA')
        self.assertAlmostEqual(df.loc[0, 'emissions_quantity'], 100.5)

    @patch('download_and_segregate_by_gas.download_and_process_zip')
    @patch('download_and_segregate_by_gas.get_retry_session')
    def test_download_and_segregate_by_gas_happy_path(self,
                                                      mock_get_retry_session,
                                                      mock_download_zip):
        with tempfile.TemporaryDirectory() as tmp_dir:
            check_country_path = os.path.join(tmp_dir, 'check_country.csv')
            with open(check_country_path, 'w') as f:
                f.write("IND\n")

            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{'id': 'USA'}]
            mock_session.get.return_value = mock_response
            mock_get_retry_session.return_value = mock_session

            def side_effect(url, iso, gas, session):
                if iso == 'USA':
                    return pd.DataFrame({
                        'iso3_country': ['USA', 'USA'],
                        'gas': [gas, gas],
                        'emissions_quantity': [1e-7, 0.0],
                    })
                return None

            mock_download_zip.side_effect = side_effect

            with patch('download_and_segregate_by_gas.os.path.dirname',
                       return_value=tmp_dir):
                download_and_segregate_by_gas.download_and_segregate_by_gas()

            output_dir = os.path.join(tmp_dir, 'input_files')
            for gas in ["co2", "ch4", "n2o", "co2e_20yr", "co2e_100yr"]:
                csv_path = os.path.join(output_dir, f"all_countries_{gas}.csv")
                tmp_path = f"{csv_path}.tmp"
                self.assertTrue(os.path.exists(csv_path))
                self.assertFalse(os.path.exists(tmp_path))
                with open(csv_path, 'r') as f:
                    content = f.read()
                self.assertIn("0.0000001", content)
                self.assertNotIn("1e-07", content)

            mock_session.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
