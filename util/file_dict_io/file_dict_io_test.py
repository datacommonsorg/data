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

import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_UTIL_DIR = os.path.dirname(_SCRIPT_DIR)
for _path in (_SCRIPT_DIR, _UTIL_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from avro_io_test import AvroFileDictIOTest
from csv_io_test import CsvFileDictIOTest
from file_dict_io import (
    AvroFileDictIO,
    CsvFileDictIO,
    FileDictIO,
    JsonFileDictIO,
    McfFileDictIO,
    ShardedFileDictIO,
    open_dict_file,
)
from json_io_test import JsonFileDictIOTest
from mcf_io_test import McfFileDictIOTest
from sharded_io_test import ShardedFileDictIOTest
from file_sharder_test import TestFileSharder


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

        with open_dict_file(avro_file_path, 'w', headers=['a', 'b']) as avro_file:
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


if __name__ == '__main__':
    unittest.main()
