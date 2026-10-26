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

import csv
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

    def tearDown(self):
        process._HISTORICAL_CACHE.clear()
        super().tearDown()

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

    def test_expand_input_files_empty_dir_raises(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pattern = os.path.join(tmp_dir, '*.csv')
            with self.assertRaises(FileNotFoundError):
                process._expand_input_files(pattern)

    def test_merge_csv_files_keeps_single_header(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p1 = os.path.join(tmp_dir, 'shard_00')
            p2 = os.path.join(tmp_dir, 'shard_01')
            with open(f'{p1}.csv', 'w', encoding='utf-8') as f:
                f.write(
                    'observationAbout,observationDate,value,variableMeasured\n'
                    'dcid:country/JPN,2020,100,dcid:Count_Person\n')
            with open(f'{p2}.csv', 'w', encoding='utf-8') as f:
                f.write(
                    'observationAbout,observationDate,value,variableMeasured\n'
                    'dcid:country/JPN,2025,95,dcid:Count_Person\n')

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
                f.write('key,value\n'
                        'svobs-added,100\n'
                        'elapsed_time,1.25\n'
                        'existing-statvars-from-mcf,12896\n'
                        'process_mem,1.50\n'
                        'processing_rate,500.00\n'
                        'start_time,1000\n'
                        'end_time,1010\n')
            with open(c2, 'w', encoding='utf-8') as f:
                f.write('key,value\n'
                        'svobs-added,250\n'
                        'elapsed_time,2.50\n'
                        'existing-statvars-from-mcf,12896\n'
                        'process_mem,2.25\n'
                        'processing_rate,700.00\n'
                        'start_time,1005\n'
                        'end_time,1025\n')

            final_counters = os.path.join(tmp_dir, 'merged_counters.csv')
            process._merge_counters([c1, c2], final_counters)
            with open(final_counters, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            self.assertEqual(
                lines,
                [
                    'key,value',
                    'elapsed_time,3.75',
                    'end_time,1025',
                    'existing-statvars-from-mcf,12896',
                    'process_mem,2.25',
                    'processing_rate,600.00',
                    'start_time,1000',
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
            node_block = ('# Auto generated comment\n\n'
                          'Node: dcid:Count_Person\n'
                          'typeOf: dcid:StatisticalVariable\n'
                          'populationType: dcid:Person\n')
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

    @mock.patch.object(process.file_util, 'file_copy')
    def test_prepare_local_statvar_mcf_copies_gcs_path(self, mock_file_copy):
        with tempfile.TemporaryDirectory() as tmp_dir:

            def _fake_copy(src, dst):
                with open(dst, 'w', encoding='utf-8') as f:
                    f.write('Node: dcid:Count_Person\n')
                return dst

            mock_file_copy.side_effect = _fake_copy
            local_path = process._prepare_local_statvar_mcf(
                'gs://unresolved_mcf/scripts/statvar/stat_vars.mcf', tmp_dir)
            self.assertEqual(local_path, os.path.join(tmp_dir, 'stat_vars.mcf'))
            mock_file_copy.assert_called_once()

    def test_apply_historical_supplement_from_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            hist_csv = os.path.join(tmp_dir, 'deleted_historical_data.csv')
            with open(hist_csv, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(
                    ['dataset', 'year', 'indicatorCd', 'regionCd', 'value'])
                writer.writerow([
                    'jpn_aa1_gender_age_total_population.csv',
                    '1920',
                    '0201010000000010000',
                    '01000',
                    '2359183',
                ])
                writer.writerow([
                    'jpn_aa1_gender_age_total_population.csv',
                    '2020',
                    '0201010000000010000',
                    '01000',
                    '9999999',
                ])
            live_rows = [{
                'year': '2020',
                'indicatorCd': '0201010000000010000',
                'regionCd': '01000',
                'value': '5224614',
            }]
            merged = process._apply_historical_supplement(
                'jpn_aa1_gender_age_total_population.csv',
                live_rows,
                historical_gcs_path=hist_csv,
            )
            by_yr = {r['year']: r for r in merged}
            self.assertEqual(len(by_yr), 2)
            self.assertEqual(by_yr['1920']['value'], '2359183')
            # Live value must be preserved over historical supplement value
            self.assertEqual(by_yr['2020']['value'], '5224614')

    def test_load_historical_rows_missing_file_raises(self):
        with self.assertRaises(Exception):
            process._load_historical_rows(
                '/nonexistent/deleted_historical_data.csv')

    def test_apply_historical_supplement_skips_unknown_dataset(self):
        rows = [{'year': '2020', 'indicatorCd': '0201010000000010000'}]
        result = process._apply_historical_supplement(
            'sample_input.csv',
            rows,
            historical_gcs_path='gs://nonexistent/deleted_historical_data.csv',
        )
        self.assertEqual(result, rows)

    def test_derive_census_population_rows(self):
        sample_records = [
            # 2020 (Census year) Total population
            {
                'year': '2020',
                'regionCd': '00000',
                'indicatorCd': '0201010000000010000',
                'value': '126146099',
            },
            # 2020 0-4, 5-9, 10-14 (<15 bracket)
            {
                'year': '2020',
                'regionCd': '00000',
                'indicatorCd': '0201010020000010010',
                'value': '4830000',
            },
            {
                'year': '2020',
                'regionCd': '00000',
                'indicatorCd': '0201010020000010020',
                'value': '5130000',
            },
            {
                'year': '2020',
                'regionCd': '00000',
                'indicatorCd': '0201010020000010030',
                'value': '5360000',
            },
            # 2021 (non-census year)
            {
                'year': '2021',
                'regionCd': '00000',
                'indicatorCd': '0201010000000010000',
                'value': '125502000',
            },
        ]
        derived = process._derive_census_population_rows(sample_records,
                                                         mode='national')
        # Non-census year 2021 should be filtered out
        years = {r['year'] for r in derived}
        self.assertEqual(years, {'2020'})
        # Should contain total and derived <15 sum (4830000 + 5130000 + 5360000 = 15320000)
        under_15 = [
            r for r in derived if r['indicatorCd'] == '0201010010000010010'
        ]
        self.assertEqual(len(under_15), 1)
        self.assertEqual(under_15[0]['value'], '15320000')

    def test_prepare_shard_inputs_stages_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = os.path.join(tmp_dir, 'inputs')
            staging_dir = os.path.join(tmp_dir, 'staged')
            os.makedirs(input_dir, exist_ok=True)
            os.makedirs(staging_dir, exist_ok=True)

            muni_file = os.path.join(input_dir, 'jpn_aa1_aa2_age_gender.csv')
            with open(muni_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=process.CSV_HEADER)
                writer.writeheader()
                writer.writerow({
                    'year': '2020',
                    'indicatorCd': '0201010000000010000',
                    'regionCd': '01100',
                    'value': '1961996',
                })
                writer.writerow({
                    'year': '2015',
                    'indicatorCd': '0201010000000010000',
                    'regionCd': '01100',
                    'value': '1952356',
                })

            staged = process._prepare_shard_inputs(
                [muni_file],
                staging_dir=staging_dir,
            )
            # Should have split into two year shards: 2015 and 2020
            self.assertEqual(len(staged), 2)
            staged_names = {os.path.basename(p) for p in staged}
            self.assertEqual(
                staged_names,
                {
                    'jpn_aa1_aa2_age_gender_2015.csv',
                    'jpn_aa1_aa2_age_gender_2020.csv'
                },
            )

    @mock.patch.object(process.logging, 'fatal')
    @mock.patch.object(process,
                       '_run_pipeline',
                       side_effect=RuntimeError('Pipeline failed'))
    def test_main_calls_logging_fatal_on_error(self, mock_run_pipeline,
                                               mock_fatal):
        process.main([])
        mock_run_pipeline.assert_called_once()
        mock_fatal.assert_called_once()


if __name__ == '__main__':
    unittest.main()
