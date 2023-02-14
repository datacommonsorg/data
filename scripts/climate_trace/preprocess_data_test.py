"""This script contains tests for preproccess_data.py.

It processes three sample API responses and checks if the output matches the
expected output.
"""
import csv
import io
import json
import os
import sys
import unittest
from .preprocess_data import *

module_dir_ = os.path.dirname(__file__)
sys.path.insert(0, module_dir_)

FIELDNAMES = [
    'observation_about', 'observation_date', 'variable_measured', 'value'
]


class PreprocessDataTest(unittest.TestCase):

    def test_write_emissions(self):
        test_dir = os.path.join(module_dir_, 'test_data')
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
        writer.writeheader()
        
        # Test Earth
        with open(os.path.join(test_dir, 'earth.json')) as f:
            write_emissions(writer, json.load(f))

        # Test continents
        with open(os.path.join(test_dir, 'europe.json')) as f:
            write_emissions(writer, json.load(f))

        # Test countries
        with open(os.path.join(test_dir, 'usa.json')) as f:
            write_emissions(writer, json.load(f))

        with open(os.path.join(test_dir, 'expected_output.csv')) as f:
            self.assertEqual(output.getvalue().replace('\r', ''), f.read())


if __name__ == "__main__":
    unittest.main()
