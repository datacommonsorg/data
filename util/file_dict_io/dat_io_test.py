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
"""Unit tests for `DatFileDictIO` and `is_dat_file`."""

from io import UnsupportedOperation
import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_UTIL_DIR = os.path.dirname(_SCRIPT_DIR)
if _UTIL_DIR not in sys.path:
    sys.path.insert(0, _UTIL_DIR)

from file_dict_io import DatFileDictIO
from file_dict_io import is_dat_file
from file_dict_io import open_dict_file


class DatFileDictIOTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def _write_file(self,
                    name: str,
                    content: str,
                    encoding: str = 'utf-8') -> str:
        """Writes `content` to a file in the test directory and returns its path."""
        path = os.path.join(self.test_dir.name, name)
        with open(path, 'w', encoding=encoding, newline='') as f:
            f.write(content)
        return path

    def _read_all(self, path: str, **kwargs) -> list:
        """Returns all records read from `path` with `DatFileDictIO`."""
        with DatFileDictIO(path, mode='r', **kwargs) as reader:
            return list(reader)

    def test_is_dat_file(self):
        self.assertTrue(is_dat_file('data/observations.dat'))
        self.assertTrue(is_dat_file('data/EC2200BASIC.DAT'))
        self.assertTrue(is_dat_file('data/observations.dat.gz'))
        self.assertFalse(is_dat_file('data/observations.csv'))
        self.assertFalse(is_dat_file('data/schema.mcf'))
        self.assertFalse(is_dat_file('data/EC2200BASIC_FIELDS.txt'))

    def test_open_dict_file_selects_dat_handler(self):
        path = self._write_file('people.dat', 'name|age\nAlice|30\n')
        with open_dict_file(path) as reader:
            self.assertIsInstance(reader, DatFileDictIO)

    def test_dat_read(self):
        path = self._write_file('test.dat', 'name|age\nAlice|30\nBob|25\n')
        reader = DatFileDictIO(path, mode='r')
        read_data = []
        while True:
            row = reader.next()
            if row is None:
                break
            read_data.append(row)
        reader.close()

        self.assertEqual(['name', 'age'], reader.headers())
        self.assertEqual([{
            'name': 'Alice',
            'age': '30'
        }, {
            'name': 'Bob',
            'age': '25'
        }], read_data)

    def test_values_kept_as_strings(self):
        # Leading zeros and commas inside values are preserved.
        path = self._write_file(
            'people.dat', 'name|age|city\n'
            'Alice|30|San Francisco, CA\n'
            'Bob|07|New York, NY\n')
        self.assertEqual([
            {
                'name': 'Alice',
                'age': '30',
                'city': 'San Francisco, CA'
            },
            {
                'name': 'Bob',
                'age': '07',
                'city': 'New York, NY'
            },
        ], self._read_all(path))

    def test_tab_delimited(self):
        path = self._write_file('people.dat', 'name\tage\nAlice\t30\n')
        self.assertEqual([{'name': 'Alice', 'age': '30'}], self._read_all(path))

    def test_header_cleanup(self):
        # Leading '#' and surrounding spaces are removed from header names.
        path = self._write_file('ec.dat', '#GEOTYPE| ST |EMP_F \n01|06|D\n')
        with DatFileDictIO(path, mode='r') as reader:
            self.assertEqual(['GEOTYPE', 'ST', 'EMP_F'], reader.headers())
            self.assertEqual([{
                'GEOTYPE': '01',
                'ST': '06',
                'EMP_F': 'D'
            }], list(reader))

    def test_bom_removed_from_header(self):
        path = self._write_file('bom.dat', '\ufeffname|age\nAlice|30\n')
        with DatFileDictIO(path, mode='r') as reader:
            self.assertEqual(['name', 'age'], reader.headers())
            self.assertEqual([{'name': 'Alice', 'age': '30'}], list(reader))

    def test_quotes_are_literal(self):
        # A stray quote must not swallow the delimiter and merge columns.
        path = self._write_file(
            'quotes.dat', 'name|nickname\n'
            '"Alice|Al\n'
            'Bob "B"|Bobby\n')
        self.assertEqual([
            {
                'name': '"Alice',
                'nickname': 'Al'
            },
            {
                'name': 'Bob "B"',
                'nickname': 'Bobby'
            },
        ], self._read_all(path))

    def test_empty_values(self):
        path = self._write_file('empty.dat', 'a|b|c\n1||3\n||\n')
        self.assertEqual([{
            'a': '1',
            'b': '',
            'c': '3'
        }, {
            'a': '',
            'b': '',
            'c': ''
        }], self._read_all(path))

    def test_crlf_line_endings(self):
        path = self._write_file('crlf.dat', 'name|age\r\nAlice|30\r\n')
        self.assertEqual([{'name': 'Alice', 'age': '30'}], self._read_all(path))

    def test_latin1_encoding(self):
        path = self._write_file('latin1.dat',
                                'name|city\nJosé|Bogotá\n',
                                encoding='latin-1')
        self.assertEqual([{
            'name': 'José',
            'city': 'Bogotá'
        }], self._read_all(path))

    def test_header_only_file(self):
        path = self._write_file('header_only.dat', 'name|age\n')
        with DatFileDictIO(path, mode='r') as reader:
            self.assertEqual(['name', 'age'], reader.headers())
            self.assertEqual([], list(reader))

    def test_write_mode_not_supported(self):
        path = os.path.join(self.test_dir.name, 'out.dat')
        with self.assertRaises(UnsupportedOperation):
            DatFileDictIO(path, mode='w', headers=['name'])

    def test_byte_range_reads_cover_all_rows_once(self):
        rows = ''.join(f'row{i}|{i:03d}\n' for i in range(100))
        path = self._write_file('ranges.dat', 'name|value\n' + rows)
        expected = self._read_all(path)
        mid = os.path.getsize(path) // 2
        first = self._read_all(path, end_offset=mid)
        second = self._read_all(path, start_offset=mid)
        self.assertEqual(100, len(expected))
        self.assertEqual(expected, first + second)
        # Records read from an offset still use the cleaned header names.
        self.assertEqual(['name', 'value'], list(second[0].keys()))


if __name__ == '__main__':
    unittest.main()
