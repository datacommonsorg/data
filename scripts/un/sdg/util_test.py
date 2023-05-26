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

Usage: python3 -m unittest discover -v -s ../ -p "util_test.py"
'''
import unittest
from .util import *


class UtilTest(unittest.TestCase):

    def test_format_description(self):
        self.assertEqual(
            format_description(
                'Indicator of Food Price Anomalies (IFPA), by Consumer Food Price Index'
            ), 'Indicator of Food Price Anomalies')

    def test_is_float(self):
        self.assertTrue(is_float(7.28))
        self.assertFalse(is_float('NA'))

    def test_make_property(self):
        self.assertEqual(make_property('Bioclimatic belt'), 'BioclimaticBelt')

    def test_make_value(self):
        self.assertEqual(make_value('100+'), '100GEQ')


if __name__ == '__main__':
    unittest.main()
