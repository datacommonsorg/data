"""Tests for process_facility.py"""

import os
import sys
import tempfile
import unittest
from unittest import mock

import pandas as pd
from shapely import geometry

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(_CODEDIR, '..', '..', '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.us_epa.facility import download_efservice
from scripts.us_epa.facility import process_facility
from scripts.us_epa.facility.process_facility import _COUNTERS
from scripts.us_epa.facility.process_facility import _extract_first_geojson
from scripts.us_epa.facility.process_facility import _parse_geojson_polygon
from scripts.us_epa.facility.process_facility import process
from scripts.us_epa.util import facilities_helper as fh

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

_FAKE_COUNTY_CANDIDATES = {
    'zip/45331': [['geoId/39037'], []],
    'zip/36922': [[], ['geoId/01023', 'geoId/01119']],
    'zip/93251': [['geoId/06029'], []],
    'zip/71443': [[], []],
    'zip/82001': [['geoId/56021'], []],
    'zip/87417': [['geoId/35045'], []],
}

_FAKE_POLYGONS = {
    'geoId/39037': geometry.box(-84.812411, 39.916528, -84.425902, 40.354259),
    'geoId/01023': geometry.box(-88.4, 31.7, -87.9, 32.3),
    'geoId/06029': geometry.box(-120.194146, 34.790629, -117.616195, 35.798149),
    'geoId/56021': geometry.box(-105.280636, 40.998048, -104.05216, 41.656655),
    'geoId/35045': geometry.box(-109.046183, 36.000288, -107.420913, 37.000005),
}


class ProcessTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        fh._COUNTY_CANDIDATES_CACHE.clear()
        fh._COUNTY_CANDIDATES_CACHE.update(_FAKE_COUNTY_CANDIDATES)
        process_facility._POLYGON_CACHE.clear()
        process_facility._POLYGON_CACHE.update(_FAKE_POLYGONS)
        process_facility._GEOJSON_CACHE.clear()
        self._dc_patcher = mock.patch.object(
            fh,
            'dc_api_get_node_property',
            side_effect=AssertionError(
                'Unexpected live Data Commons API call in unit test'))
        self._dc_patcher.start()

    def tearDown(self):
        self._dc_patcher.stop()
        super().tearDown()

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

            # Note: rows are intentionally ordered newest-first (2016 before 2010)
            # with missing county_fips in 2016 to verify order-independent backfill.
            pub_dim_csv = (
                'facility_id,facility_name,address1,address2,city,state,state_name,'
                'zip,county_fips,county,latitude,longitude,year,naics_code,frs_id\n'
                ',MISSING ID LLC,123 MAIN ST,,GREENVILLE,OH,OHIO,'
                '45331,39037,DARKE COUNTY,40.081111000000000,-84.591667000000000,2010,325193,110037615694\n'
                '1000035,THE ANDERSONS MARATHON HOLDINGS LLC,5728 E SEBRING WARNER RD,,GREENVILLE,OH,OHIO,'
                '45331,,DARKE COUNTY,40.081111000000000,-84.591667000000000,2016,325193,\n'
                '1000035,OLD NAME LLC,5728 E SEBRING WARNER RD,,GREENVILLE,OH,OHIO,'
                '45331,39037,DARKE COUNTY,40.081111000000000,-84.591667000000000,2010,325193,110037615694\n'
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

    def test_download_retry_and_atomic_replace(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            page1 = mock.Mock(text='facility_id,frs_id\n1000035,110037615694\n')
            page1.raise_for_status.return_value = None
            page2 = mock.Mock(text='')
            page2.raise_for_status.return_value = None
            with mock.patch.object(
                    fh.requests,
                    'get',
                    side_effect=[RuntimeError('transient error'), page1,
                                 page2]):
                fh.download('https://example.com/',
                            'PUB_DIM_FACILITY',
                            1,
                            tmp_dir,
                            max_retries=2,
                            retry_backoff_sec=0.001,
                            request_timeout=5)
            out_csv = os.path.join(tmp_dir, 'PUB_DIM_FACILITY.csv')
            self.assertTrue(os.path.exists(out_csv))
            self.assertFalse(os.path.exists(out_csv + '.tmp'))

    def test_oris_crosswalk_failure_and_regeneration(self):
        with mock.patch.object(download_efservice.requests,
                               'get',
                               side_effect=RuntimeError('network failure')):
            with self.assertRaises(RuntimeError):
                download_efservice._load_oris_crosswalk(max_retries=1,
                                                        retry_backoff_sec=0.001)

        with tempfile.TemporaryDirectory() as tmp_dir:
            table_csv = os.path.join(tmp_dir, 'PUB_DIM_FACILITY.csv')
            crosswalk_csv = os.path.join(tmp_dir, 'crosswalks.csv')
            # Rows ordered newest-first with empty frs_id in 2016 and populated frs_id in 2010.
            with open(table_csv, 'w') as fp:
                fp.write('facility_id,frs_id,year\n'
                         '1000035,,2016\n'
                         '1000035,110037615694,2010\n')
            with open(crosswalk_csv, 'w') as fp:
                fp.write('stale\n')
            fake_oris = pd.DataFrame({
                'Facility Id': ['1000035'],
                'ORIS CODE': ['1234'],
                'ORIS CODE 2': [''],
                'ORIS CODE 3': [''],
                'ORIS CODE 4': [''],
                'ORIS CODE 5': [''],
            })
            with mock.patch.object(download_efservice,
                                   '_load_oris_crosswalk',
                                   return_value=fake_oris):
                download_efservice._generate_crosswalk(table_csv, crosswalk_csv)
            with open(crosswalk_csv) as fp:
                content = fp.read()
            self.assertIn('110037615694', content)
            self.assertFalse(os.path.exists(crosswalk_csv + '.tmp'))


if __name__ == '__main__':
    unittest.main()
