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
import re

_HOUSEHOLD_PV = "[Person {person}]"

_NUM_OF_VEHICLES_PV = "[AvailableVehicles {vehicle}]"

# pylint: disable=unnecessary-lambda-assignment
_PV_FORMAT = lambda prop_key, prop_val: f"{prop_key}: dcs:{prop_val}"
_PV_FORMAT_NUMBERS = lambda prop_key, prop_val: f"{prop_key}: {prop_val}"

_MEASURED_PROP_PATTERN = (r"("
                          "VehicleMilesTraveled|"
                          "VehicleTrips|"
                          "PersonMilesTraveled|"
                          "PersonTrips"
                          ")")
_MEASURED_PROP_REGEX = lambda prop: re.search(_MEASURED_PROP_PATTERN, prop) \
                                   .group(0)
_MEASURED_PROP = lambda prop: prop[0].lower() + prop[1:]

_HOUSEHOLD_REGEX = lambda prop: re.search(r"(\d)(Persons)", prop).group(1)
_HOUSEHOLD_PROP = lambda prop: _HOUSEHOLD_PV.format(person=prop)

_NOOFVEHICLES_REGEX = lambda prop: re.search(r"(With)(\d)(AvailableVehicles)",
                                             prop).group(2)
_NOOFVEHICLES_PROP = lambda prop: _NUM_OF_VEHICLES_PV.format(vehicle=prop)

_PLACE_REGEX = lambda prop: re.search(r"(SemiUrban|Rural|Urban)", prop).group(0)
_DEFAULT_PROP = lambda prop: prop
# pylint: enable=unnecessary-lambda-assignment

MCF_TEMPLATE_MAPPER = {
    "PersonMilesTraveled": {
        "regex": _MEASURED_PROP_REGEX,
        "key": "measuredProperty",
        "value": _MEASURED_PROP,
        "format": _PV_FORMAT
    },
    "PersonTrips": {
        "regex": _MEASURED_PROP_REGEX,
        "key": "measuredProperty",
        "value": _MEASURED_PROP,
        "format": _PV_FORMAT
    },
    "VehicleTrips": {
        "regex": _MEASURED_PROP_REGEX,
        "key": "measuredProperty",
        "value": _MEASURED_PROP,
        "format": _PV_FORMAT
    },
    "VehicleMilesTraveled": {
        "regex": _MEASURED_PROP_REGEX,
        "key": "measuredProperty",
        "value": _MEASURED_PROP,
        "format": _PV_FORMAT
    },
    "Persons": {
        "regex": _HOUSEHOLD_REGEX,
        "key": "householdSize",
        "value": _HOUSEHOLD_PROP,
        "format": _PV_FORMAT_NUMBERS
    },
    "AvailableVehicles": {
        "regex": _NOOFVEHICLES_REGEX,
        "key": "numberOfVehicles",
        "value": _NOOFVEHICLES_PROP,
        "format": _PV_FORMAT_NUMBERS
    },
    "Urban": {
        "regex": _PLACE_REGEX,
        "key": "placeOfResidenceClassification",
        "value": _DEFAULT_PROP,
        "format": _PV_FORMAT
    },
    "Rural": {
        "regex": _PLACE_REGEX,
        "key": "placeOfResidenceClassification",
        "value": _DEFAULT_PROP,
        "format": _PV_FORMAT
    }
}
