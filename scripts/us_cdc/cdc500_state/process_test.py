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
"""Unit tests for CDC 500 State aggregation script."""

import os
import tempfile
import unittest
from unittest import mock
import pandas as pd

from scripts.us_cdc.cdc500_state import process

class CDC500StateProcessTest(unittest.TestCase):

    def test_query_constants(self):
        query = process.QUERY
        self.assertIn("spanner_dc_graph_prod_DEFAULT.TimeSeries", query)
        self.assertIn("spanner_dc_graph_prod_DEFAULT.Observation", query)
        self.assertIn("dc/base/CDC500", query)
        self.assertIn("dc/base/CensusACS5YearSurvey", query)
        self.assertIn("SAFE_DIVIDE", query)
        self.assertIn("SUBSTR(p.observation_about, 1, 8)", query)

    def test_run_process_success(self):
        mock_client = mock.MagicMock()
        sample_data = pd.DataFrame({
            'statvar': ['Percent_Person_18OrMoreYears_WithAnyDisability'],
            'observation_about': ['geoId/06'],
            'observation_date': ['2022'],
            'measurement_method': ['dcAggregate/CrudePrevalence'],
            'population_statvar': ['Count_Person_18OrMoreYears'],
            'percent': [29.6479]
        })
        mock_client.query.return_value.to_dataframe.return_value = sample_data
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, 'CDC500State_Output.csv')
            process.run_process(mock_client, output_file)
            
            mock_client.query.assert_called_once()
            self.assertTrue(os.path.exists(output_file))
            saved_df = pd.read_csv(output_file)
            self.assertEqual(len(saved_df), 1)
            self.assertEqual(saved_df['observation_about'].iloc[0], 'geoId/06')

    def test_run_process_query_error(self):
        mock_client = mock.MagicMock()
        mock_client.query.side_effect = Exception("BigQuery Access Denied")
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, 'CDC500State_Output.csv')
            with self.assertRaises(Exception):
                process.run_process(mock_client, output_file)

    def test_run_process_dataframe_error(self):
        mock_client = mock.MagicMock()
        mock_query_job = mock.MagicMock()
        mock_query_job.to_dataframe.side_effect = Exception("Failed to fetch dataframe")
        mock_client.query.return_value = mock_query_job
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, 'CDC500State_Output.csv')
            with self.assertRaises(Exception):
                process.run_process(mock_client, output_file)

if __name__ == '__main__':
    unittest.main()
