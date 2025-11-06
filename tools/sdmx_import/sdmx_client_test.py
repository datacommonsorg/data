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
"""
sdmx_client_test.py

Unit tests for SdmxClient.
"""

import unittest
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError
from .sdmx_client import SdmxClient
import sdmx
from sdmx import message, model
import pandas as pd


class SdmxClientTest(unittest.TestCase):

    @patch('sdmx.Client')
    def setUp(self, mock_sdmx_client):
        self.mock_client = mock_sdmx_client.return_value
        self.client = SdmxClient(endpoint="https://example.com",
                                 agency_id="TEST")

    def test_list_dataflows_success(self):
        # Mock the response from the sdmx client
        mock_msg = MagicMock()
        # Configure the mock objects to have name and description attributes that are strings
        mock_df1 = MagicMock()
        mock_df1.name.__str__.return_value = 'Dataflow 1'
        mock_df1.description.__str__.return_value = 'Desc 1'
        mock_df2 = MagicMock()
        mock_df2.name.__str__.return_value = 'Dataflow 2'
        mock_df2.description.__str__.return_value = 'Desc 2'

        mock_msg.dataflow = {'DF1': mock_df1, 'DF2': mock_df2}
        self.mock_client.dataflow.return_value = mock_msg

        # Call the method
        result = self.client.list_dataflows()

        # Assert the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Dataflow 1')
        self.assertEqual(result[1]['id'], 'DF2')
        self.mock_client.dataflow.assert_called_once_with()

    def test_search_dataflows(self):
        # Mock list_dataflows to return a known list
        self.client.list_dataflows = MagicMock(return_value=[{
            'id': 'DF1',
            'name': 'Alpha Beta',
            'description': 'Gamma'
        }, {
            'id': 'DF2',
            'name': 'Charlie',
            'description': 'Delta Alpha'
        }, {
            'id': 'DF3',
            'name': 'Epsilon',
            'description': 'Foxtrot'
        }])

        # Search for a term in the name
        result = self.client.search_dataflows('beta')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'DF1')

        # Search for a term in the description
        result = self.client.search_dataflows('delta')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'DF2')

        # Search for a term that appears in multiple dataflows
        result = self.client.search_dataflows('alpha')
        self.assertEqual(len(result), 2)

    @patch('sdmx.to_pandas')
    def test_get_dataflow_details_success(self, mock_to_pandas):
        # Mock the response as a DataFrame with one row.
        mock_df = pd.DataFrame([{'name': 'Dataflow 1', 'version': '1.0'}])
        mock_to_pandas.return_value = mock_df

        # Call the method
        result = self.client.get_dataflow_details('DF1')

        # Assert the result
        self.assertEqual(result['name'], 'Dataflow 1')
        self.mock_client.dataflow.assert_called_once_with('DF1')

    def test_get_dataflow_details_not_found(self):
        # Mock the client.dataflow to raise an HTTPError
        self.mock_client.dataflow.side_effect = HTTPError(
            "404 Client Error: Not Found")

        # Call the method
        result = self.client.get_dataflow_details('DF_NONEXISTENT')

        # Assert the result is an empty dictionary
        self.assertEqual(result, {})
        self.mock_client.dataflow.assert_called_once_with('DF_NONEXISTENT')

    @patch('sdmx.to_pandas')
    def test_get_dataflow_series_success(self, mock_to_pandas):
        # Mock the response from sdmx.to_pandas to simulate multiple series
        mock_data = {
            'FREQ': ['A', 'A', 'M', 'M'],
            'REF_AREA': ['AUS', 'CAN', 'AUS', 'CAN'],
            'INDICATOR': ['GDP', 'GDP', 'CPI', 'CPI'],
            'TIME_PERIOD': ['2020', '2020', '2021-01', '2021-01'],
            'OBS_VALUE': [100.0, 200.0, 1.5, 2.0]
        }
        mock_df = pd.DataFrame(mock_data)
        mock_to_pandas.return_value = mock_df

        expected_series = [
            {
                'FREQ': 'A',
                'REF_AREA': 'AUS',
                'INDICATOR': 'GDP'
            },
            {
                'FREQ': 'A',
                'REF_AREA': 'CAN',
                'INDICATOR': 'GDP'
            },
            {
                'FREQ': 'M',
                'REF_AREA': 'AUS',
                'INDICATOR': 'CPI'
            },
            {
                'FREQ': 'M',
                'REF_AREA': 'CAN',
                'INDICATOR': 'CPI'
            },
        ]

        # Call the method
        result = self.client.get_dataflow_series('DF_MULTI_SERIES')

        # Assert the result
        self.assertEqual(len(result), len(expected_series))
        self.assertListEqual(sorted(result, key=lambda x: str(x)),
                             sorted(expected_series, key=lambda x: str(x)))
        self.mock_client.data.assert_called_once_with('DF_MULTI_SERIES',
                                                      key=None,
                                                      params=None,
                                                      agency_id='TEST')


if __name__ == '__main__':
    unittest.main()
