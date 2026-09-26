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

import unittest
from unittest.mock import MagicMock, patch
import requests
import download_and_segregate_by_gas


class DownloadAndSegregateByGasTest(unittest.TestCase):

    @patch('download_and_segregate_by_gas.get_retry_session')
    def test_country_list_api_failure_raises_exception(self, mock_get_retry_session):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.exceptions.RequestException("API failure")
        mock_get_retry_session.return_value = mock_session

        with self.assertRaises(requests.exceptions.RequestException):
            download_and_segregate_by_gas.download_and_segregate_by_gas()

    @patch('download_and_segregate_by_gas.download_and_process_zip')
    @patch('download_and_segregate_by_gas.get_retry_session')
    def test_empty_gas_dataframes_raises_runtime_error(
        self, mock_get_retry_session, mock_download_zip
    ):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'id': 'USA'}, {'id': 'IND'}]
        mock_session.get.return_value = mock_response
        mock_get_retry_session.return_value = mock_session

        # Simulate all downloads returning None (e.g., HTTP 404 or no relevant CSVs)
        mock_download_zip.return_value = None

        with self.assertRaisesRegex(RuntimeError, "No data was downloaded for gas: co2"):
            download_and_segregate_by_gas.download_and_segregate_by_gas()


if __name__ == '__main__':
    unittest.main()
