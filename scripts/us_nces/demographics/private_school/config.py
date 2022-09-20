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

CSV_FILE_NAME = "us_nces_demographics_private_school.csv"
MCF_FILE_NAME = "us_nces_demographics_private_school.mcf"
TMCF_FILE_NAME = "us_nces_demographics_private_school.tmcf"
TMCF_FILE_PLACE = "us_nces_demographics_private_place.tmcf"
SCHOOL_TYPE = "private_school"
SPLIT_HEADER_ON_SCHOOL_TYPE = "[Private School]"

POSSIBLE_DATA_COLUMNS = [".*Students.*", ".*Teacher.*", "Percentage.*"]

EXCLUDE_DATA_COLUMNS = [
    "Total Students", "Prekindergarten and Kindergarten Students",
    "Ungraded Students", "Grades 1-8 Students", "Grades 9-12 Students"
]

POSSIBLE_PLACE_COLUMNS = [
    "school_state_code","ZIP",".*County.*",".*School.*", ".*Lowest.*", ".*Highest.*",
    "Physical.*", "Phone.*",  "Coeducational", ".*Level.*",".*State.*"
]

EXCLUDE_PLACE_COLUMNS = [
    "State Name","County Name", "Total Students", "Prekindergarten and Kindergarten Students",
    "Grades 1-8 Students", "Grades 9-12 Students", "Prekindergarten Students",
    "Kindergarten Students", "Grade 1 Students", "Grade 2 Students",
    "School Community Type", "Grade 3 Students", "Grade 4 Students",
    "Grade 5 Students", "Grade 6 Students", "Grade 7 Students",
    "Grade 8 Students", "Grade 9 Students", "Grade 10 Students",
    "Grade 11 Students", "Grade 12 Students", "Ungraded Students",
    "Percentage of Black Students", "American Indian/Alaska Native Students",
    "Percentage of American Indian/Alaska Native Students",
    "Asian or Asian/Pacific Islander Students",
    "Percentage of Asian or Asian/Pacific Islander Students",
    "Hispanic Students", "Percentage of Hispanic Students",
    "Black or African American Students", "White Students",
    "Percentage of White Students",
    "Nat. Hawaiian or Other Pacific Isl. Students",
    "Percentage of Nat. Hawaiian or Other Pacific Isl. Students",
    "Two or More Races Students", "Percentage of Two or More Races Students",
    "Pupil/Teacher Ratio", "Full-Time Equivalent", "year"
]
