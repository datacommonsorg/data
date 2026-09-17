# Copyright 2026 Google LLC
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
"""Unit tests for scripts/world_bank/datasets/process.py."""

import csv
import os
import tempfile
import unittest
from unittest import mock

from scripts.world_bank.datasets import process


class ProcessTest(unittest.TestCase):

    def test_merge_historical_data_deduplicates_and_preserves_formatting(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            fresh_csv = os.path.join(tmp_dir, 'fresh.csv')
            historical_csv = os.path.join(tmp_dir, 'historical.csv')

            fieldnames = [
                'indicatorcode', 'statvar', 'measurementmethod',
                'observationabout', 'observationdate', 'observationvalue',
                'unit'
            ]

            with open(fresh_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(fieldnames)
                # Integer value "100" and empty unit "" must not become "100.0" or NaN
                writer.writerow([
                    'EG.ELC.ACCS.ZS', 'worldBank/EG_ELC_ACCS_ZS',
                    'WorldBank_WDI_CSV', 'country/ABW', '2020', '100', ''
                ])

            with open(historical_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(fieldnames)
                # Duplicate key with older value "95" (should be dropped in favor of fresh "100")
                writer.writerow([
                    'EG.ELC.ACCS.ZS', 'worldBank/EG_ELC_ACCS_ZS',
                    'WorldBank_WDI_CSV', 'country/ABW', '2020', '95', ''
                ])
                # Unique historical record with high-precision scientific notation
                writer.writerow([
                    'FP.CPI.TOTL', 'worldBank/FP_CPI_TOTL',
                    'WorldBank_WDI_CSV', 'country/BRA', '1982',
                    '1.4450553258209901e-09', ''
                ])

            process.merge_historical_data(fresh_csv, historical_csv)

            with open(fresh_csv, 'r', newline='', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 2)
            # Verify fresh observation took precedence and integer string "100" was preserved
            self.assertEqual(rows[0]['observationdate'], '2020')
            self.assertEqual(rows[0]['observationvalue'], '100')
            self.assertEqual(rows[0]['unit'], '')
            # Verify unique historical observation was appended with exact float string preserved
            self.assertEqual(rows[1]['observationdate'], '1982')
            self.assertEqual(rows[1]['observationvalue'],
                             '1.4450553258209901e-09')

    @mock.patch.object(process.logging, 'fatal')
    def test_merge_historical_data_fatal_on_error(self, mock_fatal):
        with tempfile.TemporaryDirectory() as tmp_dir:
            fresh_csv = os.path.join(tmp_dir, 'fresh.csv')
            with open(fresh_csv, 'w', newline='', encoding='utf-8') as f:
                f.write(
                    'indicatorcode,statvar,measurementmethod,observationabout,observationdate,observationvalue,unit\n'
                )
            missing_csv = os.path.join(tmp_dir, 'nonexistent.csv')
            process.merge_historical_data(fresh_csv, missing_csv)
            mock_fatal.assert_called_once()


if __name__ == '__main__':
    unittest.main()
