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
"""Unit tests for Indonesia_Census_Labor download.py."""

import csv
import io
import json
import os
import tempfile
import unittest
from unittest import mock

import requests
from statvar_imports.indonesia_census.labor import download


def _make_response(status_code: int, payload: dict | None = None):
    resp = mock.MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.ok = 200 <= status_code < 300
    if payload is not None:
        resp.json.return_value = payload
    else:
        resp.json.side_effect = ValueError('Invalid JSON')
    return resp


class DownloadTest(unittest.TestCase):

    def test_clean_place_label_and_redact(self):
        self.assertEqual(download.clean_place_label(1100, '<b>ACEH</b>'),
                         'ACEH')
        self.assertEqual(download.clean_place_label(7500, '<b>GORONTALO</b>'),
                         'GORONTALO aa1')
        self.assertEqual(download.clean_place_label(7502, 'Gorontalo'),
                         'Gorontalo')
        self.assertEqual(download.clean_place_label(7206, 'Toli-Toli'),
                         'ToliToli')
        self.assertEqual(download.clean_place_label(7209, 'Tojo Una-Una'),
                         'Tojo UnaUna')
        self.assertEqual(download.clean_place_label(2100, 'KEP. RIAU'),
                         'KEPULAUAN RIAU')
        self.assertEqual(download.clean_place_label(3400, 'DI YOGYAKARTA'),
                         'D I YOGYAKARTA')
        self.assertEqual(
            download.redact_api_key(
                'https://webapi.bps.go.id/v1/api/list/key/secret123/'),
            'https://webapi.bps.go.id/v1/api/list/key/REDACTED/',
        )

    @mock.patch('time.sleep')
    def test_request_bps_json_retries_transient_and_fails_fast_on_4xx(
        self,
        mock_sleep,
    ):
        session = mock.MagicMock(spec=requests.Session)
        session.get.side_effect = [
            _make_response(502),
            _make_response(429),
            _make_response(200, {'status': 'OK'}),
        ]
        result = download.request_bps_json(
            'https://webapi.bps.go.id/v1/api/list/key/mykey/',
            retries=3,
            retry_secs=1.5,
            session=session,
        )
        self.assertEqual(result, {'status': 'OK'})
        self.assertEqual(session.get.call_count, 3)
        self.assertEqual(
            [c.args[0] for c in mock_sleep.call_args_list],
            [1.5, 3.0],
        )

        # Permanent 4xx fails fast without sleeping or retrying
        mock_sleep.reset_mock()
        session.get.reset_mock()
        session.get.side_effect = [_make_response(401)]
        with self.assertRaises(RuntimeError) as ctx:
            download.request_bps_json(
                'https://webapi.bps.go.id/v1/api/list/key/mykey/',
                retries=3,
                retry_secs=1.5,
                session=session,
            )
        self.assertEqual(session.get.call_count, 1)
        mock_sleep.assert_not_called()
        self.assertNotIn('mykey', str(ctx.exception))
        self.assertIsNotNone(ctx.exception.__cause__)

    def test_get_bps_api_key_fallbacks(self):
        with mock.patch.dict(os.environ, {'BPS_API_KEY': ''}, clear=False):
            self.assertEqual(download.get_bps_api_key('explicit_key'),
                             'explicit_key')

            with tempfile.TemporaryDirectory() as tmp_dir:
                valid_local = os.path.join(tmp_dir, 'valid.json')
                with open(valid_local, 'w', encoding='utf-8') as fp:
                    json.dump({'bps_api_key': 'local_cfg_key'}, fp)
                self.assertEqual(
                    download.get_bps_api_key(
                        '',
                        local_config_path=valid_local,
                        gcs_config_path='',
                    ),
                    'local_cfg_key',
                )

                corrupt_local = os.path.join(tmp_dir, 'corrupt.json')
                with open(corrupt_local, 'w', encoding='utf-8') as fp:
                    fp.write('{invalid json')
                with mock.patch.object(
                        download.file_util,
                        'FileIO',
                        return_value=io.StringIO('{"bps_api_key": "gcs_key"}'),
                ):
                    self.assertEqual(
                        download.get_bps_api_key(
                            '',
                            local_config_path=corrupt_local,
                            gcs_config_path='gs://unresolved_mcf/config.json',
                        ),
                        'gcs_key',
                    )

                with self.assertRaises(ValueError) as ctx:
                    download.get_bps_api_key(
                        '',
                        local_config_path=corrupt_local,
                        gcs_config_path='',
                    )
                self.assertIsNotNone(ctx.exception.__cause__)

    @mock.patch.object(download, 'request_bps_json')
    def test_fetch_lfpr_table_and_write_csv(self, mock_request_bps):
        mock_request_bps.side_effect = [
            {
                'status':
                    'OK',
                'data': [
                    {
                        'page': 1,
                        'pages': 2,
                        'total': 2
                    },
                    [{
                        'th_id': 124,
                        'th': '2024'
                    }],
                ],
            },
            {
                'status':
                    'OK',
                'data': [
                    {
                        'page': 2,
                        'pages': 2,
                        'total': 2
                    },
                    [{
                        'th_id': 200,
                        'th': '2018'
                    }],
                ],
            },
            {
                'status': 'OK',
                'var': [{
                    'val': 2200,
                    'label': 'Labor Force Participation Rate by Sex'
                }],
                'turvar': [
                    {
                        'val': 211,
                        'label': 'Male'
                    },
                    {
                        'val': 212,
                        'label': 'Female'
                    },
                ],
                'turtahun': [{
                    'val': 0,
                    'label': 'Annual'
                }],
                'vervar': [
                    {
                        'val': 7500,
                        'label': '<b>GORONTALO</b>'
                    },
                    {
                        'val': 3371,
                        'label': 'Kota Magelang'
                    },
                    {
                        'val': 9106,
                        'label': 'Sorong Selatan'
                    },
                    {
                        'val': 9203,
                        'label': 'Sorong Selatan'
                    },
                ],
                'tahun': [
                    {
                        'val': 200,
                        'label': '2018'
                    },
                    {
                        'val': 124,
                        'label': '2024'
                    },
                ],
                'datacontent': {
                    '750022002112000': 84.24,
                    '750022002122000': 51.66,
                    '337122002112000': 77.15,
                    '910622002112000': 81.51,
                    '920322002111240': 80.12,
                },
            },
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_json = os.path.join(tmp_dir, 'raw_lfpr.json')
            places, sex_labels, year_labels, values = download.fetch_lfpr_table(
                domain='0000',
                var_id=2200,
                api_key='test_key',
                raw_output_path=raw_json,
            )
            self.assertTrue(os.path.exists(raw_json))
            self.assertEqual(places, ['GORONTALO aa1', 'Sorong Selatan'])
            self.assertEqual(sex_labels, ['Male', 'Female'])
            self.assertEqual(year_labels, ['2018', '2024'])
            self.assertEqual(values[('Sorong Selatan', 'Male', '2018')],
                             '81.51')
            self.assertEqual(values[('Sorong Selatan', 'Male', '2024')],
                             '80.12')

            out_csv = os.path.join(tmp_dir, 'lfpr.csv')
            download.write_lfpr_csv(out_csv, places, sex_labels, year_labels,
                                    values)
            with open(out_csv, encoding='utf-8') as fp:
                rows = list(csv.reader(fp))
            self.assertEqual(
                rows,
                [
                    ['Province/Regency/City', 'Year', 'Male', 'Female'],
                    ['GORONTALO aa1', '2018', '84.24', '51.66'],
                    ['Sorong Selatan', '2018', '81.51', ''],
                    ['Sorong Selatan', '2024', '80.12', ''],
                ],
            )

    @mock.patch.object(download, 'request_bps_json')
    def test_fetch_formal_labor_table_and_write_csv(self, mock_request_bps):
        mock_request_bps.side_effect = [
            {
                'status':
                    'OK',
                'data': [
                    {
                        'page': 1,
                        'pages': 1,
                        'total': 2
                    },
                    [
                        {
                            'th_id': 115,
                            'th': '2015'
                        },
                        {
                            'th_id': 125,
                            'th': '2025'
                        },
                    ],
                ],
            },
            {
                'status': 'OK',
                'var': [{
                    'val': 1168,
                    'label': 'Percentage of Formal Labor by Province (Percent)'
                }],
                'turvar': [{
                    'val': 0,
                    'label': 'Tidak Ada'
                }],
                'turtahun': [{
                    'val': 0,
                    'label': 'Tahun'
                }],
                'vervar': [
                    {
                        'val': 1100,
                        'label': 'ACEH'
                    },
                    {
                        'val': 2100,
                        'label': 'KEP. RIAU'
                    },
                    {
                        'val': 9999,
                        'label': 'INDONESIA'
                    },
                ],
                'tahun': [
                    {
                        'val': 115,
                        'label': '2015'
                    },
                    {
                        'val': 125,
                        'label': '2025'
                    },
                ],
                'datacontent': {
                    '1100116801150': 39.5,
                    '2100116801250': 64.0,
                    '9999116801250': 42.2,
                },
            },
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_json = os.path.join(tmp_dir, 'raw_fl.json')
            provinces, years, values = download.fetch_formal_labor_table(
                domain='0000',
                var_id=1168,
                api_key='test_key',
                raw_output_path=raw_json,
            )
            self.assertTrue(os.path.exists(raw_json))
            self.assertEqual(provinces, ['ACEH', 'KEPULAUAN RIAU', 'INDONESIA'])
            self.assertEqual(years, ['2015', '2025'])
            self.assertEqual(values[('ACEH', '2015')], '39.5')
            self.assertEqual(values[('KEPULAUAN RIAU', '2025')], '64')
            self.assertEqual(values[('INDONESIA', '2025')], '42.2')

            out_csv = os.path.join(tmp_dir, 'fl.csv')
            download.write_formal_labor_csv(out_csv, provinces, years, values)
            with open(out_csv, encoding='utf-8') as fp:
                rows = list(csv.reader(fp))
            self.assertEqual(
                rows,
                [
                    [
                        'Province',
                        'Year',
                        'Percentage of Formal Labor by Province (Percent)',
                    ],
                    ['ACEH', '2015', '39.5'],
                    ['KEPULAUAN RIAU', '2025', '64'],
                    ['INDONESIA', '2025', '42.2'],
                ],
            )


if __name__ == '__main__':
    unittest.main()
