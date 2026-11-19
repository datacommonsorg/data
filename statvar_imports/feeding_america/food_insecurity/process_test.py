#!/usr/bin/env python3
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
"""Hermetic stat_var_processor fixture tests for FeedingAmerica_FoodInsecurity."""

import csv
import os
import subprocess
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
_SV_PROCESSOR = os.path.join(_REPO_ROOT, 'tools', 'statvar_importer',
                             'stat_var_processor.py')
_TEST_DATA_DIR = os.path.join(_SCRIPT_DIR, 'test_data')


class StatVarProcessorFixtureTest(unittest.TestCase):
    """Regression test verifying PVMap and metadata against test_data/ fixtures."""

    def test_stat_var_processor_matches_expected_fixtures(self):
        sample_input = os.path.join(
            _TEST_DATA_DIR, 'feedingamerica_foodinsecurity_sample_input.csv')
        expected_csv = os.path.join(
            _TEST_DATA_DIR, 'feedingamerica_foodinsecurity_sample_output.csv')
        expected_tmcf = os.path.join(
            _TEST_DATA_DIR, 'feedingamerica_foodinsecurity_sample_output.tmcf')
        pvmap_path = os.path.join(_SCRIPT_DIR,
                                  'feedingamerica_foodinsecurity_pvmap.csv')
        metadata_path = os.path.join(
            _SCRIPT_DIR, 'feedingamerica_foodinsecurity_metadata.csv')

        with tempfile.TemporaryDirectory() as tmp_dir:
            offline_config = os.path.join(tmp_dir, 'metadata_offline.csv')
            with (
                    open(metadata_path, 'r', encoding='utf-8') as f_in,
                    open(offline_config, 'w', encoding='utf-8') as f_out,
            ):
                content = f_in.read()
                if content and not content.endswith('\n'):
                    content += '\n'
                f_out.write(content)
                f_out.write('generate_statvar_mcf,False\n')
                f_out.write('generate_schema_mcf,False\n')
                f_out.write('reconcile_nodes,False\n')
                f_out.write('recon_lookup_api,False\n')

            output_prefix = os.path.join(
                tmp_dir, 'feedingamerica_foodinsecurity_sample_output')
            counters_path = os.path.join(tmp_dir, 'counters.csv')

            subprocess.run(
                [
                    sys.executable,
                    _SV_PROCESSOR,
                    f'--input_data={sample_input}',
                    f'--pv_map={pvmap_path}',
                    f'--config_file={offline_config}',
                    f'--output_path={output_prefix}',
                    f'--output_counters={counters_path}',
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            actual_csv = f'{output_prefix}.csv'
            actual_tmcf = f'{output_prefix}.tmcf'
            with (
                    open(expected_csv, 'r', encoding='utf-8') as f_exp,
                    open(actual_csv, 'r', encoding='utf-8') as f_act,
            ):
                self.assertEqual(f_exp.read().splitlines(),
                                 f_act.read().splitlines())

            with (
                    open(expected_tmcf, 'r', encoding='utf-8') as f_exp,
                    open(actual_tmcf, 'r', encoding='utf-8') as f_act,
            ):
                self.assertEqual(
                    sorted(f_exp.read().splitlines()),
                    sorted(f_act.read().splitlines()),
                )

            with open(actual_csv, 'r', encoding='utf-8') as f_act:
                rows = list(csv.DictReader(f_act))
            statvars = {r['variableMeasured'] for r in rows}
            self.assertEqual(len(statvars), 16)

            with open(counters_path, 'r', encoding='utf-8') as f_cnt:
                counters = {
                    row['key']: row['value'] for row in csv.DictReader(f_cnt)
                }
            self.assertEqual(int(counters['output-svobs-csv-rows']), len(rows))
            self.assertLess(
                int(counters.get('warning-missing-property-key', 0)),
                50,
            )


if __name__ == '__main__':
    unittest.main()
