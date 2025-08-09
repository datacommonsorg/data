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
# Defining file names.
CSV_FILE_NAME = "us_nces_demographics_private_school.csv"
MCF_FILE_NAME = "us_nces_demographics_private_school.mcf"
TMCF_FILE_NAME = "us_nces_demographics_private_school.tmcf"
CSV_FILE_PLACE = "us_nces_demographics_private_place.csv"
TMCF_FILE_PLACE = "us_nces_demographics_private_place.tmcf"
CSV_DUPLICATE_NAME = "dulicate_id_us_nces_demographics_private_place.csv"
SCHOOL_TYPE = "private_school"
OBSERVATION_PERIOD = "P2Y"
SPLIT_HEADER_ON_SCHOOL_TYPE = "[Private School]"

# Considering the required columns for Demographics Data.
POSSIBLE_DATA_COLUMNS = [
    ".*Students.*", ".*Teacher.*", "Percentage.*", ".*Ungraded.*", "Grades.*",
    "Prekindergarten and Kindergarten.*"
]
# Excluding the unwanted columns.
EXCLUDE_DATA_COLUMNS = [
    "(Ungraded & K-12)",
]
# Considering the required columns for Place Data.
POSSIBLE_PLACE_COLUMNS = [
    "school_state_code", "ZIP + 4", "ZIP", ".*County.*", ".*School.*",
    "Lowest Grade.*", "Highest Grade.*", "Physical.*", "Phone.*",
    "Coeducational", "School Level.*", ".*State.*", "City.*", "Religious.*"
]
# Excluding the unwanted columns.
EXCLUDE_PLACE_COLUMNS = [
    "State Name", "County Name", "Total Students",
    "Prekindergarten and Kindergarten Students", "Grades 1-8 Students",
    "Grades 9-12 Students", "Prekindergarten Students", "Kindergarten Students",
    "Grade 1 Students", "Grade 2 Students", "School Community Type",
    "Grade 3 Students", "Grade 4 Students", "Grade 5 Students",
    "Grade 6 Students", "Grade 7 Students", "Grade 8 Students",
    "Grade 9 Students", "Grade 10 Students", "Grade 11 Students",
    "Grade 12 Students", "Ungraded Students", "Percentage of Black Students",
    "American Indian/Alaska Native Students",
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
# Set of columns to exclude while checking for duplicate School IDs
EXCLUDE_LIST = [
    "school_state_code", "Private School Name", "ANSI/FIPS State Code",
    "School ID - NCES Assigned", "State Abbr"
]
# Dropping the Duplicate entries based on School ID
DROP_BY_VALUE = "School ID - NCES Assigned"
# Renaming column name.
RENAMING_PRIVATE_COLUMNS = {
    "Private School Name":
        "Private_School_Name",
    "School ID - NCES Assigned":
        "SchoolID",
    "School Type":
        "School_Type",
    "School's Religious Affiliation or Orientation":
        "School_Religion_Affiliation",
    "Religious Orientation":
        "School_Religion",
    "Physical Address":
        "Physical_Address",
    "Phone Number":
        "PhoneNumber",
    "Lowest Grade Taught":
        "Lowest_Grade",
    "Highest Grade Taught":
        "Highest_Grade",
    "School Level":
        "SchoolGrade",
    "ZIP + 4":
        "ZIP4",
    "ANSI/FIPS County Code":
        "County_code",
    "ANSI/FIPS State Code":
        "State_code",
    "State Abbr":
        "State_Abbr"
}