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
"""Unit tests for Indonesia_Census_Education download.py."""

import csv
import os
import sys
import tempfile
import unittest
from unittest import mock

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
_REPODIR = os.path.abspath(os.path.join(_CODEDIR, '../../..'))
sys.path.insert(1, _REPODIR)

from statvar_imports.indonesia_census.education import download


def _make_mock_get(responses: dict[str, dict]):
    """Returns a requests.get side_effect backed by a URL-to-JSON mapping."""

    def _side_effect(url, timeout=30):
        del timeout
        if url not in responses:
            raise AssertionError(f'Unexpected URL requested: {url}')
        resp = mock.MagicMock()
        resp.ok = True
        resp.status_code = 200
        resp.json.return_value = responses[url]
        return resp

    return _side_effect


class DownloadTest(unittest.TestCase):

    def test_redact_api_key(self):
        url = (
            'https://webapi.bps.go.id/v1/api/list/model/th/lang/eng/domain/0000'
            '/var/1458/page/1/key/super_secret_key_123/')
        redacted = download.redact_api_key(url)
        self.assertNotIn('super_secret_key_123', redacted)
        self.assertIn('/key/REDACTED/', redacted)

    def test_normalize_place_label(self):
        self.assertEqual(download.normalize_place_label('<b>Aceh</b>'), 'ACEH')
        self.assertEqual(
            download.normalize_place_label('Kep. Bangka Belitung'),
            'KEPULAUAN BANGKA BELITUNG',
        )
        self.assertEqual(
            download.normalize_place_label('Kep. Riau'),
            'KEPULAUAN RIAU',
        )
        self.assertEqual(
            download.normalize_place_label('Daerah Istimewa Yogyakarta'),
            'DI YOGYAKARTA',
        )

    def test_clean_simdasi_integer(self):
        self.assertEqual(download.clean_simdasi_integer('4.478'), '4478')
        self.assertEqual(download.clean_simdasi_integer('1.416.027'), '1416027')
        self.assertEqual(download.clean_simdasi_integer('109'), '109')
        self.assertEqual(download.clean_simdasi_integer('-'), '')
        self.assertEqual(download.clean_simdasi_integer('...'), '')
        self.assertEqual(download.clean_simdasi_integer(None), '')

    def test_fetch_literacy_and_simdasi_tables(self):
        api_key = 'test_key'
        # 1. Mock Literacy by Province (var_id=1458)
        th_1458_url = ('https://webapi.bps.go.id/v1/api/list/model/th/lang/eng/'
                       f'domain/0000/var/1458/page/1/key/{api_key}/')
        data_1458_url = (
            'https://webapi.bps.go.id/v1/api/list/model/data/lang/eng/'
            f'domain/0000/var/1458/th/122/key/{api_key}/')
        # 2. Mock Literacy by Sex (var_id=1460)
        th_1460_url = ('https://webapi.bps.go.id/v1/api/list/model/th/lang/eng/'
                       f'domain/0000/var/1460/page/1/key/{api_key}/')
        data_1460_url = (
            'https://webapi.bps.go.id/v1/api/list/model/data/lang/eng/'
            f'domain/0000/var/1460/th/111;122/key/{api_key}/')
        # 3. Mock SIMDASI table
        test_table_id = 'Uys0Mk9kelpxamVmMUYrMkRHSFcyZz09'
        simdasi_url = (
            'https://webapi.bps.go.id/v1/api/interoperabilitas/datasource/'
            f'simdasi/id/25/tahun/2022/id_tabel/{test_table_id}/'
            f'wilayah/0000000/key/{api_key}/')

        mock_responses = {
            th_1458_url: {
                'status':
                    'OK',
                'data': [
                    {
                        'page': 1,
                        'pages': 1
                    },
                    [{
                        'th_id': 122,
                        'th': '2022',
                        'var_id': 1458
                    }],
                ],
            },
            data_1458_url: {
                'status': 'OK',
                'var': [{
                    'val': 1458,
                    'label': 'Literacy Rate'
                }],
                'turvar': [{
                    'val': '0',
                    'label': 'None'
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
                        'val': 9999,
                        'label': 'INDONESIA'
                    },
                ],
                'tahun': [{
                    'val': 122,
                    'label': '2022'
                }],
                'datacontent': {
                    '1100145801220': 98.25,
                    '9999145801220': 96.35,
                },
            },
            th_1460_url: {
                'status':
                    'OK',
                'data': [
                    {
                        'page': 1,
                        'pages': 1
                    },
                    [
                        {
                            'th_id': 111,
                            'th': '2011',
                            'var_id': 1460
                        },
                        {
                            'th_id': 122,
                            'th': '2022',
                            'var_id': 1460
                        },
                    ],
                ],
            },
            data_1460_url: {
                'status': 'OK',
                'var': [{
                    'val': 1460,
                    'label': 'Literacy Rate by Sex'
                }],
                'turvar': [{
                    'val': '0',
                    'label': 'None'
                }],
                'turtahun': [{
                    'val': 0,
                    'label': 'Tahun'
                }],
                'vervar': [
                    {
                        'val': 1,
                        'label': 'Male'
                    },
                    {
                        'val': 2,
                        'label': 'Female'
                    },
                    {
                        'val': 3,
                        'label': 'Male + Female'
                    },
                ],
                'tahun': [
                    {
                        'val': 111,
                        'label': '2011'
                    },
                    {
                        'val': 122,
                        'label': '2022'
                    },
                ],
                'datacontent': {
                    '1146001110': 95.58,
                    '2146001110': 90.02,
                    '3146001110': 92.81,
                    '1146001220': 97.42,
                    '2146001220': 95.26,
                    '3146001220': 99.99,
                },
            },
            simdasi_url: {
                'status':
                    'OK',
                'data': [
                    {},
                    {
                        'list_tahun_data': [2022],
                        'kolom': {
                            'c1': {
                                'nama_variabel': 'Jumlah Sekolah MTs (Negeri)'
                            },
                            'c2': {
                                'nama_variabel': 'Jumlah Guru MTs (Negeri)'
                            },
                        },
                        'data': [{
                            'label_raw': 'Aceh',
                            'variables': {
                                'c1': {
                                    'value_raw': '109'
                                },
                                'c2': {
                                    'value_raw': '4.478'
                                },
                            },
                        }],
                    },
                ],
            },
        }

        table_data = {}
        with mock.patch.object(download.requests,
                               'get',
                               side_effect=_make_mock_get(mock_responses)):
            download.fetch_literacy_by_province('0000', 1458, api_key,
                                                table_data)
            download.fetch_literacy_by_sex('0000', 1460, api_key, table_data)
            download.fetch_simdasi_school_tables(
                api_key=api_key,
                table_data=table_data,
                tables=(('MTs', test_table_id),),
                max_seed_year=2022,
            )

        self.assertEqual(table_data[('ACEH', '2022')]['Literacy Rate (Total)'],
                         '98.25')
        self.assertEqual(
            table_data[('ACEH', '2022')]['Jumlah Sekolah MTs (Negeri)'], '109')
        self.assertEqual(
            table_data[('ACEH', '2022')]['Jumlah Guru MTs (Negeri)'], '4478')
        self.assertEqual(
            table_data[('INDONESIA', '2011')]['Literacy Rate (Total)'], '92.81')
        self.assertEqual(
            table_data[('INDONESIA', '2022')]['Literacy Rate (Total)'], '96.35')
        self.assertEqual(
            table_data[('INDONESIA', '2022')]['Literacy Rate (Male)'], '97.42')
        self.assertEqual(
            table_data[('INDONESIA', '2022')]['Literacy Rate (Female)'],
            '95.26')

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = os.path.join(tmp_dir, 'edu.csv')
            cols = (
                'Literacy Rate (Total)',
                'Literacy Rate (Male)',
                'Literacy Rate (Female)',
                'Jumlah Sekolah MTs (Negeri)',
                'Jumlah Guru MTs (Negeri)',
            )
            download.write_education_csv(out_csv, table_data, cols)
            with open(out_csv, 'r', encoding='utf-8') as fp:
                rows = list(csv.reader(fp))
            self.assertEqual(
                rows,
                [
                    ['Provinsi', 'observationDate'] + list(cols),
                    ['ACEH', '2022', '98.25', '', '', '109', '4478'],
                    ['INDONESIA', '2011', '92.81', '95.58', '90.02', '', ''],
                    ['INDONESIA', '2022', '96.35', '97.42', '95.26', '', ''],
                ],
            )

    def test_error_handling_raises_runtime_error(self):
        api_key = 'secret_test_key'
        th_url = ('https://webapi.bps.go.id/v1/api/list/model/th/lang/eng/'
                  f'domain/0000/var/1458/page/1/key/{api_key}/')
        mock_responses = {
            th_url: {
                'status': 'ERROR',
                'message': f'Failed for /key/{api_key}/',
            },
        }
        with mock.patch.object(download.requests,
                               'get',
                               side_effect=_make_mock_get(mock_responses)):
            with self.assertRaises(RuntimeError) as ctx:
                download.fetch_available_years('0000', 1458, api_key)
        self.assertNotIn(api_key, str(ctx.exception))

    def test_parse_simdasi_payload_ignores_non_dict_entries(self):
        payload = {
            'status':
                'OK',
            'data': [
                {},
                {
                    'list_tahun_data': [2022],
                    'kolom': {
                        'c1': {
                            'nama_variabel': 'Jumlah Sekolah SD (Negeri)'
                        },
                        'c2': {
                            'nama_variabel': 'Jumlah Guru SD (Negeri)'
                        },
                    },
                    'data': [
                        {
                            'label_raw': 'Bali',
                            'variables': [],
                        },
                        {
                            'label_raw': 'Aceh',
                            'variables': {
                                'c1': None,
                                'c2': 'unexpected_string',
                            },
                        },
                        {
                            'label_raw': 'Jawa Barat',
                            'variables': {
                                'c1': {
                                    'value_raw': '1.234'
                                },
                                'c2': None,
                            },
                        },
                    ],
                },
            ],
        }
        table_data = {}
        years = download._parse_simdasi_payload(payload, '2022', table_data)
        self.assertEqual(years, [2022])
        self.assertEqual(
            table_data,
            {('JAWA BARAT', '2022'): {
                 'Jumlah Sekolah SD (Negeri)': '1234'
             }},
        )

    def test_parse_yearbook_page_spans_handles_spaces_dots_and_swapped_headers(
        self,):
        # Includes a swapped Swasta year header (like Statistik Indonesia 2019
        # Table 4.1.3 Teachers), space-separated thousands, and missing '...'.
        spans = [
            (142.8, 163.1, 183.2, 176.9, '2016/2017'),
            (195.2, 163.1, 235.6, 176.9, '2017/2018'),
            (252.6, 163.1, 293.0, 176.9, '2017/2018'),
            (303.7, 163.1, 344.0, 176.9, '2016/2017'),
            (361.1, 163.1, 401.4, 176.9, '2016/2017'),
            (413.5, 163.1, 453.9, 176.9, '2017/2018'),
            (48.7, 190.1, 66.0, 202.1, 'Aceh'),
            (154.3, 190.1, 177.0, 202.1, '46 328'),
            (206.7, 190.1, 229.4, 202.1, '44.023'),
            (267.2, 190.1, 286.1, 202.1, '1 433'),
            (318.2, 190.1, 337.1, 202.1, '1 577'),
            (372.5, 190.1, 395.2, 202.1, '47 761'),
            (425.0, 190.1, 447.7, 202.1, '45 600'),
            (48.7, 205.0, 95.0, 217.0, 'Papua Barat Daya'),
            (160.0, 205.0, 170.0, 217.0, '...'),
            (210.0, 205.0, 225.0, 217.0, '120'),
        ]
        cols = (
            'Jumlah Guru SD (Negeri)',
            'Jumlah Guru SD (Swasta)',
            'Jumlah Guru SD (Negeri+Swasta)',
        )
        valid_places = {'ACEH', 'PAPUA BARAT DAYA'}
        parsed = download.parse_yearbook_page_spans(spans, cols, valid_places)
        self.assertEqual(parsed[('ACEH', '2016')]['Jumlah Guru SD (Negeri)'],
                         '46328')
        self.assertEqual(parsed[('ACEH', '2017')]['Jumlah Guru SD (Negeri)'],
                         '44023')
        self.assertEqual(parsed[('ACEH', '2016')]['Jumlah Guru SD (Swasta)'],
                         '1433')
        self.assertEqual(parsed[('ACEH', '2017')]['Jumlah Guru SD (Swasta)'],
                         '1577')
        self.assertEqual(
            parsed[('ACEH', '2016')]['Jumlah Guru SD (Negeri+Swasta)'], '47761')
        self.assertEqual(
            parsed[('ACEH', '2017')]['Jumlah Guru SD (Negeri+Swasta)'], '45600')
        self.assertNotIn(('PAPUA BARAT DAYA', '2016'), parsed)
        self.assertEqual(
            parsed[('PAPUA BARAT DAYA', '2017')]['Jumlah Guru SD (Negeri)'],
            '120')

    def test_select_yearbook_editions(self):
        editions = [
            (2019, 'p19'),
            (2020, 'p20'),
            (2021, 'p21'),
            (2022, 'p22'),
            (2023, 'p23'),
            (2024, 'p24'),
            (2025, 'p25'),
            (2026, 'p26'),
            (2027, 'p27'),
        ]
        selected = download.select_yearbook_editions(
            editions,
            {2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026},
        )
        self.assertEqual(
            [ed for ed, _ in selected],
            [2019, 2020, 2022, 2024, 2025, 2026, 2027],
        )
        selected_single = download.select_yearbook_editions(editions, {2025})
        self.assertEqual([ed for ed, _ in selected_single], [2026, 2027])

    def test_fetch_simdasi_reports_empty_years_and_fallback_preserves_live_data(
        self,):
        api_key = 'test_key'
        test_table_id = 'Uys0Mk9kelpxamVmMUYrMkRHSFcyZz09'
        simdasi_url = (
            'https://webapi.bps.go.id/v1/api/interoperabilitas/datasource/'
            f'simdasi/id/25/tahun/2022/id_tabel/{test_table_id}/'
            f'wilayah/0000000/key/{api_key}/')
        pub_list_2023 = (
            'https://webapi.bps.go.id/v1/api/list/model/publication/lang/ind/'
            f'domain/0000/keyword/Statistik+Indonesia/year/2023/page/1/key/{api_key}/'
        )
        pub_list_2024 = (
            'https://webapi.bps.go.id/v1/api/list/model/publication/lang/ind/'
            f'domain/0000/keyword/Statistik+Indonesia/year/2024/page/1/key/{api_key}/'
        )
        pub_list_2025 = (
            'https://webapi.bps.go.id/v1/api/list/model/publication/lang/ind/'
            f'domain/0000/keyword/Statistik+Indonesia/year/2025/page/1/key/{api_key}/'
        )
        pub_view_url = (
            'https://webapi.bps.go.id/v1/api/view/domain/0000/model/'
            f'publication/lang/ind/id/pub2024/key/{api_key}/')
        pdf_url = 'https://webapi.bps.go.id/download.php?f=mockpdf'

        mock_json = {
            simdasi_url: {
                'status':
                    'OK',
                'data': [
                    {},
                    {
                        'list_tahun_data': [2022],
                        'kolom': {
                            'c1': {
                                'nama_variabel': 'Jumlah Sekolah MTs (Negeri)'
                            },
                        },
                        'data': [{
                            'label_raw': 'Aceh',
                            'variables': [],
                        }],
                    },
                ],
            },
            pub_list_2023: {
                'status': 'OK',
                'data': '',
            },
            pub_list_2024: {
                'status':
                    'OK',
                'data': [
                    {
                        'page': 1,
                        'pages': 1
                    },
                    [
                        {
                            'pub_id': 'pub_info',
                            'title': 'Statistik Indonesia dalam Infografis 2024'
                        },
                        {
                            'pub_id': 'pub2024',
                            'title': 'Statistik Indonesia 2024'
                        },
                    ],
                ],
            },
            pub_list_2025: {
                'status': 'OK',
                'data': '',
            },
            pub_view_url: {
                'status': 'OK',
                'data': {
                    'pub_id': 'pub2024',
                    'pdf': pdf_url,
                },
            },
        }

        def _mock_get(url, timeout=30):
            del timeout
            resp = mock.MagicMock()
            resp.ok = True
            resp.status_code = 200
            if url == pdf_url:
                resp.content = b'%PDF-mock'
                return resp
            if url not in mock_json:
                raise AssertionError(f'Unexpected URL requested: {url}')
            resp.json.return_value = mock_json[url]
            return resp

        table_data = {('ACEH', '2022'): {'Jumlah Guru MTs (Negeri)': '9999',}}
        with mock.patch.object(download.requests, 'get', side_effect=_mock_get):
            missing = download.fetch_simdasi_school_tables(
                api_key=api_key,
                table_data=table_data,
                tables=(('MTs', test_table_id),),
                max_seed_year=2022,
            )
            # Because table_data already has a live MTs 2022 value, test empty detection on fresh dict:
            fresh_data = {}
            missing_fresh = download.fetch_simdasi_school_tables(
                api_key=api_key,
                table_data=fresh_data,
                tables=(('MTs', test_table_id),),
                max_seed_year=2022,
            )
            self.assertEqual(missing, {})
            self.assertEqual(missing_fresh, {'MTs': {'2022'}})

            with tempfile.TemporaryDirectory() as raw_dir:
                with mock.patch.object(
                        download,
                        'extract_yearbook_pdf_tables',
                        return_value={
                            ('ACEH', '2022'): {
                                'Jumlah Sekolah MTs (Negeri)': '109',
                                'Jumlah Guru MTs (Negeri)': '4478',
                            }
                        },
                ):
                    download.fetch_yearbook_school_tables_fallback(
                        domain='0000',
                        api_key=api_key,
                        missing_by_code=missing_fresh,
                        table_data=table_data,
                        raw_output_dir=raw_dir,
                    )
                self.assertTrue(
                    os.path.exists(
                        os.path.join(raw_dir, 'statistik_indonesia_2024.pdf')))
                self.assertTrue(
                    os.path.exists(
                        os.path.join(raw_dir,
                                     'bps_publication_view_2024_pub2024.json')))

        # Fallback fills missing column while preserving existing live SIMDASI value.
        self.assertEqual(
            table_data[('ACEH', '2022')]['Jumlah Sekolah MTs (Negeri)'], '109')
        self.assertEqual(
            table_data[('ACEH', '2022')]['Jumlah Guru MTs (Negeri)'], '9999')

    def test_fetch_simdasi_probes_downward_and_saves_raw_json(self):
        api_key = 'probe_secret_key'
        table_id = 'UkJNaEl6ZHRVYXNaMzZhZG9BbS9ZZz09'
        url_2026 = (
            'https://webapi.bps.go.id/v1/api/interoperabilitas/datasource/'
            f'simdasi/id/25/tahun/2026/id_tabel/{table_id}/'
            f'wilayah/0000000/key/{api_key}/')
        url_2025 = (
            'https://webapi.bps.go.id/v1/api/interoperabilitas/datasource/'
            f'simdasi/id/25/tahun/2025/id_tabel/{table_id}/'
            f'wilayah/0000000/key/{api_key}/')
        url_2024 = (
            'https://webapi.bps.go.id/v1/api/interoperabilitas/datasource/'
            f'simdasi/id/25/tahun/2024/id_tabel/{table_id}/'
            f'wilayah/0000000/key/{api_key}/')

        mock_responses = {
            url_2026: {
                'status': 'OK',
                'data': [{}, {
                    'list_tahun_data': [],
                    'data': []
                }],
            },
            url_2025: {
                'status':
                    'OK',
                'note':
                    f'debug /key/{api_key}/',
                'data': [
                    {},
                    {
                        'list_tahun_data': [2024, 2025],
                        'kolom': {
                            'c1': {
                                'nama_variabel': 'Jumlah Sekolah SD (Negeri)'
                            },
                        },
                        'data': [{
                            'label_raw': 'Aceh',
                            'variables': {
                                'c1': {
                                    'value_raw': '3.336'
                                }
                            },
                        }],
                    },
                ],
            },
            url_2024: {
                'status':
                    'OK',
                'data': [
                    {},
                    {
                        'list_tahun_data': [2024, 2025],
                        'kolom': {
                            'c1': {
                                'nama_variabel': 'Jumlah Sekolah SD (Negeri)'
                            },
                        },
                        'data': [{
                            'label_raw': 'Aceh',
                            'variables': {
                                'c1': {
                                    'value_raw': '3.300'
                                }
                            },
                        }],
                    },
                ],
            },
        }
        table_data = {}
        with tempfile.TemporaryDirectory() as raw_dir:
            with mock.patch.object(download.requests,
                                   'get',
                                   side_effect=_make_mock_get(mock_responses)):
                missing = download.fetch_simdasi_school_tables(
                    api_key=api_key,
                    table_data=table_data,
                    tables=(('SD', table_id),),
                    raw_output_dir=raw_dir,
                    max_seed_year=2026,
                    min_seed_year=2024,
                )
            self.assertEqual(missing, {})
            self.assertEqual(
                table_data[('ACEH', '2025')]['Jumlah Sekolah SD (Negeri)'],
                '3336')
            self.assertEqual(
                table_data[('ACEH', '2024')]['Jumlah Sekolah SD (Negeri)'],
                '3300')
            raw_2025 = os.path.join(raw_dir, 'simdasi_SD_2025.json')
            self.assertTrue(os.path.exists(raw_2025))
            with open(raw_2025, 'r', encoding='utf-8') as fp:
                raw_text = fp.read()
            self.assertNotIn(api_key, raw_text)
            self.assertIn('/key/REDACTED/', raw_text)

    def test_request_bps_logging_includes_method_and_status(self):
        api_key = 'log_secret_key'
        url = f'https://webapi.bps.go.id/v1/api/test/key/{api_key}/'
        resp = mock.MagicMock()
        resp.ok = True
        resp.status_code = 200
        resp.json.return_value = {'status': 'OK'}
        resp.content = b'%PDF-1.4'
        with mock.patch.object(download.requests, 'get', return_value=resp):
            with mock.patch.object(download.logging, 'info') as mock_log:
                download.request_bps_json(url, retries=1)
                download.request_bps_bytes(url, retries=1)
        messages = [
            call.args[0] % call.args[1:] for call in mock_log.call_args_list
        ]
        self.assertTrue(
            any('HTTP GET' in m and '200' in m and '/key/REDACTED/' in m
                for m in messages))
        self.assertTrue(
            any('HTTP GET (binary)' in m and '200' in m and '8 bytes' in m
                for m in messages))
        self.assertTrue(all(api_key not in m for m in messages))

    def test_extract_horizontal_pdf_spans_filters_watermarks_and_superscripts(
        self,):
        mock_page = mock.MagicMock()
        mock_page.get_text.return_value = {
            'blocks': [{
                'lines': [
                    {
                        'dir': (0.707, -0.707),
                        'spans': [{
                            'size': 24.0,
                            'text': 'https://www.bps.go.id',
                            'bbox': (50.0, 100.0, 300.0, 120.0),
                        }],
                    },
                    {
                        'dir': (1.0, 0.0),
                        'spans': [
                            {
                                'size': 4.2,
                                'text': '1',
                                'bbox': (70.0, 188.0, 74.0, 193.0),
                            },
                            {
                                'size': 7.5,
                                'text': 'Aceh',
                                'bbox': (48.0, 190.0, 68.0, 200.0),
                            },
                            {
                                'size': 7.5,
                                'text': '   ',
                                'bbox': (80.0, 190.0, 90.0, 200.0),
                            },
                        ],
                    },
                ],
            }],
        }
        spans = download._extract_horizontal_pdf_spans(mock_page)
        self.assertEqual(spans, [(48.0, 190.0, 68.0, 200.0, 'Aceh')])

    def test_extract_yearbook_pdf_tables_verifies_headers_and_skips_inserted_page(
        self,):

        class _FakePdfPage:

            def __init__(self, header_lines, values_6=None):
                self._header_lines = header_lines
                self._values_6 = values_6

            def get_text(self, mode='text'):
                if mode == 'text':
                    lines = list(self._header_lines)
                    if self._values_6 is not None:
                        lines.append('Aceh ' + ' '.join(self._values_6))
                    return '\n'.join(lines)
                if mode == 'dict':
                    spans = []
                    y = 60.0
                    for ln in self._header_lines:
                        spans.append({
                            'size': 9.0,
                            'text': ln,
                            'bbox': (48.0, y, 450.0, y + 10.0),
                        })
                        y += 14.0
                    xs = [150.0, 205.0, 260.0, 315.0, 370.0, 425.0]
                    yr_labels = [
                        '2024/2025',
                        '2025/2026',
                        '2024/2025',
                        '2025/2026',
                        '2024/2025',
                        '2025/2026',
                    ]
                    if self._values_6 is not None:
                        for x, lbl in zip(xs, yr_labels):
                            spans.append({
                                'size': 8.0,
                                'text': lbl,
                                'bbox': (x, 160.0, x + 40.0, 170.0),
                            })
                        spans.append({
                            'size': 8.0,
                            'text': 'Aceh',
                            'bbox': (48.0, 190.0, 70.0, 200.0),
                        })
                        for x, val in zip(xs, self._values_6):
                            spans.append({
                                'size': 8.0,
                                'text': val,
                                'bbox': (x, 190.0, x + 35.0, 200.0),
                            })
                        spans.append({
                            'size':
                                6.5,
                            'text':
                                'Footnote: total teachers including headmaster',
                            'bbox': (48.0, 700.0, 350.0, 710.0),
                        })
                    return {
                        'blocks': [{
                            'lines': [{
                                'dir': (1.0, 0.0),
                                'spans': spans,
                            }],
                        }],
                    }
                raise ValueError(mode)

        class _FakePdfDoc:

            def __init__(self, pages):
                self._pages = pages
                self.closed = False

            def __len__(self):
                return len(self._pages)

            def __getitem__(self, idx):
                return self._pages[idx]

            def close(self):
                self.closed = True

        pages = [
            # Page 0: Table 4.1.2 (Raudatul Athfal)
            _FakePdfPage(
                [
                    'Tabel 4.1.2 Jumlah Sekolah, Guru, dan Murid Raudatul Athfal (RA)',
                    'Table 4.1.2 Number of Schools, Teachers, and Pupils in Raudatul Athfal (RA)',
                    'Sekolah/Schools   Guru/Teachers   Murid/Pupils',
                ],
                ['300', '324', '1.500', '1.555', '14.000', '14.167'],
            ),
            # Page 1: Inserted unrelated chart/note page that blind offsets would misparse
            _FakePdfPage(['Gambar 4.1 Grafik Pendidikan / Education Chart']),
            # Pages 2-4: Table 4.1.3 (SD) using 2026 BPS terminology
            _FakePdfPage(
                [
                    'Tabel 4.1.3 Jumlah Satuan Pendidikan Sekolah Dasar (SD)',
                    'Table 4.1.3 Number of Schools in Elementary Schools',
                    'Satuan Pendidikan/Schools',
                ],
                ['3.300', '3.336', '210', '221', '3.510', '3.557'],
            ),
            _FakePdfPage(
                [
                    'Lanjutan Tabel/Continued Table 4.1.3',
                    'Kepala Sekolah dan Pendidik/Headmasters and Teachers',
                ],
                ['47.000', '47.413', '3.200', '3.358', '50.200', '50.771'],
            ),
            _FakePdfPage(
                [
                    'Lanjutan Tabel/Continued Table 4.1.3',
                    'Peserta Didik/Pupils',
                ],
                [
                    '450.000', '455.000', '35.000', '36.000', '485.000',
                    '491.000'
                ],
            ),
        ]
        fake_doc = _FakePdfDoc(pages)
        fake_pymupdf = mock.MagicMock()
        fake_pymupdf.open.return_value = fake_doc

        with mock.patch.dict(sys.modules, {'pymupdf': fake_pymupdf}):
            extracted = download.extract_yearbook_pdf_tables(
                pdf_bytes=b'%PDF-fake',
                needed_codes={'RA', 'SD'},
                valid_places={'ACEH'},
            )
        self.assertTrue(fake_doc.closed)
        self.assertEqual(
            extracted[('ACEH', '2025')]['Jumlah Sekolah Raudatul Athfal'],
            '324')
        self.assertEqual(
            extracted[('ACEH', '2025')]['Jumlah Guru Raudatul Athfal'], '1555')
        self.assertEqual(
            extracted[('ACEH', '2025')]['Jumlah Murid Raudatul Athfal'],
            '14167')
        self.assertEqual(
            extracted[('ACEH', '2025')]['Jumlah Sekolah SD (Negeri)'], '3336')
        self.assertEqual(extracted[('ACEH', '2025')]['Jumlah Guru SD (Swasta)'],
                         '3358')
        self.assertEqual(
            extracted[('ACEH', '2025')]['Jumlah Murid SD (Negeri+Swasta)'],
            '491000')

    def test_extract_yearbook_pdf_tables_raises_on_missing_expected_header(
        self,):
        p0 = mock.MagicMock()
        p0.get_text.side_effect = (
            lambda mode='text':
            'Tabel 4.1.2 Raudatul Athfal (RA) Sekolah/Schools\nAceh 300'
            if mode == 'text' else {
                'blocks': []
            })
        p1 = mock.MagicMock()
        p1.get_text.side_effect = (
            lambda mode='text': 'Tabel 9.9.9 Unrelated Health Table'
            if mode == 'text' else {
                'blocks': []
            })
        fake_doc = mock.MagicMock()
        fake_doc.__len__.return_value = 2
        fake_doc.__getitem__.side_effect = [p0, p1].__getitem__
        fake_pymupdf = mock.MagicMock()
        fake_pymupdf.open.return_value = fake_doc

        with mock.patch.dict(sys.modules, {'pymupdf': fake_pymupdf}):
            with self.assertRaises(RuntimeError) as ctx:
                download.extract_yearbook_pdf_tables(
                    pdf_bytes=b'%PDF-fake',
                    needed_codes={'SD'},
                    valid_places={'ACEH'},
                )
        self.assertIn('4.1.3', str(ctx.exception))
        fake_doc.close.assert_called_once()

    def test_validate_school_tables_populated_raises_on_empty_table(self):
        with self.assertRaises(RuntimeError) as ctx:
            download.validate_school_tables_populated(
                {('ACEH', '2022'): {
                     'Literacy Rate (Total)': '98.25'
                 }},
                tables=(('MTs', 'dummy'),),
            )
        self.assertIn('MTs', str(ctx.exception))

    def test_load_valid_places_reads_pvmap(self):
        valid_places = download._load_valid_places()
        self.assertEqual(len(valid_places), 39)
        self.assertIn('INDONESIA', valid_places)
        self.assertIn('ACEH', valid_places)
        self.assertIn('DI YOGYAKARTA', valid_places)
        self.assertIn('PAPUA BARAT DAYA', valid_places)


if __name__ == '__main__':
    unittest.main()
