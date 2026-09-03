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
"""Hermetic unit tests for Zurich wir_2552_wiki generate_rollups module."""

import os
import sys
import tempfile
import unittest
import numpy as np
import pandas as pd

# Add module directory to sys.path
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

from generate_rollups import generate_rollups, process_rollups


class GenerateRollupsTest(unittest.TestCase):
    """Unit test suite for generate_rollups preprocessor."""

    def setUp(self):
        super().setUp()
        self.sample_raw_data = pd.DataFrame({
            'Jahr': [2020, 2020, 2020, 2020],
            'RaumSort': [1, 1, 1, 1],
            'RaumLang': [
                'Ganze Stadt', 'Ganze Stadt', 'Ganze Stadt', 'Ganze Stadt'
            ],
            'RechtsformSort': [0, 1, 0, 2],
            'RechtsformLang': [
                'Alle Rechtsformen', 'Öffentliches Recht', 'Alle Rechtsformen',
                'Privates Recht'
            ],
            'BetriebsgrSort': [0, 0, 1, 2],
            'BetriebsgrLang': [
                'Alle Betriebsgrössen', 'Alle Betriebsgrössen', 'Mikrobetriebe',
                'Grossbetriebe'
            ],
            'Arbeitsstaetten': ['39747', '500', '1200', '100'],
            'AnzBesch': ['443621', 'K', '5000', '25000'],
            'AnzBeschW': ['202970', '250', '2500', '12000'],
            'AnzBeschM': ['240651', '250', '2500', '13000'],
            'AnzVZA': ['339750', '400', '4000', '20000'],
            'AnzVZAW': ['136406', '200', '2000', '10000'],
            'AnzVZAM': ['203349', '200', '2000', '10000']
        })

    def test_process_rollups_filters_total_rows(self):
        """Verifies that only total rollup rows (RechtsformSort == 0 & BetriebsgrSort == 0) are retained."""
        result_df = process_rollups(self.sample_raw_data)
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df.iloc[0]['RechtsformSort'], 0)
        self.assertEqual(result_df.iloc[0]['BetriebsgrSort'], 0)
        self.assertEqual(result_df.iloc[0]['RechtsformLang'],
                         'Alle Rechtsformen')
        self.assertEqual(result_df.iloc[0]['BetriebsgrLang'],
                         'Alle Betriebsgrössen')

    def test_process_rollups_numeric_coercion(self):
        """Verifies that metric columns are converted to numeric and markers like 'K' become NaN."""
        data = pd.DataFrame({
            'RechtsformSort': [0, 0],
            'BetriebsgrSort': [0, 0],
            'Arbeitsstaetten': ['100', '200'],
            'AnzBesch': ['1500', 'K'],
            'AnzBeschW': [500, 'K'],
            'AnzBeschM': ['1000', 100],
            'AnzVZA': ['1200.5', 'K'],
            'AnzVZAW': ['600.25', '300'],
            'AnzVZAM': ['600.25', 'K']
        })
        result_df = process_rollups(data)
        self.assertEqual(len(result_df), 2)
        self.assertEqual(result_df.iloc[0]['AnzBesch'], 1500.0)
        self.assertTrue(pd.isna(result_df.iloc[1]['AnzBesch']))
        self.assertTrue(pd.isna(result_df.iloc[1]['AnzBeschW']))
        self.assertEqual(result_df.iloc[0]['AnzVZA'], 1200.5)
        self.assertTrue(pd.isna(result_df.iloc[1]['AnzVZA']))
        self.assertEqual(result_df.iloc[1]['AnzVZAW'], 300.0)

    def test_process_rollups_empty_dataframe_raises(self):
        """Verifies that an empty DataFrame raises ValueError."""
        with self.assertRaises(ValueError):
            process_rollups(pd.DataFrame())

    def test_process_rollups_missing_columns_raises(self):
        """Verifies that missing filter columns raise KeyError."""
        df_missing = pd.DataFrame({'RechtsformSort': [0]})
        with self.assertRaises(KeyError):
            process_rollups(df_missing)

    def test_process_rollups_no_matching_rows_raises(self):
        """Verifies that data with no total rows (0, 0) raises ValueError."""
        df_no_match = pd.DataFrame({
            'RechtsformSort': [1, 2],
            'BetriebsgrSort': [1, 2]
        })
        with self.assertRaises(ValueError):
            process_rollups(df_no_match)

    def test_generate_rollups_file_io_success(self):
        """Verifies end-to-end file reading, processing, and output generation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_csv = os.path.join(tmp_dir, 'input.csv')
            output_csv = os.path.join(tmp_dir, 'output_dir',
                                      'output_rollups.csv')

            self.sample_raw_data.to_csv(input_csv,
                                        index=False,
                                        encoding='utf-8')
            result_df = generate_rollups(input_csv, output_csv)

            self.assertTrue(os.path.exists(output_csv))
            self.assertEqual(len(result_df), 1)

            read_back = pd.read_csv(output_csv)
            self.assertEqual(len(read_back), 1)
            self.assertEqual(read_back.iloc[0]['Arbeitsstaetten'], 39747)

    def test_generate_rollups_file_not_found(self):
        """Verifies that non-existent input file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            generate_rollups('/non/existent/path/file.csv', '/tmp/out.csv')

    def test_generate_rollups_empty_file_raises(self):
        """Verifies that an empty input file raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix='.csv') as tmp_file:
            with self.assertRaises(ValueError):
                generate_rollups(tmp_file.name, '/tmp/out.csv')

    def test_process_rollups_string_sort_columns(self):
        """Verifies that sort columns formatted as strings are matched correctly."""
        data = pd.DataFrame({
            'RechtsformSort': ['0', '1'],
            'BetriebsgrSort': ['0', '0'],
            'Arbeitsstaetten': ['100', '200']
        })
        result_df = process_rollups(data)
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df.iloc[0]['Arbeitsstaetten'], 100.0)


if __name__ == '__main__':
    unittest.main()
