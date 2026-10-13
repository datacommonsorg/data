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
                self.assertIn('dcid:country/USA', rows[0]['key_combined'])

            with open(schema_csv, 'r', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['dcid'], 'dcid:Count_Person')
                self.assertIn('populationType:dcid:Person',
                              rows[0]['value_combined'])

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


if __name__ == '__main__':
    unittest.main()
