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
"""Unit tests for `FileDictIO` registry, `open_dict_file`, and all format handlers."""

from io import UnsupportedOperation
import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_UTIL_DIR = os.path.dirname(_SCRIPT_DIR)
for _path in (_SCRIPT_DIR, _UTIL_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from file_dict_io import AvroFileDictIO
from file_dict_io import CsvFileDictIO
from file_dict_io import FileDictIO
from file_dict_io import JsonFileDictIO
from file_dict_io import McfFileDictIO
from file_dict_io import ShardedFileDictIO
from file_dict_io import open_dict_file
from file_dict_io import open_file_dict


class FileDictIORegistryAndFactoryTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_handler_registry(self):
        self.assertIs(FileDictIO.get_handler('output@3.csv'), ShardedFileDictIO)
        self.assertIs(FileDictIO.get_handler('output*.avro'), ShardedFileDictIO)
        self.assertIs(FileDictIO.get_handler('data.csv'), CsvFileDictIO)
        self.assertIs(FileDictIO.get_handler('data.tsv'), CsvFileDictIO)
        self.assertIs(FileDictIO.get_handler('data.avro'), AvroFileDictIO)
        self.assertIs(FileDictIO.get_handler('data.json'), JsonFileDictIO)
        self.assertIs(FileDictIO.get_handler('data.jsonl'), JsonFileDictIO)
        self.assertIs(FileDictIO.get_handler('data.ndjson'), JsonFileDictIO)
        self.assertIs(FileDictIO.get_handler('data.mcf'), McfFileDictIO)
        self.assertIs(FileDictIO.get_handler('unknown.ext'), McfFileDictIO)

        registered = FileDictIO.get_registered_handlers()
        for expected_cls in (
                ShardedFileDictIO,
                CsvFileDictIO,
                AvroFileDictIO,
                JsonFileDictIO,
                McfFileDictIO,
        ):
            self.assertIn(expected_cls, registered)

    def test_open_dict_file_dispatch(self):
        csv_file_path = os.path.join(self.test_dir.name, 'test.csv')
        mcf_file_path = os.path.join(self.test_dir.name, 'test.mcf')
        avro_file_path = os.path.join(self.test_dir.name, 'test.avro')
        json_file_path = os.path.join(self.test_dir.name, 'test.json')
        jsonl_file_path = os.path.join(self.test_dir.name, 'test.jsonl')

        with open_dict_file(csv_file_path, 'w', headers=['a', 'b']) as csv_file:
            self.assertIsInstance(csv_file, CsvFileDictIO)

        with open_dict_file(mcf_file_path, 'w') as mcf_file:
            self.assertIsInstance(mcf_file, McfFileDictIO)

        with open_dict_file(avro_file_path, 'w', headers=['a',
                                                          'b']) as avro_file:
            self.assertIsInstance(avro_file, AvroFileDictIO)
            avro_file.write_record({'a': '1', 'b': '2'})

        with open_dict_file(avro_file_path, 'r') as avro_reader:
            self.assertIsInstance(avro_reader, AvroFileDictIO)
            self.assertEqual(['a', 'b'], avro_reader.headers())
            self.assertEqual({'a': '1', 'b': '2'}, avro_reader.next())
            self.assertIsNone(avro_reader.next())

        for path in [json_file_path, jsonl_file_path]:
            with open_dict_file(path, 'w') as json_writer:
                self.assertIsInstance(json_writer, JsonFileDictIO)
                json_writer.write({'a': '1', 'b': '2'})

            with open_dict_file(path, 'r') as json_reader:
                self.assertIsInstance(json_reader, JsonFileDictIO)
                self.assertEqual({'a': '1', 'b': '2'}, json_reader.read())
                self.assertIsNone(json_reader.read())

    def test_open_file_dict_alias(self):
        csv_path = os.path.join(self.test_dir.name, 'alias.csv')
        with open_file_dict(csv_path, 'w', headers=['x']) as writer:
            writer.write({'x': '10'})
        with open_file_dict(csv_path, 'r') as reader:
            self.assertEqual([{'x': '10'}], reader.readlines())

    def test_csv_parallel_chunk_reading(self):
        csv_path = os.path.join(self.test_dir.name, 'parallel.csv')
        headers = ['id', 'val', 'note']
        expected_records = [{
            'id': f'id_{i}',
            'val': str(i),
            'note': f'note_{i}'
        } for i in range(300)]

        with open_dict_file(csv_path, 'w', headers=headers) as writer:
            for rec in expected_records:
                writer.write(rec)

        file_size = os.path.getsize(csv_path)
        # Split into 3 byte chunks
        c1_end = file_size // 3
        c2_end = 2 * file_size // 3

        with open_dict_file(csv_path, 'r', start_offset=0,
                            end_offset=c1_end) as r1:
            records1 = r1.readlines()
            self.assertEqual(0, r1.start_offset())
            self.assertEqual(c1_end, r1.end_offset())

        with open_dict_file(csv_path,
                            'r',
                            start_offset=c1_end,
                            end_offset=c2_end) as r2:
            records2 = r2.readlines()

        with open_dict_file(csv_path,
                            'r',
                            start_offset=c2_end,
                            end_offset=file_size) as r3:
            records3 = r3.readlines()

        combined = records1 + records2 + records3
        self.assertEqual(len(expected_records), len(combined))
        self.assertEqual(expected_records, combined)

    def test_jsonl_parallel_chunk_reading(self):
        jsonl_path = os.path.join(self.test_dir.name, 'parallel.jsonl')
        expected_records = [{'id': f'id_{i}', 'val': i} for i in range(300)]

        with open_dict_file(jsonl_path, 'w') as writer:
            for rec in expected_records:
                writer.write(rec)

        file_size = os.path.getsize(jsonl_path)
        c1_end = file_size // 3
        c2_end = 2 * file_size // 3

        with open_dict_file(jsonl_path, 'r', start_offset=0,
                            end_offset=c1_end) as r1:
            records1 = r1.readlines()

        with open_dict_file(jsonl_path,
                            'r',
                            start_offset=c1_end,
                            end_offset=c2_end) as r2:
            records2 = r2.readlines()

        with open_dict_file(jsonl_path,
                            'r',
                            start_offset=c2_end,
                            end_offset=file_size) as r3:
            records3 = r3.readlines()

        combined = records1 + records2 + records3
        self.assertEqual(len(expected_records), len(combined))
        self.assertEqual(expected_records, combined)

    def test_mcf_parallel_chunk_reading(self):
        mcf_path = os.path.join(self.test_dir.name, 'parallel.mcf')
        expected_records = [{
            'Node': f'dcid:place_{i}',
            'typeOf': 'dcs:Place',
            'name': f'"Place {i}"'
        } for i in range(200)]

        with open_dict_file(mcf_path, 'w',
                            headers=['# MCF Test Data']) as writer:
            for rec in expected_records:
                writer.write(rec)

        file_size = os.path.getsize(mcf_path)
        c1_end = file_size // 3
        c2_end = 2 * file_size // 3

        with open_dict_file(mcf_path, 'r', start_offset=0,
                            end_offset=c1_end) as r1:
            records1 = r1.readlines()

        with open_dict_file(mcf_path,
                            'r',
                            start_offset=c1_end,
                            end_offset=c2_end) as r2:
            records2 = r2.readlines()

        with open_dict_file(mcf_path,
                            'r',
                            start_offset=c2_end,
                            end_offset=file_size) as r3:
            records3 = r3.readlines()

        combined = records1 + records2 + records3
        self.assertEqual(len(expected_records), len(combined))
        self.assertEqual(expected_records, combined)

    def test_avro_parallel_chunk_reading(self):
        avro_path = os.path.join(self.test_dir.name, 'parallel.avro')
        headers = ['id', 'val']
        expected_records = [{
            'id': f'id_{i}',
            'val': str(i)
        } for i in range(500)]

        with open_dict_file(avro_path, 'w', headers=headers) as writer:
            for rec in expected_records:
                writer.write(rec)

        file_size = os.path.getsize(avro_path)
        c1_end = file_size // 3
        c2_end = 2 * file_size // 3

        with open_dict_file(avro_path, 'r', start_offset=0,
                            end_offset=c1_end) as r1:
            records1 = r1.readlines()

        with open_dict_file(avro_path,
                            'r',
                            start_offset=c1_end,
                            end_offset=c2_end) as r2:
            records2 = r2.readlines()

        with open_dict_file(avro_path,
                            'r',
                            start_offset=c2_end,
                            end_offset=file_size) as r3:
            records3 = r3.readlines()

        combined = records1 + records2 + records3
        self.assertEqual(len(expected_records), len(combined))
        self.assertEqual(expected_records, combined)

    def test_seek_and_tell(self):
        csv_path = os.path.join(self.test_dir.name, 'seek_tell.csv')
        headers = ['id', 'val']
        with open_dict_file(csv_path, 'w', headers=headers) as writer:
            for i in range(20):
                writer.write({'id': f'id_{i:02d}', 'val': str(i)})

        with open_dict_file(csv_path, 'r') as reader:
            first_row = reader.next()
            self.assertEqual({'id': 'id_00', 'val': '0'}, first_row)
            # Seeking to offset 0 resets to first data record
            pos = reader.seek(0)
            self.assertGreater(pos, 0)
            row_again = reader.next()
            self.assertEqual({'id': 'id_00', 'val': '0'}, row_again)

    def test_seek_in_write_mode_raises_unsupported_operation(self):
        for ext in ('.csv', '.json', '.jsonl', '.mcf', '.avro'):
            path = os.path.join(self.test_dir.name, f'write_seek{ext}')
            with open_dict_file(path, 'w', headers=['id']) as writer:
                with self.assertRaises(UnsupportedOperation):
                    writer.seek(0)
                with self.assertRaises(UnsupportedOperation):
                    writer.seek(100)

    def test_start_offset_and_end_offset_beyond_file_size(self):
        for ext in ('.csv', '.json', '.jsonl', '.mcf', '.avro'):
            path = os.path.join(self.test_dir.name, f'bounds_test{ext}')
            with open_dict_file(path, 'w', headers=['id', 'val']) as writer:
                if ext == '.mcf':
                    writer.write({'Node': 'dcid:N1', 'typeOf': 'dcs:Person'})
                    writer.write({'Node': 'dcid:N2', 'typeOf': 'dcs:Person'})
                else:
                    writer.write({'id': '1', 'val': 'a'})
                    writer.write({'id': '2', 'val': 'b'})

            file_size = os.path.getsize(path)
            self.assertGreater(file_size, 0)

            # 1. start_offset beyond file size -> 0 records read
            with open_dict_file(path, 'r',
                                start_offset=file_size + 1000) as reader:
                records = reader.readlines()
                self.assertEqual([], records)

            # 2. end_offset beyond file size -> all records read to EOF
            with open_dict_file(path, 'r',
                                end_offset=file_size + 1000) as reader:
                records = reader.readlines()
                self.assertEqual(2, len(records))

            # 3. start_offset >= end_offset -> 0 records read
            with open_dict_file(path,
                                'r',
                                start_offset=file_size,
                                end_offset=file_size // 2) as reader:
                records = reader.readlines()
                self.assertEqual([], records)

    def _assert_exact_split_at_every_byte(self,
                                          path: str,
                                          expected: list,
                                          encoding: str = None):
        """Asserts `[0, b) + [b, None) == expected` for every byte offset `b`."""
        file_size = os.path.getsize(path)
        for split in range(0, file_size + 2):
            with open_dict_file(path,
                                'r',
                                encoding=encoding,
                                start_offset=0,
                                end_offset=split) as left_reader:
                left = left_reader.readlines()
            with open_dict_file(path,
                                'r',
                                encoding=encoding,
                                start_offset=split,
                                end_offset=None) as right_reader:
                right = right_reader.readlines()
            self.assertEqual(
                expected,
                left + right,
                msg=f'Mismatch at split={split}/{file_size} for {path}',
            )

    def test_utf8_multibyte_seek_every_byte_offset(self):
        # Exercises 2-byte, 3-byte, and 4-byte UTF-8 sequences, UTF-8 BOM,
        # intervening blank lines, leading indentation, and `NodeType` properties.
        csv_rows = [
            {
                'id': '1',
                'city': 'São Paulo'
            },
            {
                'id': '2',
                'city': 'München'
            },
            {
                'id': '3',
                'city': '東京都 🌏'
            },
        ]

        # 1. CSV with raw UTF-8 and blank line between records
        csv_path = os.path.join(self.test_dir.name, 'utf8.csv')
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write('id,city\n1,São Paulo\n\n2,München\n3,東京都 🌏\n')
        self._assert_exact_split_at_every_byte(csv_path, csv_rows)

        # 2. CSV with UTF-8 BOM (`utf-8-sig`) and multiline quoted header
        bom_csv_path = os.path.join(self.test_dir.name, 'bom_utf8.csv')
        with open(bom_csv_path, 'wb') as f:
            f.write(
                '\ufeff"id","city"\r\n1,São Paulo\r\n2,München\r\n3,東京都 🌏\r\n'.
                encode('utf-8'))
        self._assert_exact_split_at_every_byte(bom_csv_path,
                                               csv_rows,
                                               encoding='utf-8-sig')

        # 3. JSONL written with raw multi-byte UTF-8 (ensure_ascii=False) and blank lines
        jsonl_path = os.path.join(self.test_dir.name, 'utf8.jsonl')
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            f.write('{"id": "1", "city": "São Paulo"}\n\n')
            f.write('  {"id": "2", "city": "München"}\n')
            f.write('{"id": "3", "city": "東京都 🌏"}\n')
        self._assert_exact_split_at_every_byte(jsonl_path, csv_rows)

        # 4. Formatted JSON array with raw multi-byte UTF-8 and indentation
        json_path = os.path.join(self.test_dir.name, 'utf8.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write('[\n')
            f.write('  {"id": "1", "city": "São Paulo"},\n\n')
            f.write('  {"id": "2", "city": "München"},\n')
            f.write('  {"id": "3", "city": "東京都 🌏"}\n')
            f.write(']\n')
        self._assert_exact_split_at_every_byte(json_path, csv_rows)

        # 4b. Multi-line pretty-printed JSON array with nested objects
        pretty_json_path = os.path.join(self.test_dir.name, 'pretty_utf8.json')
        pretty_expected = [
            {
                'id': '1',
                'city': 'São Paulo',
                'meta': {
                    'nested': 1
                },
            },
            {
                'id': '2',
                'city': 'München',
                'meta': {
                    'nested': 2
                },
            },
            {
                'id': '3',
                'city': '東京都 🌏',
                'meta': {
                    'nested': 3
                },
            },
        ]
        with open(pretty_json_path, 'w', encoding='utf-8') as f:
            f.write('[\n')
            for idx, item in enumerate(pretty_expected):
                comma = ',' if idx < len(pretty_expected) - 1 else ''
                f.write('  {\n'
                        f'    "id": "{item["id"]}",\n'
                        f'    "city": "{item["city"]}",\n'
                        '    "meta":\n'
                        '    {\n'
                        f'      "nested": {item["meta"]["nested"]}\n'
                        '    }\n'
                        f'  }}{comma}\n')
            f.write(']\n')
        self._assert_exact_split_at_every_byte(pretty_json_path,
                                               pretty_expected)

        # 5. MCF with raw multi-byte UTF-8, header comment, and `NodeType` property
        mcf_path = os.path.join(self.test_dir.name, 'utf8.mcf')
        mcf_expected = [
            {
                'Node': 'dcid:city_1',
                'NodeType': 'dcs:City',
                'name': '"São Paulo"',
            },
            {
                'Node': 'dcid:city_2',
                'NodeType': 'dcs:City',
                'name': '"München"',
            },
            {
                'Node': 'dcid:city_3',
                'NodeType': 'dcs:City',
                'name': '"東京都 🌏"',
            },
        ]
        with open(mcf_path, 'w', encoding='utf-8') as f:
            f.write('# Cities — São Paulo / 東京都\n\n')
            for node in mcf_expected:
                f.write(f"Node: {node['Node']}\n"
                        f"NodeType: {node['NodeType']}\n"
                        f"name: {node['name']}\n\n")
        self._assert_exact_split_at_every_byte(mcf_path, mcf_expected)

    def test_avro_multiblock_parallel_chunk_reading(self):
        # Generate >120 KB payload so fastavro writes multiple blocks separated
        # by 16-byte sync markers, testing true mid-file Avro block splitting.
        avro_path = os.path.join(self.test_dir.name, 'multiblock.avro')
        headers = ['id', 'payload']
        expected_records = [{
            'id': f'id_{i:04d}',
            'payload': f'São Paulo München 東京都 {"x" * 120} {i}',
        } for i in range(1200)]

        with open_dict_file(avro_path, 'w', headers=headers) as writer:
            for rec in expected_records:
                writer.write(rec)

        file_size = os.path.getsize(avro_path)
        self.assertGreater(file_size, 100000)

        num_chunks = 7
        chunk_size = file_size // num_chunks
        combined = []
        non_empty_chunks = 0
        for i in range(num_chunks):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i < num_chunks - 1 else None
            with open_dict_file(avro_path,
                                'r',
                                start_offset=start,
                                end_offset=end) as reader:
                part = reader.readlines()
                if part:
                    non_empty_chunks += 1
                combined.extend(part)

        self.assertGreater(non_empty_chunks, 2)
        self.assertEqual(len(expected_records), len(combined))
        self.assertEqual(expected_records, combined)

    def test_case_insensitive_and_multi_extension_dispatch(self):
        self.assertIs(FileDictIO.get_handler('CENSUS.CSV'), CsvFileDictIO)
        self.assertIs(FileDictIO.get_handler('DATA.TSV'), CsvFileDictIO)
        self.assertIs(FileDictIO.get_handler('DATA.AVRO'), AvroFileDictIO)
        self.assertIs(FileDictIO.get_handler('DATA.JSON'), JsonFileDictIO)
        self.assertIs(FileDictIO.get_handler('DATA.JSONL'), JsonFileDictIO)
        self.assertIs(FileDictIO.get_handler('DATA.MCF'), McfFileDictIO)
        self.assertIs(FileDictIO.get_handler('table.csv.mcf'), McfFileDictIO)
        self.assertIs(FileDictIO.get_handler('table.mcf.csv'), CsvFileDictIO)
        self.assertIs(FileDictIO.get_handler('table.csv.json'), JsonFileDictIO)
        self.assertIs(FileDictIO.get_handler('table.avro.csv'), CsvFileDictIO)

    def test_write_in_read_mode_and_immediate_close(self):
        for ext in ('.csv', '.avro', '.json', '.jsonl', '.mcf'):
            path = os.path.join(self.test_dir.name, f'readonly{ext}')
            writer = open_dict_file(path,
                                    'w',
                                    headers=['id'] if ext != '.mcf' else None)
            held_fp = writer._fp
            writer.write({'Node': 'dcid:n1'} if ext == '.mcf' else {'id': '1'})
            writer.close()
            self.assertTrue(os.path.exists(path))
            del held_fp

            with open_dict_file(path, 'r') as reader:
                with self.assertRaises(UnsupportedOperation):
                    reader.write({'id': '2'})

    def test_bom_and_corner_case_formats(self):
        # 1. UTF-8 BOM in CSV, JSONL, and JSON without explicit encoding='utf-8-sig'
        expected = [{
            'id': '1',
            'city': 'São Paulo'
        }, {
            'id': '2',
            'city': 'München'
        }]
        bom_csv = os.path.join(self.test_dir.name, 'bom_default.csv')
        with open(bom_csv, 'wb') as f:
            f.write('\ufeffid,city\n1,São Paulo\n2,München\n'.encode('utf-8'))
        self._assert_exact_split_at_every_byte(bom_csv, expected)

        bom_jsonl = os.path.join(self.test_dir.name, 'bom_default.jsonl')
        with open(bom_jsonl, 'wb') as f:
            f.write(
                '\ufeff{"id": "1", "city": "São Paulo"}\n{"id": "2", "city": "München"}\n'
                .encode('utf-8'))
        self._assert_exact_split_at_every_byte(bom_jsonl, expected)

        # 2. JSON array starting with '[{...},' on line 1 and '}, {' on same line
        inline_bracket_json = os.path.join(self.test_dir.name,
                                           'inline_bracket.json')
        with open(inline_bracket_json, 'w', encoding='utf-8') as f:
            f.write('[{"id": "1", "city": "São Paulo"},\n'
                    ' {"id": "2", "city": "München"}]\n')
        self._assert_exact_split_at_every_byte(inline_bracket_json, expected)

        same_line_close_open_json = os.path.join(self.test_dir.name,
                                                 'close_open.json')
        with open(same_line_close_open_json, 'w', encoding='utf-8') as f:
            f.write('[\n'
                    '  {\n'
                    '    "id": "1",\n'
                    '    "city": "São Paulo"\n'
                    '  }, {\n'
                    '    "id": "2",\n'
                    '    "city": "München"\n'
                    '  }\n'
                    ']\n')
        self._assert_exact_split_at_every_byte(same_line_close_open_json,
                                               expected)

        # 3. Writing MCF records (with '# comment' keys) and ragged CSV rows (with None key)
        #    directly to headerless CSV and Avro writers filters out None and '#' keys.
        for ext in ('.csv', '.avro'):
            out_path = os.path.join(self.test_dir.name,
                                    f'filtered_headers{ext}')
            with open_dict_file(out_path, 'w') as writer:
                writer.write({
                    '# comment1': '# ignored comment',
                    None: ['extra'],
                    'id': '1',
                    'name': 'Alice',
                })
            with open_dict_file(out_path, 'r') as reader:
                self.assertEqual(['id', 'name'], reader.headers())
                self.assertEqual([{
                    'id': '1',
                    'name': 'Alice'
                }], reader.readlines())

        # 4. Tuple of files passed to open_dict_file dispatches to ShardedFileDictIO
        with open_dict_file((bom_csv, bom_jsonl), 'r') as tuple_reader:
            self.assertEqual(4, len(tuple_reader.readlines()))


if __name__ == '__main__':
    unittest.main()
