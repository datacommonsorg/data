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
"""Unit tests for Japan Census process.py."""

import os
import sys
import tempfile
import unittest
from unittest import mock

# Ensure repository root and module directory are in sys.path for local and root-level test runs
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '../..'))
for _p in (_SCRIPT_DIR, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import process


class ProcessTest(unittest.TestCase):

    def test_expand_input_files_sorts_largest_first(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            small_file = os.path.join(tmp_dir, 'a_small.csv')
            large_file = os.path.join(tmp_dir, 'b_large.csv')
            with open(small_file, 'w', encoding='utf-8') as f:
                f.write('a,b\n1,2\n')
            with open(large_file, 'w', encoding='utf-8') as f:
                f.write('a,b\n' + '1,2\n' * 50)

            pattern = os.path.join(tmp_dir, '*.csv')
            expanded = process._expand_input_files(pattern)
            self.assertEqual(expanded, [large_file, small_file])

    def test_merge_csv_files_keeps_single_header(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p1 = os.path.join(tmp_dir, 'shard_00')
            p2 = os.path.join(tmp_dir, 'shard_01')
            with open(f'{p1}.csv', 'w', encoding='utf-8') as f:
                f.write(
                    'observationAbout,observationDate,value,variableMeasured\n'
                    'dcid:country/JPN,2020,100,dcid:Count_Person\n'
                )
            with open(f'{p2}.csv', 'w', encoding='utf-8') as f:
                f.write(
                    'observationAbout,observationDate,value,variableMeasured\n'
                    'dcid:country/JPN,2025,95,dcid:Count_Person\n'
                )

            final_csv = os.path.join(tmp_dir, 'merged.csv')
            total_rows = process._merge_csv_files([p1, p2], final_csv)
            self.assertEqual(total_rows, 2)
            with open(final_csv, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            self.assertEqual(
                lines,
                [
                    'observationAbout,observationDate,value,variableMeasured',
                    'dcid:country/JPN,2020,100,dcid:Count_Person',
                    'dcid:country/JPN,2025,95,dcid:Count_Person',
                ],
            )

    def test_merge_counters_aggregates_int_and_float(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            c1 = os.path.join(tmp_dir, 'c1.csv')
            c2 = os.path.join(tmp_dir, 'c2.csv')
            with open(c1, 'w', encoding='utf-8') as f:
                f.write('key,value\nsvobs-added,100\nelapsed_time,1.25\n')
            with open(c2, 'w', encoding='utf-8') as f:
                f.write('key,value\nsvobs-added,250\nelapsed_time,2.50\n')

            final_counters = os.path.join(tmp_dir, 'merged_counters.csv')
            process._merge_counters([c1, c2], final_counters)
            with open(final_counters, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            self.assertEqual(
                lines,
                [
                    'key,value',
                    'elapsed_time,3.75',
                    'svobs-added,350',
                ],
            )

    def test_merge_mcf_files_deduplicates_and_skips_empty(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p1 = os.path.join(tmp_dir, 'shard_00')
            p2 = os.path.join(tmp_dir, 'shard_01')
            final_mcf = os.path.join(tmp_dir, 'merged_stat_vars.mcf')

            # 1. Empty case: should not create final_mcf
            process._merge_mcf_files([p1, p2], '_stat_vars.mcf', final_mcf)
            self.assertFalse(os.path.exists(final_mcf))

            # 2. Non-empty case with duplicate node across shards
            node_block = (
                '# Auto generated comment\n\n'
                'Node: dcid:Count_Person\n'
                'typeOf: dcid:StatisticalVariable\n'
                'populationType: dcid:Person\n'
            )
            with open(f'{p1}_stat_vars.mcf', 'w', encoding='utf-8') as f:
                f.write(node_block)
            with open(f'{p2}_stat_vars.mcf', 'w', encoding='utf-8') as f:
                f.write(node_block)

            process._merge_mcf_files([p1, p2], '_stat_vars.mcf', final_mcf)
            self.assertTrue(os.path.exists(final_mcf))
            with open(final_mcf, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertEqual(content.count('Node: dcid:Count_Person'), 1)

    @mock.patch.object(process.subprocess, 'run')
    def test_run_shard_raises_on_nonzero_exit(self, mock_run):
        mock_proc = mock.MagicMock()
        mock_proc.returncode = 1
        mock_proc.stderr = 'Processor failure details'
        mock_run.return_value = mock_proc

        with self.assertRaises(RuntimeError):
            process._run_shard(
                shard_idx=0,
                input_file='input.csv',
                shard_output_prefix='out_prefix',
                shard_counters_path='counters.csv',
                pv_map='pv.csv',
                config_file='meta.csv',
                existing_statvar_mcf='stat_vars.mcf',
            )


if __name__ == '__main__':
    unittest.main()
