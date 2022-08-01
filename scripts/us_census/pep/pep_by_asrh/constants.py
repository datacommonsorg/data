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
TEST_DATA_DIR = "test_data/datasets"

INPUT_DIRS = [
    "1980_1989/national", "1990_1999/national", "2000_2009/national",
    "2010_2020/national", "1980_1989/state", "1990_1999/state",
    "2000_2009/state", "2010_2020/state", "1990_1999/county",
    "2000_2009/county", "2010_2020/county"
]

NATIONALS_INPUT_DIR = {
    "1980_1989": "1980_1989/national",
    "1990_1999": "1990_1999/national",
    "2000_2009": "2000_2009/national",
    "2010_2020": "2010_2020/national"
}

STATE_INPUT_DIR = {
    "1980_1989": "1980_1989/state",
    "1990_1999": "1990_1999/state",
    "2000_2009": "2000_2009/state",
    "2010_2020": "2010_2020/state"
}

COUNTY_INPUT_DIR = {
    "1980_1989": "1980_1989/county",
    "1990_1999": "1990_1999/county",
    "2000_2009": "2000_2009/county",
    "2010_2020": "2010_2020/county"
}

RACE_UPTO_1999 = "CensusPEPSurvey_RaceUpto1999"
RACE_AFTER_2000 = "CensusPEPSurvey_Race2000Onwards"
RACE_UPTO_1999_PARTIAL = "dcAggregate/" + \
                            "CensusPEPSurvey_PartialAggregate_RaceUpto1999"
RACE_AFTER_2000_PARTIAL = "dcAggregate/" + \
                            "CensusPEPSurvey_PartialAggregate_Race2000Onwards"
