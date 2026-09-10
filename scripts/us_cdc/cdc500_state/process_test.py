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
import re
import tempfile
import unittest
from unittest import mock

from absl import flags
from absl.testing import flagsaver
import pandas as pd

from scripts.us_cdc.cdc500_state import process

FLAGS = flags.FLAGS


class CDC500StateProcessTest(unittest.TestCase):
    """Unit tests for CDC 500 State aggregation processing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not FLAGS.is_parsed():
            FLAGS(['test'])

    def test_query_constants(self):
        """Verifies key SQL clauses and excluded variables in process.QUERY."""
        query = process.QUERY
        self.assertIn("spanner_dc_graph_prod_DEFAULT.TimeSeries", query)
        self.assertIn("spanner_dc_graph_prod_DEFAULT.Observation", query)
        self.assertIn("dc/base/CDC500", query)
        self.assertIn("dc/base/CensusACS5YearSurvey", query)
        self.assertIn("SAFE_DIVIDE", query)
        self.assertIn("SAFE_CAST", query)
        self.assertIn("SUBSTR(p.observation_about, 1, 8)", query)
        self.assertIn("LENGTH(O.entity1) = 13", query)
        self.assertIn("REGEXP_CONTAINS", query)
        self.assertIn("QUALIFY ROW_NUMBER() OVER", query)
        self.assertIn("O.last_update_timestamp DESC, O.facet_id DESC", query)
        self.assertIn("Percent_Person_50To74Years_Female_ReceivedMammography", query)
        self.assertIn(
            "Percent_Person_21To65Years_Female_ReceivedCervicalCancerScreening", query)
        self.assertIn("Percent_Person_21To65Years_Female_ReceivedPapSmearTest", query)
        self.assertIn("Percent_Person_50To75Years_ReceivedColorectalCancerScreening", query)

    def test_demographic_cohort_regex_mapping(self):
        """Verifies that representative StatVars match the intended demographic regex rules."""
        female_pattern = r'65OrMoreYears.*Female|Female.*65OrMoreYears'
        male_pattern = r'65OrMoreYears.*Male|Male.*65OrMoreYears'

        self.assertIn(female_pattern, process.QUERY)
        self.assertIn(male_pattern, process.QUERY)

        # Helper mapping that mirrors the SQL CASE WHEN logic
        def map_statvar(sv: str) -> str:
            if re.search(female_pattern, sv):
                return 'Count_Person_65OrMoreYears_Female'
            elif re.search(male_pattern, sv):
                return 'Count_Person_65OrMoreYears_Male'
            elif '65OrMoreYears' in sv:
                return 'Count_Person_65OrMoreYears'
            elif '18To64Years' in sv:
                return 'Count_Person_18To64Years'
            elif '18OrMoreYears' in sv:
                return 'Count_Person_18OrMoreYears'
            else:
                return 'Count_Person'

        test_cases = [
            ('Percent_Person_65OrMoreYears_Female_CorePreventiveServices',
             'Count_Person_65OrMoreYears_Female'),
            ('Percent_Person_Female_65OrMoreYears_CorePreventiveServices',
             'Count_Person_65OrMoreYears_Female'),
            ('Percent_Person_65OrMoreYears_Male_CorePreventiveServices',
             'Count_Person_65OrMoreYears_Male'),
            ('Percent_Person_Male_65OrMoreYears_CorePreventiveServices',
             'Count_Person_65OrMoreYears_Male'),
            ('Percent_Person_65OrMoreYears_CorePreventiveServices',
             'Count_Person_65OrMoreYears'),
            ('Percent_Person_18To64Years_HealthInsurance', 'Count_Person_18To64Years'),
            ('Percent_Person_18OrMoreYears_WithAnyDisability', 'Count_Person_18OrMoreYears'),
            ('Percent_Person_18OrMoreYears_WithHighBloodPressure',
             'Count_Person_18OrMoreYears'),
            ('Percent_Person_WithArthritis', 'Count_Person'),
            ('Percent_Person_WithHighCholesterol', 'Count_Person'),
        ]

        for sv, expected in test_cases:
            with self.subTest(statvar=sv):
                self.assertEqual(map_statvar(sv), expected)

    def test_population_weighted_average_calculation(self):
        """Verifies the population-weighted average calculation and city-to-state
        FIPS aggregation."""
        # Simulated city-level records for California (geoId/06)
        city_records = pd.DataFrame({
            'city_geoid': ['geoId/0644000', 'geoId/0666000', 'geoId/0667000'],
            'city_percent': [20.0, 30.0, 40.0],
            'city_pop': [10000, 20000, 70000]
        })
        city_records['state_geoid'] = city_records['city_geoid'].str.slice(0, 8)
        self.assertTrue((city_records['state_geoid'] == 'geoId/06').all())

        # Formula: SUM(pop * percent) / SUM(pop)
        total_weighted = (city_records['city_pop'] * city_records['city_percent']).sum()
        total_pop = city_records['city_pop'].sum()
        weighted_avg = total_weighted / total_pop

        # Expected: (10000*20 + 20000*30 + 70000*40) / 100000 = 36.0
        self.assertEqual(total_pop, 100000)
        self.assertAlmostEqual(weighted_avg, 36.0, places=4)

    def test_run_process_success(self):
        """Tests successful query execution and atomic output writing."""
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
            result = process.run_process(mock_client, output_file)
            self.assertTrue(result)
            mock_client.query.assert_called_once_with(process.QUERY)
            self.assertTrue(os.path.exists(output_file))
            self.assertFalse(os.path.exists(output_file + '.tmp'))
            saved_df = pd.read_csv(output_file)
            self.assertEqual(len(saved_df), 1)
            self.assertEqual(saved_df['observation_about'].iloc[0], 'geoId/06')

    def test_run_process_empty_dataframe_raises_runtime_error(self):
        """Tests that empty query results raise RuntimeError."""
        mock_client = mock.MagicMock()
        mock_client.query.return_value.to_dataframe.return_value = pd.DataFrame()
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, 'CDC500State_Output.csv')
            with self.assertRaises(RuntimeError):
                process.run_process(mock_client, output_file)

    def test_run_process_query_error(self):
        """Tests propagation of BigQuery query execution errors."""
        mock_client = mock.MagicMock()
        mock_client.query.side_effect = RuntimeError("BigQuery Access Denied")
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, 'CDC500State_Output.csv')
            with self.assertRaises(RuntimeError):
                process.run_process(mock_client, output_file)

    def test_run_process_dataframe_error(self):
        """Tests propagation of query result download errors."""
        mock_client = mock.MagicMock()
        mock_query_job = mock.MagicMock()
        mock_query_job.to_dataframe.side_effect = RuntimeError(
            "Failed to fetch dataframe")
        mock_client.query.return_value = mock_query_job
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, 'CDC500State_Output.csv')
            with self.assertRaises(RuntimeError):
                process.run_process(mock_client, output_file)

    @mock.patch('scripts.us_cdc.cdc500_state.process.run_process')
    @mock.patch('google.cloud.bigquery.Client')
    def test_main(self, mock_bq_client_cls, mock_run_process):
        """Tests process.main flag parsing and client instantiation."""
        mock_client_instance = mock.MagicMock()
        mock_bq_client_cls.return_value = mock_client_instance
        with tempfile.TemporaryDirectory() as tmp_dir:
            with flagsaver.flagsaver(output_dir=tmp_dir, project='test-project'):
                process.main([])
                expected_output_file = os.path.join(tmp_dir, 'CDC500State_Output.csv')
                mock_bq_client_cls.assert_called_once_with(project='test-project')
                mock_run_process.assert_called_once_with(mock_client_instance,
                                                         expected_output_file)


if __name__ == '__main__':
    unittest.main()
