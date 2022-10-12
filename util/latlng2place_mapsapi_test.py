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
"""Tests for util.latlng2place_mapsapi"""

import json
import os
import sys
import unittest
from unittest import mock

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
import latlng2place_mapsapi

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')


def _mock_tahiti(url):
    if 'administrative_area_level2' in url or 'administrative_area_level1' in url:
        return {'results': [], 'status': 'ZERO_RESULTS'}
    else:
        return {
            'results': [{
                'address_components': [{
                    'short_name': 'PF',
                    'types': ['country']
                }],
                'place_id': 'ChIJTddtfNB1GHQREVfDCXp6wJs',
                'types': ['country']
            }],
            'status': 'OK'
        }


class Latlng2PlaceMapsAPITest(unittest.TestCase):

    @mock.patch('latlng2place_mapsapi._call_rpc')
    def test_aa2(self, mock_mapi):
        with open(os.path.join(_TESTDIR, 'mapsapi_aa2.json')) as fp:
            mock_mapi.return_value = json.load(fp)
        ll2p = latlng2place_mapsapi.Resolver(api_key='DoesNotMatterKey')
        self.assertEqual(
            ll2p.resolve(31.6334677, 74.7300352),
            ['wikidataId/Q202822', 'wikidataId/Q22424', 'country/IND'])

    @mock.patch('latlng2place_mapsapi._call_rpc')
    def test_country(self, mock_mapi):
        mock_mapi.side_effect = _mock_tahiti
        ll2p = latlng2place_mapsapi.Resolver(api_key='DoesNotMatterKey')
        self.assertEqual(ll2p.resolve(-17.686893, -149.51289), ['country/PYF'])


if __name__ == '__main__':
    unittest.main()
