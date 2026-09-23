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
"""Unit tests for `McfFileDictIO` and `is_mcf_file`."""

import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_UTIL_DIR = os.path.dirname(_SCRIPT_DIR)
if _UTIL_DIR not in sys.path:
    sys.path.insert(0, _UTIL_DIR)

from file_dict_io import McfFileDictIO, is_mcf_file, open_dict_file


class McfFileDictIOTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_is_mcf_file(self):
        self.assertTrue(is_mcf_file('data/nodes.mcf'))
        self.assertTrue(is_mcf_file('data/template.tmcf'))
        self.assertFalse(is_mcf_file('data/observations.csv'))

    def test_mcf_write_and_read(self):
        mcf_file_path = os.path.join(self.test_dir.name, 'test.mcf')
        headers = ['# Test MCF']
        data = [{
            'Node': 'dcid:node1',
            'prop1': 'dcid:value1',
            'prop2': '"value2"'
        }, {
            'Node': 'dcid:node2',
            'prop1': 'dcid:value3',
            'prop2': '"value4"'
        }]

        with open_dict_file(mcf_file_path, mode='w', headers=headers) as writer:
            self.assertIsInstance(writer, McfFileDictIO)
            for node in data:
                writer.write_record(node)

        with open_dict_file(mcf_file_path, mode='r') as reader:
            self.assertIsInstance(reader, McfFileDictIO)
            read_data = reader.readlines()

        # Normalize read data for comparison
        normalized_read_data = []
        for node in read_data:
            normalized_node = {}
            for key, value in node.items():
                if key.startswith('#'):
                    continue
                if isinstance(value, list) and len(value) == 1:
                    normalized_node[key] = value[0]
                else:
                    normalized_node[key] = value
            normalized_read_data.append(normalized_node)

        self.assertEqual(len(data), len(normalized_read_data))
        for i in range(len(data)):
            self.assertDictEqual(data[i], normalized_read_data[i])


if __name__ == '__main__':
    unittest.main()
