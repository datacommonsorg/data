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
"""Unit and PVMAP integration tests for OpportunityInsightsOutcomes download.py."""

import csv
import io
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.opportunity_insights_outcomes import download
from statvar_imports.opportunity_insights_outcomes import preprocess


class DownloadAndPvmapTest(unittest.TestCase):

    def test_format_geo_id(self):
        self.assertEqual(
            preprocess.format_geo_id({'cz': '100'}, 'commuting_zone'),
            'geoId/cz00100',
        )
        self.assertEqual(
            preprocess.format_geo_id({'cz': '100.0'}, 'commuting_zone'),
            'geoId/cz00100',
        )
        self.assertEqual(
            preprocess.format_geo_id({'state': '6', 'county': '85'}, 'county'),
            'geoId/06085',
        )
        self.assertEqual(
            preprocess.format_geo_id({'state': '6.0', 'county': '85.0'}, 'county'),
            'geoId/06085',
        )
        self.assertEqual(
            preprocess.format_geo_id(
                {'state': '6', 'county': '85', 'tract': '500100'}, 'tract'
            ),
            'geoId/06085500100',
        )
        self.assertEqual(
            preprocess.format_geo_id(
                {'state': '6.0', 'county': '85.0', 'tract': '500100.0'}, 'tract'
            ),
            'geoId/06085500100',
        )

    def test_download_file_atomic_and_retry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = os.path.join(tmpdir, 'sample.csv')
            call_count = 0

            def fake_urlopen(req, timeout=300):
                del req, timeout
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise OSError('transient connection reset')
                return io.BytesIO(b'cz,val\n100,0.5\n')

            with mock.patch('urllib.request.urlopen', side_effect=fake_urlopen):
                download.download_file(
                    'https://example.com/sample.csv',
                    dest_path,
                    max_retries=2,
                    retry_backoff_sec=0.01,
                )

            self.assertEqual(call_count, 2)
            self.assertTrue(os.path.exists(dest_path))
            self.assertFalse(os.path.exists(f'{dest_path}.tmp'))
            with open(dest_path, 'r', encoding='utf-8') as f:
                self.assertEqual(f.read(), 'cz,val\n100,0.5\n')

    def test_skips_missing_value_placeholders(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_csv = os.path.join(tmpdir, 'commuting_zone_outcomes.csv')
            out_csv = os.path.join(tmpdir, 'commuting_zone_outcomes_cleaned.csv')
            with open(in_csv, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'cz',
                    'kir_natam_female_p1',
                    'kir_natam_female_p1_se',
                    'kir_natam_female_n',
                    'kir_natam_female_mean',
                ])
                writer.writerow(['100', 'NA', 'N/A', '.', '0.35973939'])
                writer.writerow(['101', '', 'na', ' . ', 'n/a'])

            count = preprocess.shard_wide_csv(in_csv, out_csv, 'commuting_zone')
            self.assertEqual(count, 1)

            with open(out_csv, 'r', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['geo_id'], 'geoId/cz00100')
            self.assertEqual(rows[0]['kir_natam_female_p1'], '')
            self.assertEqual(rows[0]['kir_natam_female_mean'], '0.35973939')

    def test_main_raises_on_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(FileNotFoundError):
                preprocess.prepare_parallel_shards_and_svp_inputs(
                    raw_dir=os.path.join(tmpdir, 'raw'),
                    shard_dir=os.path.join(tmpdir, 'out'),
                    sv_output_prefix=os.path.join(tmpdir, 'output', 'output'),
                    existing_statvar_mcf='',
                )

    def test_extract_csv_from_zip_skips_nested_macosx(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, 'archive.zip')
            target_csv = os.path.join(tmpdir, 'extracted.csv')
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr('folder/__MACOSX/._data.csv', 'corrupted,metadata\n')
                zf.writestr('folder/data.csv', 'cz,val\n100,0.5\n')

            download.extract_csv_from_zip(zip_path, target_csv)
            with open(target_csv, 'r', encoding='utf-8') as f:
                self.assertEqual(f.read(), 'cz,val\n100,0.5\n')

    def test_end_to_end_sharding_and_stat_var_processor(self):
        test_data_dir = os.path.join(_MODULE_DIR, 'test_data')
        in_csv = os.path.join(test_data_dir, 'raw_data', 'tract_outcomes.csv')

        with tempfile.TemporaryDirectory() as tmpdir:
            out_csv = os.path.join(tmpdir, 'tract_outcomes_cleaned.csv')
            count = preprocess.shard_wide_csv(
                in_csv, out_csv, 'tract', max_rows_per_shard=5000
            )
            self.assertEqual(count, 100)
            self.assertTrue(os.path.exists(out_csv))

            sv_out_prefix = os.path.join(tmpdir, 'output')
            res = subprocess.run(
                [
                    'python3',
                    os.path.join(
                        _REPO_ROOT,
                        'tools/statvar_importer/stat_var_processor.py',
                    ),
                    f'--input_data={out_csv}',
                    f'--pv_map={os.path.join(_MODULE_DIR, "pvmap.csv")}',
                    f'--config_file={os.path.join(_MODULE_DIR, "metadata.csv")}',
                    f'--output_path={sv_out_prefix}',
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr)
            with open(f'{sv_out_prefix}.csv', 'r', encoding='utf-8') as f:
                sv_rows = list(csv.DictReader(f))
            self.assertEqual(len(sv_rows), 560)
            dollar_rows = [
                r
                for r in sv_rows
                if 'HouseholdIncome_' in r['variableMeasured']
                or 'IndividualIncome_' in r['variableMeasured']
            ]
            for r in dollar_rows:
                self.assertEqual(r['unit'], 'USDollar')

    def test_sharding_all_datasets_and_stat_var_processor(self):
        test_data_dir = os.path.join(_MODULE_DIR, 'test_data')
        raw_dir = os.path.join(test_data_dir, 'raw_data')
        expected_input_dir = os.path.join(test_data_dir, 'input_files')
        expected_output_dir = os.path.join(test_data_dir, 'output')

        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = os.path.join(tmpdir, 'input_files')
            out_dir = os.path.join(tmpdir, 'output')
            counters_dir = os.path.join(tmpdir, 'counters')
            os.makedirs(shard_dir, exist_ok=True)
            os.makedirs(out_dir, exist_ok=True)
            os.makedirs(counters_dir, exist_ok=True)

            sv_out_prefix = os.path.join(out_dir, 'output')
            counters_file = os.path.join(counters_dir, 'output_counters.csv')
            preprocess.prepare_parallel_shards_and_svp_inputs(
                raw_dir,
                shard_dir,
                sv_out_prefix,
                rows_per_chunk=5000,
                workers=2,
                existing_statvar_mcf='',
            )
            shard_files = [
                os.path.join(shard_dir, f)
                for f in sorted(os.listdir(shard_dir))
                if f.endswith('_cleaned.csv')
            ]
            res = subprocess.run(
                [
                    'python3',
                    os.path.join(
                        _REPO_ROOT,
                        'tools/statvar_importer/stat_var_processor.py',
                    ),
                    f'--input_data={",".join(shard_files)}',
                    f'--pv_map={os.path.join(_MODULE_DIR, "pvmap.csv")}',
                    f'--config_file={os.path.join(_MODULE_DIR, "metadata.csv")}',
                    f'--output_path={sv_out_prefix}',
                    f'--output_counters={counters_file}',
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr)
            self.assertNotIn('Duplicate SVObs', res.stderr)
            self.assertNotIn('Dropping invalid SVObs', res.stderr)
            self.assertTrue(os.path.exists(counters_file))

            for fname in sorted(os.listdir(shard_dir)):
                if fname.endswith('_cleaned.csv'):
                    with open(
                        os.path.join(shard_dir, fname), 'r', encoding='utf-8'
                    ) as f_actual, open(
                        os.path.join(expected_input_dir, fname),
                        'r',
                        encoding='utf-8',
                    ) as f_expected:
                        self.assertEqual(f_actual.read(), f_expected.read())

            for fname in sorted(os.listdir(out_dir)):
                if fname.endswith('.csv') or fname.endswith('.tmcf'):
                    with open(
                        os.path.join(out_dir, fname), 'r', encoding='utf-8'
                    ) as f_actual, open(
                        os.path.join(expected_output_dir, fname),
                        'r',
                        encoding='utf-8',
                    ) as f_expected:
                        self.assertEqual(f_actual.read(), f_expected.read())

            sv_rows = []
            for fname in sorted(os.listdir(out_dir)):
                if fname.endswith('.csv'):
                    with open(
                        os.path.join(out_dir, fname), 'r', encoding='utf-8'
                    ) as f:
                        sv_rows.extend(list(csv.DictReader(f)))
            self.assertEqual(len(sv_rows), 1408)


if __name__ == '__main__':
    unittest.main()
