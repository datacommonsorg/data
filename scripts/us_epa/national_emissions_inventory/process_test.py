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

import filecmp
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _MODULE_DIR)

from config import df_columns
from process import USAirEmissionTrends, process_files


class ProcessEnhancedTest(unittest.TestCase):

    def setUp(self):
        self.test_data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'test_data')
        self.temp_dir = tempfile.mkdtemp()
        self.intermediate_path = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        if os.path.exists(self.intermediate_path):
            shutil.rmtree(self.intermediate_path)

    def test_script(self):
        input_path = os.path.join(self.test_data_dir, 'input')
        expected_path = os.path.join(self.test_data_dir, 'expected')
        process_files(input_path, self.temp_dir, self.intermediate_path)

        # Compare the output files
        expected_files = sorted(os.listdir(expected_path))
        generated_files = sorted(os.listdir(self.temp_dir))

        self.assertEqual(len(expected_files), len(generated_files),
                         "Number of files mismatch")

        for expected_file, generated_file in zip(expected_files,
                                                 generated_files):
            expected_file_path = os.path.join(expected_path, expected_file)
            generated_file_path = os.path.join(self.temp_dir, generated_file)

            self.assertTrue(
                filecmp.cmp(expected_file_path,
                            generated_file_path,
                            shallow=False),
                f"File content mismatch: {expected_file} and {generated_file}")


