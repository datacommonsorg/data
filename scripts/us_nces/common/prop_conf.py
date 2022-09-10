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
Constant value used in processing US Tract are defined here.
This module also consists of mapping between various forms of column names
found in downloaded files and its corresponding SV name.
While preprocessing files column names are changed to SV names as used in
DC import
"""
_DENOMINATOR_PROP = {
    "Pupil/Teacher Ratio": "Count_Teacher",
    "Percent": "Count_Student"
}

_POPULATION_PROP = {"Full-Time Equivalent": "Teacher"}
MELT_VAR_COL = "sv_name"

# pylint:disable=unnecessary-lambda-assignment
_PV_FORMAT = lambda prop_val: f'"{prop_val[0]}": "dcs:{prop_val[1]}"' \
                        if 'None' not in prop_val[1] else ""
_UPDATE_MEASUREMENT_DENO = lambda prop: _DENOMINATOR_PROP.get(prop, prop)
_UPDATE_POPULATION_TYPE = lambda prop: _POPULATION_PROP.get(prop, "Student")
SV_NODE_FORMAT = lambda prop_val: f'Node: dcid:{prop_val}'
# pylint:enable=unnecessary-lambda-assignment

DF_DEFAULT_MCF_PROP = [('statType', 'measuredValue', _PV_FORMAT),
                       ('measuredProperty', 'count', _PV_FORMAT)]

SV_PROP_ORDER = [
    "measuredProperty", "populationType", "statType", "race",
    "schoolGradeLevel", "measurementDenominator", "gender", "lunchEligibility"
]

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
                         r"Kindergarten"
                         r"|"
                         r"Prekindergarten"
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

_LUNCH_ELIGIBITY_PATTERN = (r"("
                            r"Free Lunch"
                            r"|"
                            r"Reduced-price Lunch"
                            r"|"
                            r"Free and Reduced Lunch"
                            r")")

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
            "pattern": _LUNCH_ELIGIBITY_PATTERN,
            "position": 1
        },
        "column": MELT_VAR_COL,
        "pv_format": _PV_FORMAT
    }
}
