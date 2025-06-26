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
Constant value used in processing US Tract are defined here.
This module also consists of mapping between various forms of column names
found in downloaded files and its corresponding SV name.
While preprocessing files column names are changed to SV names as used in
DC import
"""
# TMCF template for Demographics data. It changes based on import name.
TMCF_TEMPLATE = (
    "Node: E:us_nces_demographics_{import_name}->E0\n"
    "typeOf: dcs:StatVarObservation\n"
    "variableMeasured: C:us_nces_demographics_{import_name}->sv_name\n"
    "measurementMethod: dcs:US_NCES_Demographics\n"
    "observationAbout: C:us_nces_demographics_{import_name}->school_state_code\n"
    "observationDate: C:us_nces_demographics_{import_name}->year\n"
    "scalingFactor: C:us_nces_demographics_{import_name}->scaling_factor\n"
    "unit: C:us_nces_demographics_{import_name}->unit\n"
    "observationPeriod: \"{observation_period}\"\n"
    "value: C:us_nces_demographics_{import_name}->observation\n")

# TMCF template for Private School Place.
TMCF_TEMPLATE_PLACE_PRIVATE = (
    "Node: E:us_nces_demographics_private_place->E0\n"
    "dcid: C:us_nces_demographics_private_place->school_state_code\n"
    "typeOf: dcs:PrivateSchool\n"
    "address: C:us_nces_demographics_private_place->Physical_Address\n"
    "name: C:us_nces_demographics_private_place->Private_School_Name\n"
    "ncesId: C:us_nces_demographics_private_place->SchoolID\n"
    "lowestGrade: C:us_nces_demographics_private_place->Lowest_Grade\n"
    "highestGrade: C:us_nces_demographics_private_place->Highest_Grade\n"
    "schoolGradeLevel: C:us_nces_demographics_private_place->SchoolGrade\n"
    "containedInPlace: C:us_nces_demographics_private_place->ContainedInPlace\n"
    "telephone: C:us_nces_demographics_private_place->PhoneNumber\n"
    "educationalMethod: C:us_nces_demographics_private_place->School_Type\n"
    "religiousOrientation: C:us_nces_demographics_private_place->School_Religion\n"
    "coeducationStatus: C:us_nces_demographics_private_place->Coeducational\n")

# TMCF template for School District Place.
TMCF_TEMPLATE_PLACE_DISTRICT = (
    "Node: E:us_nces_demographics_district_place->E0\n"
    "dcid: C:us_nces_demographics_district_place->school_state_code\n"
    "typeOf: dcs:SchoolDistrict\n"
    "address: C:us_nces_demographics_district_place->Physical_Address\n"
    "name: C:us_nces_demographics_district_place->District_School_name\n"
    "geoId: C:us_nces_demographics_district_place->geoID\n"
    "ncesId: C:us_nces_demographics_district_place->School_ID\n"
    "postalCode: C:us_nces_demographics_district_place->ZIP\n"
    "containedInPlace: C:us_nces_demographics_district_place->ContainedInPlace\n"
    "schoolStateID: C:us_nces_demographics_district_place->State_school_ID\n"
    "telephone: C:us_nces_demographics_district_place->PhoneNumber\n"
    "lowestGrade: C:us_nces_demographics_district_place->Lowest_Grade_Dist\n"
    "highestGrade: C:us_nces_demographics_district_place->Highest_Grade_Dist\n"
    "longitude: C:us_nces_demographics_district_place->Longitude\n"
    "latitude: C:us_nces_demographics_district_place->Latitude\n"
    "ncesLocale: C:us_nces_demographics_district_place->Locale\n"
    "schoolManagement: C:us_nces_demographics_district_place->School_Management\n"
)

# TMCF template for Public School Place.
TMCF_TEMPLATE_PLACE_PUBLIC = (
    "Node: E:us_nces_demographics_public_place->E0\n"
    "dcid: C:us_nces_demographics_public_place->school_state_code\n"
    "typeOf: dcs:PublicSchool\n"
    "address: C:us_nces_demographics_public_place->Physical_Address\n"
    "name: C:us_nces_demographics_public_place->Public_School_Name\n"
    "ncesId: C:us_nces_demographics_public_place->School_Id\n"
    "containedInPlace: C:us_nces_demographics_public_place->ContainedInPlace\n"
    "telephone: C:us_nces_demographics_public_place->PhoneNumber\n"
    "lowestGrade: C:us_nces_demographics_public_place->Lowest_Grade_Public\n"
    "highestGrade: C:us_nces_demographics_public_place->Highest_Grade_Public\n"
    "schoolGradeLevel: C:us_nces_demographics_public_place->School_Level\n"
    "educationalMethod: C:us_nces_demographics_public_place->School_Type_Public\n"
    "longitude: C:us_nces_demographics_public_place->Longitude\n"
    "latitude: C:us_nces_demographics_public_place->Latitude\n"
    "ncesLocale: C:us_nces_demographics_public_place->Locale\n"
    "magnetStatus: C:us_nces_demographics_public_place->Magnet_School\n"
    "titleISchoolStatus: C:us_nces_demographics_public_place->Title_I_School_Status\n"
    "charterStatus: C:us_nces_demographics_public_place->Charter_School\n"
    "nationalSchoolLunchProgram: C:us_nces_demographics_public_place->National_School_Lunch_Program\n"
    "schoolDistrict: C:us_nces_demographics_public_place->State_District_ID\n"
    "schoolStateID: C:us_nces_demographics_public_place->State_School_ID\n"
    "schoolManagement: C:us_nces_demographics_public_place->School_Management\n"
)

# Denominator Property for SVs which have percent or ratio.
_DENOMINATOR_PROP = {
    "Pupil/Teacher Ratio": "Count_Teacher",
    "Percent": "Count_Student"
}

# Property map to which the Faculty anf Teacher columns are considered.
_POPULATION_PROP = {
    "Full-Time Equivalent": "Teacher",
    "Elementary Teachers": "Teacher",
    "Prekindergarten Teachers": "Teacher",
    "Secondary Teachers": "Teacher",
    "Kindergarten Teachers": "Teacher",
    "Ungraded Teachers": "Teacher",
    "Paraprofessionals/Instructional Aides": "Faculty",
    "Instructional Coordinators": "Faculty",
    "Elementary School Counselor": "Faculty",
    "Secondary School Counselor": "Faculty",
    "Other Guidance Counselors": "Faculty",
    "Total Guidance Counselors": "Faculty",
    "Librarians/media specialists": "Faculty",
    "Media Support Staff": "Faculty",
    "LEA Administrators": "Faculty",
    "LEA Administrative Support Staff": "Faculty",
    "School Administrators": "Faculty",
    "School Administrative Support Staff": "Faculty",
    "Student Support Services Staff": "Faculty",
    "School Psychologist": "Faculty",
    "Other Support Services Staff": "Faculty"
}
# One specific column comes under school grade property.
_SCHOOL_GRADE_PROP = {"Ungraded Students": "NCESUngradedClasses"}
# melting the columns based on sv_name column.
MELT_VAR_COL = "sv_name"

# pylint:disable=unnecessary-lambda-assignment
# Creating property pattern and the pattern is modified if required based on column.
_PV_FORMAT = lambda prop_val: f'"{prop_val[0]}": "dcs:{prop_val[1]}"' \
                        if 'None' not in prop_val[1] else ""
_UPDATE_MEASUREMENT_DENO = lambda prop: _DENOMINATOR_PROP.get(prop, prop)
_UPDATE_POPULATION_TYPE = lambda prop: _POPULATION_PROP.get(prop, "Student")
_UPDATE_GRADE_LEVEL = lambda prop: _SCHOOL_GRADE_PROP.get(prop, prop)
SV_NODE_FORMAT = lambda prop_val: f'Node: dcid:{prop_val}'
# pylint:enable=unnecessary-lambda-assignment
# Default property for every node.
DF_DEFAULT_MCF_PROP = [('statType', 'measuredValue', _PV_FORMAT),
                       ('measuredProperty', 'count', _PV_FORMAT),
                       ('typeOf', 'StatisticalVariable', _PV_FORMAT)]
# The order in which the property should be arranged.
SV_PROP_ORDER = [
    "measuredProperty", "populationType", "statType", "typeOf", "race",
    "schoolGradeLevel", "measurementDenominator", "gender", "lunchEligibility",
    "facultyType"
]
# Patterns of every property and its respective columns.
_RACE_PATTERN = (r"("
                 r"American Indian/Alaska Native"
                 r"|"
                 r"Asian or Asian/Pacific Islander"
                 r"|"
                 r"Hispanic"
                 r"|"
                 r"Black"
                 r"|"
                 r"Two or More Races"
                 r"|"
                 r"Nat. Hawaiian or Other Pacific Isl."
                 r"|"
                 r"White"
                 r")")

_SCHOOL_GRADE_PATTERN = (r"("
                         r"Grade \d{,2}"
                         r"|"
                         r"Prekindergarten and Kindergarten"
                         r"|"
                         r"Kindergarten"
                         r"|"
                         r"Prekindergarten"
                         r"|"
                         r"Grades 1-8"
                         r"|"
                         r"Grades 9-12"
                         r"|"
                         r"Ungraded Students"
                         r"|"
                         r"Adult Education"
                         r")")

_DENOMINATOR_PATTERN = (r"("
                        r"Percent"
                        r"|"
                        r"Pupil/Teacher Ratio"
                        r")")

_POPULATION_TYPE_PATTERN = (r"("
                            r"Pupil/Teacher Ratio"
                            r"|"
                            r"Full-Time Equivalent"
                            r"|"
                            r"Student"
                            r"|"
                            r"Elementary Teachers"
                            r"|"
                            r"Secondary Teachers"
                            r"|"
                            r"Kindergarten Teachers"
                            r"|"
                            r"Prekindergarten Teachers"
                            r"|"
                            r"Ungraded Teachers"
                            r"|"
                            r"Paraprofessionals/Instructional Aides"
                            r"|"
                            r"Instructional Coordinators"
                            r"|"
                            r"Elementary School Counselor"
                            r"|"
                            r"Secondary School Counselor"
                            r"|"
                            r"Other Guidance Counselors"
                            r"|"
                            r"Total Guidance Counselors"
                            r"|"
                            r"Librarians/media specialists"
                            r"|"
                            r"Media Support Staff"
                            r"|"
                            r"LEA Administrators"
                            r"|"
                            r"LEA Administrative Support Staff"
                            r"|"
                            r"Student Support Services Staff"
                            r"|"
                            r"School Administrative Support Staff"
                            r"|"
                            r"School Administrators"
                            r"|"
                            r"School Psychologist"
                            r"|"
                            r"Other Support Services Staff"
                            r")")

_GENDER_PATTERN = (r"("
                   r"Female"
                   r"|"
                   r"female"
                   r"|"
                   r"Male"
                   r"|"
                   r"male"
                   r")")

_LUNCH_ELIGIBILITY_PATTERN = (r"("
                              r"Free Lunch"
                              r"|"
                              r"Reduced-price Lunch"
                              r"|"
                              r"Free and Reduced Lunch"
                              r")")

_SCHOOL_STAFF_PATTERN = (r"("
                         r"Paraprofessionals/Instructional Aides"
                         r"|"
                         r"Instructional Coordinators"
                         r"|"
                         r"Elementary School Counselor"
                         r"|"
                         r"Secondary School Counselor"
                         r"|"
                         r"Other Guidance Counselors"
                         r"|"
                         r"Total Guidance Counselors"
                         r"|"
                         r"Librarians/media specialists"
                         r"|"
                         r"Media Support Staff"
                         r"|"
                         r"LEA Administrators"
                         r"|"
                         r"LEA Administrative Support Staff"
                         r"|"
                         r"Student Support Services Staff"
                         r"|"
                         r"School Administrative Support Staff"
                         r"|"
                         r"School Administrators"
                         r"|"
                         r"School Psychologist"
                         r"|"
                         r"Elementary Teachers"
                         r"|"
                         r"Secondary Teachers"
                         r"|"
                         r"Ungraded Teachers"
                         r"|"
                         r"Other Support Services Staff"
                         r")")
# Based on the above patterns, properties are mapped to values.
FORM_STATVAR = {
    "race": {
        "regex": {
            "pattern": _RACE_PATTERN,
            "position": 1
        },
        "column": MELT_VAR_COL,
        "pv_format": _PV_FORMAT
    },
    "schoolGradeLevel": {
        "regex": {
            "pattern": _SCHOOL_GRADE_PATTERN,
            "position": 1
        },
        "column": MELT_VAR_COL,
        "update_value": _UPDATE_GRADE_LEVEL,
        "pv_format": _PV_FORMAT
    },
    "measurementDenominator": {
        "regex": {
            "pattern": _DENOMINATOR_PATTERN,
            "position": 1
        },
        "column": MELT_VAR_COL,
        "update_value": _UPDATE_MEASUREMENT_DENO,
        "pv_format": _PV_FORMAT
    },
    "populationType": {
        "regex": {
            "pattern": _POPULATION_TYPE_PATTERN,
            "position": 1
        },
        "column": MELT_VAR_COL,
        "update_value": _UPDATE_POPULATION_TYPE,
        "pv_format": _PV_FORMAT
    },
    "gender": {
        "regex": {
            "pattern": _GENDER_PATTERN,
            "position": 1
        },
        "column": MELT_VAR_COL,
        "pv_format": _PV_FORMAT
    },
    "lunchEligibility": {
        "regex": {
            "pattern": _LUNCH_ELIGIBILITY_PATTERN,
            "position": 1
        },
        "column": MELT_VAR_COL,
        "pv_format": _PV_FORMAT
    },
    "facultyType": {
        "regex": {
            "pattern": _SCHOOL_STAFF_PATTERN,
            "position": 1
        },
        "column": MELT_VAR_COL,
        "pv_format": _PV_FORMAT
    }
}
