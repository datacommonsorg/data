# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for bigquery_differ.py."""

import csv
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.append(_DATA_DIR)
sys.path.append(_SCRIPT_DIR)

import bigquery_differ

_SAMPLE_CURR_MCF = """
Node: dcid:obs1
typeOf: dcs:StatVarObservation
variableMeasured: dcid:Count_Person
observationAbout: dcid:country/USA
observationDate: "2024"
value: 335000000

Node: dcid:obs2
typeOf: dcs:StatVarObservation
variableMeasured: dcid:Count_Person
observationAbout: dcid:country/CAN
observationDate: "2024"
value: 40000000

Node: dcid:Count_Person
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
measuredProperty: dcs:count
"""

_SAMPLE_PREV_MCF = """
Node: dcid:obs1
typeOf: dcs:StatVarObservation
variableMeasured: dcid:Count_Person
observationAbout: dcid:country/USA
observationDate: "2024"
value: 330000000

Node: dcid:Count_Person
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
measuredProperty: dcs:count
"""


class BigQueryDifferTest(unittest.TestCase):

    def test_stream_mcf_to_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mcf_path = os.path.join(tmpdir, 'test.mcf')
            obs_csv = os.path.join(tmpdir, 'obs.csv')
            schema_csv = os.path.join(tmpdir, 'schema.csv')
            with open(mcf_path, 'w', encoding='utf-8') as f:
                f.write(_SAMPLE_CURR_MCF)

            obs_count, schema_count = bigquery_differ.stream_mcf_to_csv(
                mcf_path, obs_csv, schema_csv)

            self.assertEqual(obs_count, 2)
            self.assertEqual(schema_count, 1)

            with open(obs_csv, 'r', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 2)
                self.assertEqual(rows[0]['variableMeasured'],
                                 'dcid:Count_Person')
                self.assertEqual(rows[0]['value'], '335000000')
                self.assertEqual(rows[0]['observationAbout'], 'country/USA')
                self.assertEqual(rows[0]['observationDate'], '2024')
                self.assertEqual(rows[0]['row_num'], '1')
                self.assertEqual(rows[1]['observationAbout'], 'country/CAN')
                self.assertEqual(rows[1]['row_num'], '2')
                self.assertIn('dcid:country/USA', rows[0]['key_combined'])

            with open(schema_csv, 'r', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['dcid'], 'dcid:Count_Person')
                self.assertIn('populationType:dcid:Person',
                              rows[0]['value_combined'])

    def test_stream_mcf_to_csv_exclude_filenames(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_mcf = os.path.join(tmpdir, 'table_mcf_nodes_0.mcf')
            agg_mcf = os.path.join(tmpdir, 'stat_var_agg_nodes.mcf')
            obs_csv = os.path.join(tmpdir, 'obs.csv')
            schema_csv = os.path.join(tmpdir, 'schema.csv')
            with open(raw_mcf, 'w', encoding='utf-8') as f:
                f.write(_SAMPLE_CURR_MCF)
            with open(agg_mcf, 'w', encoding='utf-8') as f:
                f.write(_SAMPLE_PREV_MCF)

            obs_count, schema_count = bigquery_differ.stream_mcf_to_csv(
                os.path.join(tmpdir, '*.mcf'),
                obs_csv,
                schema_csv,
                exclude_filenames={'stat_var_agg_nodes.mcf'},
            )
            self.assertEqual(obs_count, 2)
            self.assertEqual(schema_count, 1)

    def test_get_import_bq_table_ids(self):
        ids = bigquery_differ.get_import_bq_table_ids(
            'test-proj.test_dataset',
            'India-RBI:State',
            '2026-09-17',
            'input-0',
        )
        self.assertEqual(
            ids,
            {
                'raw_obs':
                    'test-proj.test_dataset.raw_obs_India_RBI_State_2026_09_17_input_0',
                'raw_schema':
                    'test-proj.test_dataset.raw_schema_India_RBI_State_2026_09_17_input_0',
                'agg_obs':
                    'test-proj.test_dataset.agg_obs_India_RBI_State_2026_09_17_input_0',
            },
        )

    def test_stream_mcf_to_csv_full_facet_properties(self):
        agg_mcf = """
Node: dcid:dc/o/test1
typeOf: dcs:StatVarObservation
dcid: "dc/o/test1"
variableMeasured: dcs:Count_Person_Producer
observationAbout: dcid:geoId/06
observationDate: "2017"
value: 66000
observationPeriod: "P1Y"
measurementMethod: dcs:dcAggregate/USDAAgricultureCensus
unit: dcs:Person
scalingFactor: "100"

Node: dcid:dc/o/test2
typeOf: dcs:StatVarObservation
dcid: "dc/o/test2"
variableMeasured: dcs:Count_Person_Total
observationAbout: dcid:country/USA
observationDate: "2020"
value: 150
measurementMethod: dcs:DataCommonsAggregate
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mcf_path = os.path.join(tmpdir, 'stat_var_agg_nodes.mcf')
            obs_csv = os.path.join(tmpdir, 'obs.csv')
            schema_csv = os.path.join(tmpdir, 'schema.csv')
            with open(mcf_path, 'w', encoding='utf-8') as f:
                f.write(agg_mcf)

            bigquery_differ.stream_mcf_to_csv(mcf_path, obs_csv, schema_csv)
            with open(obs_csv, 'r', encoding='utf-8') as f:
                csv_rows = list(csv.DictReader(f))

        self.assertEqual(len(csv_rows), 2)
        self.assertEqual(
            csv_rows[0],
            {
                'key_combined':
                    'dcid:Count_Person_Producer;dcid:geoId/06;"2017";"P1Y";'
                    'dcid:dcAggregate/USDAAgricultureCensus;dcid:Person;"100"',
                'variableMeasured': 'dcid:Count_Person_Producer',
                'value': '66000',
                'observationAbout': 'geoId/06',
                'observationDate': '2017',
                'observationPeriod': 'P1Y',
                'measurementMethod': 'dcAggregate/USDAAgricultureCensus',
                'unit': 'Person',
                'scalingFactor': '100',
                'row_num': '1',
            },
        )
        self.assertEqual(
            csv_rows[1]['key_combined'],
            'dcid:Count_Person_Total;dcid:country/USA;"2020";;'
            'dcid:DataCommonsAggregate;;',
        )
        self.assertEqual(csv_rows[1]['row_num'], '2')

    def test_cleanup_shared_bq_tables(self):
        mock_client = mock.MagicMock()
        bigquery_differ.cleanup_shared_bq_tables(
            project_id='test-proj',
            shared_table_ids=None,
            bq_client=mock_client,
        )
        mock_client.delete_table.assert_not_called()

        shared_ids = bigquery_differ.get_import_bq_table_ids(
            'test-proj.test_dataset', 'test_imp', '2026_09_17', 'input0')
        bigquery_differ.cleanup_shared_bq_tables(
            project_id='test-proj',
            shared_table_ids=shared_ids,
            bq_client=mock_client,
        )
        deleted = [
            call.args[0] for call in mock_client.delete_table.call_args_list
        ]
        self.assertEqual(
            deleted,
            [
                shared_ids['raw_obs'],
                shared_ids['raw_schema'],
                shared_ids['agg_obs'],
            ],
        )

    @mock.patch('bigquery_differ.bigquery.Client')
    def test_run_bigquery_differ_mocked(self, mock_bq_client_cls):
        mock_client = mock_bq_client_cls.return_value

        mock_table = mock.MagicMock()
        mock_client.get_table.return_value = mock_table

        mock_obs_query_job = mock.MagicMock()
        mock_obs_query_job.to_dataframe.return_value = pd.DataFrame([{
            'StatVar': 'Count_Person',
            'ADDED': 1,
            'DELETED': 0,
            'MODIFIED': 1
        }])

        mock_schema_row = mock.MagicMock()
        mock_schema_row.added_schema_count = 0
        mock_schema_row.deleted_schema_count = 0
        mock_schema_row.modified_schema_count = 0
        mock_schema_query_job = mock.MagicMock()
        mock_schema_query_job.result.return_value = [mock_schema_row]

        mock_client.query.side_effect = [
            mock_obs_query_job, mock_schema_query_job
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            curr_mcf = os.path.join(tmpdir, 'curr.mcf')
            prev_mcf = os.path.join(tmpdir, 'prev.mcf')
            out_dir = os.path.join(tmpdir, 'output')
            with open(curr_mcf, 'w', encoding='utf-8') as f:
                f.write(_SAMPLE_CURR_MCF)
            with open(prev_mcf, 'w', encoding='utf-8') as f:
                f.write(_SAMPLE_PREV_MCF)

            summary = bigquery_differ.run_bigquery_differ(
                current_data=curr_mcf,
                previous_data=prev_mcf,
                output_location=out_dir,
                project_id='test-project',
                job_name='test_job',
                dataset_id='test_dataset')

            self.assertEqual(summary['current_obs_count'], 2)
            self.assertEqual(summary['previous_obs_count'], 1)
            self.assertEqual(summary['added_obs_count'], 1)
            self.assertEqual(summary['modified_obs_count'], 1)
            self.assertEqual(summary['obs_diff_count'], 2)
            self.assertEqual(summary['schema_diff_count'], 0)

            summary_json_path = os.path.join(out_dir, 'differ_summary.json')
            summary_csv_path = os.path.join(out_dir, 'differ_summary.csv')
            self.assertTrue(os.path.exists(summary_json_path))
            self.assertTrue(os.path.exists(summary_csv_path))

            with open(summary_json_path, 'r', encoding='utf-8') as f:
                saved_json = json.load(f)
                self.assertEqual(saved_json['obs_diff_count'], 2)

            self.assertEqual(mock_client.delete_table.call_count, 4)

    @mock.patch('bigquery_differ.bigquery.Client')
    def test_run_bigquery_differ_reuses_raw_obs_and_agg_obs(
            self, mock_bq_client_cls):
        mock_client = mock_bq_client_cls.return_value

        shared_ids = bigquery_differ.get_import_bq_table_ids(
            'test-project.test_dataset', 'test_imp', '2026_09_17', 'input0')

        def _get_table(table_ref):
            t = mock.MagicMock()
            if table_ref == shared_ids['raw_obs']:
                t.num_rows = 10
            elif table_ref == shared_ids['agg_obs']:
                t.num_rows = 5
            elif table_ref == shared_ids['raw_schema']:
                t.num_rows = 2
            else:
                t.num_rows = 0
            return t

        mock_client.get_table.side_effect = _get_table

        mock_obs_query_job = mock.MagicMock()
        mock_obs_query_job.to_dataframe.return_value = pd.DataFrame([
            {
                'StatVar': 'Count_Person',
                'ADDED': 1,
                'DELETED': 0,
                'MODIFIED': 1
            },
            {
                'StatVar': 'Count_Person_Agg',
                'ADDED': 2,
                'DELETED': 0,
                'MODIFIED': 0
            },
        ])

        mock_schema_row = mock.MagicMock()
        mock_schema_row.added_schema_count = 0
        mock_schema_row.deleted_schema_count = 0
        mock_schema_row.modified_schema_count = 0
        mock_schema_query_job = mock.MagicMock()
        mock_schema_query_job.result.return_value = [mock_schema_row]

        mock_client.query.side_effect = [
            mock_obs_query_job, mock_schema_query_job
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            curr_mcf = os.path.join(tmpdir, 'curr.mcf')
            prev_mcf = os.path.join(tmpdir, 'prev.mcf')
            out_dir = os.path.join(tmpdir, 'output')
            with open(curr_mcf, 'w', encoding='utf-8') as f:
                f.write(_SAMPLE_CURR_MCF)
            with open(prev_mcf, 'w', encoding='utf-8') as f:
                f.write(_SAMPLE_PREV_MCF)

            summary = bigquery_differ.run_bigquery_differ(
                current_data=curr_mcf,
                previous_data=prev_mcf,
                output_location=out_dir,
                project_id='test-project',
                job_name='test_job',
                dataset_id='test_dataset',
                shared_table_ids=shared_ids,
            )

            # Step 1 (current_data) was skipped; only previous_data (obs + schema = 2 loads) loaded
            self.assertEqual(mock_client.load_table_from_file.call_count, 2)
            self.assertEqual(summary['current_obs_count'], 15)
            self.assertEqual(summary['current_schema_count'], 2)
            self.assertEqual(summary['previous_obs_count'], 1)
            self.assertEqual(summary['added_obs_count'], 3)
            self.assertEqual(summary['modified_obs_count'], 1)

            deleted_tables = [
                call[0][0] for call in mock_client.delete_table.call_args_list
            ]
            self.assertIn(shared_ids['raw_obs'], deleted_tables)
            self.assertIn(shared_ids['raw_schema'], deleted_tables)
            self.assertIn(shared_ids['agg_obs'], deleted_tables)
            self.assertEqual(len(deleted_tables), 5)

    @mock.patch('bigquery_differ.bigquery.Client')
    def test_run_bigquery_differ_fallback_when_raw_obs_missing(
            self, mock_bq_client_cls):
        mock_client = mock_bq_client_cls.return_value

        shared_ids = bigquery_differ.get_import_bq_table_ids(
            'test-project.test_dataset', 'test_imp', '2026_09_17', 'input0')

        def _get_table(table_ref):
            if table_ref == shared_ids['raw_obs']:
                raise RuntimeError('Table not found')
            return mock.MagicMock()

        mock_client.get_table.side_effect = _get_table

        mock_obs_query_job = mock.MagicMock()
        mock_obs_query_job.to_dataframe.return_value = pd.DataFrame([{
            'StatVar': 'Count_Person',
            'ADDED': 1,
            'DELETED': 0,
            'MODIFIED': 1
        }])

        mock_schema_row = mock.MagicMock()
        mock_schema_row.added_schema_count = 0
        mock_schema_row.deleted_schema_count = 0
        mock_schema_row.modified_schema_count = 0
        mock_schema_query_job = mock.MagicMock()
        mock_schema_query_job.result.return_value = [mock_schema_row]

        mock_client.query.side_effect = [
            mock_obs_query_job, mock_schema_query_job
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            curr_mcf = os.path.join(tmpdir, 'curr.mcf')
            prev_mcf = os.path.join(tmpdir, 'prev.mcf')
            out_dir = os.path.join(tmpdir, 'output')
            with open(curr_mcf, 'w', encoding='utf-8') as f:
                f.write(_SAMPLE_CURR_MCF)
            with open(prev_mcf, 'w', encoding='utf-8') as f:
                f.write(_SAMPLE_PREV_MCF)

            summary = bigquery_differ.run_bigquery_differ(
                current_data=curr_mcf,
                previous_data=prev_mcf,
                output_location=out_dir,
                project_id='test-project',
                job_name='test_job',
                dataset_id='test_dataset',
                shared_table_ids=shared_ids,
            )

            # Both current and previous MCF files loaded (4 file load jobs)
            self.assertEqual(mock_client.load_table_from_file.call_count, 4)
            self.assertEqual(summary['current_obs_count'], 2)
            self.assertEqual(summary['previous_obs_count'], 1)


if __name__ == '__main__':
    unittest.main()
