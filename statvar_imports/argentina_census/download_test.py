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
import subprocess
import sys
import tempfile
import unittest

import openpyxl

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..'))
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

import download


class DownloadTest(unittest.TestCase):
    """Tests for helper functions and end-to-end StatVar processing."""

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

    def test_stat_var_processor_sample(self):
        processor_script = os.path.join(_REPO_ROOT, 'tools', 'statvar_importer',
                                        'stat_var_processor.py')
        sample_input = os.path.join(_MODULE_DIR, 'test_data',
                                    'sample_input.csv')
        expected_csv = os.path.join(_MODULE_DIR, 'test_data',
                                    'sample_output.csv')
        expected_tmcf = os.path.join(_MODULE_DIR, 'test_data',
                                     'sample_output.tmcf')

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_prefix = os.path.join(tmp_dir, 'sample_output')
            cmd = [
                sys.executable,
                processor_script,
                f'--input_data={sample_input}',
                f'--pv_map={os.path.join(_MODULE_DIR, "argentina_census_pvmap.csv")}',
                f'--config_file={os.path.join(_MODULE_DIR, "argentina_census_metadata.csv")}',
                f'--places_resolved_csv={os.path.join(_MODULE_DIR, "argentina_places_resolved.csv")}',
                f'--statvar_dcid_remap_csv={os.path.join(_MODULE_DIR, "argentina_statvar_remap.csv")}',
                f'--output_path={out_prefix}',
            ]
            res = subprocess.run(cmd,
                                 capture_output=True,
                                 text=True,
                                 check=False)
            self.assertEqual(
                res.returncode,
                0,
                f'stat_var_processor failed:\n{res.stderr}',
            )
            with open(f'{out_prefix}.csv', 'r',
                      encoding='utf-8') as f_actual, open(
                          expected_csv, 'r', encoding='utf-8') as f_expected:
                self.assertEqual(f_actual.read(), f_expected.read())
            with open(f'{out_prefix}.tmcf', 'r',
                      encoding='utf-8') as f_actual_tmcf, open(
                          expected_tmcf, 'r',
                          encoding='utf-8') as f_expected_tmcf:
                self.assertEqual(f_actual_tmcf.read(), f_expected_tmcf.read())


if __name__ == '__main__':
    unittest.main()
