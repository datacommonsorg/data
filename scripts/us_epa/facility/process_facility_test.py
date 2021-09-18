"""Tests for process_facility.py"""

import os
import tempfile
import unittest
from .process_facility import process
from .process_facility import _COUNTERS

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_RAW_DATA_DIR = os.path.join(_CODEDIR, 'testdata', 'input')
_EXPECTED_DIR = os.path.join(_CODEDIR, 'testdata', 'expected')

# We have test-cases to cover all the different mapping scenarios.
_EXPECTED_COUNTERS = {
    # This is the expected common case where the given county and lat/lng are right.
    'given_county_correct_latlng': ['1000035', '1001812'],
    # For this, the Choctaw County is right, but the lat/lng is just outside the county. We drop it.
    'given_county_wrong_latlng': ['1008370'],
    # For this, the zip is not a valid ZCTA (zip/71443), so we have nothing to validate
    # that it is indeed in "Sabish Parish".
    'missing_zip_and_county': ['1002223'],
    # For this, the county info is actually missing in CSV, but we match Kern County from DC,
    # and it also matches the lat/lng.
    'zipbased_county_correct_latlng': ['1012147'],
    # This is the case of GHG facility being different from FRS facility. The CSV has Jefferson
    # County CO and corresponding lat/lng, but the zip 82001 is from Laramie County, WY.
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
