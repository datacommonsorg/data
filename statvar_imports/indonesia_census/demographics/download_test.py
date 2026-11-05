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
"""Unit tests for Indonesia Demographic Population download.py."""

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

    def _register_bps_variable_responses(
        self,
        api_key: str,
        var_id: int,
        datacontent: dict[str, int],
    ) -> None:
        th_url = ('https://webapi.bps.go.id/v1/api/list/model/th/lang/ind/'
                  f'domain/0000/var/{var_id}/page/1/key/{api_key}/')
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
                        'total': 2,
                    },
                    [
                        {
                            'th_id': 123,
                            'th': '2023',
                            'var_id': var_id,
                        },
                        {
                            'th_id': 124,
                            'th': '2024',
                            'var_id': var_id,
                        },
                    ],
                ],
            },
        )

        data_url = ('https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/'
                    f'domain/0000/var/{var_id}/th/123;124/key/{api_key}/')
        download_util.set_test_url_download_response(
            url=data_url,
            params={},
            response={
                'status': 'OK',
                'var': [{
                    'val': var_id,
                    'label': 'Penduduk',
                }],
                'turvar': [
                    {
                        'val': 23,
                        'label': 'TOTAL',
                    },
                    {
                        'val': 24,
                        'label': '0-4',
                    },
                ],
                'turtahun': [{
                    'val': 0,
                    'label': 'Tahun',
                }],
                'vervar': [
                    {
                        'val': 1100,
                        'label': '<b>ACEH</b>',
                    },
                    {
                        'val': 1101,
                        'label': 'Simeulue',
                    },
                    {
                        'val': 9999,
                        'label': '<b>INDONESIA</b>',
                    },
                ],
                'tahun': [
                    {
                        'val': 123,
                        'label': '2023',
                    },
                    {
                        'val': 124,
                        'label': '2024',
                    },
                ],
                'datacontent': datacontent,
            },
        )

    def test_format_place_name_and_thousand_comma(self):
        self.assertEqual(
            download.format_place_name(9999, '<b>INDONESIA</b>'),
            'INDONESIA',
        )
        self.assertEqual(
            download.format_place_name(1100, '<b>ACEH</b>'),
            'ACEH, INDONESIA',
        )
        self.assertEqual(
            download.format_place_name(1101, 'Simeulue'),
            'Simeulue, Aceh, Indonesia',
        )
        self.assertEqual(download.format_thousand_comma(5482527), '5482,527')
        self.assertEqual(download.format_thousand_comma(541000), '541')
        self.assertEqual(download.format_thousand_comma(259500), '259,5')

    def test_download_demographic_data(self):
        api_key = 'test_key'
        self._register_bps_variable_responses(
            api_key=api_key,
            var_id=2790,
            datacontent={
                '11002790231230': 5482527,
                '11002790241230': 502479,
                '11002790231240': 5554815,
                '11002790241240': 506039,
                '11012790231230': 97118,
                '11012790241230': 9160,
                '99992790231230': 278696200,
                '99992790241230': 22416300,
            },
        )
        self._register_bps_variable_responses(
            api_key=api_key,
            var_id=2791,
            datacontent={
                '11002791231230': 2747185,
                '11002791241230': 256480,
                '11002791231240': 2783495,
                '11002791241240': 258319,
                '11012791231230': 49818,
                '11012791241230': 4680,
                '99992791231230': 140786800,
                '99992791241230': 11432300,
            },
        )
        self._register_bps_variable_responses(
            api_key=api_key,
            var_id=2792,
            datacontent={
                '11002792231230': 2735342,
                '11002792241230': 245999,
                '11002792231240': 2771320,
                '11002792241240': 247720,
                '11012792231230': 47300,
                '11012792241230': 4480,
                '99992792231230': 137909400,
                '99992792241230': 10984000,
            },
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            pop_path, ag_path = download.download_demographic_data(
                domain='0000',
                total_var_id=2790,
                male_var_id=2791,
                female_var_id=2792,
                api_key=api_key,
                output_dir=tmp_dir,
                population_filename='idn_population_2023_2025.csv',
                age_gender_filename='idn_age_gender_2023_2025.csv',
                start_year=2023,
            )

            with open(pop_path, 'r', encoding='utf-8') as fp:
                pop_rows = list(csv.reader(fp))
            self.assertEqual(
                pop_rows,
                [
                    [
                        'observationAbout',
                        'observationDate',
                        'Jumlah Penduduk (Ribu)',
                    ],
                    ['ACEH, INDONESIA', '2023', '5482,527'],
                    ['ACEH, INDONESIA', '2024', '5554,815'],
                    ['Simeulue, Aceh, Indonesia', '2023', '97,118'],
                    ['INDONESIA', '2023', '278696,2'],
                ],
            )

            with open(ag_path, 'r', encoding='utf-8') as fp:
                ag_rows = list(csv.reader(fp))
            self.assertEqual(
                ag_rows[0],
                [
                    'observationAbout',
                    'observationDate',
                    'Kelompok Umur',
                    'Penduduk (Laki-Laki)',
                    'Penduduk (Perempuan)',
                    'Penduduk (Laki-Laki + Perempuan)',
                ],
            )
            self.assertEqual(
                ag_rows[1],
                [
                    'ACEH, INDONESIA',
                    '2023',
                    'TOTAL',
                    '2747185',
                    '2735342',
                    '',
                ],
            )
            self.assertEqual(
                ag_rows[2],
                [
                    'ACEH, INDONESIA',
                    '2023',
                    '0-4',
                    '256480',
                    '245999',
                    '502479',
                ],
            )


if __name__ == '__main__':
    unittest.main()
