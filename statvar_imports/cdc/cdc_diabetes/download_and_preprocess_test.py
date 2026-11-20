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
"""Unit tests for CDC Diabetes download_and_preprocess."""

import csv
import os
import sys
import tempfile
import unittest

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

import download_and_preprocess  # pylint: disable=wrong-import-position


class DownloadAndPreprocessTest(unittest.TestCase):
    """Tests for CDC Diabetes preprocessing logic."""

    def setUp(self):
        super().setUp()
        self.test_data_dir = os.path.join(_MODULE_DIR, 'test_data')

    def test_stat_vars_mapping_has_18_unique_dcids(self):
        self.assertEqual(len(download_and_preprocess.STAT_VARS), 9)
        all_dcids = set()
        for measured_dcid, stderr_dcid in (
                download_and_preprocess.STAT_VARS.values()):
            self.assertTrue(measured_dcid.startswith('dcid:'))
            self.assertTrue(stderr_dcid.startswith('dcid:'))
            all_dcids.add(measured_dcid)
            all_dcids.add(stderr_dcid)
        self.assertEqual(len(all_dcids), 18)

    def test_parse_raw_csv_file_filters_and_computes_std_error(self):
        raw_csv = os.path.join(
            self.test_data_dir,
            'raw',
            'DiabetesAtlasCountyData_diabetes_total_2022.csv',
        )
        rows = download_and_preprocess.parse_raw_csv_file(raw_csv)
        # 2 valid counties (01001 and 56039) * 2 StatVars = 4 rows.
        self.assertEqual(len(rows), 4)
        self.assertEqual(
            rows[0],
            [
                'dcid:geoId/01001',
                '2022',
                'dcid:Percent_Person_20OrMoreYears_WithDiabetes',
                '9.8',
                'dcid:AgeAdjustedPrevalence',
                'P1Y',
            ],
        )
        # (12.2 - 9.8) / 1.96 = 1.2244897959 -> 1.22449
        self.assertEqual(
            rows[1],
            [
                'dcid:geoId/01001',
                '2022',
                'dcid:dc/d4j16hnl53es2',
                '1.22449',
                'dcid:AgeAdjustedPrevalence',
                'P1Y',
            ],
        )
        self.assertEqual(
            rows[2],
            [
                'dcid:geoId/56039',
                '2022',
                'dcid:Percent_Person_20OrMoreYears_WithDiabetes',
                '4.5',
                'dcid:AgeAdjustedPrevalence',
                'P1Y',
            ],
        )
        # (6.5 - 4.5) / 1.96 = 1.020408163 -> 1.02041
        self.assertEqual(
            rows[3],
            [
                'dcid:geoId/56039',
                '2022',
                'dcid:dc/d4j16hnl53es2',
                '1.02041',
                'dcid:AgeAdjustedPrevalence',
                'P1Y',
            ],
        )

    def test_process_all_combines_baseline_and_raw(self):
        baseline_dir = os.path.join(self.test_data_dir, 'baseline')
        raw_dir = os.path.join(self.test_data_dir, 'raw')
        with tempfile.TemporaryDirectory() as tmp_out:
            out_csv = download_and_preprocess.process_all(
                baseline_dir=baseline_dir,
                gcs_baseline_prefix='',
                raw_input_dir=raw_dir,
                output_dir=tmp_out,
                skip_baseline=False,
                fetch_api=False,
            )
            self.assertTrue(os.path.exists(out_csv))
            self.assertTrue(
                os.path.exists(os.path.join(tmp_out, 'cdc_diabetes.tmcf')))
            with open(out_csv, 'r', encoding='utf-8') as f:
                reader = list(csv.reader(f))
            # Header + 2 baseline (2021) + 4 raw (2022) + 2 raw (2024) = 9 rows.
            self.assertEqual(len(reader), 9)
            self.assertEqual(
                reader[0],
                [
                    'observationAbout',
                    'observationDate',
                    'variableMeasured',
                    'value',
                    'measurementMethod',
                    'observationPeriod',
                ],
            )
            years = {r[1] for r in reader[1:]}
            self.assertEqual(years, {'2021', '2022', '2024'})


if __name__ == '__main__':
    unittest.main()
