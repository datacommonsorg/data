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

from statvar_imports.opportunity_insights_outcomes import preprocess


class PreprocessTest(unittest.TestCase):

    def test_format_geo_id(self):
        self.assertEqual(
            preprocess.format_geo_id({'cz': '100'}, 'commuting_zone'),
            'geoId/cz00100',
        )
        self.assertEqual(
            preprocess.format_geo_id({'state': '6', 'county': '85'}, 'county'),
            'geoId/06085',
        )
        self.assertEqual(
            preprocess.format_geo_id(
                {'state': '6', 'county': '85', 'tract': '500100'}, 'tract'
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


if __name__ == '__main__':
    unittest.main()
