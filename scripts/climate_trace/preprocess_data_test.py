"""This script contains tests for preproccess_data.py.

It processes three sample API responses and checks if the output matches the
expected output.
"""
import csv
import io
import os
import unittest
from .preprocess_data import *

FIELDNAMES = [
    'observation_about', 'observation_date', 'variable_measured', 'value'
]


class PreprocessDataTest(unittest.TestCase):

    def test_write_emissions(self):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
        writer.writeheader()
        for file in os.listdir('test_data'):
            if not file.endswith('.json'):
                continue
            with open('test_data/' + file) as f:
                write_emissions(writer, json.load(f))

        with open('test_data/expected_output.csv') as f:
            self.assertEqual(output.getvalue().replace('\r', ''), f.read())


if __name__ == "__main__":
    unittest.main()