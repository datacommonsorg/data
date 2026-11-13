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
"""Unit tests for Indonesia Crime download.py."""

import csv
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import requests

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
_REPODIR = os.path.abspath(os.path.join(_CODEDIR, '../../..'))
sys.path.insert(1, _REPODIR)
sys.path.insert(1, os.path.join(_REPODIR, 'util'))

from statvar_imports.indonesia_census.crime import download


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

    def test_redact_api_key(self):
        raw = 'https://webapi.bps.go.id/v1/api/list/page/1/key/secret123/'
        self.assertEqual(
            download.redact_api_key(raw),
            'https://webapi.bps.go.id/v1/api/list/page/1/key/REDACTED/',
        )

    @mock.patch('time.sleep')
    def test_request_bps_json_retries_transient_and_fails_fast_on_4xx(
        self,
        mock_sleep,
    ):
        session = mock.MagicMock(spec=requests.Session)
        session.get.side_effect = [
            _make_response(503),
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

        # Permanent 4xx (e.g. 401) should fail fast without sleeping or retrying
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

                # Corrupt local JSON falls back to GCS via file_util.FileIO
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

                # Missing everywhere raises ValueError
                with self.assertRaises(ValueError):
                    download.get_bps_api_key(
                        '',
                        local_config_path=os.path.join(tmp_dir, 'missing.json'),
                        gcs_config_path='',
                    )

    @mock.patch.object(download, 'request_bps_json')
    def test_fetch_and_write_crime_csv_multi_page_and_multi_chunk(
        self,
        mock_request_bps,
    ):
        api_key = 'test_key'
        th_page1_url = (
            'https://webapi.bps.go.id/v1/api/list/model/th/lang/eng/'
            f'domain/0000/var/101/page/1/key/{api_key}/')
        th_page2_url = (
            'https://webapi.bps.go.id/v1/api/list/model/th/lang/eng/'
            f'domain/0000/var/101/page/2/key/{api_key}/')
        chunk1_url = (
            'https://webapi.bps.go.id/v1/api/list/model/data/lang/eng/'
            f'domain/0000/var/101/th/200;122;123/key/{api_key}/')
        chunk2_url = (
            'https://webapi.bps.go.id/v1/api/list/model/data/lang/eng/'
            f'domain/0000/var/101/th/124/key/{api_key}/')

        responses = {
            th_page1_url: {
                'status':
                    'OK',
                'data': [
                    {
                        'page': 1,
                        'pages': 2,
                        'per_page': 2,
                        'count': 2,
                        'total': 4
                    },
                    [
                        {
                            'th_id': 123,
                            'th': '2023',
                            'var_id': 101
                        },
                        {
                            'th_id': 200,
                            'th': '2021',
                            'var_id': 101
                        },
                    ],
                ],
            },
            th_page2_url: {
                'status':
                    'OK',
                'data': [
                    {
                        'page': 2,
                        'pages': 2,
                        'per_page': 2,
                        'count': 2,
                        'total': 4
                    },
                    [
                        {
                            'th_id': 124,
                            'th': '2024',
                            'var_id': 101
                        },
                        {
                            'th_id': 122,
                            'th': '2022',
                            'var_id': 101
                        },
                    ],
                ],
            },
            chunk1_url: {
                'status': 'OK',
                'var': [{
                    'val': 101,
                    'label': download.TABLE_TITLE
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
                        'val': 1,
                        'label': 'ACEH'
                    },
                    {
                        'val': 35,
                        'label': 'INDONESIA'
                    },
                ],
                'tahun': [
                    {
                        'val': 200,
                        'label': '2021'
                    },
                    {
                        'val': 122,
                        'label': '2022'
                    },
                    {
                        'val': 123,
                        'label': '2023'
                    },
                ],
                'datacontent': {
                    '110102000': 6651,
                    '110101220': 10137,
                    '110101230': 12194,
                    '3510102000': 239481,
                    '3510101220': 372897,
                    '3510101230': 584991,
                },
            },
            chunk2_url: {
                'status': 'OK',
                'var': [{
                    'val': 101,
                    'label': download.TABLE_TITLE
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
                        'val': 1,
                        'label': 'ACEH'
                    },
                    {
                        'val': 35,
                        'label': 'INDONESIA'
                    },
                ],
                'tahun': [{
                    'val': 124,
                    'label': '2024'
                }],
                'datacontent': {
                    '110101240': 11400,
                    '3510101240': 542000,
                },
            },
        }
        mock_request_bps.side_effect = responses.__getitem__

        jurisdictions, year_labels, values = download.fetch_crime_table(
            domain='0000', var_id=101, api_key=api_key)
        self.assertEqual(jurisdictions, ['ACEH', 'INDONESIA'])
        self.assertEqual(year_labels, ['2021', '2022', '2023', '2024'])
        self.assertEqual(values[('ACEH', '2021')], '6651')
        self.assertEqual(values[('INDONESIA', '2024')], '542000')

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = os.path.join(tmp_dir, 'crime.csv')
            download.write_crime_csv(
                output_path=out_csv,
                jurisdictions=jurisdictions,
                year_labels=year_labels,
                values_by_place_year=values,
            )
            with open(out_csv, 'r', encoding='utf-8') as fp:
                rows = list(csv.reader(fp))
            self.assertEqual(
                rows,
                [
                    [
                        download.JURISDICTION_HEADER,
                        download.YEAR_HEADER,
                        download.TABLE_TITLE,
                    ],
                    ['ACEH', '2021', '6651'],
                    ['ACEH', '2022', '10137'],
                    ['ACEH', '2023', '12194'],
                    ['ACEH', '2024', '11400'],
                    ['INDONESIA', '2021', '239481'],
                    ['INDONESIA', '2022', '372897'],
                    ['INDONESIA', '2023', '584991'],
                    ['INDONESIA', '2024', '542000'],
                ],
            )

    @mock.patch.object(download, 'request_bps_json')
    def test_fetch_available_years_raises_on_error_or_malformed_data(
        self,
        mock_request_bps,
    ):
        mock_request_bps.return_value = {
            'status': 'Error',
            'message': 'Invalid API KEY',
        }
        with self.assertRaises(RuntimeError):
            download.fetch_available_years('0000', 101, 'test_key')

        mock_request_bps.return_value = {
            'status': 'OK',
            'data': [{
                'page': 1,
                'pages': 1
            }],
        }
        with self.assertRaises(RuntimeError):
            download.fetch_available_years('0000', 101, 'test_key')

    @mock.patch.object(download, 'request_bps_json')
    def test_fetch_crime_table_raises_on_incomplete_chunk(
        self,
        mock_request_bps,
    ):
        mock_request_bps.side_effect = [
            {
                'status':
                    'OK',
                'data': [{
                    'page': 1,
                    'pages': 1
                }, [{
                    'th_id': 123,
                    'th': '2023'
                }]],
            },
            {
                'status': 'OK',
                'var': [{
                    'val': 101
                }],
                'turvar': [{
                    'val': 0
                }],
                'turtahun': [{
                    'val': 0
                }],
                'vervar': [],
                'tahun': [{
                    'val': 123,
                    'label': '2023'
                }],
                'datacontent': {},
            },
        ]
        with self.assertRaises(RuntimeError):
            download.fetch_crime_table('0000', 101, 'test_key')


if __name__ == '__main__':
    unittest.main()