class RegularizeColumnsTest(unittest.TestCase):

    def setUp(self):
        self.loader = USAirEmissionTrends([], '', '', '', '')

    def test_regularize_columns_2017_nonpoint_float64_nan(self):
        # 2017 nonpoint file with float64 NaN emissions type code
        df = pd.DataFrame({
            'fips code': [1001, 1003],
            'scc': [10100101, 10100201],
            'pollutant code': ['CO', 'NOX'],
            'total emissions': [12.5, 34.2],
            'emissions uom': ['TON', 'TON'],
            'emissions type code': [np.nan, np.nan],
        })
        self.assertEqual(df['emissions type code'].dtype, np.float64)

        result = self.loader._regularize_columns(df,
                                                 '/path/to/2017_nonpoint.csv')

        self.assertEqual(list(result.columns), df_columns)
        self.assertTrue((result['year'] == '2017').all())
        self.assertTrue((result['emissions type code'] == '').all())
        self.assertEqual(result['fips code'].tolist(), [1001, 1003])

    def test_regularize_columns_2020_nonpoint_float64_nan(self):
        # 2020 nonpoint file with float64 NaN emissions type code
        df = pd.DataFrame({
            'fips code': [2013, 2016],
            'scc': [20100101, 20100201],
            'pollutant code': ['SO2', 'VOC'],
            'total emissions': [5.1, 8.7],
            'emissions uom': ['TON', 'TON'],
            'emissions type code': [np.nan, np.nan],
        })
        self.assertEqual(df['emissions type code'].dtype, np.float64)

        result = self.loader._regularize_columns(
            df, '/path/to/2020_nonpoint_data.csv')

        self.assertEqual(list(result.columns), df_columns)
        self.assertTrue((result['year'] == '2020').all())
        self.assertTrue((result['emissions type code'] == '').all())
        self.assertEqual(result['fips code'].tolist(), [2013, 2016])

    def test_regularize_columns_point_files(self):
        # 2017 point_ file with unknown
        df_pt17_unk = pd.DataFrame({
            'fips': [1001],
            'pollutant_code': ['CO'],
            'total_emissions': [15.0],
            'emissions_uom': ['TON'],
            'scc': [10100101],
        })
        res_pt17_unk = self.loader._regularize_columns(
            df_pt17_unk, '/path/to/2017_point_unknown.csv')
        self.assertEqual(list(res_pt17_unk.columns), df_columns)
        self.assertEqual(res_pt17_unk['year'].iloc[0], '2017')
        self.assertEqual(res_pt17_unk['emissions type code'].iloc[0], '')
        self.assertEqual(res_pt17_unk['fips code'].iloc[0], 1001)

        # 2017 point_ file with 678910
        df_pt17_num = pd.DataFrame({
            'fips': [1002],
            'pollutant_code': ['NOX'],
            'total_emissions': [22.0],
            'emissions_uom': ['TON'],
            'scc': [10100102],
        })
        res_pt17_num = self.loader._regularize_columns(
            df_pt17_num, '/path/to/2017_point_678910.csv')
        self.assertEqual(list(res_pt17_num.columns), df_columns)
        self.assertEqual(res_pt17_num['year'].iloc[0], '2017')
        self.assertEqual(res_pt17_num['emissions type code'].iloc[0], '')
        self.assertEqual(res_pt17_num['fips code'].iloc[0], 1002)

        # 2020 point_ file with unknown
        df_pt20_unk = pd.DataFrame({
            'fips state/county code': [1003],
            'pollutant code': ['SO2'],
            'total emissions': [30.0],
            'uom': ['TON'],
            'scc': [10100103],
        })
        res_pt20_unk = self.loader._regularize_columns(
            df_pt20_unk, '/path/to/2020_point_unknown.csv')
        self.assertEqual(list(res_pt20_unk.columns), df_columns)
        self.assertEqual(res_pt20_unk['year'].iloc[0], '2020')
        self.assertEqual(res_pt20_unk['emissions type code'].iloc[0], '')
        self.assertEqual(res_pt20_unk['fips code'].iloc[0], 1003)

        # facility_process file
        df_fac = pd.DataFrame({
            'fips code': [1004],
            'pollutant code': ['PM10-PRI'],
            'total emissions': [4.5],
            'emissions uom': ['TON'],
            'scc': [10100104],
        })
        res_fac = self.loader._regularize_columns(
            df_fac, '/path/to/2017_facility_process.csv')
        self.assertEqual(list(res_fac.columns), df_columns)
        self.assertEqual(res_fac['year'].iloc[0], '2017')
        self.assertEqual(res_fac['emissions type code'].iloc[0], '')

    def test_regularize_columns_2014_tribes(self):
        # Tribal file with 'tribal name' and without 'fips code'
        df_tribes = pd.DataFrame({
            'tribal name': ['Navajo Nation'],
            'scc': [10100101],
            'pollutant code': ['VOC'],
            'total emissions': [10.0],
            'emissions uom': ['TON'],
        })
        res_tribes = self.loader._regularize_columns(
            df_tribes, '/path/to/2014_tribes_data.csv')
        self.assertEqual(list(res_tribes.columns), df_columns)
        self.assertEqual(res_tribes['year'].iloc[0], '2014')
        self.assertEqual(res_tribes['fips code'].iloc[0], 'Navajo Nation')
        self.assertEqual(res_tribes['pollutant type(s)'].iloc[0], 'nan')

        # Tribal process file process_tribes.csv with existing 'fips' column
        df_proc_tribes = pd.DataFrame({
            'fips': [1005],
            'scc': [10100105],
            'pollutant_cd': ['CO'],
            'total_emissions': [18.0],
            'uom': ['TON'],
        })
        res_proc_tribes = self.loader._regularize_columns(
            df_proc_tribes, '/path/to/process_tribes.csv')
        self.assertEqual(list(res_proc_tribes.columns), df_columns)
        self.assertEqual(res_proc_tribes['year'].iloc[0], '2014')
        self.assertEqual(res_proc_tribes['emissions type code'].iloc[0], '')
        self.assertEqual(res_proc_tribes['fips code'].iloc[0], 1005)
        self.assertEqual(res_proc_tribes['pollutant type(s)'].iloc[0], 'nan')

        # Tribal event file event_tribes.csv
        df_event_tribes = pd.DataFrame({
            'fips': [1006],
            'scc': [10100106],
            'pollutant_cd': ['PM25-PRI'],
            'total_emissions': [2.5],
            'uom': ['TON'],
        })
        res_event_tribes = self.loader._regularize_columns(
            df_event_tribes, '/path/to/event_tribes.csv')
        self.assertEqual(list(res_event_tribes.columns), df_columns)
        self.assertEqual(res_event_tribes['year'].iloc[0], '2014')
        self.assertEqual(res_event_tribes['emissions type code'].iloc[0], '')


if __name__ == '__main__':
    unittest.main()
