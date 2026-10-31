#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for Australia Statistics download_script.py."""

import os
import sys
import tempfile
import unittest
from unittest import mock

# Ensure repository root is in sys.path for both local and root-level test runs
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '../..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.australia_statistics import download_script

for _flag_name in ('output_dir', 'max_workers'):
    if _flag_name in download_script._FLAGS:
        delattr(download_script._FLAGS, _flag_name)


class DownloadScriptTest(unittest.TestCase):

    def test_write_bytes_atomically_writes_and_cleans_up_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = os.path.join(tmp_dir, 'test.csv')
            with self.assertRaises(RuntimeError):
                download_script._write_bytes_atomically(target, b'')
            self.assertFalse(os.path.exists(target))

            with mock.patch.object(os.path, 'getsize', return_value=0):
                with self.assertRaises(RuntimeError):
                    download_script._write_bytes_atomically(
                        target, b'DATAFLOW,MEASURE\n')
            self.assertFalse(os.path.exists(target))
            self.assertEqual(os.listdir(tmp_dir), [])

            download_script._write_bytes_atomically(target,
                                                    b'DATAFLOW,MEASURE\n')
            self.assertTrue(os.path.exists(target))
            with open(target, 'rb') as f:
                self.assertEqual(f.read(), b'DATAFLOW,MEASURE\n')

    @mock.patch.object(download_script, '_fetch_bytes')
    def test_download_static_file_validates_sdmx_csv_header(self, mock_fetch):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_fetch.return_value = b'<html>Error Page</html>'
            with self.assertRaises(RuntimeError):
                download_script._download_static_file(
                    'abs_lf_sdmx.csv', 'https://example.com/lf.csv', tmp_dir)

            mock_fetch.return_value = b'DATAFLOW,MEASURE,OBS_VALUE\nABS:LF,M3,10\n'
            res = download_script._download_static_file(
                'abs_lf_sdmx.csv', 'https://example.com/lf.csv', tmp_dir)
            self.assertIn('abs_lf_sdmx.csv', res)
            self.assertTrue(
                os.path.exists(os.path.join(tmp_dir, 'abs_lf_sdmx.csv')))

    def test_cleanup_stale_files_removes_unexpected_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            keep_path = os.path.join(tmp_dir, 'abs_lf_sdmx.csv')
            stale_path = os.path.join(tmp_dir, 'obsolete_file.csv')
            with open(keep_path, 'w', encoding='utf-8') as f:
                f.write('DATAFLOW,\n')
            with open(stale_path, 'w', encoding='utf-8') as f:
                f.write('old\n')

            download_script._cleanup_stale_files(tmp_dir, {'abs_lf_sdmx.csv'})
            self.assertTrue(os.path.exists(keep_path))
            self.assertFalse(os.path.exists(stale_path))


if __name__ == '__main__':
    unittest.main()
