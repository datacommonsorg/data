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

import json
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

    def test_fetch_cbs_series_raw_csv_writes_unmodified_bytes(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        raw_csv = (
            b'id,time_name,unit_name,path_level4_name,path_name_id_name,obs_time_period,obs_value\n'
            b'3700,Year,Thousands,At End of Period,Total,2024-01,10065.5\n'
            b'3701,Year,Thousands,At End of Period,Jews,2024-01,7212.9\n'
            b'3702,Year,Thousands,At End of Period,Non-Jews,2024-01,2852.6\n'
            b'3703,Year,Thousands,At End of Period,Jews and Others,2024-01,7693.3\n'
            b'3704,Year,Thousands,At End of Period,Arab Population,2024-01,2111.8\n'
        )
        resp.content = raw_csv
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_2_1_1_1.csv')
            byte_count = download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest_csv,
                session=mock_session,
            )
            self.assertEqual(byte_count, len(raw_csv))
            with open(dest_csv, 'rb') as fp:
                self.assertEqual(fp.read(), raw_csv)

    def test_fetch_cbs_series_raw_csv_raises_on_invalid_csv(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = b'<!DOCTYPE html><html>Error</html>'
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_2_1_1_1.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest_csv,
                    session=mock_session,
                )

    def test_fetch_cbs_series_raw_csv_raises_on_incomplete_series_after_retries(
            self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = (b'id,time_name,obs_time_period,obs_value\n'
                        b'3700,Year,2024-01,10065.5\n')
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_2_1_1_1.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest_csv,
                    session=mock_session,
                    min_unique_series=5,
                )
            self.assertEqual(mock_session.get.call_count, 3)

    def test_fetch_cbs_boardsgenerator_census_raw_json(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        payload = {
            'Groups': [{
                'Id':
                    2,
                'Name':
                    'Demography',
                'Subjects': [{
                    'Id': 18,
                    'Name': 'Population – total (thousands)',
                    'Value': '104.5',
                }],
            }]
        }
        resp.json.return_value = payload
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_json = download_script.fetch_cbs_boardsgenerator_census_raw_json(
                output_dir=tmp_dir,
                session=mock_session,
            )
            with open(dest_json, 'r', encoding='utf-8') as fp:
                records = json.load(fp)
            self.assertEqual(len(records),
                             len(download_script.CBS_CENSUS_2008_REGIONS))
            self.assertEqual(records[0]['region_code'], '999')
            self.assertEqual(records[0]['data_mode'], 'Machoz')
            self.assertEqual(records[0]['payload'], payload)

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
