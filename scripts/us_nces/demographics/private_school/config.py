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
    r"\(Ungraded & K-12\)",
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

# PSS grade code (LOGRYYYY / HIGRYYYY) to ELSI grade label mapping.
PSS_GRADE_CODE_MAP = {
    "1": "All Ungraded",
    "2": "Prekindergarten",
    "3": "Kindergarten",
    "4": "Transitional Kindergarten",
    "5": "Transitional 1st grade",
    "6": "1st grade",
    "7": "2nd grade",
    "8": "3rd grade",
    "9": "4th grade",
    "10": "5th grade",
    "11": "6th grade",
    "12": "7th grade",
    "13": "8th grade",
    "14": "9th grade",
    "15": "10th grade",
    "16": "11th grade",
    "17": "12th grade",
}

# PSS coeducational status (P335) to ELSI label mapping.
PSS_COED_MAP = {
    "1": "1-Coed (school has male and female students)",
    "2": "2-All-female (school only has all-female students)",
    "3": "3-All-male (school only has all-male students)",
}

# PSS school program type (P415) to ELSI label mapping.
PSS_SCHOOL_TYPE_MAP = {
    "1": "1-Regular Elementary or Secondary",
    "2": "2-Montessori",
    "3": "3-Special Program Emphasis",
    "4": "4-Special Education",
    "5": "5-Career/technical/vocational",
    "6": "6-Alternative/other",
    "7": "7-Early Childhood Program/child care center",
}

# PSS school level (LEVEL) to ELSI label mapping.
PSS_SCHOOL_LEVEL_MAP = {
    "1":
        "1-Elementary (school has one or more of grades K-6 and does not have any grade higher than the 8th grade).",
    "2":
        "2-Secondary (school has one or more of grades 7-12 and does not have any grade lower than 7th grade).",
    "3":
        "3-Combined (school has one or more of grades K-6 and one or more of grades 9-12. Schools in which all students are ungraded are also classified as combined).",
}

# PSS religious affiliation summary (RELIG) to ELSI label mapping.
PSS_RELIG_AFFIL_MAP = {
    "1": "1-Catholic",
    "2": "2-Other religious",
    "3": "3-Nonsectarian",
}

# PSS religious orientation code (ORIENT) to ELSI label mapping.
# Note exact Unicode en-dash (\u2013) for codes "20" and "28".
PSS_ORIENT_MAP = {
    "1":
        "Roman Catholic",
    "2":
        "African Methodist Episcopal",
    "3":
        "Amish",
    "4":
        "Assembly of God",
    "5":
        "Baptist",
    "6":
        "Brethren",
    "7":
        "Calvinist",
    "8":
        "Christian (no specific denomination)",
    "9":
        "Church of Christ",
    "10":
        "Church of God",
    "11":
        "Church of God in Christ",
    "12":
        "Church of the Nazarene",
    "13":
        "Disciples of Christ",
    "14":
        "Episcopal",
    "15":
        "Friends",
    "16":
        "Greek Orthodox",
    "17":
        "Islamic",
    "18":
        "Jewish",
    "19":
        "Latter Day Saints",
    "20":
        "Lutheran Church \u2013 Missouri Synod",
    "21":
        "Evangelical Lutheran Church in America (formerly AELC or ALC or LCA)",
    "22":
        "Wisconsin Evangelical Lutheran Synod",
    "23":
        "Other Lutheran",
    "24":
        "Mennonite",
    "25":
        "Methodist",
    "26":
        "Pentecostal",
    "27":
        "Presbyterian",
    "28":
        "Seventh\u2013Day Adventist",
    "29":
        "Other",
    "30":
        "Nonsectarian",
}

# PSS community type (UCOMMTYP) to ELSI label mapping.
PSS_COMM_TYPE_MAP = {
    "1": "1-City (ulocale = 11 or 12 or 13)",
    "2": "2-Suburb (ulocale = 21 or 22 or 23)",
    "3": "3-Town (ulocale = 31 or 32 or 33)",
    "4": "4-Rural (ulocale = 41 or 42 or 43)",
}

# ANSI/FIPS state code (PSTANSI) to uppercase state name mapping.
PSS_STATE_FIPS_TO_NAME = {
    "01": "ALABAMA",
    "02": "ALASKA",
    "04": "ARIZONA",
    "05": "ARKANSAS",
    "06": "CALIFORNIA",
    "08": "COLORADO",
    "09": "CONNECTICUT",
    "10": "DELAWARE",
    "11": "DISTRICT OF COLUMBIA",
    "12": "FLORIDA",
    "13": "GEORGIA",
    "15": "HAWAII",
    "16": "IDAHO",
    "17": "ILLINOIS",
    "18": "INDIANA",
    "19": "IOWA",
    "20": "KANSAS",
    "21": "KENTUCKY",
    "22": "LOUISIANA",
    "23": "MAINE",
    "24": "MARYLAND",
    "25": "MASSACHUSETTS",
    "26": "MICHIGAN",
    "27": "MINNESOTA",
    "28": "MISSISSIPPI",
    "29": "MISSOURI",
    "30": "MONTANA",
    "31": "NEBRASKA",
    "32": "NEVADA",
    "33": "NEW HAMPSHIRE",
    "34": "NEW JERSEY",
    "35": "NEW MEXICO",
    "36": "NEW YORK",
    "37": "NORTH CAROLINA",
    "38": "NORTH DAKOTA",
    "39": "OHIO",
    "40": "OKLAHOMA",
    "41": "OREGON",
    "42": "PENNSYLVANIA",
    "44": "RHODE ISLAND",
    "45": "SOUTH CAROLINA",
    "46": "SOUTH DAKOTA",
    "47": "TENNESSEE",
    "48": "TEXAS",
    "49": "UTAH",
    "50": "VERMONT",
    "51": "VIRGINIA",
    "53": "WASHINGTON",
    "54": "WEST VIRGINIA",
    "55": "WISCONSIN",
    "56": "WYOMING",
    "60": "AMERICAN SAMOA",
    "66": "GUAM",
    "69": "NORTHERN MARIANA ISLANDS",
    "72": "PUERTO RICO",
    "78": "VIRGIN ISLANDS",
}

