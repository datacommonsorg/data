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
from tools.sdmx_import.sdmx_client import SdmxClient
from tools.sdmx_import.sdmx_models import Dataflow, StructureMessage
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
        mock_df1.maintainer.id.__str__.return_value = 'TEST'
        mock_df1.version.__str__.return_value = '1.0'
        mock_df2 = MagicMock()
        mock_df2.name.__str__.return_value = 'Dataflow 2'
        mock_df2.description.__str__.return_value = 'Desc 2'
        mock_df2.maintainer.id.__str__.return_value = 'TEST'
        mock_df2.version.__str__.return_value = '2.0'

        mock_msg.dataflow = {'DF1': mock_df1, 'DF2': mock_df2}
        self.mock_client.dataflow.return_value = mock_msg

        # Call the method
        result = self.client.list_dataflows()

        # Assert the result
        self.assertIsInstance(result, StructureMessage)
        self.assertEqual(len(result.dataflows), 2)
        self.assertIsInstance(result.dataflows[0], Dataflow)
        self.assertEqual(result.dataflows[0].name, 'Dataflow 1')
        self.assertEqual(result.dataflows[1].id, 'DF2')
        self.assertEqual(result.dataflows[0].version, '1.0')
        self.mock_client.dataflow.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
