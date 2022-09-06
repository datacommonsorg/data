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

MELT_VAR_COL = "sv_name"
# _PV_FORMAT1 = lambda prop_val: print("1", prop_val[0], "2", prop_val[1]) if 'None' not in prop_val[1] else ""
_PV_FORMAT = lambda prop_val: f'"{prop_val[0]}": "dcs:{prop_val[1]}"' if 'None' not in prop_val[1] else ""

DF_DEFAULT_MCF_PROP = [
    ('statType', 'measuredValue', _PV_FORMAT),
    ('populationType', 'Student', _PV_FORMAT),
    ('measuredProperty', 'count', _PV_FORMAT),
]

SV_NODE_FORMAT = lambda prop_val: f'Node: dcid:{prop_val}'

SV_PROP_ORDER = [
    "measuredProperty","populationType", "statType","race","schoolGradeLevel"
]

FORM_STATVAR = {
    "race": {
        "regex": {
            "pattern": r"(AmericanIndianOrAlaskaNative|AsianOrPacificIslander|BlackOrAfricanAmericanAlone|HawaiianNativeOrPacificIslander|HispanicOrLatino|TwoOrMoreRaces|White)",
            "position": 1
        },
        "column": MELT_VAR_COL,
        "pv_format": _PV_FORMAT
    },
    "schoolGradeLevel": {
        "regex": {
            "pattern": r"(SchoolGrade\d{,2})",
            "position": 1
        },
        "column": MELT_VAR_COL,
        "pv_format": _PV_FORMAT
    }
}