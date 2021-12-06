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
from .geo_id_resolver import *

_Test_Cases = [{
    'input': {
        'state_abbr': 'NB'
    },
    'expected_dcid': 'geoId/31'
}, {
    'input': {
        'state_abbr': 'GM'
    },
    'expected_dcid': 'geoId/66'
}, {
    'input': {
        'state_abbr': 'FS'
    },
    'expected_dcid': ''
}, {
    'input': {
        'state_abbr': 'AR',
        'geo_name': 'Sevier',
        'geo_type': 'County'
    },
    'expected_dcid': 'geoId/05133'
}, {
    'input': {
        'state_abbr': 'AR',
        'geo_name': 'Little Rock',
        'geo_type': 'City'
    },
    'expected_dcid': 'geoId/0541000'
}, {
    'input': {
        'state_abbr': 'CA',
        'geo_name': 'Las vegas',
        'geo_type': 'State'
    },
    'expected_dcid': ''
}]

_County_Test_Cases = [
    {
        'input': {
            'state_abbr': 'AR',
            'county': 'Governors State University'
        },
        'expected_dcid': ''
    },
    {
        'input': {
            'state_abbr': 'ID',
            'county': 'Latah'
        },
        'expected_dcid': 'geoId/16057'
    },
    {
        'input': {
            'state_abbr': 'FS',
            'county': 'Latah'
        },
        'expected_dcid': ''
    },
    {
        'input': {
            'state_abbr': 'MD',
            'county': 'Montgomery County Police Department'
        },
        'expected_dcid': 'geoId/24031'
    },
    {
        'input': {
            'state_abbr': 'NY',
            'county': 'Westchester Public Safety'
        },
        'expected_dcid': 'geoId/36119'
    },
    {
        'input': {
            'state_abbr': 'LA',
            'county': 'Acadia'
        },
        'expected_dcid': 'geoId/22001'
    },
    {
        'input': {
            'state_abbr': 'PA',
            'county': 'Lancaster '
        },
        'expected_dcid': 'geoId/42071'
    },
    {
        'input': {
            'state_abbr': 'IL',
            'county': 'DeWitt'
        },
        'expected_dcid': 'geoId/17039'
    },
    {
        'input': {
            'state_abbr': 'ND',
            'county': 'Lamoure '
        },
        'expected_dcid': 'geoId/38045'
    },
    {
        'input': {
            'state_abbr': 'UT',
            'county': 'Salt Lake County Unified Police Department'
        },
        'expected_dcid': 'geoId/49035'
    },
]

_City_Test_Cases = [{
    'input': {
        'state_abbr': 'IL',
        'city': 'Evergreen Park'
    },
    'expected_dcid': 'geoId/1724634'
}, {
    'input': {
        'state_abbr': 'IL',
        'city': 'University of Delaware'
    },
    'expected_dcid': ''
}, {
    'input': {
        'state_abbr': 'GA',
        'city': 'Dunwoody '
    },
    'expected_dcid': 'geoId/1324768'
}]


class GeoIdResolverTest(unittest.TestCase):

    def test_convert_to_place_dcid(self):

        for test_case in _Test_Cases:
            self.assertEqual(convert_to_place_dcid(**test_case['input']),
                             test_case['expected_dcid'])

    def test_county_to_dcid(self):
        for test_case in _County_Test_Cases:
            self.assertEqual(county_to_dcid(**test_case['input']),
                             test_case['expected_dcid'])

    def test_city_to_dcid(self):
        for test_case in _City_Test_Cases:
            self.assertEqual(city_to_dcid(**test_case['input']),
                             test_case['expected_dcid'])


if __name__ == '__main__':
    unittest.main()
