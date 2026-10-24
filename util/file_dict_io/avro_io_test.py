# Copyright 2026 Google LLC
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
"""Unit tests for `AvroFileDictIO` and `is_avro_file`."""

import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_UTIL_DIR = os.path.dirname(_SCRIPT_DIR)
if _UTIL_DIR not in sys.path:
    sys.path.insert(0, _UTIL_DIR)

from file_dict_io import AvroFileDictIO, is_avro_file, open_dict_file


class AvroFileDictIOTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_is_avro_file(self):
        self.assertTrue(is_avro_file('data/observations.avro'))
        self.assertFalse(is_avro_file('data/observations.csv'))

    def test_avro_write_and_read(self):
        avro_file_path = os.path.join(self.test_dir.name, 'test.avro')
        headers = ['name', 'age']
        data = [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': '25'}]
        expected_data = [{
            'name': 'Alice',
            'age': '30'
        }, {
            'name': 'Bob',
            'age': '25'
        }]

        writer = AvroFileDictIO(avro_file_path, mode='w', headers=headers)
        for row in data:
            writer.write_record(row)
        writer.close()

        reader = AvroFileDictIO(avro_file_path, mode='r')
        read_data = reader.readlines()
        reader.close()

        self.assertEqual(headers, reader.headers())
        self.assertEqual(expected_data, read_data)

    def test_avro_custom_schema_and_types(self):
        avro_file_path = os.path.join(self.test_dir.name, 'test_schema.avro')
        schema = {
            'name': 'Person',
            'type': 'record',
            'fields': [
                {'name': 'name', 'type': 'string'},
                {'name': 'age', 'type': 'int'},
                {'name': 'score', 'type': 'float'},
                {'name': 'active', 'type': 'boolean'},
            ],
        }
        input_data = [{
            'name': 'Alice',
            'age': '30',
            'score': '95.5',
            'active': 1
        }, {
            'name': 'Bob',
            'age': 25,
            'score': 88.0,
            'active': False
        }]
        expected_data = [{
            'name': 'Alice',
            'age': 30,
            'score': 95.5,
            'active': True
        }, {
            'name': 'Bob',
            'age': 25,
            'score': 88.0,
            'active': False
        }]

        with open_dict_file(avro_file_path, mode='w', schema=schema) as writer:
            writer.write(input_data)

        with open_dict_file(avro_file_path, mode='r') as reader:
            self.assertEqual(['name', 'age', 'score', 'active'],
                             reader.headers())
            self.assertEqual(expected_data, reader.readlines())

    def test_avro_write_without_headers_and_drop_in_compatibility(self):
        avro_file_path = os.path.join(self.test_dir.name, 'no_headers.avro')
        rows = [
            {'dcid': 'dc/1', 'value': '100'},
            {'dcid': 'dc/2', 'value': '200'},
        ]

        with open_dict_file(avro_file_path, 'w') as writer:
            writer.writerow(rows[0])
            writer.writerows([rows[1]])
            self.assertEqual(['dcid', 'value'], writer.fieldnames)
            self.assertEqual(2, writer.line_num)

        with open_dict_file(avro_file_path, 'r') as reader:
            self.assertEqual(['dcid', 'value'], reader.fieldnames)
            self.assertEqual(rows, [row for row in reader])
            self.assertEqual(2, reader.line_num)


if __name__ == '__main__':
    unittest.main()
