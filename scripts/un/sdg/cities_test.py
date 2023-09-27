# Copyright 2023 Google LLC
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
'''Tests for cities.py.

Usage: python3 -m unittest discover -v -s ../ -p "cities_test.py"
'''
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from un.sdg import cities

module_dir_ = os.path.dirname(__file__)

CITIES = {
    'Mazār-e Sharīf, Afghanistan': 'AF_MAZAR_E_SHARIF',
}
RESPONSE = {
    'entities': [{
        'description': 'Mazār-e Sharīf, Afghanistan',
        'dcids': ['wikidataId/Q130469']
    }]
}


class CitiesTest(unittest.TestCase):

    def test_write_cities(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cities.get_cities = mock.Mock(return_value=RESPONSE)
            output = os.path.join(tmp_dir, 'output.csv')
            cities.write_cities(output, CITIES, '')
            with open(output) as result:
                with open(
                        os.path.join(
                            module_dir_,
                            'testdata/expected_cities.csv')) as expected:
                    self.assertEqual(result.read(), expected.read())


if __name__ == '__main__':
    unittest.main()
