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
"""Unit tests for Indonesia Census Health BPS WebAPI downloader."""

import csv
import json
import logging
import os
import sys
import tempfile
import unittest
from unittest import mock

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, _CODEDIR)
sys.path.insert(1, os.path.join(_CODEDIR, '../../../util/'))

import download  # pylint: disable=wrong-import-position
import download_util  # pylint: disable=wrong-import-position


class DownloadHealthTest(unittest.TestCase):

    def test_fetch_and_write_single_turvar_dynamic_table(self):
        domain = '0000'
        var_id = '1435'
        api_key = 'test_key'

        th_url = (f'{download.BPS_API_BASE}/list/model/th/domain/{domain}/'
                  f'var/{var_id}/lang/eng/page/1/key/{api_key}/')
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
                        'total': 2
                    },
                    [
                        {
                            'th_id': 115,
                            'th': '2015'
                        },
                        {
                            'th_id': 116,
                            'th': '2016'
                        },
                    ],
                ],
            },
        )

        data_url = (f'{download.BPS_API_BASE}/list/model/data/domain/{domain}/'
                    f'var/{var_id}/th/115;116/lang/eng/key/{api_key}/')
        download_util.set_test_url_download_response(
            url=data_url,
            params={},
            response={
                'status': 'OK',
                'var': [{
                    'val': 1435,
                    'label': 'Smoked Tobacco'
                }],
                'turvar': [{
                    'val': '0',
                    'label': 'Tidak Ada'
                }],
                'vervar': [
                    {
                        'val': 1100,
                        'label': '<b>ACEH</b>'
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
                        'val': 116,
                        'label': '2016'
                    },
                ],
                'turtahun': [{
                    'val': 0,
                    'label': 'Tahun'
                }],
                'datacontent': {
                    '1100143501150': 29.79,
                    '1100143501160': 28.18,
                    '9999143501150': 30.08,
                    '9999143501160': 28.97,
                },
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            in_dir = os.path.join(tmpdir, 'input_files')
            raw_dir = os.path.join(tmpdir, 'raw_files')
            files = download.download_all_health_datasets(
                output_dir=in_dir,
                domain=domain,
                api_key=api_key,
                selected_datasets=['smoked_tobacco'],
                raw_output_dir=raw_dir,
            )
            self.assertEqual(len(files), 1)
            with open(files[0], 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))

            self.assertEqual(
                rows,
                [
                    [
                        '',
                        ('Percentage of Population Aged 15 Years and Older Who '
                         'Smoked Tobacco by Province (Percent)'),
                        '',
                    ],
                    ['Province', 'Year 2015', 'Year 2016'],
                    ['ACEH', '29.79', '28.18'],
                    ['INDONESIA', '30.08', '28.97'],
                ],
            )
            raw_path = os.path.join(raw_dir, 'smoked_tobacco_by_province.json')
            self.assertTrue(os.path.exists(raw_path))
            with open(raw_path, 'r', encoding='utf-8') as rf:
                raw_payload = json.load(rf)
            self.assertEqual(raw_payload['var_id'], '1435')
            self.assertEqual(len(raw_payload['chunks']), 1)

    def test_fetch_and_write_multi_turvar_dynamic_table(self):
        domain = '0000'
        var_id = '455'
        api_key = 'test_key'

        th_url = (f'{download.BPS_API_BASE}/list/model/th/domain/{domain}/'
                  f'var/{var_id}/lang/eng/page/1/key/{api_key}/')
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
                        'total': 2
                    },
                    [
                        {
                            'th_id': 121,
                            'th': '2021'
                        },
                        {
                            'th_id': 122,
                            'th': '2022'
                        },
                    ],
                ],
            },
        )

        data_url = (f'{download.BPS_API_BASE}/list/model/data/domain/{domain}/'
                    f'var/{var_id}/th/121;122/lang/eng/key/{api_key}/')
        download_util.set_test_url_download_response(
            url=data_url,
            params={},
            response={
                'status': 'OK',
                'var': [{
                    'val': 455,
                    'label': 'Life Expectancy'
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
                'vervar': [
                    {
                        'val': 1100,
                        'label': '<b>ACEH</b>'
                    },
                    {
                        'val': 1101,
                        'label': 'Simeulue'
                    },
                ],
                'tahun': [
                    {
                        'val': 121,
                        'label': '2021'
                    },
                    {
                        'val': 122,
                        'label': '2022'
                    },
                ],
                'turtahun': [{
                    'val': 0,
                    'label': 'Tahun'
                }],
                'datacontent': {
                    '11004552111210': 68.02,
                    '11004552111220': 68.23,
                    '11004552121210': 71.91,
                    '11004552121220': 72.11,
                    '11014552111210': 63.44,
                    '11014552111220': 63.67,
                    '11014552121210': 67.25,
                    '11014552121220': 67.47,
                },
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            files = download.download_all_health_datasets(
                output_dir=tmpdir,
                domain=domain,
                api_key=api_key,
                selected_datasets=['life_expectancy'],
            )
            self.assertEqual(len(files), 1)
            with open(files[0], 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))

            self.assertEqual(
                rows,
                [
                    ['', 'Male', 'Male', 'Female', 'Female'],
                    [
                        'Province',
                        'Year 2021',
                        'Year 2022',
                        'Year 2021',
                        'Year 2022',
                    ],
                    ['ACEH', '68.02', '68.23', '71.91', '72.11'],
                    ['Simeulue', '63.44', '63.67', '67.25', '67.47'],
                ],
            )

    def test_static_tables_parsing(self):
        domain = '0000'
        api_key = 'test_key'

        # Mock AIDS static table 1569
        aids_url = (
            f'{download.BPS_API_BASE}/view/domain/{domain}/model/statictable/'
            f'lang/ind/id/1569/key/{api_key}/')
        aids_html = """
    <table>
      <tr><td colspan="4">Jumlah Kasus dan Kumulatif Kasus AIDS</td></tr>
      <tr>
        <td rowspan="2">Provinsi</td>
        <td colspan="2">Jumlah Kasus</td>
        <td>Meninggal</td>
      </tr>
      <tr><td>2008 2</td><td>2009</td><td>2008</td></tr>
      <tr><td>Aceh</td><td>13</td><td>28</td><td>13</td></tr>
      <tr><td>Jumlah</td><td>4969</td><td>5483</td><td>899</td></tr>
      <tr><td colspan="4">Catatan: Data s/d September 2012</td></tr>
    </table>
    """
        download_util.set_test_url_download_response(
            url=aids_url,
            params={},
            response={
                'status': 'OK',
                'data': {
                    'table': aids_html
                }
            },
        )

        # Mock Outpatient static table 1620 (including redundant Jumlah column)
        outpatient_url = (
            f'{download.BPS_API_BASE}/view/domain/{domain}/model/statictable/'
            f'lang/ind/id/1620/key/{api_key}/')
        outpatient_html = """
    <table>
      <tr><td colspan="4">Persentase Penduduk yang Berobat Jalan</td></tr>
      <tr><td colspan="4">PENDUDUK LAKI-LAKI</td></tr>
      <tr><td rowspan="2">Provinsi</td><td colspan="3">2009</td></tr>
      <tr><td>RS Pemerintah</td><td>RS Swasta</td><td>Jumlah</td></tr>
      <tr><td>Aceh</td><td>11,34</td><td>2,45</td><td>100,00</td></tr>
      <tr><td>I N D O N E S I A</td><td>6,71</td><td>6,82</td><td>100,00</td></tr>
      <tr><td colspan="4">PENDUDUK PEREMPUAN</td></tr>
      <tr><td rowspan="2">Provinsi</td><td colspan="3">2009</td></tr>
      <tr><td>RS Pemerintah</td><td>RS Swasta</td><td>Jumlah</td></tr>
      <tr><td>Aceh</td><td>10,75</td><td>2,29</td><td>100,00</td></tr>
      <tr><td>I N D O N E S I A</td><td>6,29</td><td>6,90</td><td>100,00</td></tr>
    </table>
    """
        download_util.set_test_url_download_response(
            url=outpatient_url,
            params={},
            response={
                'status': 'OK',
                'data': {
                    'table': outpatient_html
                }
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            in_dir = os.path.join(tmpdir, 'input_files')
            raw_dir = os.path.join(tmpdir, 'raw_files')
            files = download.download_all_health_datasets(
                output_dir=in_dir,
                domain=domain,
                api_key=api_key,
                selected_datasets=['aids_cases', 'outpatient_treatment'],
                raw_output_dir=raw_dir,
            )
            self.assertEqual(len(files), 3)
            self.assertTrue(
                os.path.exists(
                    os.path.join(raw_dir, 'aids_cases_by_province.json')))
            self.assertTrue(
                os.path.exists(
                    os.path.join(raw_dir, 'outpatient_treatment.json')))

            with open(
                    os.path.join(in_dir, 'aids_cases_by_province.csv'),
                    'r',
                    encoding='utf-8',
            ) as f:
                aids_rows = list(csv.reader(f))
            self.assertEqual(
                aids_rows,
                [
                    ['Provinsi', 'Jumlah Kasus', 'Jumlah Kasus', 'Meninggal'],
                    ['', 'Year 2008', 'Year 2009', 'Year 2008'],
                    ['Aceh', '13', '28', '13'],
                    ['INDONESIA', '4969', '5483', '899'],
                ],
            )

            with open(
                    os.path.join(in_dir,
                                 'outpatient_treatment_male_by_province.csv'),
                    'r',
                    encoding='utf-8',
            ) as f:
                male_rows = list(csv.reader(f))
            self.assertEqual(
                male_rows,
                [
                    ['Provinsi', 'Year 2009', 'Year 2009'],
                    ['PENDUDUK LAKI-LAKI', 'RS Pemerintah', 'RS Swasta'],
                    ['Aceh', '11.34', '2.45'],
                    ['Indonesia', '6.71', '6.82'],
                ],
            )

            with open(
                    os.path.join(in_dir,
                                 'outpatient_treatment_female_by_province.csv'),
                    'r',
                    encoding='utf-8',
            ) as f:
                female_rows = list(csv.reader(f))
            self.assertEqual(
                female_rows,
                [
                    ['Provinsi', 'Year 2009', 'Year 2009'],
                    ['PENDUDUK PEREMPUAN', 'RS Pemerintah', 'RS Swasta'],
                    ['Aceh', '10.75', '2.29'],
                    ['Indonesia', '6.29', '6.90'],
                ],
            )

    def test_normalize_numeric_cell_and_static_table_error_handling(self):
        self.assertEqual(download.normalize_numeric_cell('4.969'), '4969')
        self.assertEqual(download.normalize_numeric_cell('2 727'), '2727')
        self.assertEqual(download.normalize_numeric_cell('2 727,5'), '2727.5')
        self.assertEqual(download.normalize_numeric_cell('1.234,56'), '1234.56')
        self.assertEqual(download.normalize_numeric_cell('12,34'), '12.34')
        self.assertEqual(download.normalize_numeric_cell('–'), '')

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, 'out.csv')
            with self.assertRaises(RuntimeError):
                download.process_aids_static_table(
                    [['Title'], ['Provinsi', '2008'], ['', '2009'],
                     ['Aceh', '1']],
                    out_file,
                )
            with self.assertRaises(RuntimeError):
                download.process_health_complaint_static_table(
                    [['Title'], ['Provinsi', 'NotAYear'], ['', 'L'], ['', 'U'],
                     ['Aceh', '1']],
                    out_file,
                )

    def test_api_key_resolution_and_redaction(self):
        url = 'https://webapi.bps.go.id/v1/api/list/key/secret123/'
        self.assertEqual(
            download.redact_api_key(url, 'secret123'),
            'https://webapi.bps.go.id/v1/api/list/key/<REDACTED>/',
        )
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg='Downloading URL: %s',
            args=(url,),
            exc_info=None,
        )
        filt = download._RedactApiKeyFilter('secret123')
        self.assertTrue(filt.filter(record))
        self.assertNotIn('secret123', record.getMessage())
        self.assertIn('<REDACTED>', record.getMessage())

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = os.path.join(tmpdir, 'config.json')
            with open(cfg_path, 'w', encoding='utf-8') as f:
                json.dump({'bps_api_key': 'cfg_secret_key'}, f)
            with mock.patch.dict(os.environ, {'BPS_API_KEY': ''}, clear=False):
                self.assertEqual(
                    download.resolve_api_key('', cfg_path),
                    'cfg_secret_key',
                )
                with self.assertRaises(ValueError):
                    download.resolve_api_key('',
                                             os.path.join(tmpdir, 'none.json'))


if __name__ == '__main__':
    unittest.main()
