# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.licenses/org/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Constant value used in processing EuroStat BMI are defined here.1980_1989
This module also consists of mapping between various forms of column names
found in downloaded files and its corresponding SV name.
While preprocessing files column names are changed to SV names as used in
DC import
"""

INPUT_DIR = 'input_files'
OUTPUT_DIR = 'output_files'
TEST_DATA_DIR = "test_data"

INPUT_DIRS = [
    "1990_1999/city/", "2000_2009/city/", "2010_2019/city/", "2020_2021/city/",
    "1970_1979/county/", "1980_1989/county/", "1990_1999/county/",
    "2000_2009/county/", "2010_2020/county/", "2021/county/",
    "1900_1989/state/", "1990_1999/state/", "2000_2009/state/",
    "2010_2020/state/", "2021/state/", "1900_1979/national/",
    "1980_1989/national/", "1990_1999/national/", "2000_2009/national/",
    "2010_2020/national/", "2021/national/"
]

SCALING_FACTOR_STATE_1900_1960 = 1000
USA = "United States"
USA_GEO_ID = "country/USA"
DISTRICT_OF_COLUMBIA_STATE_CODE = 11
DISTRICT_OF_COLUMBIA_COUNTY_CODE = 1
