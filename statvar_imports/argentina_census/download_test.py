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
"""Unit and integration tests for Argentina_Census download and processing."""

import io
import os
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

from absl import flags
import openpyxl

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

_SAVED_FLAGS = {
    _name: flags.FLAGS[_name]
    for _name in ('output_dir', 'max_workers')
    if _name in flags.FLAGS
}
for _flag_name in _SAVED_FLAGS:
    delattr(flags.FLAGS, _flag_name)

try:
    from statvar_imports.argentina_census import download
except ModuleNotFoundError:
    import download

for _flag_name in ('output_dir', 'max_workers'):
    if _flag_name in flags.FLAGS:
        delattr(flags.FLAGS, _flag_name)
for _flag_name, _flag_obj in _SAVED_FLAGS.items():
    flags.FLAGS[_flag_name] = _flag_obj


class DownloadTest(unittest.TestCase):
    """Tests for helper functions and dataset extraction in download.py."""

    def test_normalize_age_label(self):
        self.assertEqual(download.normalize_age_label('Total'), 'Total')
        self.assertEqual(download.normalize_age_label('0 - 4'), '0-4')
        self.assertEqual(download.normalize_age_label(15.0), '15')
        self.assertEqual(download.normalize_age_label('85 y mas'), '85 y más')
        self.assertEqual(download.normalize_age_label('100 y mas'), '100 y más')

    def test_fmt_num(self):
        self.assertEqual(download.fmt_num(27947446.0), '27947446')
        self.assertEqual(download.fmt_num('13,3'), '13.3')
        self.assertEqual(download.fmt_num('///'), '')
        self.assertEqual(download.fmt_num(None), '')

    def test_parse_age_sex_2022_xlsx(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Cuadro 4'
        ws.append(['Edad', 'Total', 'Mujer', 'Varón'])
        ws.append(['Total', 45892285, 23705494, 22186791])
        ws.append(['0-4', 2989885, 1468541, 1521344])
        buf = io.BytesIO()
        wb.save(buf)

        rows = download.parse_age_sex_2022_xlsx(buf.getvalue())
        self.assertEqual(
            rows,
            [
                ('Total', '45892285', '22186791', '23705494'),
                ('0-4', '2989885', '1521344', '1468541'),
            ],
        )

    def test_parse_age_sex_sheet_xls_and_1991_fix(self):
        fake_rows = [
            ('Total', 32615528, 15937180, 16678348),
            ('70-74', 838000, 355000, 483000),
            ('wrong_label_0', 190000, 82000, 108000),
            ('wrong_label_1', 175000, 75000, 100000),
            ('wrong_label_2', 165000, 70000, 95000),
            ('wrong_label_3', 158000, 66000, 92000),
            ('wrong_label_4', 150000, 62000, 88000),
        ]
        mock_sheet = mock.MagicMock()
        mock_sheet.nrows = len(fake_rows)
        mock_sheet.ncols = 4
        mock_sheet.cell_value.side_effect = lambda r, c: fake_rows[r][c]
        mock_wb = mock.MagicMock()
        mock_wb.sheet_by_index.return_value = mock_sheet

        with mock.patch.object(download.xlrd,
                               'open_workbook',
                               return_value=mock_wb):
            rows = download.parse_age_sex_sheet_xls(b'FAKE_XLS',
                                                    fix_1991_70_74=True)
            self.assertEqual(
                rows,
                [
                    ('Total', '32615528', '15937180', '16678348'),
                    ('70-74', '838000', '355000', '483000'),
                    ('70', '190000', '82000', '108000'),
                    ('71', '175000', '75000', '100000'),
                    ('72', '165000', '70000', '95000'),
                    ('73', '158000', '66000', '92000'),
                    ('74', '150000', '62000', '88000'),
                ],
            )

            mock_sheet.ncols = 0
            self.assertEqual(download.parse_age_sex_sheet_xls(b'EMPTY_XLS'), [])

    def test_extract_xls_from_zip(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('nested/c80b_totalpaís_g2.xls', b'XLS_CONTENT_1980')
        zip_bytes = buf.getvalue()

        self.assertEqual(
            download.extract_xls_from_zip(zip_bytes, 'c80b_totalpais_g2.xls'),
            b'XLS_CONTENT_1980',
        )
        with self.assertRaises(KeyError):
            download.extract_xls_from_zip(zip_bytes, 'missing_file.xls')

    def test_write_csv_atomically(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = os.path.join(tmp_dir, 'sample.csv')
            download._write_csv_atomically(out_csv, ['Year', 'Val'],
                                           [(2022, '100')])
            self.assertTrue(os.path.exists(out_csv))
            with open(out_csv, 'r', encoding='utf-8') as f:
                self.assertEqual(f.read().splitlines(),
                                 ['Year,Val', '2022,100'])

            with self.assertRaises(RuntimeError):
                download._write_csv_atomically(out_csv, ['Year', 'Val'], [])

    def test_collect_required_urls_uses_https_indec(self):
        urls = download.collect_required_urls()
        self.assertGreater(len(urls), 150)
        for url in urls:
            self.assertTrue(
                url.startswith('https://www.indec.gob.ar/ftp/'),
                f'Unexpected URL domain: {url}',
            )

    def test_fetch_url_with_download_util(self):
        test_url = 'https://www.indec.gob.ar/ftp/test_payload.xls'
        download.download_util.set_test_url_download_response(
            test_url, {}, b'FAKE_XLS_BYTES')
        self.assertEqual(download.fetch_url(test_url), b'FAKE_XLS_BYTES')

        html_url = 'https://www.indec.gob.ar/ftp/error.xls'
        download.download_util.set_test_url_download_response(
            html_url, {}, b'<!DOCTYPE html><html>Error</html>')
        with self.assertRaises(RuntimeError):
            download.fetch_url(html_url)

    def test_aa2_2022_aliases_resolve_to_known_places(self):
        places_csv = os.path.join(_MODULE_DIR, 'argentina_places_resolved.csv')
        with open(places_csv, 'r', encoding='utf-8') as f:
            resolved_names = {
                line.split(',', 1)[0].strip().strip('"')
                for line in f.read().splitlines()[1:]
                if line.strip()
            }
        for alias_key, canonical_key in download.AA2_2022_ALIASES.items():
            self.assertNotIn(alias_key, resolved_names)
            self.assertIn(canonical_key, resolved_names)

    def test_build_datasets_raises_on_empty_sheet(self):
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, 'w') as zf:
            zf.writestr('c80b_totalpaís_g2.xls', b'EMPTY_XLS')

        with tempfile.TemporaryDirectory() as tmp_dir, \
             mock.patch.object(download, 'parse_age_sex_sheet_xls', return_value=[]):
            with self.assertRaises(RuntimeError):
                download.build_datasets(
                    {
                        f'{download.POBLACION_FTP_URL}/pv_80_totalpais.zip':
                            zip_buf.getvalue()
                    },
                    tmp_dir,
                )

    def test_stat_var_processor_matches_golden_sample_output(self):
        repo_root = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..'))
        processor_script = os.path.join(repo_root, 'tools', 'statvar_importer',
                                        'stat_var_processor.py')
        test_data_dir = os.path.join(_MODULE_DIR, 'test_data')

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_prefix = os.path.join(tmp_dir, 'sample_output')
            counters_path = os.path.join(tmp_dir, 'sample_counters.csv')
            cmd = [
                sys.executable,
                processor_script,
                f'--input_data={os.path.join(test_data_dir, "sample_input.csv")}',
                f'--pv_map={os.path.join(_MODULE_DIR, "argentina_census_pvmap.csv")}',
                f'--config_file={os.path.join(_MODULE_DIR, "argentina_census_metadata.csv")}',
                f'--places_resolved_csv={os.path.join(_MODULE_DIR, "argentina_places_resolved.csv")}',
                f'--statvar_dcid_remap_csv={os.path.join(_MODULE_DIR, "argentina_statvar_remap.csv")}',
                f'--existing_statvar_mcf={os.path.join(test_data_dir, "sample_output_stat_vars.mcf")}',
                f'--output_path={out_prefix}',
                f'--output_counters={counters_path}',
            ]
            import subprocess
            proc = subprocess.run(cmd,
                                  capture_output=True,
                                  text=True,
                                  check=False)
            self.assertEqual(
                proc.returncode,
                0,
                f'stat_var_processor failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}',
            )

            with open(f'{out_prefix}.csv', 'r', encoding='utf-8') as f_actual, \
                 open(os.path.join(test_data_dir, 'sample_output.csv'), 'r', encoding='utf-8') as f_expected:
                self.assertEqual(f_actual.read(), f_expected.read())

            with open(f'{out_prefix}.tmcf', 'r', encoding='utf-8') as f_actual, \
                 open(os.path.join(test_data_dir, 'sample_output.tmcf'), 'r', encoding='utf-8') as f_expected:
                self.assertEqual(f_actual.read(), f_expected.read())


if __name__ == '__main__':
    unittest.main()
