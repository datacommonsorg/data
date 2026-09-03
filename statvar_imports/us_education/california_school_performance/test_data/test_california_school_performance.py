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
import os
import subprocess
import sys
import unittest


class CaliforniaSchoolPerformanceTest(unittest.TestCase):

    def setUp(self):
        self.module_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.abspath(os.path.join(self.module_dir, '..'))
        self.tools_dir = os.path.abspath(os.path.join(self.root_dir, '../../../tools/statvar_importer'))
        self.sample_input = os.path.join(self.module_dir, 'sample_input.txt')
        self.pv_map = os.path.join(self.root_dir, 'config/california_school_performance_pvmap.csv')
        self.metadata = os.path.join(self.root_dir, 'config/california_school_performance_metadata.csv')
        self.existing_mcf = os.path.join(self.root_dir, 'config/california_school_performance_stat_vars.mcf')
        self.output_prefix = os.path.join(self.module_dir, 'test_run_output')

    def tearDown(self):
        for ext in ['.csv', '.tmcf', '_stat_vars.mcf']:
            f = self.output_prefix + ext
            if os.path.exists(f):
                os.remove(f)

    def test_stat_var_processor_execution(self):
        """Verify that stat_var_processor generates valid CSV and TMCF output."""
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

        with open(output_csv) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertGreater(len(rows), 0, "Output CSV should not be empty")

        required_cols = {'observationDate', 'observationAbout', 'variableMeasured', 'value'}
        self.assertTrue(required_cols.issubset(set(reader.fieldnames)))

        vars_seen = {r['variableMeasured'] for r in rows}
        self.assertIn('dcid:Count_Student_SchoolGrade3_EnglishLanguageArts', vars_seen)
        self.assertIn('dcid:Mean_AssessmentScore_Student_SchoolGrade3_EnglishLanguageArts', vars_seen)
        self.assertIn('dcid:Percent_CA_StandardMet_In_Count_Student_SchoolGrade3_EnglishLanguageArts', vars_seen)


if __name__ == '__main__':
    unittest.main()
