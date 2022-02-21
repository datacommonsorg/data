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

import unittest
from .geo_id_resolver import *


class GeoIdResolverTest(unittest.TestCase):

    def test_georesolver_state(self):
        state = 'CA'
        geoId = convert_to_place_dcid(state, geo_type='State')
        self.assertEqual(geoId, 'geoId/06')

        state = 'GM'  # Testing _US_GEO_CODE_UPDATE_MAP
        geoId = convert_to_place_dcid(state, geo_type='State')
        self.assertEqual(geoId, 'geoId/66')

    def test_georesolver_city(self):
        # zwolle la,2283685	scripts/fbi/crime/city_geocodes.csv.
        geoId = convert_to_place_dcid('LA', geo='Zwolle', geo_type='City')
        self.assertEqual(geoId, 'geoId/2283685')

    def test_georesolver_county(self):
        # AL (Alabama), Autauga County has dcid geoId/01001
        geoId = convert_to_place_dcid('AL',
                                      geo='Autauga County',
                                      geo_type='County')
        self.assertEqual(geoId, 'geoId/01001')


if __name__ == '__main__':
    unittest.main()
