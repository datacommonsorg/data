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
"""Tests for preprocess

python3 -m unittest discover -v -s ../ -p "preprocess_test.py"
"""

import os
import unittest
from unittest import mock
import sys

MODULE_DIR = os.path.dirname(__file__)
TEST_DIR = os.path.join(MODULE_DIR, "test_data")
sys.path.insert(0, MODULE_DIR)

from preprocess import preprocess

mock_latlng_to_places = {
    (11, -66): [],
    (41.4, -81.9): ['geoId/3956882', 'geoId/39'],
    (32.6524, -93.9825): ['geoId/2251830'],
    (36.9944992, -118.3001633): ['geoId/06'],
    (31.2593, 131.471): ['country/JPN']
}


def mock_latlng2places(id_to_latlng):
    return {
        id: mock_latlng_to_places.get(latlng, [])
        for id, latlng in id_to_latlng.items()
    }


class USGSEarthquakePreprocessTest(unittest.TestCase):

    @mock.patch('util.latlng_recon_service.latlng2places', mock_latlng2places)
    def test_preprocess(self):
        input_path = os.path.join(TEST_DIR, 'input*.csv')
        output_path = os.path.join(TEST_DIR, 'output.csv')
        expected_csv = os.path.join(TEST_DIR, 'expected.csv')

        preprocess(input_path, output_path, None)

        with open(output_path, 'r') as file:
            got = file.read()
        with open(expected_csv, 'r') as file:
            want = file.read()
        self.maxDiff = None
        self.assertEqual(got, want)

        os.remove(output_path)  # clear generated output.


if __name__ == "__main__":
    unittest.main()
