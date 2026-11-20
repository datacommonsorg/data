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
from mcf_file_util import normalize_value

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

_COMPLEX_CHUNK_MCF = """# Header comment before first node
Node: dcid:obs_btb_1
typeOf: dcs:StatVarObservation
variableMeasured: dcs:Count_Person
observationAbout: dcid:country/USA
observationDate: "2020-01-01"
value: 100
Node: dcid:obs_btb_2
typeOf: dcs:StatVarObservation
variableMeasured: dcs:Mean_Concentration_AirPollutant_PM2.5
observationAbout: dcid:geoId/06085508102
observationDate: "2020-01-02"
observationPeriod: "P8H"
unit: PartsPerBillion
value: 12.34

dcid: schema_no_node_1
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
measuredProperty: dcs:count

# Comment between blank-line-separated nodes without Node: property
dcid: schema_no_node_2
typeOf: dcs:StatisticalVariable
populationType: dcs:Household
measuredProperty: dcs:count
description: "Long description spanning multiple small byte-range chunk boundaries"

Node: obs_unicode_and_multival
typeOf: dcs:StatVarObservation
typeOf: dcs:Entity
variableMeasured: Count_Household
observationAbout: "Zürich"
observationDate: "2024"
value: 555
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
                self.assertEqual(list(rows[0].keys()),
                                 ['key_combined', 'value', 'node_id'])
                self.assertEqual(rows[0]['value'], '335000000')
                self.assertEqual(rows[0]['node_id'], 'dcid:obs1')
                self.assertTrue(
                    rows[0]['key_combined'].startswith('dcid:Count_Person;'))
                self.assertIn('dcid:country/USA', rows[0]['key_combined'])

            with open(schema_csv, 'r', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['dcid'], 'dcid:Count_Person')
                self.assertIn('populationType:dcid:Person',
                              rows[0]['value_combined'])

    def test_normalize_prop_val_matches_normalize_value(self):
        sample_values = [
            '',
            '   ',
            'dcid:Count_Person',
            'dcs:Mean_Concentration_AirPollutant_PM2.5',
            'schema:City',
            'l:LocalEntity',
            'dcid:geoId/06085508102',
            'PartsPerBillion',
            '"2024"',
            '"2020-12-31"',
            '"P8H"',
            '2020-12-31',
            '335000000',
            '1,234.50',
            '1,234.00',
            '-42.5',
            '$1,234.56',
            'dcid:12345',
            'dcid:foo:bar',
            ':leading_colon',
            '[10 20 Years]',
            '[Years 10 -]',
            'dcs:B, dcs:A',
            '"a, b, c"',
            'dcs:Z__A',
            '"' + 'x' * 120 + '"',
            '"Zürich, Switzerland"',
            'dcid:\tfoo',
        ]
        for val in sample_values:
            expected = str(normalize_value(val))
            actual = bigquery_differ._normalize_prop_val(val)
            self.assertEqual(actual,
                             expected,
                             msg=f'Value mismatch for {val!r}')

        self.assertEqual(
            bigquery_differ._normalize_prop_val(['dcs:B', 'dcid:A']),
            'dcid:A, dcid:B',
        )

    def test_parallel_byte_range_chunking_exact_equivalence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mcf_path = os.path.join(tmpdir, 'complex.mcf')
            with open(mcf_path, 'w', encoding='utf-8') as f:
                f.write(_COMPLEX_CHUNK_MCF)

            ref_obs_csv = os.path.join(tmpdir, 'ref_obs.csv')
            ref_schema_csv = os.path.join(tmpdir, 'ref_schema.csv')
            ref_obs_cnt, ref_schema_cnt = bigquery_differ.stream_mcf_to_csv(
                mcf_path, ref_obs_csv, ref_schema_csv)
            self.assertEqual(ref_obs_cnt, 3)
            self.assertEqual(ref_schema_cnt, 2)

            with open(ref_obs_csv, 'r', encoding='utf-8') as f:
                expected_obs = list(csv.reader(f))
            with open(ref_schema_csv, 'r', encoding='utf-8') as f:
                expected_schema = list(csv.reader(f))

            for chunk_bytes in (17, 53, 128):
                shard_dir = os.path.join(tmpdir, f'shards_{chunk_bytes}')
                os.makedirs(shard_dir, exist_ok=True)
                o_cnt, s_cnt, obs_parts, schema_parts = (
                    bigquery_differ.convert_mcf_to_csv_shards(
                        mcf_pattern=mcf_path,
                        base_dir=shard_dir,
                        tag='_t',
                        max_workers=2,
                        chunk_size_bytes=chunk_bytes,
                    ))
                self.assertEqual(o_cnt, ref_obs_cnt)
                self.assertEqual(s_cnt, ref_schema_cnt)
                self.assertGreater(len(obs_parts), 1)

                with bigquery_differ._ChainedLocalCsvReader(obs_parts) as fh:
                    full_bytes = fh.read()
                    self.assertEqual(fh.tell(), fh.total_size)
                    fh.seek(0)
                    rewound = fh.read(10) + fh.read()
                    self.assertEqual(rewound, full_bytes)
                    actual_obs = list(
                        csv.reader(full_bytes.decode('utf-8').splitlines()))

                with bigquery_differ._ChainedLocalCsvReader(schema_parts) as fh:
                    actual_schema = list(
                        csv.reader(fh.read().decode('utf-8').splitlines()))

                self.assertEqual(actual_obs, expected_obs)
                self.assertEqual(actual_schema, expected_schema)

    def test_convert_mcf_to_csv_shards_skips_empty_schema_files(self):
        obs_only_mcf = """
