# Copyright 2023 Google LLC
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
'''Tests for geography.py.

Usage: python3 -m unittest discover -v -s ../ -p "geography_test.py"
'''
import os
import sys
import tempfile
import unittest

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from un.sdg import geography

module_dir_ = os.path.dirname(__file__)

FOLDER = os.path.join(module_dir_, 'testdata/test_geography')

# Mock input data.
SDG2TYPE = {'4': 'Country'}
UN2SDG = {
    'undata-geo:G00000020': '4',
}
SDG2UN = {'4': 'undata-geo:G00000020'}
UN2DC_CURATED = {
    'undata-geo:G00000020':
        geography.Node('country/AFG', 'Country', 'Afghanistan'),
    'undata-geo:G00003250':
        geography.Node('country/ARE', 'Country', 'United Arab Emirates'),
    'undata-geo:G00100000':
        geography.Node('Earth', 'Place', 'World'),
    'undata-geo:G00114000':
        geography.Node('asia', 'Continent', 'Asia'),
    'undata-geo:G00119000':
        geography.Node('SouthernAsia', 'UNGeoRegion', 'Southern Asia'),
    'undata-geo:G00120000':
        geography.Node('WesternAsia', 'UNGeoRegion', 'Western Asia'),
    'undata-geo:G00403000':
        geography.Node('undata-geo/G00403000', 'GeoRegion',
                       'Landlocked developing countries (LLDCs)'),
    'undata-geo:G00404000':
        geography.Node('undata-geo/G00404000', 'GeoRegion',
                       'Least developed countries (LDCs)'),
}
UN2DC_GENERATED = {
    'undata-geo:G00000030':
        geography.Node('undata-geo/G00000030', 'GeoRegion', 'Ajman')
}

# Add additional referenced objects that aren't defined in test_geographies.csv.
UN2DC_GENERATED_FULL = {
    **UN2DC_GENERATED,
    **{
        'undata-geo:G00403300':
            geography.Node('undata-geo/G00403300', 'GeoRegion', 'Landlocked developing countries (LLDCs): Asia'),
        'undata-geo:G00404300':
            geography.Node('undata-geo/G00404300', 'GeoRegion', 'Least developed countries (LDCs): Asia'),
    }
}

# Test intermediate output data.
NEW_SUBJECTS = [geography.Node('undata-geo/G00000030', 'GeoRegion', 'Ajman')]
CONTAINMENT = {
    geography.Node('country/AFG', 'Country', 'Afghanistan'): [
        'SouthernAsia', 'undata-geo/G00403000', 'undata-geo/G00403300',
        'undata-geo/G00404000', 'undata-geo/G00404300'
    ],
    geography.Node('undata-geo/G00000030', 'GeoRegion', 'Ajman'): [
        'Earth', 'asia', 'WesternAsia'
    ],
}


class GeographyTest(unittest.TestCase):

    def test_should_include_containment(self):
        self.assertTrue(
            geography.should_include_containment(
                geography.Node('AustrailiaAndNewZealand', 'UNGeoRegion',
                               'Australia and New Zealand'),
                geography.Node('oceania', 'Continent', 'Oceania')))
        self.assertFalse(
            geography.should_include_containment(
                geography.Node('geoId/3502000', 'City', 'Albuquerque'),
                geography.Node('country/USA', 'Country',
                               'United States of America')))

    def test_write_un_places(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = os.path.join(tmp_dir, 'un_places.mcf')
            un2dc_generated, new_subjects = geography.write_un_places(
                os.path.join(FOLDER, 'test_geography.csv'), output, SDG2TYPE,
                UN2SDG, UN2DC_CURATED)
            with open(output) as result:
                with open(os.path.join(FOLDER,
                                       'expected_un_places.mcf')) as expected:
                    self.assertEqual(result.read(), expected.read())
            self.assertEqual(un2dc_generated, UN2DC_GENERATED)
            self.assertEqual(new_subjects, NEW_SUBJECTS)

    def test_process_containment(self):
        containment = geography.process_containment(
            os.path.join(FOLDER, 'test_geography_hierarchy.csv'), UN2DC_CURATED,
            UN2DC_GENERATED_FULL)
        self.assertEqual(containment, CONTAINMENT)

    def test_write_un_containment(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = os.path.join(tmp_dir, 'un_containment.mcf')
            geography.write_un_containment(output, CONTAINMENT, NEW_SUBJECTS)
            with open(output) as result:
                with open(os.path.join(
                        FOLDER, 'expected_un_containment.mcf')) as expected:
                    self.assertEqual(result.read(), expected.read())

    def test_write_place_mappings(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = os.path.join(tmp_dir, 'place_mappings.csv')
            geography.write_place_mappings(os.path.join(FOLDER, output), SDG2UN,
                                           UN2DC_CURATED, UN2DC_GENERATED_FULL)
            with open(output) as result:
                with open(os.path.join(
                        FOLDER, 'expected_place_mappings.csv')) as expected:
                    self.assertEqual(result.read(), expected.read())
