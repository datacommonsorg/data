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
"""Unit tests for OpportunityInsightsOutcomes preprocess.py."""

import csv
import os
import tempfile
import unittest
import zipfile

from statvar_imports.opportunity_insights_outcomes import download
from statvar_imports.opportunity_insights_outcomes import preprocess


class PreprocessTest(unittest.TestCase):

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

    def test_classify_and_process_csv(self):
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
                writer.writerow(['100', '0.27893454', '0.0123', '49', '0.35973939'])

            count = preprocess.process_csv_file(in_csv, out_csv, 'commuting_zone')
            self.assertEqual(count, 4)

            with open(out_csv, 'r', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(rows[0]['geo_id'], 'geoId/cz00100')
            self.assertEqual(rows[0]['measured_property'], 'meanPercentileIncomeRank')
            self.assertEqual(rows[0]['stat_type'], 'measuredValue')
            self.assertEqual(rows[0]['race'], 'USC_AmericanIndianAndAlaskaNativeAlone')
            self.assertEqual(rows[0]['gender'], 'Female')
            self.assertEqual(rows[0]['parent_income'], 'Percentile1')
            self.assertEqual(rows[0]['observation_date'], '2014')
            self.assertEqual(rows[0]['observation_period'], 'P2Y')
            self.assertEqual(rows[0]['value'], '0.27893454')

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

            count = preprocess.process_csv_file(in_csv, out_csv, 'commuting_zone')
            self.assertEqual(count, 1)

            with open(out_csv, 'r', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['geo_id'], 'geoId/cz00100')
            self.assertEqual(rows[0]['stat_type'], 'meanValue')
            self.assertEqual(rows[0]['value'], '0.35973939')

    def test_main_raises_on_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            preprocess.FLAGS.mark_as_parsed()
            preprocess.FLAGS.input_dir = os.path.join(tmpdir, 'raw')
            preprocess.FLAGS.output_dir = os.path.join(tmpdir, 'out')
            preprocess.FLAGS.download = False

            with self.assertRaises(FileNotFoundError):
                preprocess.main([])

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

    def test_new_tract_and_cohort_columns(self):
        self.assertEqual(
            preprocess.classify_column('kfi_pooled_pooled_p25'),
            ('kfi', 'pooled_pooled_p25', 'measuredValue', '2014', 'P2Y'),
        )
        self.assertEqual(
            preprocess.classify_column('kii_black_female_p75'),
            ('kii', 'black_female_p75', 'measuredValue', '2014', 'P2Y'),
        )
        self.assertEqual(
            preprocess.classify_column('emp_aian_female_p25'),
            ('emp', 'aian_female_p25', 'measuredValue', '2015', 'P1Y'),
        )
        self.assertEqual(
            preprocess.classify_column('fpw_aian_male_p50'),
            ('fpw', 'aian_male_p50', 'measuredValue', '1994', 'P13Y'),
        )
        self.assertEqual(
            preprocess.classify_column('pooled_pooled_count'),
            ('kid_n', 'pooled_pooled', 'measuredValue', '2000-04-01', 'P1D'),
        )
        self.assertEqual(
            preprocess.classify_column('aian_female_blw_p50_count'),
            ('kid_blw_p50', 'aian_female', 'measuredValue', '1994', 'P7Y'),
        )
        self.assertEqual(
            preprocess.resolve_date_and_period(
                {'cohort': '1978.0'},
                'annual_cohort_1978_1992',
                'emp',
                '2015',
                'P1Y',
            ),
            ('2005', 'P1Y'),
        )

    def test_process_csv_file_sharding(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_csv = os.path.join(tmpdir, 'tract_outcomes.csv')
            out_csv = os.path.join(tmpdir, 'tract_outcomes_cleaned.csv')
            with open(in_csv, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'state',
                    'county',
                    'tract',
                    'kfi_pooled_pooled_p25',
                    'kii_pooled_pooled_p75',
                ])
                writer.writerow(['6', '85', '500100', '45000', '38000'])
                writer.writerow(['6', '85', '500200', '52000', '41000'])

            count = preprocess.process_csv_file(
                in_csv, out_csv, 'tract', max_rows_per_shard=2
            )
            self.assertEqual(count, 4)
            shard0 = out_csv
            shard1 = os.path.join(tmpdir, 'tract_outcomes_part_001_cleaned.csv')
            self.assertTrue(os.path.exists(shard0))
            self.assertTrue(os.path.exists(shard1))
            with open(shard0, 'r', encoding='utf-8') as f0, open(
                shard1, 'r', encoding='utf-8'
            ) as f1:
                rows0 = list(csv.DictReader(f0))
                rows1 = list(csv.DictReader(f1))
            self.assertEqual(len(rows0), 2)
            self.assertEqual(len(rows1), 2)
            self.assertEqual(rows0[0]['measured_property'], 'householdIncome')
            self.assertEqual(rows0[1]['measured_property'], 'individualIncome')


if __name__ == '__main__':
    unittest.main()
