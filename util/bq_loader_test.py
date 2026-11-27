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
"""Unit tests for util/bq_loader.py."""

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

from google.api_core import exceptions as gcp_exceptions
from google.cloud import bigquery

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.dirname(_SCRIPT_DIR)
for _p in (
        _DATA_DIR,
        _SCRIPT_DIR,
        os.path.join(_DATA_DIR, 'tools', 'statvar_importer'),
):
    if _p not in sys.path:
        sys.path.append(_p)

import bq_loader
from mcf_file_util import normalize_value

_COMPLEX_MCF = """# Header comment before first node
Node: dcid:obs_btb_1
typeOf: dcs:StatVarObservation
variableMeasured: dcs:Count_Person
observationAbout: dcid:country/USA
observationDate: "2020-01-01"
value: 100.0
Node: dcid:obs_btb_2
typeOf: dcs:StatVarObservation
variableMeasured: dcs:Mean_Concentration_AirPollutant_PM2.5
observationAbout: dcid:geoId/06085508102
observationDate: "2020-01-02"
observationPeriod: "P8H"
unit: PartsPerBillion
provenance: dcid:dc/p/test
value: 12.34

dcid: schema_no_node_1
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
measuredProperty: dcs:count
description: "Contains ; semicolon and : colon safely"

# Comment between blank-line-separated nodes without Node: property
dcid: schema_no_node_2
typeOf: dcs:StatisticalVariable
populationType: dcs:Household
measuredProperty: dcs:count

Node: l:obs_unicode_and_multival
typeOf: dcs:StatVarObservation
typeOf: dcs:Entity
variableMeasured: Count_Household
observationAbout: "Zürich"
observationDate: "2024"
value: 555
"""


