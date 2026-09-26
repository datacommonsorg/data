# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Unit tests for process.py.'''

import os
import shutil
import tempfile
import unittest

import pandas as pd

import process

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class ProcessTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_prefix = os.path.join(self.test_dir, 'nfip_output')
        self.counters_path = os.path.join(self.test_dir, 'counters.txt')
        self.input_file = os.path.join(_SCRIPT_DIR, 'test_data',
                                       'flood_insurance_claims_input.csv')

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_make_statvar_name(self):
        sv = process._make_statvar_name('FEMAHighRiskFloodZone',
                                        'CountOfClaims',
                                        'BuildingStructureAndContents')
        self.assertEqual(
            sv,
            'dcid:CountOfClaims_NaturalHazardInsurance_FEMAHighRiskFloodZone_BuildingStructureAndContents_FloodEvent'
        )

        sv_all = process._make_statvar_name('', 'SettlementAmount',
                                            'BuildingStructure')
        self.assertEqual(
            sv_all,
            'dcid:SettlementAmount_NaturalHazardInsurance_BuildingStructure_FloodEvent'
        )

    def test_embedded_mappings(self):
        state_map, risk_zone_map = process._load_mappings()
        self.assertEqual(state_map.get('CA'), 'dcid:geoId/06')
        self.assertEqual(state_map.get('california'), 'dcid:geoId/06')
        self.assertEqual(state_map.get('TX'), 'dcid:geoId/48')
        self.assertEqual(risk_zone_map.get('A'), 'FEMAHighRiskFloodZone')
        self.assertEqual(risk_zone_map.get('X'), 'FEMALowRiskFloodZone')
        self.assertEqual(risk_zone_map.get('B'), 'FEMAModerateRiskFloodZone')

    def test_resolve_map_path(self):
        dummy_file = os.path.join(self.test_dir, 'custom_map.py')
        with open(dummy_file, 'w', encoding='utf-8') as f:
            f.write("{'TEST': 'dcid:geoId/99'}")
        pv_arg = f"ratedFloodZone:other.py,observationAbout:{dummy_file}"
        path = process._resolve_map_path(pv_arg, 'observationAbout')
        self.assertEqual(path, dummy_file)
        self.assertIsNone(process._resolve_map_path(None, 'observationAbout'))

    def test_process_data_vectorized_execution(self):
        process.process_data_vectorized(input_data=self.input_file,
                                        output_path=self.output_prefix,
                                        pv_map_arg=None,
                                        chunk_size=50,
                                        num_workers=2,
                                        output_counters=self.counters_path)

        csv_file = f"{self.output_prefix}.csv"
        tmcf_file = f"{self.output_prefix}.tmcf"
        mcf_file = f"{self.output_prefix}.mcf"

        self.assertTrue(os.path.exists(csv_file))
        self.assertTrue(os.path.exists(tmcf_file))
        self.assertTrue(os.path.exists(mcf_file))
        self.assertTrue(os.path.exists(self.counters_path))

        df = pd.read_csv(csv_file)
        self.assertGreater(len(df), 0)
        expected_cols = [
            'observationDate', 'observationAbout', 'value',
            'observationPeriod', 'unit', 'variableMeasured'
        ]
        self.assertEqual(list(df.columns), expected_cols)

        with open(self.counters_path, 'r', encoding='utf-8') as f:
            counters_content = f.read()
        self.assertIn('num_input_rows=99', counters_content)
        self.assertIn(f'num_cleaned_observations={len(df)}', counters_content)

        with open(tmcf_file, 'r', encoding='utf-8') as f:
            tmcf_content = f.read()
        self.assertIn('Node: E:nfip_output->E0', tmcf_content)
        self.assertIn('measurementMethod: dcs:dcAggregate/NFIPInsuranceClaims',
                      tmcf_content)


if __name__ == '__main__':
    unittest.main()
