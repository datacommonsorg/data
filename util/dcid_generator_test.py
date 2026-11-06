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
"""Unit tests for `util/dcid_generator.py`."""

import os
import sys
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))

import dcid_generator


class DcidGeneratorTest(unittest.TestCase):

    def test_farmhash_and_get_long_id_golden_vectors(self):
        # Golden key strings and expected DCIDs from DcidGeneratorTest.java in
        # datacommonsorg/import.
        golden = [
            (
                'observationAbout=geoId/06001variableMeasured=Count_Person'
                'observationDate=2017-01value=1000observationPeriod=P1M'
                'unit=$measurementMethod=CACensusscalingFactor=100',
                'dc/o/',
                'dc/o/3mptcb1vdfvr5',
            ),
            (
                'observationAbout=geoId/41051002901'
                'variableMeasured=Count_Person_18OrMoreYears_Civilian_Male'
                'observationDate=2014value=1654'
                'measurementMethod=CensusACS5yrSurvey',
                'dc/o/',
                'dc/o/pvb91vhnpw9r3',
            ),
            (
                'observationAbout=geoId/3152960'
                'variableMeasured=dc/25mvfy1h7yws9'
                'observationDate=2012value=10'
                'measurementMethod=CensusACS5yrSurvey',
                'dc/o/',
                'dc/o/pvb91vhnpw9r3',
            ),
            (
                'gender=MalemeasuredProperty=countpopType=Person'
                'race=AsianstatType=measuredValuetypeOf=StatisticalVariable',
                'dc/',
                'dc/g9y3wr60lwcg',
            ),
            (
                'age=Years16OnwardsmeasuredProperty=countpopType=Person'
                'typeOf=StatisticalVariable',
                'dc/',
                'dc/2v3xz3y0dbd8b',
            ),
            (
                'NewType22',
                'dc/',
                'dc/bsxxcsbwvey61',
            ),
        ]
        for key_str, prefix, expected_dcid in golden:
            self.assertEqual(
                expected_dcid,
                f'{prefix}{dcid_generator.get_long_id(key_str)}',
                key_str,
            )

    def test_generate_statvar_obs_dcid_success(self):
        # Matches DcidGeneratorTest.funcSVObsSuccess
        node = {
            'Node': 'SVObs',
            'typeOf': 'dcs:StatVarObservation',
            'variableMeasured': 'dcid:Count_Person',
            'observationAbout': 'dcid:geoId/06001',
            'value': 1000,
            'observationDate': '"2017-01"',
            'observationPeriod': '"P1M"',
            'measurementMethod': 'dcid:CACensus',
            'scalingFactor': '"100"',
            'unit': '"$"',
        }
        self.assertEqual(
            'dc/o/3mptcb1vdfvr5',
            dcid_generator.generate_statvar_obs_dcid(node),
        )
        self.assertEqual(
            'dc/o/3mptcb1vdfvr5',
            dcid_generator.generate_node_dcid(node),
        )

    def test_generate_statvar_obs_dcid_hash_collision_parity(self):
        # Matches DcidGeneratorTest.funcSVObsHashCollision
        node1 = {
            'Node': 'SVObs',
            'typeOf': 'dcs:StatVarObservation',
            'variableMeasured':
            'dcid:Count_Person_18OrMoreYears_Civilian_Male',
            'observationAbout': 'dcid:geoId/41051002901',
            'value': 1654,
            'observationDate': '"2014"',
            'measurementMethod': 'dcid:CensusACS5yrSurvey',
        }
        node2 = {
            'Node': 'SVObs',
            'typeOf': 'dcs:StatVarObservation',
            'variableMeasured': 'dcid:dc/25mvfy1h7yws9',
            'observationAbout': 'dcid:geoId/3152960',
            'value': 10,
            'observationDate': '"2012"',
            'measurementMethod': 'dcid:CensusACS5yrSurvey',
        }
        self.assertEqual(
            'dc/o/pvb91vhnpw9r3',
            dcid_generator.generate_statvar_obs_dcid(node1),
        )
        self.assertEqual(
            'dc/o/pvb91vhnpw9r3',
            dcid_generator.generate_statvar_obs_dcid(node2),
        )

    def test_generate_statvar_obs_dcid_failures(self):
        # Matches DcidGeneratorTest.funcSVObsFailure
        # Missing observationAbout
        self.assertEqual(
            '',
            dcid_generator.generate_statvar_obs_dcid({
                'typeOf':
                'dcs:StatVarObservation',
                'variableMeasured':
                'dcid:Count_Person',
                'value':
                1000,
                'observationDate':
                '"2017-01"',
            }),
        )
        # Missing variableMeasured
        self.assertEqual(
            '',
            dcid_generator.generate_statvar_obs_dcid({
                'typeOf':
                'dcs:StatVarObservation',
                'observationAbout':
                'dcid:geoId/06001',
                'value':
                1000,
                'observationDate':
                '"2017-01"',
            }),
        )
        # Missing observationDate
        self.assertEqual(
            '',
            dcid_generator.generate_statvar_obs_dcid({
                'typeOf': 'dcs:StatVarObservation',
                'variableMeasured': 'dcid:Count_Person',
                'observationAbout': 'dcid:geoId/06001',
                'value': 1000,
            }),
        )
        # Missing value
        self.assertEqual(
            '',
            dcid_generator.generate_statvar_obs_dcid({
                'typeOf':
                'dcs:StatVarObservation',
                'variableMeasured':
                'dcid:Count_Person',
                'observationAbout':
                'dcid:geoId/06001',
                'observationDate':
                '"2017-01"',
            }),
        )
        # Unresolved local reference in variableMeasured
        self.assertEqual(
            '',
            dcid_generator.generate_statvar_obs_dcid({
                'typeOf': 'dcs:StatVarObservation',
                'variableMeasured': 'l:LocalStatVarId',
                'observationAbout': 'dcid:geoId/06001',
                'observationDate': '"2017-01"',
                'value': 1000,
            }),
        )
        # Unresolved local reference in observationAbout
        self.assertEqual(
            '',
            dcid_generator.generate_statvar_obs_dcid({
                'typeOf': 'dcs:StatVarObservation',
                'variableMeasured': 'dcid:Count_Person',
                'observationAbout': 'l:LocalPlaceId',
                'observationDate': '"2017-01"',
                'value': 1000,
            }),
        )

    def test_generate_statvar_obs_dcid_with_ignored_value(self):
        obs1 = {
            'typeOf': 'dcs:StatVarObservation',
            'observationAbout': 'dcid:geoId/06001',
            'variableMeasured': 'dcid:Count_Person',
            'observationDate': '2020',
            'value': '100',
        }
        obs2 = {**obs1, 'value': '200'}
        self.assertNotEqual(
            dcid_generator.generate_statvar_obs_dcid(obs1),
            dcid_generator.generate_statvar_obs_dcid(obs2),
        )
        # Ignoring 'value' produces the same DCID for duplicate observations
        # with different values.
        self.assertEqual(
            dcid_generator.generate_statvar_obs_dcid(obs1, {'value'}),
            dcid_generator.generate_statvar_obs_dcid(obs2, {'value'}),
        )

    def test_generate_place_dcid(self):
        # Matches DcidGeneratorTest.funcPlace and funcPlaceMakesDcidFromOtherIds
        self.assertEqual(
            'nuts/nutsCode_node_0',
            dcid_generator.generate_place_dcid({
                'Node':
                'node_0',
                'typeOf':
                'dcs:City',
                'nutsCode':
                '"nutsCode_node_0"',
                'wikidataId':
                '"wikidataId_node_0"',
            }),
        )
        self.assertEqual(
            '',
            dcid_generator.generate_place_dcid({
                'Node': 'node_1',
                'typeOf': 'dcs:City',
                'name': '"name_node_1"',
            }),
        )
        self.assertEqual(
            'wikidataId/someWikidataId',
            dcid_generator.generate_place_dcid({
                'Node': 'node_0',
                'typeOf': 'dcs:City',
                'wikidataId': 'someWikidataId',
                'mid': 'someMid',
            }),
        )
        self.assertEqual(
            'geoNamesId/someGeoNamesId',
            dcid_generator.generate_place_dcid({
                'Node': 'node_1',
                'typeOf': 'dcs:City',
                'geoNamesId': 'someGeoNamesId',
                'mid': 'someMid',
            }),
        )
        self.assertEqual(
            'istatId/someIstatId',
            dcid_generator.generate_place_dcid({
                'Node': 'node_2',
                'typeOf': 'dcs:City',
                'istatId': 'someIstatId',
            }),
        )
        self.assertEqual(
            'geoId/06001',
            dcid_generator.generate_node_dcid({
                'typeOf': 'dcs:County',
                'geoId': '06001',
                'name': 'Alameda County',
            }),
        )
        self.assertEqual(
            'iso/US-CA',
            dcid_generator.generate_node_dcid({
                'typeOf': 'dcs:State',
                'isoCode': 'US-CA',
            }),
        )

    def test_generate_statvar_hash_dcid(self):
        # Matches DcidGeneratorTest.funcStatVar and funcStatVarWithComplexValue
        sv = {
            'Node': 'SomeNode',
            'typeOf': 'dcs:StatisticalVariable',
            'measuredProperty': 'dcs:count',
            'popType': 'dcid:Person',
            'race': 'dcid:Asian',
            'gender': 'dcid:Male',
            'statType': 'dcs:measuredValue',
            'dcid': '"manuallyCuratedDcid"',
            'isPublic': '"true"',
            'provenance': '"Jupiter"',
            'keyString': '"k1=v1k2=v2"',
            'resMCFFile': '"/path/to/the/black/hole"',
            'label': '"SomeNode"',
            'name': '"SomeNode"',
            'description': '"Description of SomeNode"',
            'descriptionUrl': '"http://wikipedia.org"',
            'alternateName': '"SomeNode"',
            'censusACSTableId': '"B01003"',
            'memberOf': 'dcid:dc/g/FooSVG',
        }
        self.assertEqual('dc/g9y3wr60lwcg',
                         dcid_generator.generate_node_dcid(sv))

        sv_unresolved = {
            'Node': 'unresolved',
            'typeOf': 'dcs:StatisticalVariable',
            'measuredProperty': 'dcs:count',
            'popType': 'dcid:Person',
            'age': '[Years 16 -]',
        }
        sv_resolved = {
            'Node': 'resolved',
            'typeOf': 'dcs:StatisticalVariable',
            'measuredProperty': 'dcs:count',
            'popType': 'dcid:Person',
            'age': 'dcid:Years16Onwards',
        }
        self.assertEqual('dc/2v3xz3y0dbd8b',
                         dcid_generator.generate_node_dcid(sv_unresolved))
        self.assertEqual('dc/2v3xz3y0dbd8b',
                         dcid_generator.generate_node_dcid(sv_resolved))

    def test_generate_node_dcid_general_normalization_and_zero_values(self):
        # General nodes normalize ranges, lists, numbers, namespaces, and '__'.
        node1 = {
            'typeOf': 'Place',
            'age': '[10 20 Years]',
            'mm': 'dcs:B, A,B',
            'v': '1.50',
            'e': 'a__c__b',
        }
        node2 = {
            'typeOf': 'schema:Place',
            'age': 'Years10To20',
            'mm': 'A,dcid:B',
            'v': 1.5,
            'e': 'dcid:a__b__c',
        }
        self.assertEqual('dc/2ecet3e4wx0w2',
                         dcid_generator.generate_node_dcid(node1))
        self.assertEqual(dcid_generator.generate_node_dcid(node1),
                         dcid_generator.generate_node_dcid(node2))

        # Preserves numeric zero values (0, 0.0, '0', '0.0').
        base = {
            'observationAbout': 'geoId/06',
            'variableMeasured': 'Count_Crime',
            'observationDate': '2020',
        }
        missing_dcid = dcid_generator.generate_node_dcid(dict(base))
        int_zero = dcid_generator.generate_node_dcid({**base, 'value': 0})
        float_zero = dcid_generator.generate_node_dcid({**base, 'value': 0.0})
        str_zero = dcid_generator.generate_node_dcid({**base, 'value': '0'})
        str_zero_dec = dcid_generator.generate_node_dcid({
            **base, 'value': '0.0'
        })
        self.assertNotEqual(missing_dcid, int_zero)
        self.assertEqual(int_zero, float_zero)
        self.assertEqual(int_zero, str_zero)
        self.assertEqual(int_zero, str_zero_dec)

    def test_local_refs_quoted_strings_and_list_values(self):
        # Unresolved local references ('l:') in namespaces or lists return ''.
        self.assertEqual(
            '',
            dcid_generator.generate_node_dcid({
                'typeOf': 'dcs:City',
                'geoId': 'dcid:l:LocalGeoId',
            }),
        )
        self.assertEqual(
            '',
            dcid_generator.generate_node_dcid({
                'typeOf':
                'dcs:StatisticalVariable',
                'measuredProperty':
                'dcs:count',
                'populationType':
                'dcs:Person',
                'gender': ['dcid:Male', 'l:LocalGender'],
            }),
        )
        # Quoted strings containing commas or colons in StatVarObservation do
        # not fail or collide by stripping non-MCF prefixes.
        obs_usd = {
            'typeOf': 'dcs:StatVarObservation',
            'observationAbout': 'dcid:geoId/06',
            'variableMeasured': 'dcid:Count_Person',
            'observationDate': '2020',
            'value': '100',
            'unit': '"USD:nominal, adjusted"',
            'measurementMethod': [],
        }
        obs_eur = {**obs_usd, 'unit': '"EUR:nominal, adjusted"'}
        dcid_usd = dcid_generator.generate_statvar_obs_dcid(obs_usd)
        dcid_eur = dcid_generator.generate_statvar_obs_dcid(obs_eur)
        self.assertTrue(dcid_usd.startswith('dc/o/'))
        self.assertTrue(dcid_eur.startswith('dc/o/'))
        self.assertNotEqual(dcid_usd, dcid_eur)

        # Python list values in StatisticalVariable match comma-separated values.
        sv_list = {
            'typeOf': 'dcs:StatisticalVariable',
            'measuredProperty': 'dcs:count',
            'populationType': 'dcs:Person',
            'gender': ['dcid:Male'],
        }
        sv_str = {
            'typeOf': 'dcs:StatisticalVariable',
            'measuredProperty': 'dcs:count',
            'populationType': 'dcs:Person',
            'gender': 'dcid:Male',
        }
        self.assertEqual(
            dcid_generator.generate_statvar_hash_dcid(sv_str),
            dcid_generator.generate_statvar_hash_dcid(sv_list),
        )


if __name__ == '__main__':
    unittest.main()
