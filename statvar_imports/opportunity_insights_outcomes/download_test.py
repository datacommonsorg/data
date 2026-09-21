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
import os
import subprocess
import tempfile
import unittest
import zipfile

from statvar_imports.opportunity_insights_outcomes import download


class DownloadAndPvmapTest(unittest.TestCase):

    def test_format_geo_id(self):
        self.assertEqual(
            download.format_geo_id({'cz': '100'}, 'commuting_zone'),
            'geoId/cz00100',
        )
        self.assertEqual(
            download.format_geo_id({'cz': '100.0'}, 'commuting_zone'),
            'geoId/cz00100',
        )
        self.assertEqual(
            download.format_geo_id({'state': '6', 'county': '85'}, 'county'),
            'geoId/06085',
        )
        self.assertEqual(
            download.format_geo_id({'state': '6.0', 'county': '85.0'}, 'county'),
            'geoId/06085',
        )
        self.assertEqual(
            download.format_geo_id(
                {'state': '6', 'county': '85', 'tract': '500100'}, 'tract'
            ),
            'geoId/06085500100',
        )
        self.assertEqual(
            download.format_geo_id(
                {'state': '6.0', 'county': '85.0', 'tract': '500100.0'}, 'tract'
            ),
            'geoId/06085500100',
        )

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

            count = download.shard_wide_csv(in_csv, out_csv, 'commuting_zone')
            self.assertEqual(count, 1)

            with open(out_csv, 'r', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['geo_id'], 'geoId/cz00100')
            self.assertEqual(rows[0]['kir_natam_female_p1'], '')
            self.assertEqual(rows[0]['kir_natam_female_mean'], '0.35973939')

    def test_main_raises_on_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            download.FLAGS.mark_as_parsed()
            download.FLAGS.output_dir = os.path.join(tmpdir, 'raw')
            download.FLAGS.shard_dir = os.path.join(tmpdir, 'out')
            download.FLAGS.download = False

            with self.assertRaises(FileNotFoundError):
                download.main([])

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
        with tempfile.TemporaryDirectory() as tmpdir:
            in_csv = os.path.join(tmpdir, 'tract_outcomes.csv')
            out_csv = os.path.join(tmpdir, 'tract_outcomes_cleaned.csv')
            with open(in_csv, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'state',
                    'county',
                    'tract',
                    'kir_natam_female_p1',
                    'kir_natam_female_p1_se',
                    'kfi_pooled_pooled_p25',
                    'kfi_white_pooled_p25',
                    'kfr_top20_white_pooled_p25',
                    'kfr_white_male_p25_mean_se',
                    'kid_white_male_n',
                    'kii_black_female_p75',
                ])
                writer.writerow([
                    '6', '85', '500100',
                    '0.27893454', '0.0123', '45000', '48000', '0.32', '0.005', '120', '38000',
                ])
                writer.writerow([
                    '6', '85', '500200',
                    'NA', '.', '52000', '55000', '0.41', '0.006', '150', '41000',
                ])

            count = download.shard_wide_csv(
                in_csv, out_csv, 'tract', max_rows_per_shard=1
            )
            self.assertEqual(count, 2)
            shard0 = out_csv
            shard1 = os.path.join(tmpdir, 'tract_outcomes_part_001_cleaned.csv')
            self.assertTrue(os.path.exists(shard0))
            self.assertTrue(os.path.exists(shard1))

            import_dir = os.path.dirname(os.path.abspath(download.__file__))
            repo_root = os.path.abspath(os.path.join(import_dir, '..', '..'))
            sv_out_prefix = os.path.join(tmpdir, 'sv_out')
            res = subprocess.run(
                [
                    'python3',
                    os.path.join(
                        repo_root, 'tools/statvar_importer/stat_var_processor.py'
                    ),
                    f'--input_data={shard0},{shard1}',
                    f'--pv_map={os.path.join(import_dir, "pvmap.csv")}',
                    f'--config_file={os.path.join(import_dir, "metadata.csv")}',
                    f'--output_path={sv_out_prefix}',
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr)
            with open(f'{sv_out_prefix}.csv', 'r', encoding='utf-8') as f:
                sv_rows = list(csv.DictReader(f))
            self.assertEqual(len(sv_rows), 14)
            self.assertEqual(sv_rows[0]['observationAbout'], 'geoId/06085500100')

    def test_sharding_all_datasets_and_stat_var_processor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = os.path.join(tmpdir, 'raw_data')
            shard_dir = os.path.join(tmpdir, 'input_files')
            out_dir = os.path.join(tmpdir, 'output_files')
            os.makedirs(raw_dir, exist_ok=True)
            os.makedirs(shard_dir, exist_ok=True)
            os.makedirs(out_dir, exist_ok=True)

            sample_schemas = {
                'commuting_zone_outcomes.csv': (
                    ['cz', 'kfr_pooled_pooled_p25', 'kfr_white_pooled_p25'],
                    [['100', '0.42', '0.45'], ['101', '0.43', '0.46']],
                ),
                'county_outcomes.csv': (
                    ['state', 'county', 'kfr_top20_white_male_p25', 'working_black_pooled_p75_se'],
                    [['6', '85', '0.31', '0.031'], ['6', '87', '0.35', '0.035']],
                ),
                'tract_outcomes.csv': (
                    ['state', 'county', 'tract', 'kfi_pooled_pooled_p25', 'kid_white_male_n'],
                    [['6', '85', '500100', '45000', '120'], ['6', '85', '500200', '52000', '150']],
                ),
                'tract_outcomes_late_simple.csv': (
                    ['state', 'county', 'tract', 'kfr_white_male_p25', 'jail_white_male_p25'],
                    [['6', '85', '500100', '0.48', '0.01'], ['6', '85', '500200', '0.50', '0.02']],
                ),
                'county_by_cohort_outcomes.csv': (
                    ['state', 'county', 'cohort', 'kfr_white_male_p25', 'emp_black_pooled_p75_se'],
                    [['6', '85', '1988', '0.39', '0.050'], ['6', '87', '1988', '0.40', '0.052']],
                ),
                'cz_by_cohort_outcomes.csv': (
                    ['cz', 'cohort', 'kfr_white_male_p25'],
                    [['100', '1980', '0.41'], ['101', '1980', '0.44']],
                ),
            }
            for fname, (headers, rows) in sample_schemas.items():
                with open(os.path.join(raw_dir, fname), 'w', encoding='utf-8', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(headers)
                    w.writerows(rows)

            for filename, geo_level, dataset_mode in download.DATASET_CONFIGS:
                stem = os.path.splitext(filename)[0]
                download.shard_wide_csv(
                    os.path.join(raw_dir, filename),
                    os.path.join(shard_dir, f'{stem}_cleaned.csv'),
                    geo_level,
                    dataset_mode,
                    max_rows_per_shard=10,
                )

            sv_out_prefix = os.path.join(out_dir, 'opportunity_insights_outcomes')
            import_dir = os.path.dirname(os.path.abspath(download.__file__))
            repo_root = os.path.abspath(os.path.join(import_dir, '..', '..'))
            shard_files = [
                os.path.join(shard_dir, f)
                for f in sorted(os.listdir(shard_dir))
                if f.endswith('_cleaned.csv')
            ]
            res = subprocess.run(
                [
                    'python3',
                    os.path.join(repo_root, 'tools/statvar_importer/stat_var_processor.py'),
                    f'--input_data={",".join(shard_files)}',
                    f'--pv_map={os.path.join(import_dir, "pvmap.csv")}',
                    f'--config_file={os.path.join(import_dir, "metadata.csv")}',
                    f'--output_path={sv_out_prefix}',
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr)
            self.assertNotIn('Duplicate SVObs', res.stderr)
            self.assertNotIn('Dropping invalid SVObs', res.stderr)

            with open(f'{sv_out_prefix}.csv', 'r', encoding='utf-8') as f:
                sv_rows = list(csv.DictReader(f))
            self.assertEqual(len(sv_rows), 22)


if __name__ == '__main__':
    unittest.main()
