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
"""Unit tests for `JsonFileDictIO`, `is_json_file`, and `is_jsonl_file`."""

import json
import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_UTIL_DIR = os.path.dirname(_SCRIPT_DIR)
if _UTIL_DIR not in sys.path:
    sys.path.insert(0, _UTIL_DIR)

from file_dict_io import JsonFileDictIO, is_json_file, is_jsonl_file, open_dict_file


class JsonFileDictIOTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_is_json_and_jsonl_file(self):
        self.assertTrue(is_json_file('data/records.json'))
        self.assertTrue(is_json_file('data/records.jsonl'))
        self.assertTrue(is_json_file('data/records.ndjson'))
        self.assertFalse(is_json_file('data/records.csv'))

        self.assertTrue(is_jsonl_file('data/records.jsonl'))
        self.assertTrue(is_jsonl_file('data/records.ndjson'))
        self.assertFalse(is_jsonl_file('data/records.json'))

    def test_json_and_jsonl_write_and_read(self):
        data = [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]
        for ext in ['.json', '.jsonl']:
            file_path = os.path.join(self.test_dir.name, f'test{ext}')
            with JsonFileDictIO(file_path, mode='w') as writer:
                for row in data:
                    writer.write_record(row)

            with JsonFileDictIO(file_path, mode='r') as reader:
                read_data = reader.readlines()
                self.assertEqual(data, read_data)

        # Verify multi-line pretty-printed JSON objects are streamed line-by-line up to closing '}'
        multiline_path = os.path.join(self.test_dir.name, 'multiline.json')
        with open(multiline_path, 'w') as fp:
            fp.write(
                '[\n  {\n    "name": "Alice",\n    "meta": {\n      "id": 1\n    }\n  },\n'
                '  {\n    "name": "Bob",\n    "meta": {\n      "id": 2\n    }\n  }\n]\n'
            )
        with open_dict_file(multiline_path, 'r') as reader:
            self.assertEqual([
                {'name': 'Alice', 'meta': {'id': 1}},
                {'name': 'Bob', 'meta': {'id': 2}},
            ], reader.readlines())

    def test_json_nested_dicts_and_escaped_characters(self):
        complex_records = [
            {
                'id': '1',
                'nested': {'level1': {'level2': [1, 2, {'k': 'v'}]}},
                'braces_in_str': 'value with } and { and }} inside string',
                'escaped': 'quote: \"} backslash: \\\\ parens: (a, b) [c]',
            },
            {
                'id': '2',
                'nested': {'empty': {}},
                'braces_in_str': '} leading and trailing {',
                'escaped': 'line1\\nline2 (escaped) \"nested_quote_with_}_inside\"',
            },
        ]
        for ext in ['.json', '.jsonl']:
            file_path = os.path.join(self.test_dir.name, f'complex{ext}')
            with open_dict_file(file_path, 'w') as writer:
                writer.write(complex_records)
            with open_dict_file(file_path, 'r') as reader:
                self.assertEqual(complex_records, reader.readlines())

        pretty_json_path = os.path.join(self.test_dir.name,
                                        'complex_pretty.json')
        with open(pretty_json_path, 'w') as fp:
            json.dump(complex_records, fp, indent=2)
        with open_dict_file(pretty_json_path, 'r') as reader:
            self.assertEqual(complex_records, reader.readlines())

    def test_json_drop_in_compatibility(self):
        rows = [
            {'dcid': 'dc/1', 'value': '100'},
            {'dcid': 'dc/2', 'value': '200'},
        ]
        for ext in ['.json', '.jsonl']:
            file_path = os.path.join(self.test_dir.name, f'drop_in{ext}')
            with open_dict_file(file_path, 'w') as writer:
                writer.writeheader()
                writer.writerow(rows[0])
                writer.writerows([rows[1]])
                self.assertEqual(2, writer.line_num)

            with open_dict_file(file_path, 'r') as reader:
                self.assertEqual(rows, [row for row in reader])
                self.assertEqual(2, reader.line_num)


if __name__ == '__main__':
    unittest.main()
