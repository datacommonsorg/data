# Copyright 2025 Google LLC
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
for us nces demographic public school.
"""
# Defining file names.
CSV_FILE_NAME = "us_nces_demographics_public_school.csv"
MCF_FILE_NAME = "us_nces_demographics_public_school.mcf"
TMCF_FILE_NAME = "us_nces_demographics_public_school.tmcf"
CSV_FILE_PLACE = "us_nces_demographics_public_place.csv"
CSV_DUPLICATE_NAME = "dulicate_id_us_nces_demographics_public_place.csv"
TMCF_FILE_PLACE = "us_nces_demographics_public_place.tmcf"
SCHOOL_TYPE = "public_school"
OBSERVATION_PERIOD = "P1Y"
SPLIT_HEADER_ON_SCHOOL_TYPE = "[Public School]"
# Considering the required columns for Demographics Data.
POSSIBLE_DATA_COLUMNS = [
    ".*Students.*", ".*Lunch.*", ".*Teacher.*", ".*American.*", ".*Asian.*",
    ".*Hispanic.*", ".*Black.*", ".*White.*", ".*Adult Education.*",
    "Ungraded.*", "Two or More Races.*", "Nat. Hawaiian or Other Pacific Isl.*"
]
# Excluding the unwanted columns.
EXCLUDE_DATA_COLUMNS = [
    'Migrant Students', '(Includes AE)',
    'Total Students - Calculated Sum of Reported Grade Totals', 'Unknown',
    'unknown', 'Total Race/Ethnicity', 'Agency ID - NCES Assigned'
]
# Considering the required columns for Place Data.
POSSIBLE_PLACE_COLUMNS = [
    "school_state_code", "ZIP", ".*County.*", ".*School.*", ".*Lowest.*",
    ".*Highest.*", "Physical.*", "Phone.*", "Coeducational", ".*Level.*",
    ".*State.*", "Latitude.*", "Longitude.*", "Locale.*", "Location.*",
    "Charter.*", "Magnet.*", "Title.*", "Agency.*", "State Name"
]
# Excluding the unwanted columns.
EXCLUDE_PLACE_COLUMNS = ["Metro Micro Area Code"]
# Since Public school has multiple input file for one year, all the coulmns are
# merged based on the place_key_columns.
PLACE_KEY_COLUMNS = ["year", "School ID (12-digit) - NCES Assigned"]
# Set of columns to exclude while checking for duplicate School IDs
EXCLUDE_LIST = [
    'school_state_code', 'School Name', 'School ID (12-digit) - NCES Assigned',
    'ANSI/FIPS State Code'
]
# Dropping the Duplicate entries based on School ID
DROP_BY_VALUE = "School ID (12-digit) - NCES Assigned"
# Renaming column name.
RENAMING_PUBLIC_COLUMNS = {
    'County Number': 'County_code',
    'School Name': 'Public_School_Name',
    'School ID (12-digit) - NCES Assigned': 'School_Id',
    'Lowest Grade Offered': 'Lowest_Grade_Public',
    'Highest Grade Offered': 'Highest_Grade_Public',
    'Phone Number': 'PhoneNumber',
    'ANSI/FIPS State Code': 'State_code',
    'Location Address 1': 'Physical_Address',
    'Location City': 'City',
    'Location ZIP': 'ZIP',
    'Magnet School': 'Magnet_School',
    'Charter School': 'Charter_School',
    'School Type': 'School_Type_Public',
    'Title I School Status': 'Title_I_School_Status',
    'National School Lunch Program': 'National_School_Lunch_Program',
    'School Level (SY 2017-18 onward)': 'School_Level_17',
    'State School ID': 'State_School_ID',
    'State Agency ID': 'State_Agency_ID',
    'State Abbr': 'State_Abbr',
    'Agency Name': 'Agency_Name',
    'Location ZIP4': 'Location_ZIP4',
    'Agency ID - NCES Assigned': 'State_District_ID',
    'School Level': 'School_Level_16',
    'State Name': 'State_Name'
}
