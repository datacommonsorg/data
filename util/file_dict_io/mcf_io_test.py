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

from file_dict_io import (
    McfFileDictIO,
    get_record_dcid,
    is_mcf_file,
    open_dict_file,
)


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

    def _write_mcf_text(self, nodes: list) -> str:
        """Writes `nodes` to an MCF file and returns the file text."""
        mcf_file_path = os.path.join(self.test_dir.name, 'nodes.mcf')
        with open_dict_file(mcf_file_path, mode='w') as writer:
            for node in nodes:
                writer.write_record(node)
        with open(mcf_file_path, 'r') as f:
            return f.read()

    def test_mcf_write_adds_node_from_dcid(self):
        record = {'dcid': 'geoId/06', 'typeOf': 'dcs:State'}
        text = self._write_mcf_text([record])
        self.assertTrue(text.startswith('Node: dcid:geoId/06\n'), text)
        # The caller's record is not modified.
        self.assertEqual({'dcid': 'geoId/06', 'typeOf': 'dcs:State'}, record)

    def test_mcf_write_blank_node_uses_dcid(self):
        text = self._write_mcf_text([{'Node': '', 'dcid': '"geoId/06"'}])
        self.assertTrue(text.startswith('Node: dcid:geoId/06\n'), text)

    def test_mcf_write_keeps_existing_node(self):
        text = self._write_mcf_text([{'Node': 'l:obs1', 'dcid': 'dc/o/abc'}])
        self.assertTrue(text.startswith('Node: l:obs1\n'), text)
        self.assertEqual(1, text.count('Node:'))

    def test_mcf_write_without_ids_has_no_node(self):
        text = self._write_mcf_text([{'dcid': '', 'value': '1'}])
        self.assertNotIn('Node:', text)

    def test_get_record_dcid(self):
        self.assertEqual('geoId/06', get_record_dcid({'dcid': 'geoId/06'}))
        self.assertEqual('geoId/06', get_record_dcid({'dcid': '"geoId/06"'}))
        self.assertEqual('geoId/06',
                         get_record_dcid({'Node': 'dcid:geoId/06'}))
        # A blank dcid falls back to the Node.
        self.assertEqual(
            'geoId/06', get_record_dcid({
                'dcid': '',
                'Node': 'dcid:geoId/06'
            }))
        # The dcid takes precedence over the Node.
        self.assertEqual(
            'dc/o/abc', get_record_dcid({
                'dcid': 'dc/o/abc',
                'Node': 'l:obs1'
            }))
        self.assertEqual('12345', get_record_dcid({'dcid': 12345}))
        self.assertEqual('', get_record_dcid({'dcid': '', 'Node': ' '}))
        self.assertEqual('', get_record_dcid({'value': '1'}))
        self.assertEqual('', get_record_dcid(None))


if __name__ == '__main__':
    unittest.main()
