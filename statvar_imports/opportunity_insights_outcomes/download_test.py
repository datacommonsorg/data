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
                    'kii_black_female_p75',
                ])
                writer.writerow(['6', '85', '500100', '0.27893454', '0.0123', '45000', '38000'])
                writer.writerow(['6', '85', '500200', 'NA', '.', '52000', '41000'])

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
                    f'--pv_map={os.path.join(import_dir, "opportunity_insights_outcomes_pvmap.csv")}',
                    f'--config_file={os.path.join(import_dir, "opportunity_insights_outcomes_metadata.csv")}',
                    f'--output_path={sv_out_prefix}',
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr)
            with open(f'{sv_out_prefix}.csv', 'r', encoding='utf-8') as f:
                sv_rows = list(csv.DictReader(f))
            self.assertEqual(len(sv_rows), 6)
            self.assertEqual(sv_rows[0]['observationAbout'], 'geoId/06085500100')
            self.assertEqual(sv_rows[0]['observationDate'], '2014')
            self.assertEqual(sv_rows[0]['observationPeriod'], 'P2Y')


if __name__ == '__main__':
    unittest.main()
