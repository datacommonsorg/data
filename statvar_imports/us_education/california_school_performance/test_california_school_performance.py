# Copyright 2025 Google LLC
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
"""Tests for California School Performance StatVar import."""

import csv
import io
import os
import subprocess
import sys
import unittest


class CaliforniaSchoolPerformanceTest(unittest.TestCase):

    def setUp(self):
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_data_dir = os.path.join(self.root_dir, 'test_data')
        self.tools_dir = os.path.abspath(os.path.join(self.root_dir, '../../../tools/statvar_importer'))
        self.sample_input = os.path.join(self.test_data_dir, 'sample_input.txt')
        self.expected_output = os.path.join(self.test_data_dir, 'sample_state_output.csv')
        self.pv_map = os.path.join(self.root_dir, 'config/california_school_performance_pvmap.csv')
        self.metadata = os.path.join(self.root_dir, 'config/california_school_performance_metadata.csv')
        self.existing_mcf = 'gs://unresolved_mcf/scripts/statvar/stat_vars.mcf'
        self.output_prefix = os.path.join(self.test_data_dir, 'test_run_output')

        if self.root_dir not in sys.path:
            sys.path.insert(0, self.root_dir)

    def tearDown(self):
        for ext in ['.csv', '.tmcf', '_stat_vars.mcf']:
            f = self.output_prefix + ext
            if os.path.exists(f):
                os.remove(f)

    def test_stat_var_processor_execution_and_parity(self):
        """Verify that stat_var_processor generates valid CSV/TMCF matching sample_state_output.csv."""
        cmd = [
            sys.executable,
            os.path.join(self.tools_dir, 'stat_var_processor.py'),
            f'--input_data={self.sample_input}',
            f'--pv_map={self.pv_map}',
            f'--config_file={self.metadata}',
            f'--existing_statvar_mcf={self.existing_mcf}',
            f'--output_path={self.output_prefix}',
        ]
        env = os.environ.copy()
        env['PYTHONPATH'] = self.tools_dir

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Processor failed: {result.stderr}")

        output_csv = self.output_prefix + '.csv'
        output_tmcf = self.output_prefix + '.tmcf'

        self.assertTrue(os.path.exists(output_csv), f"Missing output CSV: {output_csv}")
        self.assertTrue(os.path.exists(output_tmcf), f"Missing output TMCF: {output_tmcf}")

        with open(output_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertGreater(len(rows), 0, "Output CSV should not be empty")

        required_cols = {'observationDate', 'observationAbout', 'variableMeasured', 'value'}
        self.assertTrue(required_cols.issubset(set(reader.fieldnames)))

        # Compare generated output with expected sample fixture
        with open(self.expected_output, 'r', encoding='utf-8') as f_exp:
            exp_reader = csv.DictReader(f_exp)
            expected_rows = list(exp_reader)

        self.assertEqual(
            len(rows), len(expected_rows),
            f"Row count mismatch: got {len(rows)}, expected {len(expected_rows)}"
        )
        for i, (act, exp) in enumerate(zip(rows, expected_rows)):
            self.assertEqual(act, exp, f"Discrepancy at row {i}:\nActual:   {act}\nExpected: {exp}")

    def test_download_parse_years(self):
        """Verify year string parsing logic."""
        import download
        self.assertEqual(download.parse_years('2023'), [2023])
        self.assertEqual(download.parse_years('2023, 2024'), [2023, 2024])
        self.assertEqual(download.parse_years('2021-2023'), [2021, 2022, 2023])
        all_years = download.parse_years('all')
        self.assertIn(2015, all_years)
        self.assertIn(2024, all_years)

    def test_download_normalize_and_filter_stream(self):
        """Verify record normalization and entity filtering logic."""
        import download

        sample_csv = (
            'County Code^District Code^School Code^Type ID^Test Year^Test ID^Student Group ID^Grade^'
            'Total Students Tested with Scores^Mean Scale Score^Percentage Standard Exceeded^'
            'Percentage Standard Met^Percentage Standard Met and Above^Percentage Standard Nearly Met^Percentage Standard Not Met\n'
            '00^00000^0000000^4^2024^1^1^3^100^2400.0^20.0^25.0^45.0^25.0^30.0\n'
            '01^12345^6789012^7^2024^1^1^3^50^2350.0^10.0^20.0^30.0^30.0^40.0\n'
        )

        stream = io.StringIO(sample_csv)
        rows = list(download.normalize_and_filter_stream(stream, keep_all_entities=False))
        # School-level entity (Type ID 7) should be filtered out
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], '00')
        self.assertEqual(rows[0][1], '2024')
        self.assertEqual(rows[0][3], '3')  # Grade
        self.assertEqual(rows[0][4], '1')  # Test ID


if __name__ == '__main__':
    unittest.main()
