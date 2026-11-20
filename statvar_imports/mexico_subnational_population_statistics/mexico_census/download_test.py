# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for MexicoCensus download.py."""

import os
import sys
import tempfile
import unittest
from unittest import mock

import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import download  # pylint: disable=wrong-import-position


class DownloadUnitTest(unittest.TestCase):
    """Unit tests for extraction, reconciliation, unpacking, and archiving."""

    def test_reconcile_variable_codes_renames_legacy_dimensions(self):
        t_vars = [
            {
                'code': 'Entidad federativa de registro'
            },
            {
                'code': 'Año de registro'
            },
            {
                'code': 'Sexo'
            },
        ]
        stubs, headings = download.reconcile_variable_codes(
            q_stubs=['Entidad federativa'],
            q_headings=['Año', 'Sexo'],
            t_variables=t_vars,
        )
        self.assertEqual(stubs, ['Entidad federativa de registro'])
        self.assertEqual(headings, ['Año de registro', 'Sexo'])

    def test_unpack_pxweb_1stub_1heading_and_footnotes(self):
        q_meta = {
            'file': 'Poblacion/Test_01',
            'stub': ['Entidad federativa'],
            'heading': ['Periodo'],
        }
        t_meta = {
            'title':
                'Edad mediana por entidad federativa, 2020 a 2025',
            'variables': [
                {
                    'code':
                        'Entidad federativa',
                    'values': ['00', '01', '999999999999999999999'],
                    'valueTexts': [
                        'Estados Unidos Mexicanos',
                        'Aguascalientes',
                        'Nota: Cifras preliminares.',
                    ],
                },
                {
                    'code': 'Periodo',
                    'values': ['2020', '2025'],
                    'valueTexts': ['2020', '2025'],
                },
            ],
        }
        payload_info = download.build_pxweb_datatable_payload(q_meta, t_meta)
        dt_resp = {'data': ['29|a', '31', '28', '30']}
        rows = download.unpack_pxweb_datatable(dt_resp, payload_info)

        self.assertEqual(rows[0], [download._INEGI_HEADER_TITLE, '', ''])
        self.assertEqual(
            rows[1],
            ['Edad mediana por entidad federativa, 2020 a 2025', '', ''],
        )
        self.assertEqual(rows[2], ['Entidad federativa', '2020', '2025'])
        self.assertEqual(rows[3], ['Estados Unidos Mexicanos', '29', '31'])
        self.assertEqual(rows[4], ['Aguascalientes', '28', '30'])
        self.assertEqual(rows[5], ['Nota: Cifras preliminares.', '', ''])

    def test_unpack_pxweb_2stub_2heading_blanks_continuation_rows(self):
        q_meta = {
            'file': 'Educacion/Test_06',
            'stub': ['Entidad federativa', 'Nivel educativo'],
            'heading': ['Ciclo', 'Sexo'],
        }
        t_meta = {
            'title':
                'Matrícula escolar, 2023/2024 a 2024/2025',
            'variables': [
                {
                    'code':
                        'Entidad federativa',
                    'values': ['00', '01'],
                    'valueTexts': [
                        'Estados Unidos Mexicanos', 'Aguascalientes'
                    ],
                },
                {
                    'code': 'Nivel educativo',
                    'values': ['1', '2'],
                    'valueTexts': ['Preescolar', 'Primaria'],
                },
                {
                    'code': 'Ciclo',
                    'values': ['2024'],
                    'valueTexts': ['2023/2024'],
                },
                {
                    'code': 'Sexo',
                    'values': ['T', 'H'],
                    'valueTexts': ['Total', 'Hombres'],
                },
            ],
        }
        payload_info = download.build_pxweb_datatable_payload(q_meta, t_meta)
        dt_resp = {
            'data': [
                '1,000', '510', '2,000', '1,020', '100', '51', '200', '102'
            ]
        }
        rows = download.unpack_pxweb_datatable(dt_resp, payload_info)

        self.assertEqual(
            rows[2],
            ['Entidad federativa', 'Nivel educativo', '2023/2024', ''],
        )
        self.assertEqual(rows[3], ['', '', 'Total', 'Hombres'])
        self.assertEqual(
            rows[4],
            ['Estados Unidos Mexicanos', 'Preescolar', '1000', '510'],
        )
        self.assertEqual(rows[5], ['', 'Primaria', '2000', '1020'])
        self.assertEqual(rows[6], ['Aguascalientes', 'Preescolar', '100', '51'])
        self.assertEqual(rows[7], ['', 'Primaria', '200', '102'])

    def test_unpack_pxweb_cell_count_mismatch_raises(self):
        payload_info = {
            'stubs': ['Entidad'],
            'stub_headers': ['Entidad'],
            'headings': ['Año'],
            'var_Selections': {
                'Entidad': [('00', 'Total'), ('01', 'Aguascalientes')],
                'Año': [('2020', '2020'), ('2025', '2025')],
            },
            'title': 'Title',
            'footnotes': [],
        }
        with self.assertRaises(ValueError):
            download.unpack_pxweb_datatable({'data': ['1', '2']}, payload_info)

    def test_parse_cuadros_response(self):
        sample_json = [{
            'Data': [
                {
                    'MetaData': {
                        'Indicador': '446566'
                    },
                    'Serie': {
                        'Obs': [
                            {
                                'TimePeriod': '2024/01',
                                'CurrentValue': '1,800.0'
                            },
                            {
                                'TimePeriod': '2024/02',
                                'CurrentValue': '1850.5'
                            },
                        ]
                    },
                },
                {
                    'MetaData': {
                        'Indicador': '446713'
                    },
                    'Serie': {
                        'Obs': [
                            {
                                'TimePeriod': '2024/01',
                                'CurrentValue': '1600'
                            },
                            {
                                'TimePeriod': '2024/02',
                                'CurrentValue': '1650'
                            },
                        ]
                    },
                },
                {
                    'MetaData': {
                        'Indicador': '446718'
                    },
                    'Serie': {
                        'Obs': [
                            {
                                'TimePeriod': '2024/01',
                                'CurrentValue': '200'
                            },
                            {
                                'TimePeriod': '2024/02',
                                'CurrentValue': '200.5'
                            },
                        ]
                    },
                },
            ]
        }]
        rows = download.parse_cuadros_response(sample_json)
        self.assertEqual(
            rows,
            [
                ['Period', 'Total', 'With experience', 'Without experience'],
                ['2024', '', '', ''],
                ['I', '1800', '1600', '200'],
                ['II', '1850.5', '1650', '200.5'],
            ],
        )

    def test_extract_year_and_write_year_archived_dataset_local(self):
        rows_2020 = [
            [download._INEGI_HEADER_TITLE],
            ['Población de 6 a 14 años según aptitud, 2020'],
            ['Entidad federativa', 'Valor'],
            ['Estados Unidos Mexicanos', '100'],
        ]
        rows_2025 = [
            [download._INEGI_HEADER_TITLE],
            ['Población de 6 a 14 años según aptitud, 2025'],
            ['Entidad federativa', 'Valor'],
            ['Estados Unidos Mexicanos', '110'],
        ]
        self.assertEqual(download._extract_snapshot_year(rows_2020), '2020')
        self.assertEqual(download._extract_snapshot_year(rows_2025), '2025')

        with tempfile.TemporaryDirectory() as tmpdir:
            hist_dir = os.path.join(tmpdir, 'hist')
            out_dir = os.path.join(tmpdir, 'out')
            os.makedirs(out_dir, exist_ok=True)
            legacy_file = os.path.join(out_dir, 'Mexico_Lit_input.csv')
            with open(legacy_file, 'w', encoding='utf-8') as f:
                f.write('legacy')

            download._write_year_archived_dataset('Mexico_Lit', {},
                                                  rows_2020,
                                                  out_dir,
                                                  historical_override=hist_dir)
            download._write_year_archived_dataset('Mexico_Lit', {},
                                                  rows_2025,
                                                  out_dir,
                                                  historical_override=hist_dir)

            self.assertFalse(os.path.exists(legacy_file))
            self.assertEqual(
                sorted(os.listdir(out_dir)),
                ['Mexico_Lit_2020_input.csv', 'Mexico_Lit_2025_input.csv'],
            )

    def test_ssl_error_fallback_in_http_get_and_post(self):
        mock_resp = mock.MagicMock()
        mock_resp.json.return_value = {'ok': True}
        mock_resp.raise_for_status.return_value = None

        session_get = mock.MagicMock(spec=requests.Session)
        session_get.get.side_effect = [
            requests.exceptions.SSLError('cert failed'),
            mock_resp,
        ]
        res_get = download._http_get_json(session_get, 'https://example.test/q')
        self.assertEqual(res_get, {'ok': True})
        self.assertEqual(session_get.get.call_count, 2)
        self.assertFalse(session_get.verify)

        session_post = mock.MagicMock(spec=requests.Session)
        session_post.post.side_effect = [
            requests.exceptions.SSLError('cert failed'),
            mock_resp,
        ]
        res_post = download._http_post_json(session_post,
                                            'https://example.test/dt', {'a': 1})
        self.assertEqual(res_post, {'ok': True})
        self.assertEqual(session_post.post.call_count, 2)
        self.assertFalse(session_post.verify)


if __name__ == '__main__':
    unittest.main()
