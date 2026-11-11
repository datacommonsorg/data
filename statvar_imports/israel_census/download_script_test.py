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

    def test_fetch_cbs_series_path_rows_and_build_population_unscaled(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = (
            b'id,time_name,unit_name,path_level4_name,path_name_id_name,obs_time_period,obs_value\n'
            b'3700,Year,Thousands,At End of Period,Total,2024-01,10065.5\n'
            b'3701,Year,Thousands,At End of Period,Jews,2024-01,7212.9\n'
            b'3703,Year,Thousands,At End of Period,Jews and Others,2024-01,7693.3\n'
            b'3704,Year,Thousands,At End of Period,Arab Population,2024-01,2111.8\n'
        )
        mock_session.get.return_value = resp

        series_rows = download_script.fetch_cbs_series_path_rows(
            path_id='2,1,1,1',
            session=mock_session,
        )
        pop_rows = download_script.build_population_religion_rows(series_rows)
        self.assertEqual(len(pop_rows), 1)
        self.assertEqual(pop_rows[0]['Region'], 'ISR')
        self.assertEqual(pop_rows[0]['Year'], '2024')
        self.assertEqual(pop_rows[0]['total'], '10065.5')
        self.assertEqual(pop_rows[0]['jews'], '7212.9')
        self.assertEqual(pop_rows[0]['Others'], '480.4')
        self.assertEqual(pop_rows[0]['arab'], '2111.8')

    def test_fetch_cbs_series_path_rows_raises_on_invalid_csv(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = b'<!DOCTYPE html><html>Error</html>'
        mock_session.get.return_value = resp

        with self.assertRaises(RuntimeError):
            download_script.fetch_cbs_series_path_rows(
                path_id='2,1,1,1',
                session=mock_session,
            )

    def test_fetch_cbs_series_path_rows_raises_on_incomplete_series_after_retries(
            self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = (b'id,time_name,obs_time_period,obs_value\n'
                        b'3700,Year,2024-01,10065.5\n')
        mock_session.get.return_value = resp

        with self.assertRaises(RuntimeError):
            download_script.fetch_cbs_series_path_rows(
                path_id='2,1,1,1',
                session=mock_session,
                min_unique_series=5,
            )
        self.assertEqual(mock_session.get.call_count, 3)

    def test_fetch_cbs_boardsgenerator_census_to_csv(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.json.return_value = {
            'Groups': [
                {
                    'Id':
                        2,
                    'Name':
                        'Demography',
                    'Subjects': [{
                        'Id': 18,
                        'Name': 'Population – total (thousands)',
                        'Value': '104.5',
                    }],
                },
                {
                    'Id':
                        3,
                    'Name':
                        'Total',
                    'Subjects': [{
                        'Id': 218,
                        'Name': 'Those aged 15 and over – total (thousands)',
                        'Value': '5227.3',
                    }],
                },
            ]
        }
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            paths = download_script.fetch_cbs_boardsgenerator_census_to_csv(
                output_dir=tmp_dir,
                session=mock_session,
            )
            self.assertEqual(len(paths), 3)
            with open(
                    os.path.join(tmp_dir, 'isr_agebracket_gender_aa1_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                machoz_rows = list(csv.DictReader(fp))
            isr_row = next(r for r in machoz_rows if r['Region'] == 'ISR')
            self.assertEqual(isr_row['Year'], '2008')
            self.assertEqual(
                isr_row['Those aged 15 and over – total'],
                '5227.3',
            )

            with open(
                    os.path.join(tmp_dir,
                                 'isr_subdistrict_population_gender_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                nafa_pop_rows = list(csv.DictReader(fp))
            sub21_row = next(
                r for r in nafa_pop_rows if r['Region'] == 'SUBDIST_21')
            self.assertEqual(sub21_row['Year'], '2008')
            self.assertEqual(sub21_row['Population – total'], '104.5')

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
