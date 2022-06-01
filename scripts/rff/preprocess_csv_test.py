"""Tests for preprocess_csv.py"""

import os
import sys
import tempfile
import unittest

# Allows the following module imports to work when running as a script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rff import preprocess_csv


class ProcessTest(unittest.TestCase):

    def test_preprocess(self):
        src_fldr = "test_data/input/prism/daily/county"
        expected_csv = "test_data/expected/WeatherVariability_Counties.csv"
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_csv = f"{tmp_dir}/WeatherVariability_Counties.csv"
            preprocess_csv.main(src_fldr, output_csv)
            with open(expected_csv, 'rb') as wantf:
                with open(output_csv, 'rb') as gotf:
                    self.assertEqual(gotf.read(), wantf.read())


if __name__ == '__main__':
    unittest.main()
