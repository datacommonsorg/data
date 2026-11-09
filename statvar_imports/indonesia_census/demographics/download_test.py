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
import logging as std_logging
import os
import sys
import tempfile
import unittest
from unittest import mock

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
                population_filename='idn_population.csv',
                age_gender_filename='idn_age_gender.csv',
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

    def test_missing_api_key_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, 'BPS WebAPI key is required'):
            download.fetch_available_years(domain='0000',
                                           var_id=2790,
                                           api_key='')
        with self.assertRaisesRegex(ValueError, 'BPS WebAPI key is required'):
            download.fetch_variable_data(domain='0000',
                                         var_id=2790,
                                         api_key='   ',
                                         start_year=2023)
        with self.assertRaisesRegex(ValueError, 'BPS WebAPI key is required'):
            download._resolve_api_key(api_key='', api_key_gcs_path='')
        with self.assertRaisesRegex(ValueError, 'BPS WebAPI key is required'):
            download._resolve_api_key(
                api_key='',
                api_key_gcs_path='/nonexistent/path/api_key.json',
            )
        with self.assertRaisesRegex(ValueError, 'BPS WebAPI key is required'):
            download._resolve_api_key(
                api_key='',
                api_key_gcs_path='gs://invalid_gcs_path_without_blob',
            )
        with (
                mock.patch.object(
                    download.storage,
                    'Client',
                    side_effect=RuntimeError('GCS unavailable'),
                ),
                self.assertRaisesRegex(ValueError,
                                       'BPS WebAPI key is required'),
        ):
            download._resolve_api_key(api_key='')

    def test_api_key_gcs_fallback(self):
        fallback_key = 'fallback_gcs_key'
        self._register_bps_variable_responses(
            api_key=fallback_key,
            var_id=2790,
            datacontent={'11002790231230': 5482527},
        )
        self._register_bps_variable_responses(
            api_key=fallback_key,
            var_id=2791,
            datacontent={'11002791231230': 2747185},
        )
        self._register_bps_variable_responses(
            api_key=fallback_key,
            var_id=2792,
            datacontent={'11002792231230': 2735342},
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            key_file = os.path.join(tmp_dir, 'api_key.json')
            with open(key_file, 'w', encoding='utf-8') as fp:
                fp.write(f'{{"api_key": "{fallback_key}"}}\n')

            self.assertEqual(
                download._resolve_api_key(api_key='',
                                          api_key_gcs_path=key_file),
                fallback_key,
            )
            self.assertEqual(
                download._resolve_api_key(api_key='explicit_key',
                                          api_key_gcs_path=key_file),
                'explicit_key',
            )

            with mock.patch.object(download.storage, 'Client') as mock_client:
                mock_blob = (mock_client.return_value.bucket.return_value.blob.
                             return_value)
                mock_blob.download_as_text.return_value = (
                    f'{{"api_key": "{fallback_key}"}}')
                self.assertEqual(
                    download._resolve_api_key(api_key=''),
                    fallback_key,
                )
                mock_client.return_value.bucket.assert_called_once_with(
                    'unresolved_mcf')
                mock_client.return_value.bucket.return_value.blob.assert_called_once_with(
                    'country/indonesia/demographic/api_key.json')

            pop_path, _ = download.download_demographic_data(
                domain='0000',
                total_var_id=2790,
                male_var_id=2791,
                female_var_id=2792,
                api_key='',
                output_dir=tmp_dir,
                population_filename='idn_population.csv',
                age_gender_filename='idn_age_gender.csv',
                start_year=2023,
                api_key_gcs_path=key_file,
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
                ],
            )

            for idx, invalid_payload in enumerate([
                    '{"api_key": ""}\n',
                    '{"api_key": "   "}\n',
                    '{"api_key": true}\n',
                    'null\n',
                    '[]\n',
                    'not-json-at-all\n',
            ]):
                bad_key_file = os.path.join(tmp_dir, f'bad_key_{idx}.json')
                with open(bad_key_file, 'w', encoding='utf-8') as fp:
                    fp.write(invalid_payload)
                with self.assertRaisesRegex(ValueError,
                                            'BPS WebAPI key is required'):
                    download.download_demographic_data(
                        domain='0000',
                        total_var_id=2790,
                        male_var_id=2791,
                        female_var_id=2792,
                        api_key='',
                        output_dir=tmp_dir,
                        population_filename='idn_population.csv',
                        age_gender_filename='idn_age_gender.csv',
                        start_year=2023,
                        api_key_gcs_path=bad_key_file,
                    )

    def test_api_error_raises_runtime_error_with_redacted_key(self):
        api_key = 'secret_bps_key'
        th_url = ('https://webapi.bps.go.id/v1/api/list/model/th/lang/ind/'
                  f'domain/0000/var/2790/page/1/key/{api_key}/')
        download_util.set_test_url_download_response(
            url=th_url,
            params={},
            response={
                'status': 'Error',
                'message': 'Invalid key'
            },
        )
        with self.assertRaises(RuntimeError) as ctx:
            download.fetch_available_years(domain='0000',
                                           var_id=2790,
                                           api_key=api_key)
        self.assertIn('<REDACTED>', str(ctx.exception))
        self.assertNotIn(api_key, str(ctx.exception))

    def test_empty_years_and_data_errors_raise_exceptions(self):
        api_key = 'secret_bps_key'
        th_url = ('https://webapi.bps.go.id/v1/api/list/model/th/lang/ind/'
                  f'domain/0000/var/2790/page/1/key/{api_key}/')
        download_util.set_test_url_download_response(
            url=th_url,
            params={},
            response={
                'status': 'OK',
                'data': [{
                    'page': 1,
                    'pages': 1
                }, []]
            },
        )
        with self.assertRaisesRegex(ValueError,
                                    'No years returned for BPS var_id=2790'):
            download.fetch_variable_data(domain='0000',
                                         var_id=2790,
                                         api_key=api_key,
                                         start_year=2023)

        download_util.set_test_url_download_response(
            url=th_url,
            params={},
            response={
                'status':
                    'OK',
                'data': [
                    {
                        'page': 1,
                        'pages': 1
                    },
                    [{
                        'th_id': 123,
                        'th': '2023',
                        'var_id': 2790
                    }],
                ],
            },
        )
        data_url = ('https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/'
                    f'domain/0000/var/2790/th/123/key/{api_key}/')
        download_util.set_test_url_download_response(
            url=data_url,
            params={},
            response={
                'status': 'Error',
                'message': 'Backend error'
            },
        )
        with self.assertRaises(RuntimeError) as ctx:
            download.fetch_variable_data(domain='0000',
                                         var_id=2790,
                                         api_key=api_key,
                                         start_year=2023)
        self.assertIn('<REDACTED>', str(ctx.exception))
        self.assertNotIn(api_key, str(ctx.exception))

        download_util.set_test_url_download_response(
            url=data_url,
            params={},
            response={
                'status': 'OK',
                'var': [],
                'turvar': [],
                'turtahun': []
            },
        )
        with self.assertRaisesRegex(RuntimeError,
                                    'Incomplete metadata in BPS response'):
            download.fetch_variable_data(domain='0000',
                                         var_id=2790,
                                         api_key=api_key,
                                         start_year=2023)

    def test_no_years_meeting_start_year_raises_value_error(self):
        api_key = 'test_key'
        th_url = ('https://webapi.bps.go.id/v1/api/list/model/th/lang/ind/'
                  f'domain/0000/var/2790/page/1/key/{api_key}/')
        download_util.set_test_url_download_response(
            url=th_url,
            params={},
            response={
                'status':
                    'OK',
                'data': [
                    {
                        'page': 1,
                        'pages': 1
                    },
                    [{
                        'th_id': 120,
                        'th': '2020',
                        'var_id': 2790
                    }],
                ],
            },
        )
        with self.assertRaisesRegex(
                ValueError,
                'No available years >= 2023 found for BPS var_id=2790'):
            download.fetch_variable_data(domain='0000',
                                         var_id=2790,
                                         api_key=api_key,
                                         start_year=2023)

    def test_skips_legacy_pre_2022_split_papua_regencies(self):
        api_key = 'test_key'
        th_url = ('https://webapi.bps.go.id/v1/api/list/model/th/lang/ind/'
                  f'domain/0000/var/2790/page/1/key/{api_key}/')
        download_util.set_test_url_download_response(
            url=th_url,
            params={},
            response={
                'status':
                    'OK',
                'data': [
                    {
                        'page': 1,
                        'pages': 1
                    },
                    [{
                        'th_id': 123,
                        'th': '2023',
                        'var_id': 2790
                    }],
                ],
            },
        )
        data_url = ('https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/'
                    f'domain/0000/var/2790/th/123/key/{api_key}/')
        download_util.set_test_url_download_response(
            url=data_url,
            params={},
            response={
                'status': 'OK',
                'var': [{
                    'val': 2790,
                    'label': 'Penduduk'
                }],
                'turvar': [{
                    'val': 23,
                    'label': 'TOTAL'
                }],
                'turtahun': [{
                    'val': 0,
                    'label': 'Tahun'
                }],
                'vervar': [
                    {
                        'val': 9401,
                        'label': 'Merauke'
                    },  # Legacy Papua code
                    {
                        'val': 9403,
                        'label': 'Jayapura'
                    },  # Non-split Papua code
                    {
                        'val': 9501,
                        'label': 'Merauke'
                    },  # Post-2022 South Papua
                    {
                        'val': 9107,
                        'label': 'Sorong'
                    },  # Legacy West Papua
                    {
                        'val': 9201,
                        'label': 'Sorong'
                    },  # Post-2022 SW Papua
                ],
                'tahun': [{
                    'val': 123,
                    'label': '2023'
                }],
                'datacontent': {
                    '94012790231230': 237197,
                    '94032790231230': 203159,
                    '95012790231230': 237197,
                    '91072790231230': 122033,
                    '92012790231230': 122033,
                },
            },
        )
        places, _, _, values = download.fetch_variable_data(domain='0000',
                                                            var_id=2790,
                                                            api_key=api_key,
                                                            start_year=2023)
        self.assertEqual(
            places,
            [
                (9403, 'Jayapura, Papua, Indonesia'),
                (9501, 'Merauke, Papua Selatan, Indonesia'),
                (9201, 'Sorong, Papua Barat Daya, Indonesia'),
            ],
        )
        self.assertNotIn((9401, 'TOTAL', '2023'), values)
        self.assertNotIn((9107, 'TOTAL', '2023'), values)
        self.assertEqual(values[(9501, 'TOTAL', '2023')], '237197')
        self.assertEqual(values[(9201, 'TOTAL', '2023')], '122033')

    def test_copy_historical_files_from_gcs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch.object(download.file_util,
                                   'file_copy') as mock_copy:
                download.copy_historical_files_from_gcs('', tmp_dir)
                mock_copy.assert_not_called()
                self.assertFalse(
                    os.path.exists(os.path.join(tmp_dir, 'common_tmcf.tmcf')))

                gcs_dir = ('gs://unresolved_mcf/country/indonesia/demographic/'
                           'historical/')
                download.copy_historical_files_from_gcs(gcs_dir, tmp_dir)

                dst_tmcf = os.path.join(tmp_dir, 'common_tmcf.tmcf')
                self.assertTrue(os.path.exists(dst_tmcf))
                with open(dst_tmcf, 'r', encoding='utf-8') as fp:
                    self.assertEqual(fp.read(), download.COMMON_TMCF_CONTENT)

                expected_calls = [
                    mock.call(
                        'gs://unresolved_mcf/country/indonesia/demographic/'
                        f'historical/{fname}',
                        os.path.join(tmp_dir, fname),
                    ) for fname in download.HISTORICAL_CSVS
                ]
                mock_copy.assert_has_calls(expected_calls)
                self.assertEqual(mock_copy.call_count,
                                 len(download.HISTORICAL_CSVS))

            with (
                    mock.patch.object(
                        download.file_util,
                        'file_copy',
                        side_effect=RuntimeError('GCS copy failed'),
                    ),
                    self.assertRaisesRegex(RuntimeError, 'GCS copy failed'),
            ):
                download.copy_historical_files_from_gcs(
                    'gs://unresolved_mcf/country/indonesia/demographic/'
                    'historical',
                    tmp_dir,
                )

    def test_write_age_gender_csv_skips_blank_rows_and_suppresses_total(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = os.path.join(tmp_dir, 'nested', 'idn_age_gender.csv')
            download.write_age_gender_csv(
                output_path=out_path,
                places=[(1100, 'ACEH, INDONESIA')],
                age_groups=['TOTAL', '0-4', '5-9', '10-14'],
                year_labels=['2023'],
                total_values={
                    (1100, 'TOTAL', '2023'): '5482527',
                    (1100, '0-4', '2023'): '502479',
                    (1100, '5-9', '2023'): '',
                },
                male_values={
                    (1100, 'TOTAL', '2023'): '2747185',
                    (1100, '0-4', '2023'): '256480',
                    (1100, '5-9', '2023'): '',
                },
                female_values={
                    (1100, 'TOTAL', '2023'): '2735342',
                    (1100, '0-4', '2023'): '',
                    (1100, '5-9', '2023'): '',
                },
            )

            with open(out_path, 'r', encoding='utf-8') as fp:
                rows = list(csv.reader(fp))
            self.assertEqual(
                rows,
                [
                    [
                        'observationAbout',
                        'observationDate',
                        'Kelompok Umur',
                        'Penduduk (Laki-Laki)',
                        'Penduduk (Perempuan)',
                        'Penduduk (Laki-Laki + Perempuan)',
                    ],
                    [
                        'ACEH, INDONESIA',
                        '2023',
                        'TOTAL',
                        '2747185',
                        '2735342',
                        '',
                    ],
                    [
                        'ACEH, INDONESIA',
                        '2023',
                        '0-4',
                        '256480',
                        '',
                        '502479',
                    ],
                ],
            )

    def test_request_bps_json_redacts_api_key_in_logs(self):
        api_key = 'super_secret_bps_key_999'
        url = ('https://webapi.bps.go.id/v1/api/list/model/th/lang/ind/'
               f'domain/0000/var/2790/page/1/key/{api_key}/')
        captured_messages: list[str] = []

        class _CaptureHandler(std_logging.Handler):

            def emit(self, record: std_logging.LogRecord) -> None:
                captured_messages.append(record.getMessage())

        handler = _CaptureHandler()
        root_logger = std_logging.getLogger()
        root_logger.setLevel(std_logging.INFO)
        root_logger.addHandler(handler)
        try:
            with mock.patch.object(
                    download_util,
                    'request_url',
                    side_effect=lambda url, output:
                (root_logger.info('Downloading URL: %s', url) or {
                    'status': 'OK',
                    'data': [{
                        'pages': 1
                    }, []],
                }),
            ):
                download.fetch_available_years('0000', 2790, api_key)
        finally:
            root_logger.removeHandler(handler)

        self.assertTrue(captured_messages)
        for msg in captured_messages:
            self.assertNotIn(api_key, msg)
            self.assertIn('<REDACTED>', msg)


if __name__ == '__main__':
    unittest.main()
