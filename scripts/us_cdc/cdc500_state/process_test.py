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
import duckdb
import pandas as pd

from scripts.us_cdc.cdc500_state import process

FLAGS = flags.FLAGS


def _prepare_duckdb_query(sql: str) -> str:
    """Adapts BigQuery SQL syntax in process.QUERY for in-memory DuckDB execution."""
    adapted = sql.replace(
        '`datcom-store.spanner_dc_graph_prod_DEFAULT.TimeSeries`', 'TimeSeries')
    adapted = adapted.replace(
        '`datcom-store.spanner_dc_graph_prod_DEFAULT.Observation`',
        'Observation')
    adapted = adapted.replace('SAFE_CAST(', 'TRY_CAST(')
    adapted = adapted.replace('AS FLOAT64)', 'AS DOUBLE)')
    adapted = adapted.replace("r'", "'")
    return adapted


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
        self.assertIn("SAFE_CAST(O.value AS FLOAT64) IS NOT NULL", query)
        self.assertIn("HAVING percent IS NOT NULL", query)
        self.assertIn("SUBSTR(p.observation_about, 1, 8)", query)
        self.assertIn(
            "AND (LENGTH(O.entity1) = 13 OR O.entity1 = 'geoId/15003')", query)
        self.assertIn("O.entity1 = 'geoId/15003'", query)
        self.assertIn("O.date <= '2016'", query)
        self.assertIn("O.date = '2017'", query)
        self.assertIn("HighBloodPressure|Cholesterol", query)
        self.assertNotIn("svo_percent_dedup", query)
        self.assertIn("REGEXP_CONTAINS", query)
        self.assertIn("QUALIFY ROW_NUMBER() OVER", query)
        self.assertIn("O.last_update_timestamp DESC, O.facet_id DESC", query)
        self.assertIn("Percent_Person_50To74Years_Female_ReceivedMammography",
                      query)
        self.assertIn(
            "Percent_Person_21To65Years_Female_ReceivedCervicalCancerScreening",
            query)
        self.assertIn("Percent_Person_21To65Years_Female_ReceivedPapSmearTest",
                      query)
        self.assertIn(
            "Percent_Person_50To75Years_ReceivedColorectalCancerScreening",
            query)
        self.assertIn("'Count_Person_65OrMoreYears_Female'", query)
        self.assertIn("'Count_Person_65OrMoreYears_Male'", query)
        self.assertIn("'Count_Person_65OrMoreYears'", query)
        self.assertIn("'Count_Person_18To64Years'", query)
        self.assertIn("'Count_Person_18OrMoreYears'", query)
        self.assertIn("'Count_Person'", query)
        self.assertIn(
            "SUM(SAFE_CAST(c.population AS FLOAT64) * "
            "SAFE_CAST(p.percent AS FLOAT64))", query)
        self.assertNotIn("p.pop_statvar AS population_statvar", query)

    def test_demographic_cohort_regex_mapping(self):
        """Executes cdc_sv CTE from process.QUERY in DuckDB to verify cohort mapping."""
        con = duckdb.connect(':memory:')
        con.create_function(
            'REGEXP_CONTAINS', lambda s, p: bool(re.search(p, s))
            if s and p else False, [str, str], bool)

        test_cases = [
            ('Percent_Person_65OrMoreYears_Female_CorePreventiveServices',
             'Count_Person_65OrMoreYears_Female'),
            ('Percent_Person_65OrMoreYears_Male_CorePreventiveServices',
             'Count_Person_65OrMoreYears_Male'),
            ('Percent_Person_65OrMoreYears_CorePreventiveServices',
             'Count_Person_65OrMoreYears'),
            ('Percent_Person_18To64Years_HealthInsurance',
             'Count_Person_18To64Years'),
            ('Percent_Person_18OrMoreYears_WithAnyDisability',
             'Count_Person_18OrMoreYears'),
            ('Percent_Person_18OrMoreYears_WithHighBloodPressure',
             'Count_Person_18OrMoreYears'),
            ('Percent_Person_WithArthritis', 'Count_Person'),
            ('Percent_Person_WithHighCholesterol', 'Count_Person'),
        ]
        excluded_statvars = [
            'Percent_Person_50To74Years_Female_ReceivedMammography',
            'Percent_Person_21To65Years_Female_ReceivedCervicalCancerScreening',
            'Percent_Person_21To65Years_Female_ReceivedPapSmearTest',
            'Percent_Person_50To75Years_ReceivedColorectalCancerScreening',
        ]

        rows = [{
            'variable_measured': sv,
            'provenance': 'dc/base/CDC500'
        } for sv, _ in test_cases]
        rows.extend([{
            'variable_measured': sv,
            'provenance': 'dc/base/CDC500'
        } for sv in excluded_statvars])
        ts_df = pd.DataFrame(rows)
        con.register('TimeSeries', ts_df)

        # Extract cdc_sv CTE from process.QUERY and execute against TimeSeries
        adapted_sql = _prepare_duckdb_query(process.QUERY)
        cdc_sv_sql = adapted_sql.split('svo_percent AS (',
                                       maxsplit=1)[0].rstrip().rstrip(',')
        result_df = con.execute(
            f"{cdc_sv_sql} SELECT cdc500, pop_statvar FROM cdc_sv").df()

        result_map = dict(zip(result_df['cdc500'], result_df['pop_statvar']))
        self.assertEqual(len(result_map), len(test_cases))
        for sv, expected_cohort in test_cases:
            with self.subTest(statvar=sv):
                self.assertEqual(result_map.get(sv), expected_cohort)
        for excluded_sv in excluded_statvars:
            with self.subTest(excluded=excluded_sv):
                self.assertNotIn(excluded_sv, result_map)

    def test_population_weighted_average_calculation(self):
        """Executes full process.QUERY in DuckDB to verify state weighted average."""
        con = duckdb.connect(':memory:')
        con.create_function(
            'REGEXP_CONTAINS', lambda s, p: bool(re.search(p, s))
            if s and p else False, [str, str], bool)
        con.create_function(
            'SAFE_DIVIDE', lambda a, b: float(a) / float(b)
            if (a is not None and b) else None, [float, float], float)

        ts_df = pd.DataFrame([
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/0644000',
                'facet_id': 'f1',
                'provenance': 'dc/base/CDC500',
                'measurement_method': 'CrudePrevalence'
            },
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/0666000',
                'facet_id': 'f1',
                'provenance': 'dc/base/CDC500',
                'measurement_method': 'CrudePrevalence'
            },
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/0667000',
                'facet_id': 'f1',
                'provenance': 'dc/base/CDC500',
                'measurement_method': 'CrudePrevalence'
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/0644000',
                'facet_id': 'f2',
                'provenance': 'dc/base/CensusACS5YearSurvey',
                'measurement_method': ''
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/0666000',
                'facet_id': 'f2',
                'provenance': 'dc/base/CensusACS5YearSurvey',
                'measurement_method': ''
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/0667000',
                'facet_id': 'f2',
                'provenance': 'dc/base/CensusACS5YearSurvey',
                'measurement_method': ''
            },
        ])
        obs_df = pd.DataFrame([
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/0644000',
                'date': '2022',
                'value': '20.0',
                'facet_id': 'f1',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/0666000',
                'date': '2022',
                'value': '30.0',
                'facet_id': 'f1',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/0667000',
                'date': '2022',
                'value': '40.0',
                'facet_id': 'f1',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/0644000',
                'date': '2022',
                'value': '10000',
                'facet_id': 'f2',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/0666000',
                'date': '2022',
                'value': '20000',
                'facet_id': 'f2',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/0667000',
                'date': '2022',
                'value': '70000',
                'facet_id': 'f2',
                'last_update_timestamp': 100
            },
        ])
        con.register('TimeSeries', ts_df)
        con.register('Observation', obs_df)

        sql = _prepare_duckdb_query(process.QUERY)
        result_df = con.execute(sql).df()

        # Expected: (10000*20 + 20000*30 + 70000*40) / 100000 = 36.0
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df['statvar'].iloc[0],
                         'Percent_Person_WithArthritis')
        self.assertEqual(result_df['observation_about'].iloc[0], 'geoId/06')
        self.assertEqual(result_df['observation_date'].iloc[0], '2022')
        self.assertEqual(result_df['measurement_method'].iloc[0],
                         'dcAggregate/CrudePrevalence')
        self.assertAlmostEqual(result_df['percent'].iloc[0], 36.0, places=4)

    def test_hawaii_honolulu_county_edge_cases(self):
        """Tests Honolulu County (geoId/15003) filtering across 2016, 2017, 2018."""
        con = duckdb.connect(':memory:')
        con.create_function(
            'REGEXP_CONTAINS', lambda s, p: bool(re.search(p, s))
            if s and p else False, [str, str], bool)
        con.create_function(
            'SAFE_DIVIDE', lambda a, b: float(a) / float(b)
            if (a is not None and b) else None, [float, float], float)

        # Test 2016 (county included), 2017 non-BP (county included),
        # 2017 BP (county excluded, 13-char CDP used),
        # 2018 non-BP (county excluded, 13-char CDP used), and empty measurement_method.
        ts_df = pd.DataFrame([
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/15003',
                'facet_id': 'f1',
                'provenance': 'dc/base/CDC500',
                'measurement_method': ''
            },
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/1571550',
                'facet_id': 'f1',
                'provenance': 'dc/base/CDC500',
                'measurement_method': 'CrudePrevalence'
            },
            {
                'variable_measured': 'Percent_Person_WithHighBloodPressure',
                'entity1': 'geoId/15003',
                'facet_id': 'f1',
                'provenance': 'dc/base/CDC500',
                'measurement_method': 'CrudePrevalence'
            },
            {
                'variable_measured': 'Percent_Person_WithHighBloodPressure',
                'entity1': 'geoId/1571550',
                'facet_id': 'f1',
                'provenance': 'dc/base/CDC500',
                'measurement_method': 'CrudePrevalence'
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/15003',
                'facet_id': 'f2',
                'provenance': 'dc/base/CensusACS5YearSurvey',
                'measurement_method': ''
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/1571550',
                'facet_id': 'f2',
                'provenance': 'dc/base/CensusACS5YearSurvey',
                'measurement_method': ''
            },
        ])
        obs_df = pd.DataFrame([
            # 2016: geoId/15003 should be INCLUDED (value 22.5)
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/15003',
                'date': '2016',
                'value': '22.5',
                'facet_id': 'f1',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/15003',
                'date': '2016',
                'value': '950000',
                'facet_id': 'f2',
                'last_update_timestamp': 100
            },
            # 2017 non-BP Arthritis: geoId/15003 (24.0) must be INCLUDED
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/15003',
                'date': '2017',
                'value': '24.0',
                'facet_id': 'f1',
                'last_update_timestamp': 100
            },
            # 2017 HighBloodPressure: geoId/15003 (99.0) must be EXCLUDED;
            # 13-char CDP geoId/1571550 (31.2) must be INCLUDED.
            {
                'variable_measured': 'Percent_Person_WithHighBloodPressure',
                'entity1': 'geoId/15003',
                'date': '2017',
                'value': '99.0',
                'facet_id': 'f1',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Percent_Person_WithHighBloodPressure',
                'entity1': 'geoId/1571550',
                'date': '2017',
                'value': '31.2',
                'facet_id': 'f1',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/15003',
                'date': '2017',
                'value': '950000',
                'facet_id': 'f2',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/1571550',
                'date': '2017',
                'value': '350000',
                'facet_id': 'f2',
                'last_update_timestamp': 100
            },
            # 2018 Arthritis: geoId/15003 (88.0) must be EXCLUDED;
            # 13-char CDP geoId/1571550 (20.4) must be INCLUDED.
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/15003',
                'date': '2018',
                'value': '88.0',
                'facet_id': 'f1',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/1571550',
                'date': '2018',
                'value': '20.4',
                'facet_id': 'f1',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/15003',
                'date': '2018',
                'value': '950000',
                'facet_id': 'f2',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/1571550',
                'date': '2018',
                'value': '350000',
                'facet_id': 'f2',
                'last_update_timestamp': 100
            },
        ])
        con.register('TimeSeries', ts_df)
        con.register('Observation', obs_df)

        sql = _prepare_duckdb_query(process.QUERY)
        result_df = con.execute(sql).df().sort_values(
            by=['observation_date', 'statvar']).reset_index(drop=True)

        self.assertEqual(len(result_df), 4)
        # 2016 row: geoId/15003 included, empty measurement_method -> 'dcAggregate'
        self.assertEqual(result_df['observation_about'].iloc[0], 'geoId/15')
        self.assertEqual(result_df['observation_date'].iloc[0], '2016')
        self.assertEqual(result_df['statvar'].iloc[0],
                         'Percent_Person_WithArthritis')
        self.assertEqual(result_df['measurement_method'].iloc[0], 'dcAggregate')
        self.assertAlmostEqual(result_df['percent'].iloc[0], 22.5, places=4)
        # 2017 non-BP row: geoId/15003 included
        self.assertEqual(result_df['observation_about'].iloc[1], 'geoId/15')
        self.assertEqual(result_df['observation_date'].iloc[1], '2017')
        self.assertEqual(result_df['statvar'].iloc[1],
                         'Percent_Person_WithArthritis')
        self.assertEqual(result_df['measurement_method'].iloc[1], 'dcAggregate')
        self.assertAlmostEqual(result_df['percent'].iloc[1], 24.0, places=4)
        # 2017 BP row: geoId/15003 excluded, only geoId/1571550 (31.2) included
        self.assertEqual(result_df['observation_about'].iloc[2], 'geoId/15')
        self.assertEqual(result_df['observation_date'].iloc[2], '2017')
        self.assertEqual(result_df['statvar'].iloc[2],
                         'Percent_Person_WithHighBloodPressure')
        self.assertEqual(result_df['measurement_method'].iloc[2],
                         'dcAggregate/CrudePrevalence')
        self.assertAlmostEqual(result_df['percent'].iloc[2], 31.2, places=4)
        # 2018 Arthritis row: geoId/15003 excluded, only geoId/1571550 (20.4) included
        self.assertEqual(result_df['observation_about'].iloc[3], 'geoId/15')
        self.assertEqual(result_df['observation_date'].iloc[3], '2018')
        self.assertEqual(result_df['statvar'].iloc[3],
                         'Percent_Person_WithArthritis')
        self.assertEqual(result_df['measurement_method'].iloc[3],
                         'dcAggregate/CrudePrevalence')
        self.assertAlmostEqual(result_df['percent'].iloc[3], 20.4, places=4)

    def test_qualify_row_number_deduplication(self):
        """Tests QUALIFY ROW_NUMBER() deduplication by timestamp and facet_id."""
        con = duckdb.connect(':memory:')
        con.create_function(
            'REGEXP_CONTAINS', lambda s, p: bool(re.search(p, s))
            if s and p else False, [str, str], bool)
        con.create_function(
            'SAFE_DIVIDE', lambda a, b: float(a) / float(b)
            if (a is not None and b) else None, [float, float], float)

        ts_df = pd.DataFrame([
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/0644000',
                'facet_id': 'f_old',
                'provenance': 'dc/base/CDC500',
                'measurement_method': 'CrudePrevalence'
            },
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/0644000',
                'facet_id': 'f_new',
                'provenance': 'dc/base/CDC500',
                'measurement_method': 'CrudePrevalence'
            },
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/0666000',
                'facet_id': 'f_city2',
                'provenance': 'dc/base/CDC500',
                'measurement_method': 'CrudePrevalence'
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/0644000',
                'facet_id': 'f_low',
                'provenance': 'dc/base/CensusACS5YearSurvey',
                'measurement_method': ''
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/0644000',
                'facet_id': 'f_high',
                'provenance': 'dc/base/CensusACS5YearSurvey',
                'measurement_method': ''
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/0666000',
                'facet_id': 'f_city2_pop',
                'provenance': 'dc/base/CensusACS5YearSurvey',
                'measurement_method': ''
            },
        ])
        obs_df = pd.DataFrame([
            # Competing percent observations for geoId/0644000:
            # newer timestamp (200) must win over (100)
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/0644000',
                'date': '2022',
                'value': '99.0',
                'facet_id': 'f_old',
                'last_update_timestamp': 100
            },
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/0644000',
                'date': '2022',
                'value': '25.0',
                'facet_id': 'f_new',
                'last_update_timestamp': 200
            },
            # Second city in CA (geoId/0666000) with percent 10.0 and pop 10,000
            {
                'variable_measured': 'Percent_Person_WithArthritis',
                'entity1': 'geoId/0666000',
                'date': '2022',
                'value': '10.0',
                'facet_id': 'f_city2',
                'last_update_timestamp': 200
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/0666000',
                'date': '2022',
                'value': '10000',
                'facet_id': 'f_city2_pop',
                'last_update_timestamp': 200
            },
            # Competing count observations for geoId/0644000 with identical timestamp (200):
            # higher facet_id ('f_low' > 'f_high' alphabetically: 'f_low' (50,000) wins)
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/0644000',
                'date': '2022',
                'value': '10000',
                'facet_id': 'f_high',
                'last_update_timestamp': 200
            },
            {
                'variable_measured': 'Count_Person',
                'entity1': 'geoId/0644000',
                'date': '2022',
                'value': '50000',
                'facet_id': 'f_low',
                'last_update_timestamp': 200
            },
        ])
        con.register('TimeSeries', ts_df)
        con.register('Observation', obs_df)

        sql = _prepare_duckdb_query(process.QUERY)
        result_df = con.execute(sql).df()

        self.assertEqual(len(result_df), 1)
        # Choosing 'f_low' (50,000) over 'f_high' (10,000) yields weighted average:
        # (25.0 * 50,000 + 10.0 * 10,000) / (50,000 + 10,000) = 1,350,000 / 60,000 = 22.5.
        # If 'f_high' (10,000) had been chosen, average would be 17.5.
        self.assertAlmostEqual(result_df['percent'].iloc[0], 22.5, places=4)

    def test_run_process_success(self):
        """Tests successful query execution and atomic output writing."""
        mock_client = mock.MagicMock()
        sample_data = pd.DataFrame({
            'statvar': ['Percent_Person_18OrMoreYears_WithAnyDisability'],
            'observation_about': ['geoId/06'],
            'observation_date': ['2022'],
            'measurement_method': ['dcAggregate/CrudePrevalence'],
            'percent': [29.6479]
        })
        mock_client.query.return_value.to_dataframe.return_value = sample_data

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, 'CDC500State_Output.csv')
            result = process.run_process(mock_client, output_file)
            self.assertTrue(result)
            mock_client.query.assert_called_once_with(
                process.QUERY, timeout=process.DEFAULT_BQ_TIMEOUT_SECONDS)
            mock_client.query.return_value.to_dataframe.assert_called_once_with(
                timeout=process.DEFAULT_BQ_TIMEOUT_SECONDS)
            self.assertTrue(os.path.exists(output_file))
            self.assertFalse(os.path.exists(output_file + '.tmp'))
            saved_df = pd.read_csv(output_file)
            self.assertEqual(len(saved_df), 1)
            self.assertEqual(saved_df['observation_about'].iloc[0], 'geoId/06')

    def test_run_process_empty_dataframe_raises_runtime_error(self):
        """Tests that empty query results raise RuntimeError."""
        mock_client = mock.MagicMock()
        mock_client.query.return_value.to_dataframe.return_value = pd.DataFrame(
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, 'CDC500State_Output.csv')
            with self.assertRaisesRegex(RuntimeError,
                                        "BigQuery query returned 0 rows"):
                process.run_process(mock_client, output_file)

    def test_run_process_query_error(self):
        """Tests propagation of BigQuery query execution errors."""
        mock_client = mock.MagicMock()
        mock_client.query.side_effect = RuntimeError("BigQuery Access Denied")
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, 'CDC500State_Output.csv')
            with self.assertRaisesRegex(RuntimeError, "BigQuery Access Denied"):
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
            with self.assertRaisesRegex(RuntimeError,
                                        "Failed to fetch dataframe"):
                process.run_process(mock_client, output_file)

    def test_run_process_empty_output_file_raises_runtime_error(self):
        """Tests that creating an empty (0-byte) output file raises RuntimeError."""
        mock_client = mock.MagicMock()
        mock_df = mock.MagicMock()
        mock_df.empty = False
        mock_df.__len__.return_value = 1

        def fake_to_csv(filepath, *args, **kwargs):
            del args, kwargs  # Unused.
            with open(filepath, 'w', encoding='utf-8'):
                pass  # Create 0-byte file

        mock_df.to_csv.side_effect = fake_to_csv
        mock_client.query.return_value.to_dataframe.return_value = mock_df
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, 'CDC500State_Output.csv')
            with self.assertRaisesRegex(RuntimeError,
                                        "was created empty or missing"):
                process.run_process(mock_client, output_file)
            self.assertFalse(os.path.exists(output_file))
            self.assertFalse(os.path.exists(output_file + '.tmp'))

    @mock.patch('scripts.us_cdc.cdc500_state.process.run_process')
    @mock.patch('google.cloud.bigquery.Client')
    def test_main(self, mock_bq_client_cls, mock_run_process):
        """Tests process.main flag parsing and client instantiation."""
        mock_client_instance = mock.MagicMock()
        mock_bq_client_cls.return_value = mock_client_instance
        with tempfile.TemporaryDirectory() as tmp_dir:
            with flagsaver.flagsaver(output_dir=tmp_dir,
                                     project='test-project',
                                     timeout=300):
                process.main([])
                expected_output_file = os.path.join(tmp_dir,
                                                    'CDC500State_Output.csv')
                mock_bq_client_cls.assert_called_once_with(
                    project='test-project')
                mock_run_process.assert_called_once_with(mock_client_instance,
                                                         expected_output_file,
                                                         timeout=300)

    @mock.patch('scripts.us_cdc.cdc500_state.process.logging.fatal')
    @mock.patch('scripts.us_cdc.cdc500_state.process.run_process')
    @mock.patch('google.cloud.bigquery.Client')
    def test_main_error_logs_fatal(self, mock_bq_client_cls, mock_run_process,
                                   mock_logging_fatal):
        """Tests process.main catches unhandled exceptions and logs via logging.fatal."""
        del mock_bq_client_cls  # Unused.
        mock_run_process.side_effect = RuntimeError(
            "BigQuery query returned 0 rows.")
        with tempfile.TemporaryDirectory() as tmp_dir:
            with flagsaver.flagsaver(output_dir=tmp_dir):
                process.main([])
                mock_logging_fatal.assert_called_once()

    @mock.patch('scripts.us_cdc.cdc500_state.process.logging.fatal')
    @mock.patch('google.cloud.bigquery.Client')
    def test_main_client_init_error_logs_fatal(self, mock_bq_client_cls,
                                               mock_logging_fatal):
        """Tests process.main catches client init errors and logs via logging.fatal."""
        mock_bq_client_cls.side_effect = RuntimeError(
            "DefaultCredentialsError: Could not automatically determine credentials."
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            with flagsaver.flagsaver(output_dir=tmp_dir):
                process.main([])
                mock_logging_fatal.assert_called_once()


if __name__ == '__main__':
    unittest.main()
