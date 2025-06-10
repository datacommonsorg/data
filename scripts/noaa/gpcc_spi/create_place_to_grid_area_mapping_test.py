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
'''
Unit tests for create_place_to_grid_area_mapping.py
Usage: python -m unittest discover -v -s ../ -p "create_place_to_grid_area_mapping_test.py"
'''
import unittest
from .create_place_to_grid_area_mapping import create_place_to_grid_mapping


class PlaceToGridMappingTest(unittest.TestCase):

    def test_create_place_to_grid_mapping(self):
        want = {
            # San Bernardino County
            # maps to many grids.
            'geoId/06071': [{
                'grid': '33^-118',
                'ratio': 0.0033239325139923634
            }, {
                'grid': '34^-118',
                'ratio': 0.1276123022731056
            }, {
                'grid': '34^-117',
                'ratio': 0.18870566451400175
            }, {
                'grid': '34^-116',
                'ratio': 0.18532960437637513
            }, {
                'grid': '34^-115',
                'ratio': 0.10690315005766632
            }, {
                'grid': '35^-118',
                'ratio': 0.09802330851363907
            }, {
                'grid': '35^-117',
                'ratio': 0.1547896428427359
            }, {
                'grid': '35^-116',
                'ratio': 0.12463595784741413
            }, {
                'grid': '35^-115',
                'ratio': 0.010676437061070328
            }],
            # San Francisco County
            # maps to two grids (one is an island).
            'geoId/06075': [{
                'grid': '37^-124',
                'ratio': 0.006601930938213778
            }, {
                'grid': '37^-123',
                'ratio': 0.9933980690617857
            }],
            # Arlington County
            # Fully contained in a grid.
            'geoId/51013': [{
                'grid': '38^-78',
                'ratio': 1
            }]
        }
        places_with_geojson = [
            'geoId/06071',  # San Bernardino County
            'geoId/06075',  # San Francisco County
            'geoId/51013'  # Arlington County
        ]
        got = create_place_to_grid_mapping(places_with_geojson,
                                           write_results=False)
        self.assertDictEqual(got, want)


if __name__ == '__main__':
    unittest.main()