# Ordered 58-column ELSI schema template (parameterized by {school_year}).
ELSI_58_COLUMN_TEMPLATE = [
    "Private School Name",
    "State Name [Private School] Latest available year",
    "State Name [Private School] {school_year}",
    "ANSI/FIPS State Code [Private School] Latest available year",
    "Private School Name [Private School] {school_year}",
    "School ID - NCES Assigned [Private School] Latest available year",
    "County Name [Private School] {school_year}",
    "ANSI/FIPS County Code [Private School] {school_year}",
    "Phone Number [Private School] {school_year}",
    "Physical Address [Private School] {school_year}",
    "City [Private School] {school_year}",
    "State Abbr [Private School] Latest available year",
    "ZIP [Private School] {school_year}",
    "ZIP + 4 [Private School] {school_year}",
    "Lowest Grade Taught [Private School] {school_year}",
    "Highest Grade Taught [Private School] {school_year}",
    "Coeducational [Private School] {school_year}",
    "School Type [Private School] {school_year}",
    "School Level [Private School] {school_year}",
    "School's Religious Affiliation or Orientation [Private School] {school_year}",
    "School Community Type [Private School] {school_year}",
    "Religious Orientation [Private School] {school_year}",
    "Total Students (Ungraded & PK-12) [Private School] {school_year}",
    "Total Students (Ungraded & K-12) [Private School] {school_year}",
    "Prekindergarten and Kindergarten Students [Private School] {school_year}",
    "Grades 1-8 Students [Private School] {school_year}",
    "Grades 9-12 Students [Private School] {school_year}",
    "Prekindergarten Students [Private School] {school_year}",
    "Kindergarten Students [Private School] {school_year}",
    "Grade 1 Students [Private School] {school_year}",
    "Grade 2 Students [Private School] {school_year}",
    "Grade 3 Students [Private School] {school_year}",
    "Grade 4 Students [Private School] {school_year}",
    "Grade 5 Students [Private School] {school_year}",
    "Grade 6 Students [Private School] {school_year}",
    "Grade 7 Students [Private School] {school_year}",
    "Grade 8 Students [Private School] {school_year}",
    "Grade 9 Students [Private School] {school_year}",
    "Grade 10 Students [Private School] {school_year}",
    "Grade 11 Students [Private School] {school_year}",
    "Grade 12 Students [Private School] {school_year}",
    "Ungraded Students [Private School] {school_year}",
    "American Indian/Alaska Native Students [Private School] {school_year}",
    "Percentage of American Indian/Alaska Native Students [Private School] {school_year}",
    "Asian or Asian/Pacific Islander Students [Private School] {school_year}",
    "Percentage of Asian or Asian/Pacific Islander Students [Private School] {school_year}",
    "Hispanic Students [Private School] {school_year}",
    "Percentage of Hispanic Students [Private School] {school_year}",
    "Black or African American Students [Private School] {school_year}",
    "Percentage of Black Students [Private School] {school_year}",
    "White Students [Private School] {school_year}",
    "Percentage of White Students [Private School] {school_year}",
    "Nat. Hawaiian or Other Pacific Isl. Students [Private School] {school_year}",
    "Percentage of Nat. Hawaiian or Other Pacific Isl. Students [Private School] {school_year}",
    "Two or More Races Students [Private School] {school_year}",
    "Percentage of Two or More Races Students [Private School] {school_year}",
    "Pupil/Teacher Ratio [Private School] {school_year}",
    "Full-Time Equivalent (FTE) Teachers [Private School] {school_year}",
]

# Cross-year lowercase column aliases across 1997-2023 PSS public-use files.
PSS_COLUMN_ALIASES = {
    "ppin": ["ppin", "rpin", "spin"],
    "pinst": ["pinst", "rinst", "sinst"],
    "paddrs": ["paddrs", "raddrs", "saddrs"],
    "pcity": ["pcity", "rcity", "scity"],
    "pstabb": ["pstabb", "rstabb", "sstabb"],
    "pstansi": ["pstansi", "pstfip", "rstfip", "sstfips"],
    "pcnty": ["pcnty", "rcnty", "scnty"],
    "pcntnm": ["pcntnm", "rcntnm", "scntynm"],
    "pzip": ["pzip", "rzip", "szip"],
    "pzip4": ["pzip4", "rzip4", "szip4"],
    "pphone": ["pphone", "rphone", "sphone"],
    "ucommtyp": ["ucommtyp", "commtype"],
    "p316": ["p316", "p315"],
    "f_p316": ["f_p316", "f_p315"],
    "p_tr": ["p_tr", "p_two"],
}
