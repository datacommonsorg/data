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
#
"""Tests for place_map."""

import unittest
from util.state_division_to_dcid import get_place_dcid


class PlaceMapTest(unittest.TestCase):

    def test_place_id_resolution_by_name(self):
        self.assertEqual(get_place_dcid('United States'), 'country/USA')
        self.assertEqual(get_place_dcid('California'), 'geoId/06')
        self.assertEqual(get_place_dcid('Calif.'), 'geoId/06')
        self.assertEqual(get_place_dcid('MultiState'), '')
        self.assertEqual(get_place_dcid('Total'), '')
        self.assertEqual(get_place_dcid('Multistate'), '')


if __name__ == '__main__':
    unittest.main()
