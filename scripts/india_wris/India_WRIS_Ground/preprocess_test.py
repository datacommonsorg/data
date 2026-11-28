# Copyright 2020 Google LLC
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
"""Hermetic unit tests for India_WRIS_Ground preprocessing."""

import json
import os
import sys
import tempfile
import unittest

import pandas as pd

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..'))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from india_wris.India_WRIS_Ground import preprocess

DATASET_NAME = 'India_WRIS_Ground'
_JSON_FILE_PATH = os.path.join(_MODULE_DIR, '..', 'util', 'groundWater.json')

with open(_JSON_FILE_PATH, 'r', encoding='utf-8') as j:
    _PROPERTIES = json.loads(j.read())

_POLLUTANTS, _CHEM_PROPS = _PROPERTIES
_TMCF_FILE = os.path.join(_MODULE_DIR, f'{DATASET_NAME}.tmcf')
_MCF_FILE = os.path.join(_MODULE_DIR, f'{DATASET_NAME}.mcf')


class TestPreprocess(unittest.TestCase):

    def test_all_nodes_in_mcf_tmcf(self):
        with (
                open(_MCF_FILE, 'r', encoding='utf-8') as mcf,
                open(_TMCF_FILE, 'r', encoding='utf-8') as tmcf,
        ):
            mcf_data = mcf.read()
            tmcf_data = tmcf.read()

        for pollutant in _POLLUTANTS['Pollutant']:
            self.assertIn(pollutant['statvar'], mcf_data)
            self.assertIn(pollutant['statvar'], tmcf_data)
            self.assertIn(pollutant['name'], tmcf_data)

        for chem_prop in _CHEM_PROPS['ChemicalProperty']:
            self.assertIn(chem_prop['statvar'], mcf_data)
            self.assertIn(chem_prop['statvar'], tmcf_data)
            self.assertIn(chem_prop['name'], tmcf_data)

    def test_preprocess_normalizes_districts_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_csv = os.path.join(tmpdir, 'groundWater.csv')
            rows = [
                {
                    'Station Name': 'Adbhar',
                    'State Name': 'Chhattisgarh',
                    'District Name': 'Janjgir - Champa',
                    'Basin Name': 'Mahanadi Basin',
                    'Latitude': 21.9625,
                    'Longitude': 83.0194,
                    'Date Collection': '2023-04',
                    'Arsenic (mg/L)': 0.01,
                    'Calcium (mg/L)': 56.0,
                },
                {
                    'Station Name':
                        ('Borewell Located At Rahiv Gruha Ka;Pa Ahmedguda'
                         ' Ambedkar Nagar Kapra Medchal District.'),
                    'State Name': 'Andhra Pradesh',
                    'District Name': 'Rangareddy',
                    'Basin Name': 'Krishna Basin',
                    'Latitude': 17.5124,
                    'Longitude': 78.5739,
                    'Date Collection': '2021-10',
                    'Arsenic (mg/L)': 0.02,
                    'Calcium (mg/L)': 225.0,
                },
                # Duplicate station/date row where the last row should be kept
                {
                    'Station Name': 'Dera Bassi Punjab',
                    'State Name': 'Punjab',
                    'District Name': 'Patiala',
                    'Basin Name': 'Indus Basin',
                    'Latitude': 30.5872,
                    'Longitude': 76.8428,
                    'Date Collection': '2021-10',
                    'Arsenic (mg/L)': 0.01,
                    'Calcium (mg/L)': 50.0,
                },
                {
                    'Station Name': 'Dera Bassi Punjab',
                    'State Name': 'Punjab',
                    'District Name': 'Patiala',
                    'Basin Name': 'Indus Basin',
                    'Latitude': 30.588197,
                    'Longitude': 76.84608,
                    'Date Collection': '2021-10',
                    'Arsenic (mg/L)': 0.01,
                    'Calcium (mg/L)': 83.0,
                },
                # Empty observation row that should be dropped
                {
                    'Station Name': 'EmptyStation',
                    'State Name': 'Gujarat',
                    'District Name': 'Daman',
                    'Basin Name': 'West Coast',
                    'Latitude': 20.4,
                    'Longitude': 72.8,
                    'Date Collection': '2020-04',
                    'Arsenic (mg/L)': None,
                    'Calcium (mg/L)': None,
                },
            ]
            pd.DataFrame(rows).to_csv(input_csv, index=False)

            retained_csv = os.path.join(tmpdir, 'retained.csv')
            with open(retained_csv, 'w', encoding='utf-8') as f:
                f.write(
                    'variable_measured,observation_about,observation_date,'
                    'observation_period,measurement_method,unit,value\n'
                    'WaterAlkalinity_BodyOfWater_GroundWater,indiaWris/102_Mahal,'
                    '2018,P1Y,IndiaWRIS,MilligramsCaCO3PerLitre,'
                    '685.25Concentration_Fluorine_BodyOfWater_GroundWater,'
                    'indiaWris/463_BhimporKFalia,2000,P1Y,IndiaWRIS,'
                    'MilligramsPerLitre,0.13\n'
                    'WaterAlkalinity_BodyOfWater_GroundWater,indiaWris/102_EmptyVal,'
                    '2018,P1Y,IndiaWRIS,MilligramsCaCO3PerLitre,'
                    'Concentration_Arsenic_BodyOfWater_GroundWater,'
                    'indiaWris/463_BhimporKFalia,2001,P1Y,IndiaWRIS,'
                    'MilligramsPerLitre,0.05\n')

            out_dir = os.path.join(tmpdir, 'output')
            preprocess.main([
                f'--input_csv={input_csv}',
                f'--retained_input_csv={retained_csv}',
                f'--output_dir={out_dir}',
            ])

            out_df = pd.read_csv(os.path.join(out_dir, f'{DATASET_NAME}.csv'))
            self.assertEqual(len(out_df), 3)
            self.assertEqual(
                list(out_df['dcid']),
                [
                    'indiaWris/379_Adbhar',
                    ('indiaWris/518_BorewellLocatedAtRahivGruhaKaPa'
                     'AhmedgudaAmbedkarNagarKapraMedchalDistrict'),
                    'indiaWris/041_DeraBassiPunjab',
                ],
            )
            self.assertEqual(list(out_df['DistrictCode'].astype(str)),
                             ['379', '518', '41'])

            ret_df = pd.read_csv(
                os.path.join(out_dir, 'India_WRIS_Ground_Prod_Retained.csv'))
            self.assertEqual(len(ret_df), 4)
            self.assertEqual(ret_df['value'].iloc[0], 685.25)
            self.assertEqual(ret_df['value'].iloc[1], 0.13)
            self.assertTrue(pd.isna(ret_df['value'].iloc[2]))
            self.assertEqual(ret_df['value'].iloc[3], 0.05)


if __name__ == '__main__':
    unittest.main()
