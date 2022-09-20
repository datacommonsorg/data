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

_PV_FORMAT = lambda prop_val: f'"{prop_val[0]}": "dcs:{prop_val[1]}"' \
                        if 'None' not in prop_val[1] else ""

_PV_FORMAT_WITHOUT_DCS = lambda prop_val: f'"{prop_val[0]}": "{prop_val[1]}"' \
                        if 'None' not in prop_val[1] else ""

_PV_FORMAT_WITHOUT_ZIP = lambda prop_val: f'"{prop_val[0]}": "zip/{prop_val[1]}"' \
                        if 'None' not in prop_val[1] else ""

DF_DEFAULT_TMCF_PROP = [('typeOf', 'PrivateSchool', _PV_FORMAT_WITHOUT_DCS)]

SV_PROP_ORDER_PLACE = [ "dcid", "typeOf", "address",  "name",
    "ncesId", "containedInPlace", "telephone", "lowestGrade", "highestGrade", "schoolGradeLevel",
    "privateSchoolType", "schoolReligiousOrientation", "coeducationalType"
]

PLACE_STATVAR = {
    "lowestGrade": {
        "column": "Lowest Grade Taught",
        "pv_format": _PV_FORMAT_WITHOUT_DCS
    },
    "highestGrade": {
        "column": "Highest Grade Taught",
        "pv_format": _PV_FORMAT_WITHOUT_DCS
    },
    "name": {
        "column": "Private School Name",
        "pv_format": _PV_FORMAT_WITHOUT_DCS
    },
    "address": {
        "column": "Physical Address",
        "pv_format": _PV_FORMAT_WITHOUT_DCS
    },
    "telephone": {
        "column": "Phone Number",
        "pv_format": _PV_FORMAT_WITHOUT_DCS
    },
    "ncesId": {
        "column": "School ID - NCES Assigned",
        "pv_format": _PV_FORMAT_WITHOUT_DCS
    },
    "containedInPlace": {
        "column": "ZIP",
        "pv_format": _PV_FORMAT_WITHOUT_ZIP
    },
    "schoolGradeLevel": {
        "column": "School Level",
        "pv_format": _PV_FORMAT_WITHOUT_DCS
    },
    "privateSchoolType": {
        "column": "School Type",
        "pv_format": _PV_FORMAT_WITHOUT_DCS
    },
    "schoolReligiousOrientation": {
        "column": "School's Religious Affiliation or Orientation",
        "pv_format": _PV_FORMAT_WITHOUT_DCS
    },
    "coeducationalType": {
        "column": "Coeducational",
        "pv_format": _PV_FORMAT_WITHOUT_DCS
    },
    "dcid":{
        "column": "school_state_code",
        "pv_format": _PV_FORMAT_WITHOUT_DCS
    }
}