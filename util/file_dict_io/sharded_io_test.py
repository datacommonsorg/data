# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for `ShardedFileDictIO` across CSV, MCF, Avro, and JSON formats."""

import csv
import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_UTIL_DIR = os.path.dirname(_SCRIPT_DIR)
if _UTIL_DIR not in sys.path:
    sys.path.insert(0, _UTIL_DIR)

from file_dict_io import (
    AvroFileDictIO,
    McfFileDictIO,
    ShardedFileDictIO,
    is_sharded_file,
    open_dict_file,
)


class ShardedFileDictIOTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_is_sharded_file(self):
        self.assertTrue(is_sharded_file('output@3.csv'))
        self.assertTrue(is_sharded_file('output*.avro'))
        self.assertTrue(is_sharded_file('output-{id}.mcf'))
        self.assertTrue(is_sharded_file(['file1.csv', 'file2.csv']))
        self.assertFalse(is_sharded_file('single_file.csv'))

    def test_shard_csv_write_and_read(self):
        data = [
            {'id': '11', 'value': 'a'},
            {'id': '21', 'value': 'b'},
            {'id': '11', 'value': 'c'},
            {'id': '31', 'value': 'd'},
        ]
        output_path = os.path.join(self.test_dir.name, 'output@3.csv')
        with open_dict_file(output_path, 'w', shard_key='{id}') as writer:
            self.assertIsInstance(writer, ShardedFileDictIO)
            writer.write(data)

        for i in range(3):
            shard_path = os.path.join(self.test_dir.name,
                                      f'output-{i:05d}-of-00003.csv')
            self.assertTrue(os.path.exists(shard_path))

        # Verify records with id='11' are routed to the same shard (shard 1)
        shard_1_path = os.path.join(self.test_dir.name,
                                    'output-00001-of-00003.csv')
        with open(shard_1_path, 'r') as f:
            rows = list(csv.DictReader(f))
            self.assertEqual(2, len(rows))
            self.assertEqual('11', rows[0]['id'])
            self.assertEqual('11', rows[1]['id'])

        # Read all shards back via open_dict_file('output@3.csv', 'r')
        with open_dict_file(output_path, 'r') as reader:
            self.assertIsInstance(reader, ShardedFileDictIO)
            read_rows = reader.readlines()
            self.assertEqual(4, len(read_rows))
            self.assertCountEqual(data, read_rows)

    def test_shard_mcf_write_and_read(self):
        data = [
            {'Node': 'dcid:node11', 'prop': 'a'},
            {'Node': 'dcid:node22', 'prop': 'b'},
            {'Node': 'dcid:node11', 'prop': 'c'},
            {'Node': 'dcid:node33', 'prop': 'd'},
        ]
        output_path = os.path.join(self.test_dir.name, 'output@3.mcf')
        with open_dict_file(output_path, 'w', shard_key='Node') as writer:
            self.assertIsInstance(writer, ShardedFileDictIO)
            writer.write(data)

        for i in range(3):
            shard_path = os.path.join(self.test_dir.name,
                                      f'output-{i:05d}-of-00003.mcf')
            self.assertTrue(os.path.exists(shard_path))

        shard_0_path = os.path.join(self.test_dir.name,
                                    'output-00000-of-00003.mcf')
        with McfFileDictIO(shard_0_path, 'r') as reader:
            nodes = reader.readlines()
            self.assertEqual(2, len(nodes))
            self.assertEqual('dcid:node11', nodes[0]['Node'])
            self.assertEqual('dcid:node11', nodes[1]['Node'])

        with open_dict_file(output_path, 'r') as sharded_reader:
            all_nodes = sharded_reader.readlines()
            self.assertEqual(4, len(all_nodes))

    def test_shard_avro_write_and_read(self):
        data = [
            {'dcid': 'dc/11', 'value': '100'},
            {'dcid': 'dc/22', 'value': '200'},
            {'dcid': 'dc/11', 'value': '300'},
            {'dcid': 'dc/33', 'value': '400'},
        ]
        output_path = os.path.join(self.test_dir.name, 'output@3.avro')
        with open_dict_file(output_path, 'w', shard_key='dcid') as writer:
            self.assertIsInstance(writer, ShardedFileDictIO)
            writer.write(data)

        for i in range(3):
            shard_path = os.path.join(self.test_dir.name,
                                      f'output-{i:05d}-of-00003.avro')
            self.assertTrue(os.path.exists(shard_path))
            with AvroFileDictIO(shard_path, 'r') as shard_reader:
                self.assertEqual(['dcid', 'value'], shard_reader.headers())

        with open_dict_file(output_path, 'r') as sharded_reader:
            read_rows = sharded_reader.readlines()
            self.assertEqual(4, len(read_rows))
            self.assertCountEqual(data, read_rows)

    def test_shard_options_skip_duplicates_limit_prefix_and_column_naming(self):
        data = [
            {'id': 'US_CA', 'value': 'a'},
            {'id': 'IN_MH', 'value': 'b'},
            {'id': 'US_CA', 'value': 'a'},  # duplicate
            {'id': 'US_NY', 'value': 'd'},
            {'id': 'IN_KA', 'value': 'e'},
        ]
        # 1. Test shard_skip_duplicates + shard_key_prefix_length=2 + shard_input_records=4
        output_path = os.path.join(self.test_dir.name, 'filtered@2.csv')
        config = {
            'shard_key': 'id',
            'shard_key_prefix_length': 2,
            'shard_skip_duplicates': True,
            'shard_input_records': 4,
        }
        with open_dict_file(output_path, 'w', config=config) as writer:
            writer.write(data)

        with open_dict_file(output_path, 'r') as reader:
            read_rows = reader.readlines()
            # 5th record skipped due to shard_input_records=4; 3rd skipped due to duplicate
            self.assertEqual(3, len(read_rows))
            self.assertCountEqual(
                [
                    {'id': 'US_CA', 'value': 'a'},
                    {'id': 'IN_MH', 'value': 'b'},
                    {'id': 'US_NY', 'value': 'd'},
                ],
                read_rows,
            )

        # 2. Test dynamic column-value shard naming ('by_country-{country}.csv')
        col_pattern = os.path.join(self.test_dir.name,
                                   'by_country-{country}.csv')
        country_rows = [
            {'country': 'USA', 'v': '1'},
            {'country': 'IND', 'v': '2'},
            {'country': 'USA', 'v': '3'},
        ]
        with open_dict_file(col_pattern, 'w', shard_key='country') as writer:
            writer.write(country_rows)

        usa_file = os.path.join(self.test_dir.name, 'by_country-USA.csv')
        ind_file = os.path.join(self.test_dir.name, 'by_country-IND.csv')
        self.assertTrue(os.path.exists(usa_file))
        self.assertTrue(os.path.exists(ind_file))
        with open_dict_file(usa_file, 'r') as usa_reader:
            self.assertEqual(
                [{'country': 'USA', 'v': '1'}, {'country': 'USA', 'v': '3'}],
                usa_reader.readlines(),
            )

    def test_shard_extension_before_at_sign(self):
        # Verify patterns of the form 'shards.mcf@10', 'shards.csv@3', 'shards.avro@3', 'shards.json@3'
        mcf_data = [
            {'Node': 'dcid:n1', 'typeOf': 'dcs:Place'},
            {'Node': 'dcid:n2', 'typeOf': 'dcs:Place'},
        ]
        mcf_pattern = os.path.join(self.test_dir.name, 'shards.mcf@10')
        with open_dict_file(mcf_pattern, 'w', shard_key='Node') as writer:
            self.assertIsInstance(writer, ShardedFileDictIO)
            writer.write(mcf_data)

        self.assertTrue(
            os.path.exists(
                os.path.join(self.test_dir.name, 'shards.mcf-00000-of-00010')))
        with open_dict_file(mcf_pattern, 'r') as reader:
            self.assertEqual(2, len(reader.readlines()))

        row_data = [
            {'dcid': 'dc/1', 'val': '10'},
            {'dcid': 'dc/2', 'val': '20'},
        ]
        for ext in ['csv', 'avro', 'json']:
            pattern = os.path.join(self.test_dir.name, f'shards.{ext}@3')
            with open_dict_file(pattern, 'w', shard_key='dcid') as writer:
                self.assertIsInstance(writer, ShardedFileDictIO)
                writer.write(row_data)

            self.assertTrue(
                os.path.exists(
                    os.path.join(self.test_dir.name,
                                 f'shards.{ext}-00000-of-00003')))
            with open_dict_file(pattern, 'r') as reader:
                self.assertCountEqual(row_data, reader.readlines())


if __name__ == '__main__':
    unittest.main()
