# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for file_util.py"""

import io
import math
import os
import sys
import tempfile
import unittest
from unittest import mock

from google.api_core import exceptions as gcp_exceptions

# Allows the following module imports to work when running as a script
_SCRIPTS_DIR = os.path.dirname(__file__)
if _SCRIPTS_DIR not in sys.path:
    sys.path.append(_SCRIPTS_DIR)

import file_util

_SAMPLE_CSV_HEADER = 'area,latitude,longitude,s2CellId,s2Level,water\n'
_SAMPLE_CSV_ROWS = [
    '0.894664,26.055635,84.131718,dcid:s2CellId/0x39925b1c00000000,13,1\n',
    '0.894664,26.055635,84.967151,dcid:s2CellId/0x39ed336400000000,13,1\n',
    '0.894731,26.046652,84.958168,dcid:s2CellId/0x39ed34a400000000,13,1\n',
]


def _create_sample_csv_files(test_dir: str):
    file_row_multipliers = {
        'sample_output.csv': 1,
        'sample_1.csv': 10,
        # ~10KB (>4KB sample window in file_estimate_num_rows)
        'sample_2.csv': 50,
    }
    for name, multiplier in file_row_multipliers.items():
        path = os.path.join(test_dir, name)
        with open(path, 'w') as f:
            f.write(_SAMPLE_CSV_HEADER)
            f.writelines(_SAMPLE_CSV_ROWS * multiplier)


class FileIOTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self._temp_dir = tempfile.TemporaryDirectory()
        self._test_dir = self._temp_dir.name
        _create_sample_csv_files(self._test_dir)

    def tearDown(self):
        self._temp_dir.cleanup()
        super().tearDown()

    def test_read_write(self):
        filename = file_util.file_get_matching(
            os.path.join(self._test_dir, 'sample*.csv'))[0]
        # Create a copy in a new directory
        copy_filename = file_util.file_get_name(file_path=os.path.join(
            os.path.join(self._test_dir, 'test'), 'copy'),
                                                suffix='temp')

        # Read from file and write to a copy.
        with file_util.FileIO(filename, mode='r') as input_file:
            with file_util.FileIO(copy_filename, mode='w',
                                  use_tempfile=True) as output_file:
                file_content = input_file.read()
                output_file.write(file_content)
                # Verify target file is empty until file is closed.
                self.assertEqual(0, file_util.file_get_size(copy_filename))

        # Output file should exists after file is closed.
        self.assertTrue(file_util.file_get_size(copy_filename) > 0)

        # Compare files.
        with open(filename) as expected_input:
            with open(copy_filename) as expected_output:
                self.assertEqual(expected_input.read(), expected_output.read())

    def test_write_exception_preserves_existing_file(self):
        target = os.path.join(self._test_dir, 'atomic_output.txt')
        with file_util.FileIO(target, mode='w') as f:
            f.write('original content')

        with self.assertRaises(RuntimeError):
            with file_util.FileIO(target, mode='w') as f:
                f.write('partial corrupt content')
                raise RuntimeError('simulated write failure')

        with file_util.FileIO(target, mode='r') as f:
            self.assertEqual('original content', f.read())

    @mock.patch('file_util.storage.fileio.BlobReader')
    @mock.patch('file_util.file_get_gcs_blob')
    def test_gcs_streaming_text_read_and_binary_read(self, mock_get_blob,
                                                     mock_blob_reader_cls):
        mock_blob = mock.MagicMock()
        mock_get_blob.return_value = mock_blob
        mock_blob_reader_cls.side_effect = [
            io.BytesIO('line1\nSão Paulo\n'.encode('utf-8')),
            io.BytesIO(b'raw-bytes'),
        ]

        with file_util.FileIO('gs://test-bucket/data.mcf',
                              mode='r',
                              use_tempfile=False) as f:
            self.assertEqual('line1\nSão Paulo\n', f.read())

        with file_util.FileIO('gs://test-bucket/data.mcf',
                              mode='rb',
                              use_tempfile=False) as f:
            self.assertEqual(b'raw-bytes', f.read())

        self.assertEqual(2, mock_blob_reader_cls.call_count)
        for call in mock_blob_reader_cls.call_args_list:
            self.assertEqual(call.args[0], mock_blob)
            self.assertGreater(call.kwargs['chunk_size'], 0)

    @mock.patch('file_util.file_get_gcs_blob', return_value=None)
    def test_gcs_streaming_read_missing_blob_raises(self, _):
        with self.assertRaises(FileNotFoundError):
            file_util.FileIO('gs://test-bucket/missing.mcf',
                             mode='r',
                             use_tempfile=False)

    @mock.patch('file_util.storage.fileio.BlobWriter')
    @mock.patch('file_util.file_get_gcs_blob')
    def test_gcs_streaming_text_write_ignores_flush(self, mock_get_blob,
                                                    mock_blob_writer_cls):
        mock_blob = mock.MagicMock()
        mock_get_blob.return_value = mock_blob
        raw_buf = io.BytesIO()
        raw_buf.close = mock.MagicMock()
        mock_blob_writer_cls.return_value = raw_buf

        with file_util.FileIO('gs://test-bucket/out.jsonl',
                              mode='w',
                              use_tempfile=False) as f:
            f.write('{"a":"1"}\n')

        mock_blob_writer_cls.assert_called_once()
        self.assertEqual(mock_blob_writer_cls.call_args.args[0], mock_blob)
        self.assertTrue(mock_blob_writer_cls.call_args.kwargs['ignore_flush'])
        raw_buf.close.assert_called_once()
        self.assertEqual(b'{"a":"1"}\n', raw_buf.getvalue())


class FileUtilsTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self._temp_dir = tempfile.TemporaryDirectory()
        self._test_dir = self._temp_dir.name
        _create_sample_csv_files(self._test_dir)

    def tearDown(self):
        self._temp_dir.cleanup()
        super().tearDown()

    def test_file_get_matching(self):
        files = file_util.file_get_matching(
            os.path.join(self._test_dir, 'sample*.csv'))
        self.assertTrue(len(files) > 2)
        for file in files:
            self.assertTrue(os.path.exists(file))

    def test_file_type(self):
        self.assertTrue(file_util.file_is_local('/abc/def.csv'))
        self.assertFalse(file_util.file_is_local('https://abc/def.csv'))
        self.assertFalse(
            file_util.file_is_local('gs://gcs_bucket/gcs_path/file.csv'))

        self.assertTrue(file_util.file_is_gcs('gs://some_bucket/some_path'))
        self.assertFalse(file_util.file_is_gcs('https://some_bucket/some_path'))
        self.assertFalse(file_util.file_is_gcs('/dir/some_path'))

        self.assertTrue(
            file_util.file_is_google_spreadsheet(
                'https://docs.google.com/spreadsheets/d/some-sheet-id/edit#gid=12345'
            ))
        self.assertFalse(
            file_util.file_is_google_spreadsheet('gs://folders/some-path'))
        self.assertFalse(
            file_util.file_is_google_spreadsheet(
                'http://drive.google.com/folders/some-path'))
        self.assertFalse(
            file_util.file_is_google_spreadsheet('/folders/some-path'))

    def test_file_get_estimate_num_rows(self):
        files = file_util.file_get_matching(
            os.path.join(self._test_dir, 'sample*.csv'))
        for file in files:
            estimate_rows = file_util.file_estimate_num_rows(file)
            with file_util.FileIO(file, 'r') as fp:
                num_lines = len(fp.readlines())
                self.assertTrue(
                    math.isclose(num_lines, estimate_rows, rel_tol=1))

    def test_file_get_estimate_num_rows_non_utf8(self):
        # latin-1 bytes within the first 4K bytes must not raise
        # UnicodeDecodeError.
        path = os.path.join(self._test_dir, 'latin1.dat')
        with open(path, 'wb') as f:
            f.write(b'GEO_ID|GEOGRAPHY\n')
            f.write('05000US66075|Hagåtña District, GU\n'.encode('latin-1') *
                    200)
        estimate_rows = file_util.file_estimate_num_rows(path)
        self.assertTrue(math.isclose(201, estimate_rows, rel_tol=0.1))

    def test_file_load_csv_dict(self):
        csv_dict = file_util.file_load_csv_dict(
            os.path.join(self._test_dir, 'sample_output.csv'), 's2CellId')
        self.assertTrue(len(csv_dict) > 0)
        test_key = 'dcid:s2CellId/0x39925b1c00000000'
        self.assertTrue(test_key in csv_dict)
        self.assertEqual('1', csv_dict[test_key]['water'])
        self.assertEqual('13', csv_dict[test_key]['s2Level'])

    def test_file_write_load_py_dict(self):
        test_dict = {'test_key': 'test_value', 'int_key': 10, 'list': [1, 2, 3]}
        # read/write dict as a py file
        tmp_py_filename = os.path.join(self._test_dir, 'test_dict.py')
        file_util.file_write_py_dict(test_dict, tmp_py_filename)
        self.assertTrue(os.path.getsize(tmp_py_filename) > 10)
        read_dict = file_util.file_load_py_dict(tmp_py_filename)
        self.assertEqual(test_dict, read_dict)
        # Repeat test with pkl file.
        tmp_pkl_filename = os.path.join(self._test_dir, 'test_dict.pkl')
        file_util.file_write_py_dict(test_dict, tmp_pkl_filename)
        self.assertTrue(os.path.getsize(tmp_pkl_filename) > 10)
        read_pkl_dict = file_util.file_load_py_dict(tmp_pkl_filename)
        self.assertEqual(test_dict, read_pkl_dict)
        # check pkl and py files are different.
        self.assertTrue(
            file_util.file_get_size(tmp_pkl_filename) !=
            file_util.file_get_size(tmp_py_filename))

    def test_file_list_with_sizes_and_remove(self):
        items = file_util.file_list_with_sizes(
            os.path.join(self._test_dir, 'sample_*.csv'))
        self.assertEqual(3, len(items))
        for path, size in items:
            self.assertEqual(os.path.getsize(path), size)

        target = items[0][0]
        file_util.file_remove(target)
        self.assertFalse(os.path.exists(target))
        # Removing a non-existent file is a safe no-op.
        file_util.file_remove(target)

    @mock.patch('file_util.file_get_gcs_bucket')
    def test_file_list_with_sizes_gcs_wildcard(self, mock_get_bucket):
        mock_bucket = mock.MagicMock()
        mock_bucket.name = 'my-bucket'
        blob1 = mock.MagicMock()
        blob1.name = 'dir/a.mcf'
        blob1.size = 100
        blob2 = mock.MagicMock()
        blob2.name = 'dir/b.txt'
        blob2.size = 50
        blob3 = mock.MagicMock()
        blob3.name = 'dir/c.mcf'
        blob3.size = 250
        mock_bucket.list_blobs.return_value = [blob3, blob2, blob1]
        mock_get_bucket.return_value = mock_bucket

        items = file_util.file_list_with_sizes('gs://my-bucket/dir/*.mcf')
        self.assertEqual(
            [
                ('gs://my-bucket/dir/a.mcf', 100),
                ('gs://my-bucket/dir/c.mcf', 250),
            ],
            items,
        )
        mock_bucket.list_blobs.assert_called_once_with(prefix='dir/')

    @mock.patch('file_util.file_get_gcs_blob')
    def test_file_remove_gcs_ignores_not_found(self, mock_get_blob):
        mock_blob = mock.MagicMock()
        mock_blob.delete.side_effect = gcp_exceptions.NotFound('missing')
        mock_get_blob.return_value = mock_blob

        file_util.file_remove('gs://my-bucket/tmp/part.jsonl')
        mock_blob.delete.assert_called_once()


if __name__ == '__main__':
    unittest.main()
