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
        self.test_data_dir = os.path.join(_MODULE_DIR, 'test_data')

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
        self.assertEqual(res_pt20_unk['total emissions'].iloc[0], 30.0)
        self.assertEqual(res_pt20_unk['emissions uom'].iloc[0], 'TON')

        # 2017 point_ file for regions 1-5 (point_12345.csv)
        df_pt17_reg15 = pd.DataFrame({
            'fips': [1005],
            'pollutant_code': ['CO'],
            'total_emissions': [18.0],
            'emissions_uom': ['TON'],
            'scc': [10100105],
        })
        res_pt17_reg15 = self.loader._regularize_columns(
            df_pt17_reg15, '/path/to/2017neiJan_facility_process_byregions/point_12345.csv')
        self.assertEqual(list(res_pt17_reg15.columns), df_columns)
        self.assertEqual(res_pt17_reg15['year'].iloc[0], '2017')
        self.assertEqual(res_pt17_reg15['emissions type code'].iloc[0], '')
        self.assertEqual(res_pt17_reg15['fips code'].iloc[0], 1005)
        self.assertEqual(res_pt17_reg15['total emissions'].iloc[0], 18.0)
        self.assertEqual(res_pt17_reg15['emissions uom'].iloc[0], 'TON')

        # 2020 point_ file for regions 1-10 (point_1.csv ... point_10.csv)
        df_pt20_reg1 = pd.DataFrame({
            'fips state/county code': [1006],
            'pollutant code': ['NOX'],
            'total emissions': [25.0],
            'uom': ['TON'],
            'scc': [10100106],
        })
        res_pt20_reg1 = self.loader._regularize_columns(
            df_pt20_reg1, '/path/to/2020nei_facility_process_byregions/point_1.csv')
        self.assertEqual(list(res_pt20_reg1.columns), df_columns)
        self.assertEqual(res_pt20_reg1['year'].iloc[0], '2020')
        self.assertEqual(res_pt20_reg1['emissions type code'].iloc[0], '')
        self.assertEqual(res_pt20_reg1['fips code'].iloc[0], 1006)
        self.assertEqual(res_pt20_reg1['total emissions'].iloc[0], 25.0)
        self.assertEqual(res_pt20_reg1['emissions uom'].iloc[0], 'TON')

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

    def test_regularize_columns_unhandled_year_raises_value_error(self):
        df = pd.DataFrame({
            'fips code': [1001],
            'pollutant code': ['CO'],
            'total emissions': [10.0],
            'emissions uom': ['TON'],
            'scc': [10100101],
        })
        with self.assertRaises(ValueError):
            self.loader._regularize_columns(df, '/path/to/2023_data.csv')

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

    def test_national_emissions_fips_padding_and_scc_cleaning(self):
        # Verify 4-digit string FIPS ('1001') -> 'geoId/01001',
        # float SCC ('10100101.0') -> stripped of '.0' and Level 1 mapped to ExternalCombustion,
        # non-numeric observation '.' -> dropped
        temp_dir = tempfile.mkdtemp()
        try:
            csv_path = os.path.join(temp_dir, '2020nei_point_1.csv')
            df = pd.DataFrame({
                'fips state/county code': ['1001', '01003', '1001'],
                'pollutant code': ['CO', 'CO', 'CO'],
                'total emissions': ['12.5', '.', '15.0'],
                'uom': ['TON', 'TON', 'TON'],
                'scc': ['10100101.0', '10100101', '10100101.0'],
            })
            df.to_csv(csv_path, index=False)
            result = self.loader._national_emissions(csv_path)

            # Check that 4-digit FIPS was padded to 'geoId/01001', NOT 'geoId/10010'
            self.assertTrue((result['geo_Id'] == 'geoId/01001').all())
            # Observation '.' was dropped. The 2 remaining rows each generate
            # aggregate and pollutant-specific StatVars (total 4 rows)
            self.assertEqual(len(result), 4)
            self.assertCountEqual(result['observation'].tolist(),
                                  [12.5, 15.0, 12.5, 15.0])
            # SCC was correctly extracted as '1' (External Combustion), not '10'
            self.assertTrue(
                all('SCC_1_ExternalCombustion' in sv for sv in result['SV'])
            )
        finally:
            shutil.rmtree(temp_dir)

    def test_mcf_property_generator(self):
        loader = USAirEmissionTrends([], '', '', '', '')
        loader.final_df = pd.DataFrame({
            'SV': [
                'Annual_Amount_Emissions_CarbonMonoxide_SCC_1_ExternalCombustion',
                'Annual_Amount_Emissions_SCC_21_StationarySourceFuelCombustion'
            ],
            'observation': [10.0, 20.0],
            'geo_Id': ['geoId/01001', 'geoId/01001'],
            'year': ['2020', '2020'],
            'Measurement_Method': [
                'dcAggregate/EPA_NationalEmissionInventory',
                'dcAggregate/EPA_NationalEmissionInventory'
            ],
            'unit': ['Ton', 'Ton']
        })
        loader._mcf_property_generator()
        mcf = loader.final_mcf_template
        self.assertIn(
            'Node: dcid:Annual_Amount_Emissions_CarbonMonoxide_SCC_1_ExternalCombustion',
            mcf)
        self.assertIn(
            'Node: dcid:Annual_Amount_Emissions_SCC_21_StationarySourceFuelCombustion',
            mcf)
        self.assertIn('epaSccCode: dcs:EPA_SCC/1', mcf)
        self.assertIn('epaSccCode: dcs:EPA_SCC/21', mcf)
        self.assertIn('emittedThing: dcs:CarbonMonoxide', mcf)

    def test_worker_exception_bubbling(self):
        temp_dir = tempfile.mkdtemp()
        inter_dir = tempfile.mkdtemp()
        # Unhandled year raises ValueError in _regularize_columns which must bubble up through _process()
        bad_file = os.path.join(temp_dir, '2023_unhandled_year.csv')
        df = pd.DataFrame({'fips code': [1001]})
        df.to_csv(bad_file, index=False)
        try:
            loader = USAirEmissionTrends([bad_file], '', '', '', inter_dir)
            with self.assertRaises(ValueError):
                loader._process()
        finally:
            shutil.rmtree(temp_dir)
            if os.path.exists(inter_dir):
                shutil.rmtree(inter_dir)

    def test_intermediate_directory_purged_on_rerun(self):
        inter_dir = tempfile.mkdtemp()
        temp_out = tempfile.mkdtemp()
        stale_file = os.path.join(inter_dir, 'stale_intermediate.csv')
        with open(stale_file, 'w') as f:
            f.write("stale data")
        self.assertTrue(os.path.exists(stale_file))

        input_path = os.path.join(self.test_data_dir, 'input')
        process_files(input_path, temp_out, inter_dir)

        self.assertFalse(os.path.exists(stale_file))
        shutil.rmtree(temp_out)
        if os.path.exists(inter_dir):
            shutil.rmtree(inter_dir)

    def test_multi_year_processing(self):
        temp_in = tempfile.mkdtemp()
        temp_out = tempfile.mkdtemp()
        inter_dir = tempfile.mkdtemp()
        try:
            dir_17 = os.path.join(temp_in, '2017neiJan_facility_process')
            dir_20 = os.path.join(temp_in, '2020nei_facility_process')
            os.makedirs(dir_17)
            os.makedirs(dir_20)

            df_17 = pd.DataFrame({
                'fips': [1001],
                'pollutant_code': ['CO'],
                'total_emissions': [10.0],
                'emissions_uom': ['TON'],
                'scc': [10100101],
            })
            df_17.to_csv(os.path.join(dir_17, 'point_12345.csv'), index=False)

            df_20 = pd.DataFrame({
                'fips state/county code': [1001],
                'pollutant code': ['CO'],
                'total emissions': [20.0],
                'uom': ['TON'],
                'scc': [10100101],
            })
            df_20.to_csv(os.path.join(dir_20, 'point_1.csv'), index=False)

            csv_out = os.path.join(temp_out, 'national_emissions.csv')
            mcf_out = os.path.join(temp_out, 'national_emissions.mcf')
            tmcf_out = os.path.join(temp_out, 'national_emissions.tmcf')

            ip_files = [
                os.path.join(dir_17, 'point_12345.csv'),
                os.path.join(dir_20, 'point_1.csv')
            ]
            loader = USAirEmissionTrends(ip_files, csv_out, mcf_out, tmcf_out,
                                         inter_dir)
            loader.generate_csv()
            loader.generate_mcf()
            loader.generate_tmcf()

            self.assertTrue(os.path.exists(csv_out))
            res_df = pd.read_csv(csv_out)
            # Each year generates aggregate and CO-specific StatVars (2 * 2 = 4 rows)
            self.assertEqual(len(res_df), 4)
            self.assertCountEqual(
                res_df['year'].astype(str).tolist(),
                ['2017', '2017', '2020', '2020'])
            self.assertCountEqual(
                res_df['observation'].tolist(), [10.0, 10.0, 20.0, 20.0])
            self.assertTrue((res_df['geo_Id'] == 'geoId/01001').all())
        finally:
            shutil.rmtree(temp_in)
            shutil.rmtree(temp_out)
            if os.path.exists(inter_dir):
                shutil.rmtree(inter_dir)


if __name__ == '__main__':
    unittest.main()
