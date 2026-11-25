# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for preprocess_aggregations.py"""

import csv
import os
import sys
import tempfile
import unittest
from unittest import mock

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_PATH not in sys.path:
    sys.path.append(_SCRIPT_PATH)

if __package__:
    from . import preprocess_aggregations
else:
    import preprocess_aggregations


class HatecrimeAggTest(unittest.TestCase):

    def test_process_main(self):
        # testdata/hate_crime_sample.csv and aggregations_expected/aggregation.csv
        # are Git LFS pointer files not populated in standard checkouts/CI, so
        # exercise process_main end-to-end with a small synthetic input CSV.
        rows = [
            {
                'INCIDENT_ID': '1',
                'DATA_YEAR': '2020',
                'OFFENDER_RACE': 'White',
                'OFFENDER_ETHNICITY': 'Not Hispanic or Latino',
                'STATE_ABBR': 'WY',
                'OFFENSE_NAME': 'Simple Assault',
                'BIAS_DESC': 'Anti-White',
                'AGENCY_TYPE_NAME': 'City',
                'MULTIPLE_OFFENSE': 'S',
                'MULTIPLE_BIAS': 'S',
                'PUG_AGENCY_NAME': 'Casper',
                'TOTAL_OFFENDER_COUNT': '1',
                'ADULT_OFFENDER_COUNT': '1',
                'JUVENILE_OFFENDER_COUNT': '0',
                'INCIDENT_DATE': '2020-01-15',
                'VICTIM_TYPES': 'Individual',
                'LOCATION_NAME': 'Residence/Home',
                'VICTIM_COUNT': '1',
                'ADULT_VICTIM_COUNT': '1',
                'JUVENILE_VICTIM_COUNT': '0',
            },
            {
                'INCIDENT_ID': '2',
                'DATA_YEAR': '2020',
                'OFFENDER_RACE': 'Unknown',
                'OFFENDER_ETHNICITY': 'Unknown',
                'STATE_ABBR': 'WY',
                'OFFENSE_NAME': 'Intimidation',
                'BIAS_DESC': 'Anti-Jewish;Anti-White',
                'AGENCY_TYPE_NAME': 'City',
                'MULTIPLE_OFFENSE': 'S',
                'MULTIPLE_BIAS': 'M',
                'PUG_AGENCY_NAME': 'Casper',
                'TOTAL_OFFENDER_COUNT': '0',
                'ADULT_OFFENDER_COUNT': '0',
                'JUVENILE_OFFENDER_COUNT': '0',
                'INCIDENT_DATE': '2020-02-20',
                'VICTIM_TYPES': 'Individual;Business',
                'LOCATION_NAME': 'Highway/Road/Alley/Street/Sidewalk',
                'VICTIM_COUNT': '2',
                'ADULT_VICTIM_COUNT': '1',
                'JUVENILE_VICTIM_COUNT': '1',
            },
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_csv = os.path.join(tmp_dir, 'hate_crime_sample.csv')
            with open(input_csv, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

            cache_dir = os.path.join(tmp_dir, 'cache')
            with mock.patch.object(preprocess_aggregations, '_CACHE_DIR',
                                   cache_dir):
                preprocess_aggregations.process_main(input_csv=input_csv,
                                                     output_path=tmp_dir)

            agg_csv = os.path.join(tmp_dir, 'aggregation.csv')
            agg_mcf = os.path.join(tmp_dir, 'aggregation.mcf')
            self.assertTrue(os.path.exists(agg_csv))
            self.assertTrue(os.path.exists(agg_mcf))

            with open(agg_csv, 'r', encoding='utf-8') as f:
                csv_rows = list(csv.DictReader(f))
            self.assertIn(
                {
                    'DATA_YEAR': '2020',
                    'Place': 'country/USA',
                    'StatVar': 'Count_CriminalIncidents_IsHateCrime',
                    'Value': '2',
                }, csv_rows)
            self.assertIn(
                {
                    'DATA_YEAR': '2020',
                    'Place': 'geoId/56',
                    'StatVar': 'Count_CriminalIncidents_IsHateCrime',
                    'Value': '2',
                }, csv_rows)
            self.assertIn(
                {
                    'DATA_YEAR': '2020',
                    'Place': 'geoId/5613150',
                    'StatVar': 'Count_CriminalIncidents_IsHateCrime',
                    'Value': '2',
                }, csv_rows)

            with open(agg_mcf, 'r', encoding='utf-8') as f:
                mcf_text = f.read()
            self.assertIn('Node: dcid:Count_CriminalIncidents_IsHateCrime',
                          mcf_text)


if __name__ == '__main__':
    unittest.main()
