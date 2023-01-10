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
CSV_FILE_PLACE = "us_nces_demographics_district_place.csv"
CSV_DUPLICATE_NAME = "dulicate_id_us_nces_demographics_district_place.csv"
TMCF_FILE_PLACE = "us_nces_demographics_district_place.tmcf"
SCHOOL_TYPE = "district_school"
OBSERVATION_PERIOD = "P1Y"
SPLIT_HEADER_ON_SCHOOL_TYPE = "[District]"

POSSIBLE_DATA_COLUMNS = [
    "[Public School]", ".*Students.*", ".*Teacher.*", ".*American.*",
    ".*Asian.*", ".*Hispanic.*", ".*Black.*", ".*White.*", ".*Adult Education.*"
    ".*Staff.*", ".*Admin.*", ".*Counselor.*", ".*Psychologist.*", "Ungraded.*",
    "Two or More Races.*", "Nat. Hawaiian or Other Pacific Isl.*", "Grades.*",
    "Prekindergarten and Kindergarten.*"
]

EXCLUDE_DATA_COLUMNS = [
    "Individualized Education Program Students", '(Includes AE)',
    "Phone Number", "State Agency ID", "State Name"
]

POSSIBLE_PLACE_COLUMNS = [
    "school_state_code", ".*ZIP.*", ".*County.*", ".*Agency.*", "Physical.*",
    "Phone.*", "Coeducational", ".*Level.*", ".*State.*", "Latitude.*",
    "Longitude.*", "Locale.*", "Location.*", "Lowest.*", "Highest.*"
]

EXCLUDE_PLACE_COLUMNS = [
    "Metro Micro Area Code", "Location Address 2", "Location Address 3",
    ".*Congress.*", "Mailing ZIP"
]

PLACE_KEY_COLUMNS = ["year", "Agency ID - NCES Assigned"]

EXCLUDE_LIST = [
    'school_state_code', 'Agency Name', 'Agency ID - NCES Assigned',
    'ANSI/FIPS State Code'
]

DROP_BY_VALUE = "Agency ID - NCES Assigned"

RENAMING_DISTRICT_COLUMNS = {
    'Location ZIP': 'ZIP',
    'County Number': 'County_code',
    'Agency Name': 'District_School_name',
    'Agency ID - NCES Assigned': 'School_ID',
    'Agency Type': 'School_Type',
    'State Agency ID': 'State_school_ID',
    'Phone Number': 'PhoneNumber',
    'ANSI/FIPS State Code': 'State_code',
    'Location Address 1': 'Physical_Address',
    'Location City': 'City',
    'Agency Level (SY 2017-18 onward)': 'Agency_level',
    "Lowest Grade Offered": "Lowest_Grade_Dist",
    "Highest Grade Offered": "Highest_Grade_Dist",
    "State Name": "State_Name",
    "Location ZIP4": "Location_ZIP4",
    "State Abbr": "State_Abbr"
}