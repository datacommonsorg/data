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
"""Unit tests for download.py."""

import io
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.noaa.gpcc_spi import download


class DownloadTest(unittest.TestCase):

    def test_main_forwards_flags_in_order(self):
        fake_flags = types.SimpleNamespace(download_dir='/tmp/gpcc_in',
                                           distribution='pearson',
                                           periods=['1', '12'])
        with mock.patch.object(download, 'FLAGS',
                               fake_flags), mock.patch.object(
                                   download, 'download_all') as mock_dl_all:
            download.main(None)
        mock_dl_all.assert_called_once_with('/tmp/gpcc_in', 'pearson',
                                            ['1', '12'])

    def test_download_all_uses_custom_args_and_formats_periods(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = os.path.join(tmp_dir, 'nested_input')
            with mock.patch.object(download, 'download_one') as mock_dl_one:
                download.download_all(out_dir, 'pearson', ['1', '12'])

            self.assertTrue(os.path.isdir(out_dir))
            self.assertCountEqual(
                mock_dl_one.call_args_list,
                [
                    mock.call(
                        'https://www.ncei.noaa.gov/pub/data/nidis/gpcc/'
                        'spi-pearson/gpcc-spi-pearson-01.nc',
                        os.path.join(out_dir, 'gpcc_spi_pearson_01.nc'),
                    ),
                    mock.call(
                        'https://www.ncei.noaa.gov/pub/data/nidis/gpcc/'
                        'spi-pearson/gpcc-spi-pearson-12.nc',
                        os.path.join(out_dir, 'gpcc_spi_pearson_12.nc'),
                    ),
                ],
            )

    def test_download_all_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch.object(download, 'download_one') as mock_dl_one:
                download.download_all(tmp_dir, '', None)

            expected_calls = [
                mock.call(
                    'https://www.ncei.noaa.gov/pub/data/nidis/gpcc/'
                    f'spi-pearson/gpcc-spi-pearson-{p}.nc',
                    os.path.join(tmp_dir, f'gpcc_spi_pearson_{p}.nc'),
                ) for p in ['01', '03', '06', '09', '36', '72']
            ]
            self.assertCountEqual(mock_dl_one.call_args_list, expected_calls)

    def test_download_all_propagates_worker_exception(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch.object(
                    download,
                    'download_one',
                    side_effect=[None, RuntimeError('download failed')],
            ):
                with self.assertRaisesRegex(RuntimeError, 'download failed'):
                    download.download_all(tmp_dir, 'pearson', ['1', '3'])

    def test_download_one_writes_stream_to_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = os.path.join(tmp_dir, 'gpcc_spi_pearson_01.nc')
            with mock.patch.object(download,
                                   'download_retry',
                                   return_value=io.BytesIO(b'test-nc-payload')):
                download.download_one('https://example.com/test.nc', dest)

            with open(dest, 'rb') as f:
                self.assertEqual(f.read(), b'test-nc-payload')


if __name__ == '__main__':
    unittest.main()
