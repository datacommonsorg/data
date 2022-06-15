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
        _TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'test_data')
        src_fldr = os.path.join(_TESTDIR, 'input/prism/daily/county')
        print(src_fldr)
        expected_csv = os.path.join(_TESTDIR,
                                    'expected/WeatherVariability_Counties.csv')
        print(expected_csv)
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_csv = f"{tmp_dir}/WeatherVariability_Counties.csv"
            preprocess_csv.main(src_fldr, output_csv)
            with open(expected_csv) as wantf:
                with open(output_csv) as gotf:
                    self.assertEqual(gotf.read(), wantf.read())


if __name__ == '__main__':
    unittest.main()
