"""Tests for resolve_geo_id."""

import unittest
from resolve_geo_id import convert_to_place_dcid


class ResolveGeoIdForTheUSTest(unittest.TestCase):

    def test_county_geoId(self):
        # Sussex County, Delaware (0500000US10005)
        self.assertEqual(convert_to_place_dcid("0500000US10005"),
                         'geoId/10005')
        # Natchitoches Parish, Louisiana (0500000US22069)
        self.assertEqual(convert_to_place_dcid("0500000US22069"),
                         'geoId/22069')

    def test_state_geoId(self):
        # California
        self.assertEqual(convert_to_place_dcid("0400000US06"), 'geoId/06')

    def test_city_geoId(self):
        # Arlington CDP, Virginia(1600000US5103000)
        self.assertEqual(convert_to_place_dcid("1600000US5103000"),
                         'geoId/5103000')

    def test_school_district_geoId(self):
        # Portsmouth City Public Schools, Virginia (9700000US5103000)
        self.assertEqual(convert_to_place_dcid("9700000US5103000"),
                         'geoId/sch5103000')

    def test_not_interesting_summary_levels(self):
        # Dalton, GA Urbanized Area (2010)[400C100US22069]
        self.assertEqual(convert_to_place_dcid("400C100US22069"), '')

    def test_zip_code(self):
        # 65203
        self.assertEqual(convert_to_place_dcid("86000US65203"), 'zip/65203')


if __name__ == '__main__':
    unittest.main()
