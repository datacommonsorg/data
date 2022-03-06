# Copyright 2022 Google LLC
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
"""Tests for geo_id_resolver.py"""

import unittest
from . import geo_id_resolver


class GeoIdResolverTest(unittest.TestCase):

    def test_georesolver_state(self):
        state = 'CA'  # California geoId/06
        geo_id = geo_id_resolver.convert_to_place_dcid(state, geo_type='State')
        self.assertEqual(geo_id, 'geoId/06')

        state = 'GM'  # Testing _US_GEO_CODE_UPDATE_MAP
        geo_id = geo_id_resolver.convert_to_place_dcid(state, geo_type='State')
        self.assertEqual(geo_id, 'geoId/66')

        state = 'ZZ'  # ZZ is not resolved
        geo_id = geo_id_resolver.convert_to_place_dcid(state, geo_type='State')
        self.assertEqual(geo_id, '')

    def test_georesolver_city(self):
        # zwolle la,2283685	scripts/fbi/crime/city_geocodes.csv.
        geo_id = geo_id_resolver.convert_to_place_dcid('LA',
                                                       geo='Zwolle',
                                                       geo_type='City')
        self.assertEqual(geo_id, 'geoId/2283685')

        # big bear ca: 0606406 from the initialised _CITY map
        geo_id = geo_id_resolver.convert_to_place_dcid('CA',
                                                       geo='Big Bear',
                                                       geo_type='City')
        self.assertEqual(geo_id, 'geoId/0606406')

        # fox valley wi is not resolved
        geo_id = geo_id_resolver.convert_to_place_dcid('WI',
                                                       geo='Fox Valley',
                                                       geo_type='City')
        self.assertEqual(geo_id, '')

    def test_georesolver_county(self):
        # AL (Alabama), Autauga County has dcid geoId/01001
        geo_id = geo_id_resolver.convert_to_place_dcid('AL',
                                                       geo='Autauga County',
                                                       geo_type='County')
        self.assertEqual(geo_id, 'geoId/01001')

        # AL (Alabama), Winston County has geoId/01133
        # Suffix 'County' will be added by _get_county_variants function
        geo_id = geo_id_resolver.convert_to_place_dcid('AL',
                                                       geo='Winston',
                                                       geo_type='County')
        self.assertEqual(geo_id, 'geoId/01133')

        # AK (Alaska), Anchorage Borough has dcid geoId/02020
        geo_id = geo_id_resolver.convert_to_place_dcid('AK',
                                                       geo='Anchorage Borough',
                                                       geo_type='County')
        self.assertEqual(geo_id, 'geoId/02020')

        # LA (Louisiana), Allen Parish has dcid geoId/22003
        # Suffix 'Parish' will be added by _get_county_variants function
        geo_id = geo_id_resolver.convert_to_place_dcid('LA',
                                                       geo='Allen',
                                                       geo_type='County')
        self.assertEqual(geo_id, 'geoId/22003')

        # GM (Guam), Guam County has dcid geoId/66010
        # The alpha code GM is changed to GU from _US_ALPHA_CODE_UPDATE_MAP
        geo_id = geo_id_resolver.convert_to_place_dcid('GM',
                                                       geo='Guam County',
                                                       geo_type='County')
        self.assertEqual(geo_id, 'geoId/66010')

        # AL (Alabama), Z County is not resolved
        geo_id = geo_id_resolver.convert_to_place_dcid('AL',
                                                       geo='Z',
                                                       geo_type='County')
        self.assertEqual(geo_id, '')

        # ZZ, Z County is not resolved
        geo_id = geo_id_resolver.convert_to_place_dcid('ZZ',
                                                       geo='Z',
                                                       geo_type='County')
        self.assertEqual(geo_id, '')


if __name__ == '__main__':
    unittest.main()
