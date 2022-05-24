"""Tests for preprocess_csv.py"""

import os, sys, unittest

# Allows the following module imports to work when running as a script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rff import preprocess_csv

class ProcessTest(unittest.TestCase):
    def test_preprocess(self):
        src_fldr = f"test_data/input/prism/daily/county"
        output_csv = f"test_data/output/WeatherVariability_Counties.csv"
        preprocess_csv.main(src_fldr, output_csv)
        expected_csv = output_csv.replace("output", "expected")
        with open(expected_csv) as wantf:
            with open(output_csv) as gotf:
                self.assertEqual(gotf.read(), wantf.read())

if __name__ == '__main__':
    unittest.main()