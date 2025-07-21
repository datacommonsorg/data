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
import os
import sys
import unittest

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from un.sdg import util


class UtilTest(unittest.TestCase):

    def test_format_description(self):
        self.assertEqual(
            util.format_description(
                'Indicator of Food Price Anomalies (IFPA), by Consumer Food Price Index'
            ),
            'Indicator of Food Price Anomalies, by Consumer Food Price Index')

    def test_is_float(self):
        self.assertTrue(util.is_float(7.28))
        self.assertFalse(util.is_float('NA'))

    def test_is_valid(self):
        self.assertFalse(util.is_valid(float('nan')))
        self.assertFalse(util.is_valid(''))

    def test_curate_pvs(self):
        self.assertEqual(
            util.curate_pvs(
                '[Age = 15 years old and over | Education level = Primary education or less]',
                util.TITLE_MAPPINGS),
            '[Age = 15 years old and over, Primary education or less]')
        self.assertEqual(
            util.curate_pvs('[Deviation Level = Extreme (75-100%)]',
                            util.TITLE_MAPPINGS),
            '[Extreme deviation (75-100%)]')

    def test_format_variable_description(self):
        self.assertEqual(
            util.format_variable_description(
                'Employed population below international poverty line, by sex and age (%) [Age = 15 to 24 years old]',
                'Employed population below international poverty line, by sex and age (%)'
            ),
            'Employed population below international poverty line [15 to 24 years old]'
        )
        self.assertEqual(
            util.format_variable_description(
                'Number of chairs of permanent committees, by age sex and focus of the committee, Joint Committees [Age = under 46 years old | Sex = Female | Parliamentary committees = Gender Equality]',
                'Number of chairs of permanent committees, by age sex and focus of the committee, Joint Committees'
            ),
            'Number of chairs of permanent committees, Joint Committees [under 46 years old, Female, Parliamentary committees = Gender Equality]'
        )
        self.assertEqual(
            util.format_variable_description(
                'Proportion of population achieving at least a fixed level of proficiency in functional skills, by sex, age and type of skill (%) [Age = 16 to 65 years old | Sex = Female | Type of skill = Literacy]',
                'Proportion of population achieving at least a fixed level of proficiency in functional skills, by sex, age and type of skill (%)'
            ),
            'Proportion of population achieving at least a fixed level of proficiency in functional skills [16 to 65 years old, Female, Literacy]'
        )
        self.assertEqual(
            util.format_variable_description(
                'Adjusted gender parity index for achieving at least a fixed level of proficiency in functional skills, by numeracy/literacy skills (ratio) [Age = 16 to 65 years old | Type of skill = Literacy]',
                'Adjusted gender parity index for achieving at least a fixed level of proficiency in functional skills, by numeracy/literacy skills (ratio)'
            ),
            'Adjusted gender parity index for achieving at least a fixed level of proficiency in functional skills [16 to 65 years old, Literacy]'
        )

    def test_format_variable_code(self):
        self.assertEqual(
            util.format_variable_code(
                'AG_FOOD_WST@FOOD_WASTE_SECTOR--FWS_OOHC'),
            'AG_FOOD_WST.FOOD_WASTE_SECTOR--FWS_OOHC')

    def test_format_title(self):
        self.assertEqual(util.format_title('FOOD_WASTE_SECTOR'),
                         'Food Waste Sector')

    def test_format_property(self):
        self.assertEqual(util.format_property('FOOD_WASTE_SECTOR'),
                         'FoodWasteSector')


if __name__ == '__main__':
    unittest.main()
