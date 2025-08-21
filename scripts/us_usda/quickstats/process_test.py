
# Copyright 2021 Google LLC
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
"""Tests for process.py"""

import csv
import io
import json
import unittest
from unittest import mock
from absl.testing import absltest
from process import to_csv_rows, get_survey_county_data, write_csv, load_svs


class ProcessTest(unittest.TestCase):
    def setUp(self):
        """Setup mock data and objects for the test."""
        # This is a sample of what the USDA API response would look like.
        # You should replace this with a representative sample from your 'testdata/ABBEVILLE.json'
        self.mock_api_data = {
            'data': [{
                "short_desc": "CORN, GRAIN - ACRES HARVESTED",
                "domaincat_desc": "NOT SPECIFIED",
                "county_code": "001",
                "state_fips_code": "45",
                "year": "2024",
                "value": "15000",
            }, {
                "short_desc": "WHEAT - ACRES HARVESTED",
                "domaincat_desc": "",
                "county_code": "001",
                "state_fips_code": "45",
                "year": "2024",
                "value": "5000",
            }]
        }
    
    @mock.patch('process.get_data')
    @mock.patch('process.os.path.exists')
    @mock.patch('process.get_usda_api_key', return_value='mock-api-key')
    def test_write_csv(self, mock_get_api_key, mock_exists, mock_get_data):
        """Tests the write_csv function without making a real API call."""

        # Configure mocks to simulate API 
        mock_exists.return_value = False
        mock_get_data.return_value = self.mock_api_data

        expected_csv_rows = [
    {
        'variableMeasured': 'dcs:Area_Farm_CornForGrain',
        'observationDate': '2024',
        'observationAbout': 'dcid:geoId/45001',
        'value': 15000,
        'unit': 'dcs:Acre'
    }, {
        'variableMeasured': 'dcs:Area_Farm_WheatForGrain',
        'observationDate': '2024',
        'observationAbout': 'dcid:geoId/45001',
        'value': 5000,
        'unit': 'dcs:Acre'
    }
]
        api_data = get_survey_county_data(2025, 'ABBEVILLE', 'testdata')
        
        # Verify that the mocked data is being used correctly
        self.assertEqual(len(api_data['data']), 2)

        svs = load_svs()
        csv_rows = to_csv_rows(api_data, svs)
        self.assertEqual(csv_rows, expected_csv_rows)

        out = io.StringIO()
        write_csv(out, csv_rows)
        
        # Manually created the expected CSV string
        expected_csv_output = """variableMeasured,observationDate,observationAbout,value,unit
dcs:Area_Farm_CornForGrain,2024,dcid:geoId/45001,15000,dcs:Acre
dcs:Area_Farm_WheatForGrain,2024,dcid:geoId/45001,5000,dcs:Acre
"""
        self.assertEqual(expected_csv_output, out.getvalue())

if __name__ == '__main__':
    absltest.main()