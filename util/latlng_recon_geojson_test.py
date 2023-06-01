# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for util.latlng_recon_geojson"""

import json
import os
import sys
import unittest
from shapely import geometry
from unittest import mock

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
import latlng_recon_geojson

_SC_COUNTY_GJ_STR = """
{"type": "Polygon", "coordinates": [[[-122.202653, 37.363046], [-122.026107, 37.16681], [-121.575402, 36.893033], [-121.488949, 36.983148], [-121.215406, 36.961248], [-121.23711, 37.157204], [-121.399019, 37.150135], [-121.45575, 37.24944], [-121.409075, 37.380672], [-121.472952, 37.482333], [-122.115161, 37.46628], [-122.202653, 37.363046]]]}
"""

_ZIP_94041_GJ_STR = """
{"type": "Polygon", "coordinates": [[[-122.09562, 37.39428],  [-122.096323, 37.393119],  [-122.093774, 37.392494],  [-122.09255, 37.389938],  [-122.09128, 37.38951],  [-122.080708, 37.384256],  [-122.07758, 37.38254],  [-122.07666, 37.38388],  [-122.07523, 37.38315],  [-122.07612, 37.38201],  [-122.072794, 37.380387],  [-122.07188, 37.38151],  [-122.07051, 37.38089],  [-122.068999, 37.382159],  [-122.068418, 37.384224],  [-122.067774, 37.378295],  [-122.06243, 37.37632],  [-122.06099, 37.37742],  [-122.060203, 37.37959],  [-122.059226, 37.380059],  [-122.062096, 37.38068],  [-122.061869, 37.381343],  [-122.05932, 37.3808],  [-122.058148, 37.381386],  [-122.057883, 37.383031],  [-122.057211, 37.384908],  [-122.05533, 37.38648],  [-122.057857, 37.387535],  [-122.06291, 37.38909],  [-122.091312, 37.400534],  [-122.092117, 37.396977],  [-122.093738, 37.397298],  [-122.09457, 37.39595],  [-122.092358, 37.395033],  [-122.093435, 37.393435],  [-122.09562, 37.39428]]]}
"""


def _mock_get_gj(place_type, parent_place):
    # In this test, we pretend USA has the geoshape of SC County!
    if place_type == 'Country':
        return {'country/USA': geometry.shape(json.loads(_SC_COUNTY_GJ_STR))}
    elif place_type == 'State':
        return {'geoId/06': geometry.shape(json.loads(_ZIP_94041_GJ_STR))}
    else:
        return {'geoId/06085': geometry.shape(json.loads(_ZIP_94041_GJ_STR))}


class LatlngReconGeojsonTest(unittest.TestCase):

    @mock.patch('latlng_recon_geojson._get_geojsons')
    @mock.patch('latlng_recon_geojson._get_continent_map')
    def test_main(self, mock_cmap, mock_gj):
        mock_cmap.return_value = {'country/USA': ['northamerica']}
        mock_gj.side_effect = _mock_get_gj

        ll2p = latlng_recon_geojson.LatLng2Places()
        # Cascal in MTV exists in "county", "state" (94041) and "country" (SC county)
        self.assertEqual(
            ll2p.resolve(37.391, -122.081),
            ['geoId/06', 'geoId/06085', 'country/USA', 'northamerica'])
        # Zareen's doesn't exist in the "state".
        self.assertEqual(ll2p.resolve(37.419, -122.079),
                         ['country/USA', 'northamerica'])
        # Bi-rite creamery in SF exists in neither.
        self.assertEqual(ll2p.resolve(37.762, -122.426), [])


if __name__ == '__main__':
    unittest.main()