Node: dcid:obs_only_1
typeOf: dcs:StatVarObservation
variableMeasured: dcid:Count_Person
observationAbout: dcid:country/USA
observationDate: "2024"
value: 10
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mcf_path = os.path.join(tmpdir, 'obs_only.mcf')
            shard_dir = os.path.join(tmpdir, 'shards')
            os.makedirs(shard_dir, exist_ok=True)
            with open(mcf_path, 'w', encoding='utf-8') as f:
                f.write(obs_only_mcf)

            o_cnt, s_cnt, obs_parts, schema_parts = (
                bigquery_differ.convert_mcf_to_csv_shards(
                    mcf_pattern=mcf_path,
                    base_dir=shard_dir,
                    max_workers=1,
                    chunk_size_bytes=64,
                ))
            self.assertEqual(o_cnt, 1)
            self.assertEqual(s_cnt, 0)
            self.assertEqual(len(obs_parts), 1)
            self.assertEqual(schema_parts, [])

    def test_load_csv_to_bq_table_multi_uri_and_empty_shards(self):
        mock_client = mock.MagicMock()
        mock_table = mock.MagicMock()
        mock_client.get_table.return_value = mock_table

        uris = [
            'gs://bucket/obs_part_00000.csv', 'gs://bucket/obs_part_00001.csv'
        ]
        bigquery_differ.load_csv_to_bq_table(
            mock_client,
            uris,
            'proj.ds.obs_tbl',
            bigquery_differ.OBS_BQ_SCHEMA,
            expiration_hours=6,
        )
        mock_client.load_table_from_uri.assert_called_once()
        self.assertEqual(mock_client.load_table_from_uri.call_args[0][0], uris)
        mock_client.update_table.assert_called_once()

        mock_client.reset_mock()
        bigquery_differ.load_csv_to_bq_table(
            mock_client,
            [],
            'proj.ds.empty_schema_tbl',
            bigquery_differ.SCHEMA_NODE_BQ_SCHEMA,
            expiration_hours=6,
        )
        mock_client.load_table_from_file.assert_called_once()
        mock_client.update_table.assert_called_once()

    @mock.patch('bigquery_differ.bigquery.Client')
    def test_run_bigquery_differ_mocked(self, mock_bq_client_cls):
        mock_client = mock_bq_client_cls.return_value

        mock_table = mock.MagicMock()
        mock_client.get_table.return_value = mock_table

        mock_obs_query_job = mock.MagicMock()
        mock_obs_query_job.result.return_value = [
            {
                'key_combined': 'dcid:Count_Person;dcid:country/CAN;"2024";;;;',
                'curr_value': '40000000',
                'prev_value': None,
                'curr_node': 'dcid:obs2',
                'prev_node': None,
                'diff_type': 'ADDED',
            },
            {
                'key_combined': 'dcid:Count_Person;dcid:country/USA;"2024";;;;',
                'curr_value': '335000000',
                'prev_value': '330000000',
                'curr_node': 'dcid:obs1',
                'prev_node': 'dcid:obs1',
                'diff_type': 'MODIFIED',
            },
        ]

        mock_schema_query_job = mock.MagicMock()
        mock_schema_query_job.result.return_value = []

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
                self.assertIn('value: 335000000', f.read())

            with open(original_mcf_path, 'r', encoding='utf-8') as f:
                self.assertIn('value: 330000000', f.read())

            with open(summary_json_path, 'r', encoding='utf-8') as f:
                saved_json = json.load(f)
                self.assertEqual(saved_json['obs_diff_count'], 2)

            self.assertEqual(mock_client.update_table.call_count, 4)
            mock_client.delete_table.assert_not_called()

    @mock.patch('bigquery_differ.storage.fileio.BlobWriter')
    @mock.patch('bigquery_differ.file_get_gcs_blob')
    def test_open_text_stream_gcs_write_ignores_flush(self, mock_get_blob,
                                                      mock_blob_writer_cls):
        mock_blob = mock.MagicMock()
        mock_get_blob.return_value = mock_blob
        raw_buf = io.BytesIO()
        raw_buf.close = mock.MagicMock()
        mock_blob_writer_cls.return_value = raw_buf

        with bigquery_differ._open_text_stream('gs://test-bucket/out.csv',
                                               mode='w') as stream:
            stream.write('col1,col2\n1,2\n')

        mock_blob_writer_cls.assert_called_once_with(mock_blob,
                                                     ignore_flush=True)
        raw_buf.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
