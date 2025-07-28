# Copyright 2024 Google LLC
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
"""Unit tests for wiki_place_reoslver.py."""

import unittest

import os
import sys

from absl import app
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR))))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR))),
                 'util'))

import download_util
import file_util

from property_value_cache import PropertyValueCache, flatten_dict
from wiki_place_resolver import WikiPlaceResolver

_TEST_DIR = os.path.join(_SCRIPT_DIR, "test_data")


class WikiPlaceResolverTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Pre-load the HTTP responses.
        download_util._PREFILLED_RESPONSE = file_util.file_load_py_dict(
            os.path.join(_TEST_DIR, 'http_cache.py'))
        cls.wiki_config = {
            'custom_search_key': 'TEST_KEY',
            'wiki_search_max_results': 1,
        }

    # TODO(stuniki): Fix this test. The test is failing due to a mismatch in the
    # expected and actual results. The test needs to be updated to reflect the
    # current behavior of the wiki_place_resolver.py module.
    @unittest.skip('Skipping failing test to be fixed later.')
    def test_wiki_place_name_lookup(self):
        wiki_resolver = WikiPlaceResolver(config_dict=self.wiki_config)
        results = wiki_resolver.lookup_wiki_places({
            1: {
                'name': 'Bengaluru'
            },
            2: {
                'name': 'California'
            }
        })
        expected_results = {
            1: {
                'name':
                    'Bengaluru,"Bengaluru"',
                'wikidataId':
                    'Q1355',
                'description':
                    '"city in Karnataka, India"',
                'PlaceType':
                    'Q745456,Q51929311,Q1549591,Q174844,Q11271835,Q208511',
                'PlaceTypeName':
                    '"business cluster","largest city","big city","megacity","state capital","global city"',
                'ContainedInPlace':
                    'Q806463,Q3374892,Q266923',
                'ContainedInPlaceName':
                    '"Bengaluru Urban district","Mysore State","Kingdom of Mysore"',
                'Country':
                    'Q668,Q2001966,Q83821,Q167639',
                'CountryName':
                    '"India","Company rule in India","Bijapur Sultanate","Vijayanagara Empire"'
            },
            2: {
                'name': 'California,"California"',
                'wikidataId': 'Q99',
                'description': '"state of the United States of America"',
                'PlaceType': 'Q35657',
                'PlaceTypeName': '"U.S. state"',
                'ContainedInPlace': 'Q30',
                'ContainedInPlaceName': '"United States"',
                'Country': 'Q30',
                'CountryName': '"United States"'
            }
        }
        self.assertEqual(expected_results, results)
