# Copyright 2021 Google LLC
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

import filecmp
import os
import tempfile
import unittest
import geocode_cities


class GeocodeCitiesTest(unittest.TestCase):
    def setUp(self):
        self.geo_codes = geocode_cities.read_geocodes()

    def test_geocode_city(self):
        state = 'ca'
        city = geocode_cities.normalize_fbi_city('Mountain View', state)
        city_state = '{} {}'.format(city, state)
        self.assertEqual(city_state, 'mountain view ca')
        self.assertEqual(self.geo_codes[city_state], '0649670')

    def test_manual_geocode_city(self):
        # west bloomfield township mi	2612585480 is from manual_geocodes.csv.
        state = 'mi'
        city = geocode_cities.normalize_fbi_city('West Bloomfield Township',
                                                 state)
        city_state = '{} {}'.format(city, state)
        self.assertEqual(city_state, 'west bloomfield township mi')
        self.assertEqual(self.geo_codes[city_state], '2612585480')

    def test_update_crime_geocode(self):
        geo_codes = {'mineral point wi': 5553100}
        crime = {
            'Year': 2019,
            'State': 'WISCONSIN',
            'City': 'Mineral Point',
            'Population': 2477.0
        }
        found_set = set()
        cities_not_found_set = set()
        result = geocode_cities.update_crime_geocode(crime, geo_codes,
                                                     found_set,
                                                     cities_not_found_set)
        self.assertTrue(result)
        self.assertEqual(found_set, {'mineral point wi'})
        self.assertEqual(5553100, crime['Geocode'])

        # Deuplicate state and city, assert exception.
        with self.assertRaises(Exception):
            geocode_cities.update_crime_geocode(crime, geo_codes, found_set,
                                                cities_not_found_set)

        not_found_crime = {
            'Year': 2019,
            'State': 'Wyoming',
            'City': 'Random City',
            'Population': 1.0
        }
        result = geocode_cities.update_crime_geocode(not_found_crime,
                                                     geo_codes, found_set,
                                                     cities_not_found_set)
        self.assertFalse(result)
        self.assertEqual(found_set, {'mineral point wi'})
        self.assertEqual(5553100, crime['Geocode'])


if __name__ == '__main__':
    unittest.main()
