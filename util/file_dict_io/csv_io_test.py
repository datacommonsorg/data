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
"""Unit tests for `CsvFileDictIO` and `is_csv_file`."""

import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_UTIL_DIR = os.path.dirname(_SCRIPT_DIR)
if _UTIL_DIR not in sys.path:
    sys.path.insert(0, _UTIL_DIR)

from file_dict_io import CsvFileDictIO, is_csv_file, open_dict_file


class CsvFileDictIOTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_is_csv_file(self):
        self.assertTrue(is_csv_file('data/observations.csv'))
        self.assertTrue(is_csv_file('data/observations.tsv'))
        self.assertFalse(is_csv_file('data/nodes.mcf'))
        self.assertFalse(is_csv_file('data/records.json'))

    def test_csv_write_and_read(self):
        csv_file_path = os.path.join(self.test_dir.name, 'test.csv')
        headers = ['name', 'age']
        data = [{'name': 'Alice', 'age': '30'}, {'name': 'Bob', 'age': '25'}]

        writer = CsvFileDictIO(csv_file_path, mode='w', headers=headers)
        for row in data:
            writer.write_record(row)
        writer.close()

        reader = CsvFileDictIO(csv_file_path, mode='r')
        read_data = []
        while True:
            row = reader.next()
            if row is None:
                break
            read_data.append(row)
        reader.close()

        self.assertEqual(headers, reader.headers())
        self.assertEqual(data, read_data)

    def test_csv_write_without_headers_and_iteration(self):
        csv_file_path = os.path.join(self.test_dir.name, 'no_headers.csv')
        data = [{'name': 'Alice', 'age': '30'}, {'name': 'Bob', 'age': '25'}]

        with open_dict_file(csv_file_path, 'w') as writer:
            writer.write(data)
            self.assertEqual(2, writer.current_record_index())

        with open_dict_file(csv_file_path, 'r') as reader:
            self.assertEqual(['name', 'age'], reader.headers())
            self.assertEqual(data, [row for row in reader])

    def test_csv_dict_reader_writer_drop_in_compatibility(self):
        csv_file_path = os.path.join(self.test_dir.name, 'drop_in.csv')
        headers = ['dcid', 'value']
        rows = [
            {'dcid': 'dc/1', 'value': '100'},
            {'dcid': 'dc/2', 'value': '200'},
        ]

        with open_dict_file(csv_file_path, 'w', headers=headers) as writer:
            writer.writeheader()
            writer.writerow(rows[0])
            writer.writerows([rows[1]])
            self.assertEqual(headers, writer.fieldnames)
            self.assertEqual(2, writer.line_num)

        with open_dict_file(csv_file_path, 'r') as reader:
            self.assertEqual(headers, reader.fieldnames)
            self.assertEqual(rows, reader.readlines())
            self.assertEqual(2, reader.line_num)


if __name__ == '__main__':
    unittest.main()
