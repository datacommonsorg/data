"""Tests for process_facility.py"""

import csv
import os
import tempfile
import sys
import unittest
from .process_facility import process
from .process_facility import _COUNTERS

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_RAW_DATA_DIR = os.path.join(_CODEDIR, 'testdata', 'input')
_EXPECTED_DIR = os.path.join(_CODEDIR, 'testdata', 'expected')
_EXPECTED_COUNTERS = {
    'given_county_correct_latlng': ['1000035', '1000413', '1001812'],
    'given_county_wrong_latlng': ['1008370'],
    'missing_zip_and_county': ['1002223'],
    'zipbased_county_correct_latlng': ['1012147'],
    'zipbased_county_wrong_latlng': ['1006603']
}


class ProcessTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        with tempfile.TemporaryDirectory() as tmp_dir:
            process(_RAW_DATA_DIR, tmp_dir)
            self.assertEqual(_COUNTERS, _EXPECTED_COUNTERS)
            for fname in ['us_epa_facility.csv', 'us_epa_facility.tmcf']:
                with open(os.path.join(tmp_dir, fname)) as gotf:
                    got = gotf.read()
                    with open(os.path.join(_EXPECTED_DIR, fname)) as wantf:
                        want = wantf.read()
                        self.assertEqual(got, want)


if __name__ == '__main__':
    unittest.main()
