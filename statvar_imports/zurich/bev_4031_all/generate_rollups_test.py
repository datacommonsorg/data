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
"""Hermetic unit tests for Zurich bev_4031_all generate_rollups module."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd

# Add repository root to sys.path
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.zurich.bev_4031_all import generate_rollups as rollup_mod
from statvar_imports.zurich.bev_4031_all.generate_rollups import FLAGS, OUTPUT_COLS, generate_rollups, main, process_rollups


class GenerateRollupsTest(unittest.TestCase):
    """Unit test suite for bev_4031_all generate_rollups preprocessor."""

    def setUp(self):
        super().setUp()
        FLAGS.mark_as_parsed()
        self.sample_raw_data = pd.DataFrame({
            'GueltigAbDatJahr': [2025, 2025],
            'QuarLang': ['Rathaus', 'Hochschulen'],
            'KreisLang': ['Kreis 1', 'Kreis 1'],
            'SexLang': ['männlich', 'weiblich'],
            'HerkunftLang': ['Schweizer*in', 'Ausländer*in'],
            'AnzGebuWir': [5, 15]
        })

    def test_process_rollups_generates_all_demographic_and_spatial_slices(self):
        """Verifies that all demographic slices and spatial levels (Quar, Kreis, Ganze Stadt) are generated."""
        result_df = process_rollups(self.sample_raw_data)
        self.assertListEqual(list(result_df.columns), OUTPUT_COLS)

        # Should include Rathaus, Hochschulen, Kreis 1, and Ganze Stadt
        places = set(result_df['QuarLang'].unique())
        self.assertSetEqual(
            places, {'Rathaus', 'Hochschulen', 'Kreis 1', 'Ganze Stadt'})

        # Total for Ganze Stadt should sum all rows (5 + 15 = 20)
        city_total = result_df[(result_df['QuarLang'] == 'Ganze Stadt') &
                               (result_df['SexLang'] == '') &
                               (result_df['HerkunftLang'] == '')]
        self.assertEqual(len(city_total), 1)
        self.assertEqual(city_total.iloc[0]['AnzGebuWir'], 20)

        # Total for Kreis 1 should also be 20
        kreis_total = result_df[(result_df['QuarLang'] == 'Kreis 1') &
                                (result_df['SexLang'] == '') &
                                (result_df['HerkunftLang'] == '')]
        self.assertEqual(len(kreis_total), 1)
        self.assertEqual(kreis_total.iloc[0]['AnzGebuWir'], 20)

    def test_process_rollups_numeric_coercion(self):
        """Verifies that string/non-numeric values in AnzGebuWir are coerced properly."""
        data = pd.DataFrame({
            'GueltigAbDatJahr': [2025, 2025],
            'QuarLang': ['Rathaus', 'Rathaus'],
            'KreisLang': ['Kreis 1', 'Kreis 1'],
            'SexLang': ['männlich', 'männlich'],
            'HerkunftLang': ['Schweizer*in', 'Schweizer*in'],
            'AnzGebuWir': ['12', 'invalid']
        })
        result_df = process_rollups(data)
        city_total = result_df[(result_df['QuarLang'] == 'Ganze Stadt') &
                               (result_df['SexLang'] == '') &
                               (result_df['HerkunftLang'] == '')]
        self.assertEqual(city_total.iloc[0]['AnzGebuWir'], 12)

    def test_process_rollups_all_nan_slice_dropped(self):
        """Verifies that slices with only non-numeric values ('K') are dropped rather than emitted as 0."""
        data = pd.DataFrame({
            'GueltigAbDatJahr': [2025, 2025],
            'QuarLang': ['Rathaus', 'City'],
            'KreisLang': ['Kreis 1', 'Kreis 1'],
            'SexLang': ['männlich', 'männlich'],
            'HerkunftLang': ['Schweizer*in', 'Schweizer*in'],
            'AnzGebuWir': ['12', 'K']
        })
        result_df = process_rollups(data)
        self.assertNotIn('City', set(result_df['QuarLang'].unique()))

    def test_process_rollups_filters_unknown_regions(self):
        """Verifies that unknown regions (QuarCd/KreisCd 990 or 999, or Unbekannt) are excluded."""
        data = pd.DataFrame({
            'GueltigAbDatJahr': [2025, 2025, 2025],
            'QuarCd': [11, 999, 12],
            'QuarLang': ['Rathaus', 'Unbekannt', 'Hochschulen'],
            'KreisCd': [1, 990, 990],
            'KreisLang': ['Kreis 1', 'Kreis Unbekannt', 'Kreis Unbekannt'],
            'SexLang': ['männlich', 'männlich', 'weiblich'],
            'HerkunftLang': ['Schweizer*in', 'Schweizer*in', 'Ausländer*in'],
            'AnzGebuWir': [5, 20, 10]
        })
        result_df = process_rollups(data)
        places = set(result_df['QuarLang'].unique())
        self.assertSetEqual(places, {'Rathaus', 'Kreis 1', 'Ganze Stadt'})
        city_total = result_df[(result_df['QuarLang'] == 'Ganze Stadt') &
                               (result_df['SexLang'] == '') &
                               (result_df['HerkunftLang'] == '')]
        self.assertEqual(city_total.iloc[0]['AnzGebuWir'], 5)

    def test_process_rollups_empty_dataframe_raises(self):
        """Verifies that an empty DataFrame raises ValueError."""
        with self.assertRaises(ValueError):
            process_rollups(pd.DataFrame())

    def test_process_rollups_missing_columns_raises(self):
        """Verifies that missing required columns raise KeyError."""
        df_missing = pd.DataFrame({'GueltigAbDatJahr': [2025]})
        with self.assertRaises(KeyError):
            process_rollups(df_missing)

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
            self.assertFalse(os.path.exists(f'{output_csv}.tmp'))
            read_back = pd.read_csv(output_csv, keep_default_na=False)
            self.assertEqual(len(read_back), len(result_df))

    def test_generate_rollups_utf8_bom_input(self):
        """Verifies that input CSV with UTF-8 BOM (utf-8-sig) is parsed cleanly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_csv = os.path.join(tmp_dir, 'input_bom.csv')
            output_csv = os.path.join(tmp_dir, 'output_rollups.csv')

            self.sample_raw_data.to_csv(input_csv,
                                        index=False,
                                        encoding='utf-8-sig')
            result_df = generate_rollups(input_csv, output_csv)
            self.assertIn('GueltigAbDatJahr', result_df.columns)
            self.assertTrue(os.path.exists(output_csv))

    def test_generate_rollups_file_not_found(self):
        """Verifies that non-existent input file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            generate_rollups('/non/existent/path/file.csv', '/tmp/out.csv')

    def test_generate_rollups_empty_file_raises(self):
        """Verifies that an empty input file raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix='.csv') as tmp_file:
            with self.assertRaises(ValueError):
                generate_rollups(tmp_file.name, '/tmp/out.csv')

    def test_main_success(self):
        """Verifies that main executes successfully with valid flag parameters."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_csv = os.path.join(tmp_dir, 'input.csv')
            output_csv = os.path.join(tmp_dir, 'output.csv')
            self.sample_raw_data.to_csv(input_csv,
                                        index=False,
                                        encoding='utf-8')
            FLAGS.input_csv = input_csv
            FLAGS.output_csv = output_csv
            main([])
            self.assertTrue(os.path.exists(output_csv))

    def test_main_failure_logs_fatal(self):
        """Verifies that main logs a fatal error with exc_info on exception."""
        FLAGS.input_csv = '/non/existent/path/file.csv'
        FLAGS.output_csv = '/tmp/dummy_output.csv'
        with patch.object(rollup_mod.logging, 'fatal') as mock_fatal:
            main([])
            mock_fatal.assert_called_once()
            self.assertIn('Failed to generate rollups',
                          mock_fatal.call_args[0][0])
            self.assertTrue(mock_fatal.call_args[1].get('exc_info'))

    def test_generate_rollups_on_test_data_fixture(self):
        """Verifies generate_rollups on test_data/bev_4031_wiki_raw_input.csv matches bev_4031_wiki_input.csv."""
        raw_input_csv = os.path.join(_MODULE_DIR, 'test_data',
                                     'bev_4031_wiki_raw_input.csv')
        expected_input_csv = os.path.join(_MODULE_DIR, 'test_data',
                                          'bev_4031_wiki_input.csv')
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_csv = os.path.join(tmp_dir, 'output_rollups.csv')
            result_df = generate_rollups(raw_input_csv, output_csv)
            expected_df = pd.read_csv(expected_input_csv, keep_default_na=False)
            pd.testing.assert_frame_equal(result_df.reset_index(drop=True),
                                          expected_df)
            pd.testing.assert_frame_equal(
                pd.read_csv(output_csv, keep_default_na=False), expected_df)


if __name__ == '__main__':
    unittest.main()
