#!/usr/bin/env python3
# Copyright 2026 Google LLC
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
"""Hermetic unit tests for India WRIS Water Quality download.py and fixtures."""

import csv
import os
import sys
import tempfile
import unittest
from unittest import mock

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.india_wris.water_quality import download  # pylint: disable=wrong-import-position


class DownloadTest(unittest.TestCase):
    """Tests staged GCS downloading, failure propagation, and fixture bounds."""

    @mock.patch.object(download.file_util, 'file_copy')
    def test_download_staged_files_copies_required_csvs_only(
        self,
        mock_file_copy: mock.Mock,
    ) -> None:
        source_payloads = {
            'gs://test-bucket/wris/groundWater.csv':
                'Station Name,Value\nA,1\n',
            'gs://test-bucket/wris/India_WRIS_Ground_Prod_Retained.csv':
                ('variable_measured,value\nSV1,2\n'),
            'gs://test-bucket/wris/surfaceWater.csv':
                'StateName,Value\nS,3\n',
        }

        def fake_copy(src: str, dst: str) -> str:
            if src not in source_payloads:
                raise FileNotFoundError(f'Object not found: {src}')
            with open(dst, 'w', encoding='utf-8') as f:
                f.write(source_payloads[src])
            return dst

        mock_file_copy.side_effect = fake_copy

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, 'input_files')
            downloaded = download.download_staged_files(
                gcs_input_dir='gs://test-bucket/wris/',
                output_dir=out_dir,
            )
            self.assertEqual(len(downloaded), 3)
            for src_uri, expected_text in source_payloads.items():
                fname = os.path.basename(src_uri)
                local_path = os.path.join(out_dir, fname)
                self.assertTrue(os.path.exists(local_path))
                with open(local_path, 'r', encoding='utf-8') as f:
                    self.assertEqual(f.read(), expected_text)
            leftover_tmp = [
                f for f in os.listdir(out_dir) if f.endswith('.tmp')
            ]
            self.assertEqual(leftover_tmp, [])

    @mock.patch.object(download.file_util, 'file_copy')
    def test_download_missing_required_file_propagates_exception(
        self,
        mock_file_copy: mock.Mock,
    ) -> None:
        mock_file_copy.side_effect = FileNotFoundError('Blob does not exist')

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, 'input_files')
            with self.assertRaisesRegex(
                    RuntimeError,
                    'gs://test-bucket/wris/groundWater.csv',
            ):
                download.download_staged_files(
                    gcs_input_dir='gs://test-bucket/wris',
                    output_dir=out_dir,
                )
            self.assertEqual(os.listdir(out_dir), [])

    @mock.patch.object(download.file_util, 'file_copy')
    def test_download_empty_file_raises_and_cleans_temp_file(
        self,
        mock_file_copy: mock.Mock,
    ) -> None:

        def write_empty(_src: str, dst: str) -> str:
            with open(dst, 'w', encoding='utf-8'):
                pass
            return dst

        mock_file_copy.side_effect = write_empty

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, 'input_files')
            with self.assertRaisesRegex(RuntimeError, 'empty \\(0 bytes\\)'):
                download.download_staged_files(
                    gcs_input_dir='gs://test-bucket/wris',
                    output_dir=out_dir,
                )
            self.assertEqual(os.listdir(out_dir), [])

    def test_invalid_arguments_raise_value_error(self) -> None:
        with self.assertRaises(ValueError):
            download.download_staged_files(gcs_input_dir='   ')
        with self.assertRaises(ValueError):
            download.download_staged_files(
                gcs_input_dir='gs://test-bucket/wris',
                required_files=[],
            )

    def test_test_data_fixtures_exist_and_respect_size_caps(self) -> None:
        test_data_dir = os.path.join(_MODULE_DIR, 'test_data')
        expected_fixtures = (
            'ground_water_input.csv',
            'india_wris_ground.csv',
            'india_wris_ground.tmcf',
            'ground_water_retained_input.csv',
            'india_wris_ground_retained.csv',
            'india_wris_ground_retained.tmcf',
            'surface_water_input.csv',
            'india_wris_surface.csv',
            'india_wris_surface.tmcf',
        )
        for fname in expected_fixtures:
            fpath = os.path.join(test_data_dir, fname)
            self.assertTrue(os.path.exists(fpath), f'Missing fixture: {fname}')
            size_bytes = os.path.getsize(fpath)
            self.assertGreater(size_bytes, 0)
            self.assertLess(size_bytes, 100 * 1024,
                            f'Fixture {fname} exceeds 100 KB target')
            if fname.endswith('_input.csv'):
                with open(fpath, 'r', encoding='utf-8') as f:
                    row_count = sum(1 for _ in csv.reader(f))
                self.assertLess(row_count, 100,
                                f'Input fixture {fname} exceeds 100 rows')


if __name__ == '__main__':
    unittest.main()
