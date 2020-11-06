# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import filecmp
import os
import json
import tempfile
import unittest
from india_census.geo.convert_census_location_to_json import ConvertResolvedLocationData

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestConvertResolvedLocationData(unittest.TestCase):

    def test_create_csv(self):
        census_data_dir = os.path.join(os.path.dirname(__file__),
                                       "geo/test_data")

        resolved_geos_file_name_pattern = "india_census_2011_geo_resolved.csv"
        census_location_to_dcid_json_file_pattern = "india_census_2011_location_to_dcid_expected.json"

        census_year = 2011
        converter = ConvertResolvedLocationData(
            census_data_dir, resolved_geos_file_name_pattern,
            census_location_to_dcid_json_file_pattern, census_year)
        converter.generate_location_json()

        expected_file = os.path.join(census_data_dir,
                                     "india_census_2011_geo_cleaned.csv")
        result_file = os.path.join(
            census_data_dir, "india_census_2011_geo_cleaned_expected.csv")

        same = filecmp.cmp(result_file, expected_file)
        self.assertTrue(same)


if __name__ == '__main__':
    unittest.main()
