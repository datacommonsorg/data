"""Tests for resolve_geo_id."""

import unittest
from resolve_geo_id import _convert_to_geoId


class ResolveGeoIdTest(unittest.TestCase):

    def test_county_geoId(self):
        # Sussex County, Delaware (0500000US10005)
        self.assertEqual(_convert_to_geoId("0500000US10005"),
                         'dcid:geoId/10005')
        # Natchitoches Parish, Louisiana (0500000US22069)
        self.assertEqual(_convert_to_geoId("0500000US22069"),
                         'dcid:geoId/22069')

    def test_state_geoId(self):
        # California
        self.assertEqual(_convert_to_geoId("0400000US06"), 'dcid:geoId/06')

    def test_city_geoId(self):
        # Arlington CDP, Virginia(1600000US5103000)
        self.assertEqual(_convert_to_geoId("1600000US5103000"),
                         'dcid:geoId/5103000')

    def test_school_district_geoId(self):
        # Portsmouth City Public Schools, Virginia (9700000US5103000)
        self.assertEqual(_convert_to_geoId("9700000US5103000"),
                         'dcid:geoId/sch5103000')

    def test_not_interesting_summary_levels(self):
        # Dalton, GA Urbanized Area (2010)[400C100US22069]
        self.assertEqual(_convert_to_geoId("400C100US22069"), '')

    def test_zip_code(self):
        # 65203
        self.assertEqual(_convert_to_geoId("86000US65203"), 'dcid:zip/65203')


if __name__ == '__main__':
    unittest.main()
