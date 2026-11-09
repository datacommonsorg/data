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
"""Unit tests for Japan Census download_script.py."""

import os
import sys
import tempfile
import unittest
from unittest import mock

# Ensure repository root and module directory are in sys.path for local and root-level test runs
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '../..'))
for _p in (_SCRIPT_DIR, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from statvar_imports.japan_census import download_script


class DownloadScriptTest(unittest.TestCase):

    def test_write_text_atomically_failure_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = os.path.join(tmp_dir, 'test_output.csv')
            with mock.patch.object(os.path, 'getsize', return_value=0):
                with self.assertRaises(RuntimeError):
                    download_script._write_text_atomically(
                        target_path, '"col1","col2"\n')
            self.assertFalse(os.path.exists(target_path))
            self.assertEqual(os.listdir(tmp_dir), [])

    @mock.patch.object(download_script, 'fetch_dbview_csv')
    def test_download_dbview_dataset_writes_raw_csv(self, mock_fetch_dbview):
        mock_fetch_dbview.return_value = '"col1","col2"\n"val1","val2"\n'
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = os.path.join(tmp_dir,
                                    'jpn_gender_age_total_population.csv')
            line_count = download_script.download_dbview_dataset(
                output_filepath=out_file,
                sid='0003410380',
                select_filters={'18': {'020'}},
            )
            self.assertEqual(line_count, 2)
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, 'r', encoding='utf-8') as f:
                self.assertEqual(f.read(), '"col1","col2"\n"val1","val2"\n')

    @mock.patch.object(download_script, 'fetch_dashboard_csv')
    @mock.patch.object(download_script, 'fetch_dbview_csv')
    def test_download_all_downloads_all_17_datasets_and_cleans_stale(
        self,
        mock_fetch_dbview,
        mock_fetch_dashboard,
    ):
        mock_fetch_dbview.return_value = '"col1","col2"\n"val1","val2"\n'
        mock_fetch_dashboard.return_value = '"col1","col2"\n"val1","val2"\n'
        with tempfile.TemporaryDirectory() as tmp_dir:
            stale_file = os.path.join(tmp_dir, 'stale.csv')
            with open(stale_file, 'w', encoding='utf-8') as f:
                f.write('stale\n')
            download_script.download_all(output_dir=tmp_dir, max_workers=1)
            self.assertFalse(os.path.exists(stale_file))
            self.assertEqual(set(os.listdir(tmp_dir)),
                             set(download_script.DBVIEW_CONFIGS.keys()))
            self.assertEqual(len(os.listdir(tmp_dir)), 17)


if __name__ == '__main__':
    unittest.main()
