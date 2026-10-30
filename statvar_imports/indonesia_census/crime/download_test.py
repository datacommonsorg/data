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
import os
import sys
import tempfile
import unittest

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, _CODEDIR)
sys.path.insert(1, os.path.join(_CODEDIR, '../../../util/'))

import download
import download_util


class DownloadTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        download_util._PREFILLED_RESPONSE.clear()

    def tearDown(self):
        download_util._PREFILLED_RESPONSE.clear()
        super().tearDown()

    def test_fetch_and_write_crime_csv(self):
        api_key = 'test_key'
        th_url = ('https://webapi.bps.go.id/v1/api/list/model/th/lang/eng/'
                  f'domain/0000/var/101/page/1/key/{api_key}/')
        download_util.set_test_url_download_response(
            url=th_url,
            params={},
            response={
                'status':
                    'OK',
                'data': [
                    {
                        'page': 1,
                        'pages': 1,
                        'per_page': 10,
                        'count': 2,
                        'total': 2
                    },
                    [
                        {
                            'th_id': 123,
                            'th': '2023',
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
        )

        data_url = ('https://webapi.bps.go.id/v1/api/list/model/data/lang/eng/'
                    f'domain/0000/var/101/th/122;123/key/{api_key}/')
        download_util.set_test_url_download_response(
            url=data_url,
            params={},
            response={
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
                        'val': 122,
                        'label': '2022'
                    },
                    {
                        'val': 123,
                        'label': '2023'
                    },
                ],
                'datacontent': {
                    '110101220': 10137,
                    '110101230': 12194,
                    '3510101220': 372897,
                    '3510101230': 584991,
                },
            },
        )

        jurisdictions, year_labels, values = download.fetch_crime_table(
            domain='0000', var_id=101, api_key=api_key)
        self.assertEqual(jurisdictions, ['ACEH', 'INDONESIA'])
        self.assertEqual(year_labels, ['2022', '2023'])
        self.assertEqual(values[('ACEH', '2022')], '10137')
        self.assertEqual(values[('INDONESIA', '2023')], '584991')

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
                    [download.TABLE_TITLE, '', ''],
                    [download.JURISDICTION_HEADER, '2022', '2023'],
                    ['ACEH', '10137', '12194'],
                    ['INDONESIA', '372897', '584991'],
                ],
            )


if __name__ == '__main__':
    unittest.main()
