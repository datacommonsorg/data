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
for us nces demographic district school.
"""
CSV_FILE_NAME = "us_nces_demographics_district_school.csv"
MCF_FILE_NAME = "us_nces_demographics_district_school.mcf"
TMCF_FILE_NAME = "us_nces_demographics_district_school.tmcf"
TMCF_FILE_PLACE = "us_nces_demographics_district_place.tmcf"
SCHOOL_TYPE = "district_school"
SPLIT_HEADER_ON_SCHOOL_TYPE = "[District]"

POSSIBLE_DATA_COLUMNS = [
    ".*Students.*", ".*Teacher.*", ".*American.*", ".*Asian.*", ".*Hispanic.*",
    ".*Black.*", ".*White.*", ".*Adult Education.*"
    ".*Staff.*", ".*Admin.*", ".*Counselor.*", ".*Psychologist.*"
]

EXCLUDE_DATA_COLUMNS = [
    "Individualized Education Program Students",
    "Grades 1-8 Students",
    "Grades 9-12 Students",
    ".*Ungraded.*",
    ".*Total.*",
]

POSSIBLE_PLACE_COLUMNS = [
    "school_state_code", ".*ZIP.*", ".*County.*", ".*Agency.*", "Physical.*",
    "Phone.*", "Coeducational", ".*Level.*", ".*State.*", "Latitude.*",
    "Longitude.*", "Locale.*", "Location.*", ".*Congress.*", "Lowest.*",
    "Highest.*"
]

EXCLUDE_PLACE_COLUMNS = [
    "State Name", "Metro Micro Area Code", "Location Address 2",
    "Location Address 3"
]
