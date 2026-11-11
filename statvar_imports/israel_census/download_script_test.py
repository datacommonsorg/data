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
"""Unit tests for download_script.py."""

import csv
import os
import sys
import tempfile
import unittest
from unittest import mock

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.israel_census import download_script  # pylint: disable=g-import-not-at-top


class DownloadScriptTest(unittest.TestCase):

    def test_fetch_cbs_series_path_csv_raw_writes_untouched_bytes(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        raw_csv = (b'id,time_name,obs_time_period,obs_value\n'
                   b'3700,Year,2024-01,10065.5\n')
        resp.content = raw_csv
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series.csv')
            byte_count = download_script.fetch_cbs_series_path_csv_raw(
                path_id='2,1,1,1',
                dest_path=dest_csv,
                session=mock_session,
            )
            self.assertEqual(byte_count, len(raw_csv))
            with open(dest_csv, 'rb') as fp:
                self.assertEqual(fp.read(), raw_csv)

    def test_fetch_cbs_series_path_csv_raw_raises_on_invalid_csv(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = b'<!DOCTYPE html><html>Error</html>'
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'invalid.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_path_csv_raw(
                    path_id='2,1,1,1',
                    dest_path=dest_csv,
                    session=mock_session,
                )

    def test_fetch_cbs_boardsgenerator_census_to_csv(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.json.return_value = {
            'Groups': [{
                'Id':
                    2,
                'Name':
                    'Demography',
                'Subjects': [{
                    'Id': 18,
                    'Name': 'Population – total (thousands)',
                    'Value': '7412.2',
                }],
            }]
        }
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_census_2008_regions.csv')
            count = download_script.fetch_cbs_boardsgenerator_census_to_csv(
                dest_path=dest_csv,
                session=mock_session,
            )
            self.assertEqual(count,
                             len(download_script.CBS_CENSUS_2008_REGIONS))
            with open(dest_csv, 'r', encoding='utf-8') as fp:
                rows = list(csv.DictReader(fp))
            self.assertEqual(rows[0]['region_code'], '999')
            self.assertEqual(rows[0]['subject_id'], '18')
            self.assertEqual(rows[0]['value'], '7412.2')

    def test_fetch_cbs_mifkad_table_raw_writes_untouched_bytes(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        raw_xls = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1mock_xls_bytes'
        resp.content = raw_xls
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_xls = os.path.join(tmp_dir, 'dem1_2.xls')
            byte_count = download_script.fetch_cbs_mifkad_table_raw(
                xls_name='dem1_2.xls',
                dest_path=dest_xls,
                session=mock_session,
            )
            self.assertEqual(byte_count, len(raw_xls))
            with open(dest_xls, 'rb') as fp:
                self.assertEqual(fp.read(), raw_xls)


if __name__ == '__main__':
    unittest.main()
