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
'''Tests for util.py.

Usage: python3 -m unittest discover -v -s ../ -p "preprocess_test.py"
'''
import os
import tempfile
import sys
import unittest
from .preprocess import *

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

module_dir_ = os.path.dirname(__file__)


class PreprocessTest(unittest.TestCase):

    def test_add_concepts(self):
        concepts = set()
        add_concepts('AG_FOOD_WST', 'Dimensions', concepts)
        expected = {('Food Waste Sector', 'OOHC', 'Out-of-home consumption',
                     'FWS_OOHC'), ('Reporting Type', 'R', 'Regional', 'R'),
                    ('Food Waste Sector', 'MNFC', 'Manufacturing', 'FWS_MNFC'),
                    ('Reporting Type', 'N', 'National', 'N'),
                    ('Food Waste Sector', 'RTL', 'Retail', 'FWS_RTL'),
                    ('Reporting Type', 'G', 'Global', 'G'),
                    ('Food Waste Sector', 'ALL',
                     'All food waste sectors', '_T'),
                    ('Food Waste Sector', 'HHS', 'Households', 'FWS_HHS')}
        self.assertEqual(concepts, expected)

    def test_write_concepts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            concepts = set()
            add_concepts('AG_FLS_INDEX', 'Dimensions', concepts)
            output = os.path.join(tmp_dir, 'output.csv')
            write_concepts(output, concepts)
            with open(output) as result:
                expected = 'Reporting Type,G,Global,G\nReporting Type,N,National,N\n'
                self.assertEqual(result.read(), expected)


if __name__ == '__main__':
    unittest.main()
