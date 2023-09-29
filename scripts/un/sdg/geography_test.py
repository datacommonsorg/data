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

# Read input geography mappings.
SDG2TYPE = geography.get_sdg2type('sdg-dataset/output/SDG_geographies.csv')
UN2SDG, SDG2UN = geography.get_sdg_un_maps(
    'sssom-mappings/output_mappings/undata-geo__sdg-geo.csv')
UN2DC = geography.get_un2dc('geography/places.csv')

FOLDER = os.path.join(module_dir_, 'testdata/test_geography')

UN2DC2 = {
    'undata-geo:G00000010': ('undata-geo/G00000010', 'GeoRegion', 'Abu Dhabi'),
    'undata-geo:G00000030': ('undata-geo/G00000030', 'GeoRegion', 'Ajman')
}

# Add additional referenced objects that aren't defined in test_geographies.csv.
UN2DC2_FULL = UN2DC2 | {
    'undata-geo:G00403300': ('undata-geo/G00403300', 'GeoRegion',
                             'Landlocked developing countries (LLDCs): Asia'),
    'undata-geo:G00404100': ('undata-geo/G00404100', 'GeoRegion',
                             'Least developed countries (LDCs): Africa'),
    'undata-geo:G00404300': ('undata-geo/G00404300', 'GeoRegion',
                             'Least developed countries (LDCs): Asia'),
    'undata-geo:G00405200': ('undata-geo/G00405200', 'GeoRegion',
                             'Small Island Developing States (SIDS): Americas'),
    'undata-geo:G00405400': ('undata-geo/G00405400', 'GeoRegion',
                             'Small Island Developing States (SIDS): Oceania')
}

NEW_SUBJECTS = {('undata-geo/G00000030', 'GeoRegion'),
                ('undata-geo/G00000010', 'GeoRegion')}
CONTAINMENT = {
    ('undata-geo/G00000010', 'GeoRegion'): ['Earth', 'asia', 'WesternAsia'],
    ('country/AFG', 'Country'): [
        'SouthernAsia', 'undata-geo/G00403000', 'undata-geo/G00403300',
        'undata-geo/G00404000', 'undata-geo/G00404300'
    ],
    ('undata-geo/G00000030', 'GeoRegion'): ['Earth', 'asia', 'WesternAsia'],
    ('country/ALA', 'Country'): ['NorthernEurope'],
    ('country/ALB', 'Country'): ['SouthernEurope'],
    ('country/DZA', 'Country'): ['NorthernAfrica'],
    ('country/AND', 'Country'): ['SouthernEurope'],
    ('country/AGO', 'Country'): [
        'SubSaharanAfrica', 'MiddleAfrica', 'undata-geo/G00404000',
        'undata-geo/G00404100'
    ]
}


class GeographyTest(unittest.TestCase):

    def test_should_include_containment(self):
        self.assertTrue(
            geography.should_include_containment('UNGeoRegion',
                                                 'AustrailiaAndNewZealand',
                                                 'Continent', 'oceania'))
        self.assertFalse(
            geography.should_include_containment('City', 'geoId/3502000',
                                                 'Country', 'country/USA'))

    def test_write_un_places(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = os.path.join(tmp_dir, 'un_places.mcf')
            un2dc2, new_subjects = geography.write_un_places(
                os.path.join(FOLDER, 'test_geographies.csv'), output, SDG2TYPE,
                UN2SDG, UN2DC)
            with open(output) as result:
                with open(os.path.join(FOLDER,
                                       'expected_un_places.mcf')) as expected:
                    self.assertEqual(result.read(), expected.read())
            self.assertEqual(un2dc2, UN2DC2)
            self.assertEqual(new_subjects, NEW_SUBJECTS)

    def test_process_containment(self):
        containment = geography.process_containment(
            os.path.join(FOLDER, 'test_geography_hierarchy.csv'), UN2DC,
            UN2DC2_FULL)
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
                                           UN2DC, UN2DC2_FULL)
            with open(output) as result:
                with open(os.path.join(
                        FOLDER, 'expected_place_mappings.csv')) as expected:
                    self.assertEqual(result.read(), expected.read())
