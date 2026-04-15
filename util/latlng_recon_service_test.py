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
"""Tests for util.latlng_recon_service"""

import os
import sys
import unittest
from unittest import mock

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from util import latlng_recon_service


class LatlngReconServiceTest(unittest.TestCase):

    def assert_list_contains(self, superset_list, subset_list):
        """Asserts that superset_list contains all items in subset_list."""
        missing_items = set(subset_list) - set(superset_list)
        self.assertFalse(
            missing_items,
            f"The following items were expected but not found: {sorted(list(missing_items))}"
        )

    def test_basic(self):
        idmap_in = {
            'cascal_mtv': (37.391, -122.081),
            'besant_beach_chennai': (12.998, 80.272),
            'farallon_islands': (37.700, -123.015)
        }
        idmap_out = latlng_recon_service.latlng2places(idmap_in)
        self.assert_list_contains(idmap_out['cascal_mtv'], [
            'zip/94041', 'ipcc_50/37.25_-122.25_USA', 'geoId/sch0626280',
            'geoId/0649670', 'geoId/0618', 'geoId/0608592830',
            'geoId/060855096001', 'geoId/06085509600', 'geoId/06085',
            'geoId/06', 'country/USA'
        ])
        self.assert_list_contains(idmap_out['besant_beach_chennai'], [
            'wikidataId/Q15116', 'wikidataId/Q1445', 'ipcc_50/12.75_80.25_IND',
            'country/IND'
        ])
        self.assertEqual(idmap_out['farallon_islands'], [])

    def test_filter(self):
        idmap_in = {
            'cascal_mtv': (37.391, -122.081),
            'farallon_islands': (37.700, -123.015)
        }
        idmap_out = latlng_recon_service.latlng2places(
            idmap_in, lambda x: [y for y in x if 'country' in y])
        self.assertEqual(idmap_out['cascal_mtv'], ['country/USA'])
        self.assertEqual(idmap_out['farallon_islands'], [])


if __name__ == '__main__':
    unittest.main()
