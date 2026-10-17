"""Tests for process_facility.py"""

import os
import tempfile
import unittest
from .process_facility import process
from .process_facility import _COUNTERS
from .process_facility import _extract_first_geojson
from .process_facility import _parse_geojson_polygon

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_RAW_DATA_DIR = os.path.join(_CODEDIR, 'testdata', 'input')
_EXPECTED_DIR = os.path.join(_CODEDIR, 'testdata', 'expected')

# We have test-cases to cover all the different mapping scenarios.
_EXPECTED_COUNTERS = {
    # This is the expected common case where the given county and lat/lng are right.
    'given_county_correct_latlng': ['1000035', '1001812'],
    # For this, the Choctaw County is right, but the lat/lng is just outside the county.
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

    def test_pub_dim_facility_dedup_and_format(self):
        self.maxDiff = None
        with tempfile.TemporaryDirectory(
        ) as in_dir, tempfile.TemporaryDirectory() as out_dir:
            with open(os.path.join(_RAW_DATA_DIR, 'crosswalks.csv')) as src, \
                 open(os.path.join(in_dir, 'crosswalks.csv'), 'w') as dst:
                dst.write(src.read())

            pub_dim_csv = (
                'facility_id,facility_name,address1,address2,city,state,state_name,'
                'zip,county_fips,county,latitude,longitude,year,naics_code,frs_id\n'
                '1000035,OLD NAME LLC,5728 E SEBRING WARNER RD,,GREENVILLE,OH,OHIO,'
                '45331,39037,DARKE COUNTY,40.081111000000000,-84.591667000000000,2010,325193,110037615694\n'
                '1000035,THE ANDERSONS MARATHON HOLDINGS LLC,5728 E SEBRING WARNER RD,,GREENVILLE,OH,OHIO,'
                '45331,,DARKE COUNTY,40.081111000000000,-84.591667000000000,2016,325193,110037615694\n'
            )
            with open(os.path.join(in_dir, 'PUB_DIM_FACILITY.csv'), 'w') as fp:
                fp.write(pub_dim_csv)

            process(in_dir, out_dir)
            with open(os.path.join(out_dir, 'us_epa_facility.csv')) as gotf:
                lines = gotf.read().splitlines()
            with open(os.path.join(_EXPECTED_DIR,
                                   'us_epa_facility.csv')) as wantf:
                want_lines = wantf.read().splitlines()
            self.assertEqual(lines, want_lines[:2])

    def test_multiple_geojson_values(self):
        multi_val = (
            '\'{"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}\''
            .replace("'", '"') + ',' +
            '\'{"type": "Polygon", "coordinates": [[[2, 2], [2, 3], [3, 3], [3, 2], [2, 2]]]}\''
            .replace("'", '"'))
        gj = _extract_first_geojson(multi_val)
        polygon = _parse_geojson_polygon(gj)
        self.assertTrue(polygon.is_valid)


if __name__ == '__main__':
    unittest.main()
