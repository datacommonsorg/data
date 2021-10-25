"""Tests for generate_mcf.py"""

import csv
import os
import tempfile
import sys
import unittest
from .generate_mcf import generate

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_RAW_DATA_DIR = os.path.join(_CODEDIR, 'testdata', 'input')
_EXPECTED_DIR = os.path.join(_CODEDIR, 'testdata', 'expected')
_OUT_FILES = ['India_States_GeoJson.mcf', 'India_Districts_GeoJson.mcf']


class ProcessTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        with tempfile.TemporaryDirectory() as tmp_dir:
            generate(os.path.join(_RAW_DATA_DIR, 'states.geojson'),
                     os.path.join(_RAW_DATA_DIR, 'districts.geojson'), tmp_dir)
            for csv_fname in _OUT_FILES:
                with open(os.path.join(tmp_dir, csv_fname)) as gotf:
                    got = gotf.read()
                    with open(os.path.join(_EXPECTED_DIR, csv_fname)) as wantf:
                        want = wantf.read()
                        self.assertEqual(got, want)


if __name__ == '__main__':
    unittest.main()
