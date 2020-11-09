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
from india_census.geo.clean_census_location_code_generator import LoadCensusGeoData

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestLoadCensusGeoData(unittest.TestCase):

    def test_create_csv(self):
        census_data_dir = os.path.join(os.path.dirname(__file__),
                                       "geo/test_data")
        census_data_file = 'DDW_PCA0000_2011_Indiastatedist.xlsx'

        loader = LoadCensusGeoData(census_data_dir, census_data_file, 2011)
        loader.generate_location_csv()

        expected_file = os.path.join(census_data_dir,
                                     "india_census_2011_geo_cleaned_expected.csv")
        result_file = os.path.join(
            census_data_dir, "india_census_2011_geo_cleaned.csv")

        same = filecmp.cmp(result_file, expected_file)

        #remove the created file, after comparison
        if os.path.exists(result_file):
            os.remove(result_file)
        self.assertTrue(same)


if __name__ == '__main__':
    unittest.main()
