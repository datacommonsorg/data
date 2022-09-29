# Copyright 2022 Google LLC
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
"""
This Python Script is config file
for us nces demographic private school.
"""
CSV_FILE_NAME = "us_nces_demographics_public_school.csv"
MCF_FILE_NAME = "us_nces_demographics_public_school.mcf"
TMCF_FILE_NAME = "us_nces_demographics_public_school.tmcf"
TMCF_FILE_PLACE = "us_nces_demographics_public_place.tmcf"
SCHOOL_TYPE = "public_school"
SPLIT_HEADER_ON_SCHOOL_TYPE = "[Public School]"

POSSIBLE_DATA_COLUMNS = [
    ".*Students.*", ".*Lunch.*", ".*Teacher.*", ".*American.*", ".*Asian.*",
    ".*Hispanic.*", ".*Black.*", ".*White.*", ".*Adult Education.*",'Ungraded'
]

EXCLUDE_DATA_COLUMNS = [
    'Migrant Students',
    'Total Students - Calculated Sum of Reported Grade Totals',
    'Unknown', 'unknown',
    'Total Race/Ethnicity', 'Grades 1-8 Students', 'Grades 9-12 Students'
]

POSSIBLE_PLACE_COLUMNS = [
     "school_state_code","ZIP",".*County.*",".*School.*", ".*Lowest.*", ".*Highest.*",
    "Physical.*", "Phone.*",  "Coeducational", ".*Level.*",".*State.*"
]

EXCLUDE_PLACE_COLUMNS = ["State Name","Metro Micro Area Code"]