class BqLoaderTest(unittest.TestCase):

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
            actual = bq_loader.normalize_prop_val(val)
            self.assertEqual(actual,
                             expected,
                             msg=f'Value mismatch for {val!r}')

        self.assertEqual(
            bq_loader.normalize_prop_val(['dcs:B', 'dcid:A']),
            'dcid:A, dcid:B',
        )

    def test_mcf_node_to_bq_record_obs_and_schema(self):
        stats: dict[str, int] = {}
        obs_row = bq_loader.mcf_node_to_bq_record(
            {
                'Node': 'l:obs1',
                'typeOf': 'dcs:StatVarObservation',
                'variableMeasured': 'dcs:Count_Person',
                'observationAbout': 'country/USA',
                'observationDate': '"2024"',
                'value': '22.0',
                'provenance': 'dcs:dc/p/src',
                '# comment1': '# ignored',
            },
            stats,
        )
        self.assertEqual(obs_row['dcid'], 'l:obs1')
        self.assertEqual(obs_row['typeOf'], 'dcid:StatVarObservation')
        self.assertEqual(
            obs_row['properties'],
            {
                'variableMeasured': 'dcid:Count_Person',
                'observationAbout': 'dcid:country/USA',
                'observationDate': '"2024"',
                'value': '22.0',
                'provenance': 'dcid:dc/p/src',
            },
        )
        self.assertEqual(stats.get('bq-obs-count'), 1)

        schema_row = bq_loader.mcf_node_to_bq_record(
            {
                'dcid': 'Count_Person',
                'typeOf': 'dcs:StatisticalVariable',
                'populationType': 'dcs:Person',
                'description': '"Has ; and :"',
            },
            stats,
        )
        self.assertEqual(schema_row['dcid'], 'dcid:Count_Person')
        self.assertEqual(schema_row['typeOf'], 'dcid:StatisticalVariable')
        self.assertEqual(
            schema_row['properties'],
            {
                'description': '"Has ; and :"',
                'populationType': 'dcid:Person',
            },
        )
        self.assertEqual(stats.get('bq-schema-count'), 1)

    def test_convert_mcf_to_jsonl_shards_parallel_exact_equivalence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mcf_path = os.path.join(tmpdir, 'complex.mcf')
            with open(mcf_path, 'w', encoding='utf-8') as f:
                f.write(_COMPLEX_MCF)

            ref_dir = os.path.join(tmpdir, 'ref')
            os.makedirs(ref_dir, exist_ok=True)
            ref_obs, ref_schema, ref_shards = (
                bq_loader.convert_mcf_to_jsonl_shards(
                    mcf_pattern=mcf_path,
                    output_dir=ref_dir,
                    max_workers=1,
                    chunk_size_bytes=64,
                ))
            self.assertEqual(ref_obs, 3)
            self.assertEqual(ref_schema, 2)
            self.assertEqual(len(ref_shards), 1)
            with open(ref_shards[0], 'r', encoding='utf-8') as f:
                expected_rows = [json.loads(line) for line in f]

            for chunk_bytes in (29, 64, 128):
                par_dir = os.path.join(tmpdir, f'par_{chunk_bytes}')
                os.makedirs(par_dir, exist_ok=True)
                o_cnt, s_cnt, shards = bq_loader.convert_mcf_to_jsonl_shards(
                    mcf_pattern=mcf_path,
                    output_dir=par_dir,
                    max_workers=2,
                    chunk_size_bytes=chunk_bytes,
                )
                self.assertEqual(o_cnt, ref_obs)
                self.assertEqual(s_cnt, ref_schema)
                self.assertGreater(len(shards), 1)

                actual_rows = []
                with bq_loader._ChainedLocalFileReader(
                        shards, skip_subsequent_headers=False) as chained:
                    data = chained.read()
                    self.assertEqual(chained.tell(), chained.total_size)
                    chained.seek(0)
                    self.assertEqual(chained.read(15) + chained.read(), data)
                    for line in data.decode('utf-8').splitlines():
                        actual_rows.append(json.loads(line))
                self.assertEqual(actual_rows, expected_rows)

    def test_load_files_to_bq_table_multi_uri_and_empty(self):
        mock_client = mock.MagicMock()
        mock_table = mock.MagicMock()
        mock_client.get_table.return_value = mock_table

        uris = [
            'gs://bucket/mcf_00000-of-00002.jsonl',
            'gs://bucket/mcf_00001-of-00002.jsonl',
        ]
        bq_loader.load_files_to_bq_table(
            mock_client,
            uris,
            'proj.ds.tbl',
            schema=bq_loader.MCF_BQ_SCHEMA,
            expiration_hours=6,
        )
        mock_client.load_table_from_uri.assert_called_once()
        self.assertEqual(mock_client.load_table_from_uri.call_args[0][0], uris)
        job_cfg = mock_client.load_table_from_uri.call_args.kwargs['job_config']
        self.assertEqual(job_cfg.source_format,
                         bigquery.SourceFormat.NEWLINE_DELIMITED_JSON)
        mock_client.update_table.assert_called_once()

        mock_client.reset_mock()
        bq_loader.load_files_to_bq_table(
            mock_client,
            [],
            'proj.ds.empty_tbl',
            schema=bq_loader.MCF_BQ_SCHEMA,
            expiration_hours=6,
        )
        mock_client.load_table_from_file.assert_called_once()
        mock_client.update_table.assert_called_once()

    def test_load_mcf_to_bq_table_cleans_up_temp_shards(self):
        mock_client = mock.MagicMock()
        mock_client.get_table.return_value = mock.MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            mcf_path = os.path.join(tmpdir, 'input.mcf')
            stage_dir = os.path.join(tmpdir, 'stage')
            os.makedirs(stage_dir, exist_ok=True)
            with open(mcf_path, 'w', encoding='utf-8') as f:
                f.write(_COMPLEX_MCF)

            counts = bq_loader.load_mcf_to_bq_table(
                bq_client=mock_client,
                mcf_pattern=mcf_path,
                table_ref='proj.ds.mcf_tbl',
                temp_dir=stage_dir,
                suffix='unit',
                expiration_hours=4,
                max_workers=2,
                chunk_size_bytes=64,
            )
            self.assertEqual(counts, {
                'obs_count': 3,
                'schema_count': 2,
                'total_count': 5,
            })
            mock_client.load_table_from_file.assert_called_once()
            mock_client.update_table.assert_called_once()
            self.assertEqual(os.listdir(stage_dir), [])

    def test_chained_local_file_reader_truncated_segment_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            seg = os.path.join(tmpdir, 'part.jsonl')
            with open(seg, 'wb') as f:
                f.write(b'{"a":1}\n')
            with bq_loader._ChainedLocalFileReader(
                [seg], skip_subsequent_headers=False) as reader:
                # Truncate file after reader computed segment size.
                with open(seg, 'wb'):
                    pass
                self.assertEqual(reader.read(), b'')

    def test_ensure_bq_dataset_creates_when_missing(self):
        mock_client = mock.MagicMock()
        mock_client.get_dataset.side_effect = gcp_exceptions.NotFound('missing')

        bq_loader.ensure_bq_dataset(mock_client,
                                    'proj.new_ds',
                                    expiration_hours=6)
        mock_client.create_dataset.assert_called_once()


if __name__ == '__main__':
    unittest.main()
