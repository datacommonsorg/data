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
"""Hermetic unit tests for India_WRIS_Surface preprocessing."""

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

from india_wris.India_WRIS_Surface import preprocess

DATASET_NAME = 'India_WRIS_Surface'
_JSON_FILE_PATH = os.path.join(_MODULE_DIR, '..', 'util', 'surfaceWater.json')

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

    def test_preprocess_creates_surface_dcids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_csv = os.path.join(tmpdir, 'surfaceWater.csv')
            rows = [
                {
                    'StateName': 'Assam',
                    'DistrictName': 'Cachar',
                    'Month': '2008-01',
                    'Year': 2008,
                    'StationName': 'Dholai',
                    'SurfaceWaterStationLatitude': 24.58611,
                    'SurfaceWaterStationLongitude': 92.84222,
                    'Calcium(Ca)': 58.8,
                    'Chloride(Cl)': 19.88,
                },
                {
                    'StateName': 'Telangana',
                    'DistrictName': 'Warangal Rural',
                    'Month': '2019-05',
                    'Year': 2019,
                    'StationName': 'Perur',
                    'SurfaceWaterStationLatitude': 18.0,
                    'SurfaceWaterStationLongitude': 79.5,
                    'Calcium(Ca)': 42.0,
                    'Chloride(Cl)': 15.0,
                },
            ]
            pd.DataFrame(rows).to_csv(input_csv, index=False)

            out_dir = os.path.join(tmpdir, 'output')
            preprocess.main([
                f'--input_csv={input_csv}',
                f'--output_dir={out_dir}',
            ])

            out_df = pd.read_csv(os.path.join(out_dir, f'{DATASET_NAME}.csv'))
            self.assertEqual(len(out_df), 2)
            self.assertEqual(
                list(out_df['dcid']),
                ['indiaWris/282_Dholai', 'indiaWris/36_Perur'],
            )


if __name__ == '__main__':
    unittest.main()
