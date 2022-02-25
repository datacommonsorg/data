# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for resolve_geo_id."""

import os
import sys
import unittest

# Allows the following module imports to work when running as a script
# relative to data/scripts/
sys.path.append(os.path.sep.join([
    '..' for x in filter(lambda x: x == os.path.sep,
                         os.path.abspath(__file__).split('data/scripts/')[1])
]))

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)

from resolve_geo_id import convert_to_place_dcid

_TEST_GEOIDS = {
    '0100000US': 'country/USA',  # Country (US)
    '0400000US06': 'geoId/06',  # California State
    '0400000US36': 'geoId/36',  # New York State
    '0500000US10005': 'geoId/10005',  # Sussex County, Delaware (0500000US10005)
    '0500000US22069':
        'geoId/22069',  # Natchitoches Parish, Louisiana (0500000US22069)
    '1400000US06007000104':
        'geoId/06007000104',  # Census Tract 1.04, Butte County, California
    '1500000USC17020': 'geoId/C17020',  # Chico, CA Metro Area
    '1600000US5103000':
        'geoId/5103000',  # Arlington CDP, Virginia(1600000US5103000)
    '5000000US0601':
        'geoId/0601',  # Congressional District 1 (113th Congress), California
    '86000US65203': 'zip/65203',  # Zip Code (ZCTA)
    '9500000US0602250':
        'geoId/sch0602250',  # Alta-Dutch Flat Union Elementary School District
    '9600000US0605940':
        'geoId/sch0605940',  # Bret Harte Union High School District
    '9700000US5103000':
        'geoId/sch5103000',  # Portsmouth City Public Schools, Virginia (9700000US5103000)
    '400C100US22069': '',  # Dalton, GA Urbanized Area (2010)[400C100US22069] 
    '1600000US1377652': 'geoId/1377652',  # Tucker city, Georgia 
    '1600000US1377625': 'geoId/1377652',  # Tucker city, Georgia
    '9700000US0699999':
        '',  # Remainder of California for summary level code-970
    '9600000US0699999':
        '',  # Remainder of California for summary level code-960
    '9500000US0699999':
        '',  # Remainder of California for summary level code-950
    '310M500US49820': 'geoId/C49820',  # Zapata, TX Micro Area
    '0300000US1': 'usc/NewEnglandDivision',  # Census division in region 1
    '0300000US10': '',  # Invalid census division code
}


class ResolveCensusGeoIdTest(unittest.TestCase):

    def test_geoIds_at_all_summary_levels(self):
        for geo_str, expected_geoId in _TEST_GEOIDS.items():
            self.assertEqual(convert_to_place_dcid(geo_str), expected_geoId)


if __name__ == '__main__':
    unittest.main()
