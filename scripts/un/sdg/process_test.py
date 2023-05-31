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
'''Tests for process.py.

Usage: python3 -m unittest discover -v -s ../ -p "process_test.py"
'''
import collections
import os
import tempfile
import sys
import unittest
from .process import *

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

module_dir_ = os.path.dirname(__file__)

INPUT_ROW = {
    'Goal': '12',
    'Target': '12.3',
    'Indicator': '12.3.1',
    'SeriesCode': 'AG_FOOD_WST',
    'SeriesDescription': 'Food waste (Tonnes)',
    'GeoAreaCode': '4',
    'GeoAreaName': 'Afghanistan',
    'TimePeriod': '2019',
    'Value': '3109152.67104',
    'Time_Detail': '2019',
    'TimeCoverage': '',
    'UpperBound': '',
    'LowerBound': '',
    'BasePeriod': '',
    'Source': 'Food Waste Index Report 2021 / WESR',
    'GeoInfoUrl': '',
    'FootNote': 'Very Low Confidence',
    '[Food Waste Sector]': 'HHS',
    '[Nature]': 'E',
    '[Observation Status]': 'A',
    '[Reporting Type]': 'G',
    '[Units]': 'TONNES'
}


class ProcessTest(unittest.TestCase):

    def test_write_templates(self):
        templates = {
            ('\nNode: dcid:SDG_CA_G\n'
             'typeOf: dcs:SDG_MeasurementMethodEnum\n'
             'name: "SDG_CA_G"\n'
             'description: "SDG Measurement Method: Country adjusted data, Global"\n'
            ),
            ('\nNode: dcid:SDG_CA_A_G\n'
             'typeOf: dcs:SDG_MeasurementMethodEnum\n'
             'name: "SDG_CA_A_G"\n'
             'description: "SDG Measurement Method: Country adjusted data, Normal value, Global"\n'
            )
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = os.path.join(tmp_dir, 'output.mcf')
            write_templates(output, templates)
            with open(output) as result:
                with open(
                        os.path.join(
                            module_dir_,
                            'testdata/expected_measurement_method.mcf')
                ) as expected:
                    self.assertEqual(result.read(), expected.read())

    def tests_add_concepts(self):
        concepts = collections.defaultdict(dict)
        add_concepts('testdata/test_dimensions.csv', concepts)
        expected = {
            'Activity': {
                'INDUSTRIES': ('Industries', 'INDUSTRIES'),
                'ISIC3_D': ('Manufacturing (ISIC3 D)', 'ISIC3D')
            },
            'Age': {
                '1-14': ('1 to 14 years old', '1-14'),
                '1-17': ('1 to 17 years old', '1-17')
            }
        }
        self.assertEqual(concepts, expected)

    def test_get_observation_about(self):
        self.assertEqual(get_observation_about(124, 'Canada', ''),
                         'dcs:country/CAN')
        self.assertEqual(get_observation_about(124, 'Canada', 'Toronto'),
                         'dcs:wikidataId/Q172')

    def test_get_variable_measured(self):
        properties = ['[Food Waste Sector]']
        concepts = collections.defaultdict(dict)
        add_concepts('preprocessed/attributes.csv', concepts)
        add_concepts('preprocessed/dimensions.csv', concepts)
        expected = ('\nNode: dcid:sdg/AG_FOOD_WST_HHS\n'
                    'typeOf: dcs:StatisticalVariable\n'
                    'measuredProperty: dcs:value\n'
                    'name: "Food waste: Households"\n'
                    'populationType: dcs:SDG_AG_FOOD_WST\n'
                    'statType: dcs:measuredValue\n'
                    'sdg_foodWasteSector: dcs:SDG_FoodWasteSectorEnum_HHS\n')
        self.assertEqual(get_variable_measured(INPUT_ROW, properties, concepts),
                         expected)

    def test_get_measurement_method(self):
        concepts = collections.defaultdict(dict)
        add_concepts('preprocessed/attributes.csv', concepts)
        add_concepts('preprocessed/dimensions.csv', concepts)
        expected = (
            '\nNode: dcid:SDG_E_A_G\n'
            'typeOf: dcs:SDG_MeasurementMethodEnum\n'
            'name: "SDG_E_A_G"\n'
            'description: "SDG Measurement Method: Estimated data, Normal value, Global"\n'
        )
        self.assertEqual(get_measurement_method(INPUT_ROW, concepts), expected)

    def test_get_unit(self):
        expected = ('\nNode: dcid:TONNES\n'
                    'typeOf: dcs:UnitOfMeasure\n'
                    'name: "t"\n'
                    'description: "SDG unit type TONNES."\n')
        self.assertEqual(get_unit(INPUT_ROW), expected)

    def test_write_schema(self):
        concepts = collections.defaultdict(dict)
        add_concepts('testdata/test_dimensions.csv', concepts)
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = os.path.join(tmp_dir, 'output.mcf')
            write_schema(output, concepts)
            with open(output) as result:
                with open(
                        os.path.join(
                            module_dir_,
                            'testdata/expected_schema.mcf')) as expected:
                    self.assertEqual(result.read(), expected.read())

    def test_process_input_file(self):
        concepts = collections.defaultdict(dict)
        add_concepts('preprocessed/attributes.csv', concepts)
        add_concepts('preprocessed/dimensions.csv', concepts)
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = os.path.join(tmp_dir, 'output.mcf')
            with open(output, 'w') as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writeheader()
                process_input_file('testdata/test_input.csv', writer, concepts,
                                   set(), set(), set())
            with open(output) as result:
                with open(
                        os.path.join(
                            module_dir_,
                            'testdata/expected_output.csv')) as expected:
                    self.assertEqual(result.read(), expected.read())


if __name__ == '__main__':
    unittest.main()
