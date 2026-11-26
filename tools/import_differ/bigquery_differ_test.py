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

import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
for _p in (
        _DATA_DIR,
        _SCRIPT_DIR,
        os.path.join(_DATA_DIR, 'util'),
        os.path.join(_DATA_DIR, 'tools', 'statvar_importer'),
):
    if _p not in sys.path:
        sys.path.append(_p)

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
description: "Total count; updated: 2024"
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
description: "Total count; old: 2023"
"""


class BigQueryDifferTest(unittest.TestCase):

    def test_build_obs_diff_sql_uses_json_properties_and_numeric_compare(self):
        sql = bigquery_differ._build_obs_diff_sql('p.d.curr', 'p.d.prev')
        for prop in bigquery_differ.OBSERVATION_KEY_PROPERTIES:
            self.assertIn(f"JSON_VALUE(properties, '$.{prop}')", sql)
        self.assertIn("JSON_VALUE(properties, '$.value')", sql)
        self.assertIn('SAFE_CAST(c.value AS BIGNUMERIC)', sql)
        self.assertIn('SAFE_CAST(c.value AS FLOAT64)', sql)
        self.assertIn("WHERE diff_type != 'UNMODIFIED'", sql)

    def test_build_schema_diff_sql_uses_to_json_string_and_distinct(self):
        sql = bigquery_differ._build_schema_diff_sql('p.d.curr', 'p.d.prev')
        self.assertIn('SELECT DISTINCT', sql)
        self.assertIn('TO_JSON_STRING(properties)', sql)
        self.assertIn('ON c.dcid = p.dcid', sql)
        self.assertIn("WHERE diff_type != 'UNMODIFIED'", sql)

    def test_format_schema_mcf_node_preserves_semicolons_and_colons(self):
        block = bigquery_differ._format_schema_mcf_node(
            'dcid:Count_Person',
            'dcid:StatisticalVariable',
            json.dumps({
                'description': '"Has ; semicolon and : colon"',
                'populationType': 'dcid:Person',
            }),
        )
        self.assertEqual(
            block,
            'dcid: Count_Person\n'
            'description: "Has ; semicolon and : colon"\n'
            'populationType: dcid:Person\n'
            'typeOf: dcid:StatisticalVariable\n\n',
        )

    @mock.patch('bigquery_differ.bigquery.Client')
    def test_run_bigquery_differ_mocked(self, mock_bq_client_cls):
        mock_client = mock_bq_client_cls.return_value

        mock_table = mock.MagicMock()
        mock_client.get_table.return_value = mock_table

        mock_obs_query_job = mock.MagicMock()
        mock_obs_query_job.result.return_value = [
            {
                'variableMeasured': 'dcid:Count_Person',
                'observationAbout': 'dcid:country/CAN',
                'observationDate': '"2024"',
                'observationPeriod': '',
                'measurementMethod': '',
                'unit': '',
                'scalingFactor': '',
                'curr_value': '40000000',
                'prev_value': None,
                'curr_node': 'dcid:obs2',
                'prev_node': None,
                'diff_type': 'ADDED',
            },
            {
                'variableMeasured': 'dcid:Count_Person',
                'observationAbout': 'dcid:country/USA',
                'observationDate': '"2024"',
                'observationPeriod': '',
                'measurementMethod': '',
                'unit': '',
                'scalingFactor': '',
                'curr_value': '335000000',
                'prev_value': '330000000',
                'curr_node': 'dcid:obs1',
                'prev_node': 'dcid:obs1',
                'diff_type': 'MODIFIED',
            },
        ]

        mock_schema_query_job = mock.MagicMock()
        mock_schema_query_job.result.return_value = [
            {
                'dcid':
                    'dcid:Count_Person',
                'curr_type':
                    'dcid:StatisticalVariable',
                'prev_type':
                    'dcid:StatisticalVariable',
                'curr_props':
                    json.dumps({
                        'description': '"Total count; updated: 2024"',
                        'measuredProperty': 'dcid:count',
                        'populationType': 'dcid:Person',
                    }),
                'prev_props':
                    json.dumps({
                        'description': '"Total count; old: 2023"',
                        'measuredProperty': 'dcid:count',
                        'populationType': 'dcid:Person',
                    }),
                'diff_type':
                    'MODIFIED',
            },
        ]

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
                expiration_hours=6,
                max_workers=1,
            )

            self.assertEqual(summary['current_obs_count'], 2)
            self.assertEqual(summary['previous_obs_count'], 1)
            self.assertEqual(summary['current_schema_count'], 1)
            self.assertEqual(summary['previous_schema_count'], 1)
            self.assertEqual(summary['added_obs_count'], 1)
            self.assertEqual(summary['modified_obs_count'], 1)
            self.assertEqual(summary['obs_diff_count'], 2)
            self.assertEqual(summary['modified_schema_count'], 1)
            self.assertEqual(summary['schema_diff_count'], 1)

            summary_json_path = os.path.join(out_dir, 'differ_summary.json')
            summary_csv_path = os.path.join(out_dir, 'differ_summary.csv')
            added_mcf_path = os.path.join(out_dir, 'nodes-added.mcf')
            modified_mcf_path = os.path.join(out_dir, 'nodes-modified.mcf')
            original_mcf_path = os.path.join(out_dir, 'nodes-original.mcf')
            deleted_mcf_path = os.path.join(out_dir, 'nodes-deleted.mcf')

            self.assertTrue(os.path.exists(summary_json_path))
            self.assertTrue(os.path.exists(summary_csv_path))
            self.assertTrue(os.path.exists(added_mcf_path))
            self.assertTrue(os.path.exists(modified_mcf_path))
            self.assertTrue(os.path.exists(original_mcf_path))
            self.assertFalse(os.path.exists(deleted_mcf_path))

            with open(added_mcf_path, 'r', encoding='utf-8') as f:
                added_text = f.read()
                self.assertIn('Node: dcid:obs2', added_text)
                self.assertIn('value: 40000000', added_text)

            with open(modified_mcf_path, 'r', encoding='utf-8') as f:
                mod_text = f.read()
                self.assertIn('value: 335000000', mod_text)
                self.assertIn('description: "Total count; updated: 2024"',
                              mod_text)

            with open(original_mcf_path, 'r', encoding='utf-8') as f:
                orig_text = f.read()
                self.assertIn('value: 330000000', orig_text)
                self.assertIn('description: "Total count; old: 2023"',
                              orig_text)

            with open(summary_json_path, 'r', encoding='utf-8') as f:
                saved_json = json.load(f)
                self.assertEqual(saved_json['obs_diff_count'], 2)
                self.assertEqual(saved_json['schema_diff_count'], 1)

            # Combined table loads once per version (curr + prev = 2 tables).
            self.assertEqual(mock_client.load_table_from_file.call_count, 2)
            self.assertEqual(mock_client.update_table.call_count, 2)
            mock_client.delete_table.assert_not_called()

    @mock.patch('file_util.storage.fileio.BlobWriter')
    @mock.patch('file_util.file_get_gcs_blob')
    def test_open_output_stream_gcs_write_ignores_flush(self, mock_get_blob,
                                                        mock_blob_writer_cls):
        mock_blob = mock.MagicMock()
        mock_get_blob.return_value = mock_blob
        raw_buf = io.BytesIO()
        raw_buf.close = mock.MagicMock()
        mock_blob_writer_cls.return_value = raw_buf

        with bigquery_differ._open_output_stream(
                'gs://test-bucket/nodes-added.mcf') as stream:
            stream.write('Node: dcid:obs1\nvalue: 1\n\n')

        mock_blob_writer_cls.assert_called_once()
        self.assertEqual(mock_blob_writer_cls.call_args.args[0], mock_blob)
        self.assertTrue(mock_blob_writer_cls.call_args.kwargs['ignore_flush'])
        raw_buf.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
