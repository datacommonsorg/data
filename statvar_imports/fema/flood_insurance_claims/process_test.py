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

    def test_load_mappings_and_resolve(self):
        state_map, risk_zone_map = process._load_mappings()
        self.assertEqual(state_map.get('CA'), 'dcid:geoId/06')
        self.assertEqual(risk_zone_map.get('A'), 'FEMAHighRiskFloodZone')
        self.assertEqual(risk_zone_map.get('X'), 'FEMALowRiskFloodZone')

        dummy = os.path.join(self.test_dir, 'custom.py')
        with open(dummy, 'w', encoding='utf-8') as f:
            f.write("{}")
        pv_arg = f"observationAbout:{dummy}"
        self.assertEqual(process._resolve_map_path(pv_arg, 'observationAbout'),
                         dummy)
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
        self.assertEqual(list(df.columns), [
            'observationDate', 'observationAbout', 'value',
            'observationPeriod', 'unit', 'variableMeasured'
        ])

        with open(self.counters_path, 'r', encoding='utf-8') as f:
            counters_content = f.read()
        self.assertIn('num_input_rows=99', counters_content)
        self.assertIn(f'num_cleaned_observations={len(df)}', counters_content)

        with open(tmcf_file, 'r', encoding='utf-8') as f:
            self.assertIn('Node: E:nfip_output->E0', f.read())

    def test_unpadded_fips_and_null_values(self):
        fixture_csv = os.path.join(self.test_dir, 'nulls_fixture.csv')
        with open(fixture_csv, 'w', encoding='utf-8') as f:
            f.write(
                'censusTract,countyCode,state,dateOfLoss,yearOfLoss,ratedFloodZone,amountPaidOnBuildingClaim,amountPaidOnContentsClaim,policyCount\n'
                ',,CA,2020-05-10,2020,A,100.0,50.0,1\n'
                '6079012705,6079,CA,2020-05-10,2020,A,200.0,100.0,1\n'
                ',6079,CA,2020-05-10,2020,X,300.0,150.0,1\n')

        process.process_data_vectorized(input_data=fixture_csv,
                                        output_path=self.output_prefix,
                                        pv_map_arg=None,
                                        chunk_size=10,
                                        num_workers=1,
                                        output_counters=self.counters_path)
        df = pd.read_csv(f"{self.output_prefix}.csv")
        places = set(df['observationAbout'].unique())

        self.assertIn('dcid:country/USA', places)
        self.assertIn('dcid:geoId/06', places)
        self.assertIn('dcid:geoId/06079', places)
        self.assertIn('dcid:geoId/06079012705', places)

    def test_empty_input_raises_runtime_error(self):
        empty_csv = os.path.join(self.test_dir, 'empty.csv')
        with open(empty_csv, 'w', encoding='utf-8') as f:
            f.write(
                'censusTract,countyCode,state,dateOfLoss,yearOfLoss,ratedFloodZone,amountPaidOnBuildingClaim,amountPaidOnContentsClaim,policyCount\n'
            )
        with self.assertRaises(RuntimeError):
            process.process_data_vectorized(input_data=empty_csv,
                                            output_path=self.output_prefix,
                                            pv_map_arg=None,
                                            chunk_size=50,
                                            num_workers=1,
                                            output_counters=self.counters_path)

    def test_aggregation_numerical_values(self):
        fixture_csv = os.path.join(self.test_dir, 'fixture.csv')
        with open(fixture_csv, 'w', encoding='utf-8') as f:
            f.write(
                'censusTract,countyCode,state,dateOfLoss,yearOfLoss,ratedFloodZone,amountPaidOnBuildingClaim,amountPaidOnContentsClaim,policyCount\n'
                '06079012705,06079,CA,2020-05-10,2020,A,1000.0,500.0,1\n'
                '06079012705,06079,CA,2020-05-20,2020,UNKNOWN_ZONE,200.0,100.0,1\n'
            )

        process.process_data_vectorized(input_data=fixture_csv,
                                        output_path=self.output_prefix,
                                        pv_map_arg=None,
                                        chunk_size=10,
                                        num_workers=1,
                                        output_counters=self.counters_path)
        df = pd.read_csv(f"{self.output_prefix}.csv")

        def _get_val(place, date, period, sv):
            match = df[(df['observationAbout'] == place)
                       & (df['observationDate'] == date) &
                       (df['observationPeriod'] == period) &
                       (df['variableMeasured'] == sv)]
            return match['value'].iloc[0] if len(match) > 0 else None

        # State-level monthly totals
        self.assertEqual(
            _get_val(
                'dcid:geoId/06', '2020-05', 'P1M',
                'dcid:CountOfClaims_NaturalHazardInsurance_BuildingStructureAndContents_FloodEvent'
            ), 2.0)
        self.assertEqual(
            _get_val(
                'dcid:geoId/06', '2020-05', 'P1M',
                'dcid:SettlementAmount_NaturalHazardInsurance_BuildingStructure_FloodEvent'
            ), 1200.0)
        self.assertEqual(
            _get_val(
                'dcid:geoId/06', '2020-05', 'P1M',
                'dcid:SettlementAmount_NaturalHazardInsurance_BuildingContents_FloodEvent'
            ), 600.0)
        self.assertEqual(
            _get_val(
                'dcid:geoId/06', '2020-05', 'P1M',
                'dcid:SettlementAmount_NaturalHazardInsurance_BuildingStructureAndContents_FloodEvent'
            ), 1800.0)

        # Unknown flood zone preserves zone suffix
        self.assertEqual(
            _get_val(
                'dcid:geoId/06', '2020-05', 'P1M',
                'dcid:CountOfClaims_NaturalHazardInsurance_FEMAFloodZoneUNKNOWN_ZONE_BuildingStructureAndContents_FloodEvent'
            ), 1.0)


if __name__ == '__main__':
    unittest.main()
