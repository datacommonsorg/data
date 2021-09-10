"""Tests for process_facility.py"""

import csv
import os
import tempfile
import sys
import unittest
from .process_facility import process

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_RAW_DATA_DIR = os.path.join(_CODEDIR, 'testdata', 'input')
_EXPECTED_DIR = os.path.join(_CODEDIR, 'testdata', 'expected')


class ProcessTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        with tempfile.TemporaryDirectory() as tmp_dir:
            process(os.path.join(_RAW_DATA_DIR, 'ghg_emitter_facilities.csv'),
                    os.path.join(_RAW_DATA_DIR, 'crosswalk.csv'), tmp_dir)
            for fname in ['us_epa_facility.csv', 'us_epa_facility.tmcf']:
                with open(os.path.join(tmp_dir, fname)) as gotf:
                    got = gotf.read()
                    with open(os.path.join(_EXPECTED_DIR, fname)) as wantf:
                        want = wantf.read()
                        self.assertEqual(got, want)


if __name__ == '__main__':
    unittest.main()
