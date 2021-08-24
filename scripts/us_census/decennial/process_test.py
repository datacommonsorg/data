"""Tests for process.py"""

import csv
import os
import tempfile
import sys
import unittest
from .process import process

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_RAW_DATA_DIR = os.path.join(_CODEDIR, 'testdata', 'input')
_EXPECTED_DIR = os.path.join(_CODEDIR, 'testdata', 'expected')
_OUT_FILES = ['2010/Alabama.csv', '2020/Wyoming.csv']


class ProcessTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        with tempfile.TemporaryDirectory() as tmp_dir:
            process(_RAW_DATA_DIR, tmp_dir, verbose=False)
            for csv_fname in _OUT_FILES:
                with open(os.path.join(tmp_dir, csv_fname)) as gotf:
                    got = gotf.read()
                    with open(os.path.join(_EXPECTED_DIR, csv_fname)) as wantf:
                        want = wantf.read()
                        self.assertEqual(got, want)


if __name__ == '__main__':
    unittest.main()
