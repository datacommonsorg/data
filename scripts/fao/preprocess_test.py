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
"""Unit tests for scripts/fao/preprocess.py."""

import csv
import os
import tempfile
import unittest

from scripts.fao import preprocess


class PreprocessTest(unittest.TestCase):

    def test_resolve_country(self):
        self.assertEqual(preprocess.resolve_country("'004"), 'country/AFG')
        self.assertEqual(preprocess.resolve_country("'200"), 'country/CSK')
        self.assertEqual(preprocess.resolve_country("'810"), 'country/SUN')

    def test_preprocess_merges_and_cleans_rows(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_csv_1 = os.path.join(tmp_dir, 'baseline.csv')
            input_csv_2 = os.path.join(tmp_dir, 'latest.csv')
            output_csv = os.path.join(tmp_dir, 'cleaned_output.csv')

            fieldnames = [
                'Area Code', 'Area Code (M49)', 'Area', 'Element Code',
                'Element', 'ISO Currency Code', 'Currency', 'Year Code', 'Year',
                'Months Code', 'Months', 'Unit', 'Value', 'Flag'
            ]
            with open(input_csv_1, 'w', encoding='ISO-8859-1', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow({
                    'Area Code': '2',
                    'Area Code (M49)': "'004",
                    'Area': 'Afghanistan',
                    'Element Code': 'LCU',
                    'Element': 'Local currency units per USD',
                    'ISO Currency Code': 'AFA',
                    'Currency': 'Afghani',
                    'Year Code': '1970',
                    'Year': '1970',
                    'Months Code': '7021',
                    'Months': 'Annual value',
                    'Unit': '',
                    'Value': '44.9984271',
                    'Flag': 'X'
                })

            with open(input_csv_2, 'w', encoding='ISO-8859-1', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow({
                    'Area Code': '2',
                    'Area Code (M49)': "'004",
                    'Area': 'Afghanistan',
                    'Element Code': 'SLC',
                    'Element': 'Standard local currency units per USD',
                    'ISO Currency Code': 'AFN',
                    'Currency': 'Afghani',
                    'Year Code': '2025',
                    'Year': '2025',
                    'Months Code': '7001',
                    'Months': 'January',
                    'Unit': '',
                    'Value': '70.5',
                    'Flag': 'X'
                })

            preprocess.preprocess([input_csv_1, input_csv_2], output_csv)

            with open(output_csv, 'r', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['Country'], 'country/AFG')
            self.assertEqual(rows[0]['Currency'], 'AFA')
            self.assertEqual(rows[0]['YearMonth'], '1970')
            self.assertEqual(rows[0]['ObservationPeriod'], 'P1Y')
            self.assertEqual(rows[0]['ExchangeRatePerUSD'], '44.9984271')
            self.assertEqual(rows[0]['ExchangeRatePerUSD_Standardized'], '')

            self.assertEqual(rows[1]['Country'], 'country/AFG')
            self.assertEqual(rows[1]['Currency'], 'AFN')
            self.assertEqual(rows[1]['YearMonth'], '2025-01')
            self.assertEqual(rows[1]['ObservationPeriod'], 'P1M')
            self.assertEqual(rows[1]['ExchangeRatePerUSD'], '')
            self.assertEqual(rows[1]['ExchangeRatePerUSD_Standardized'], '70.5')


if __name__ == '__main__':
    unittest.main()
