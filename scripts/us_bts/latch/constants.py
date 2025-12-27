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

INPUT_URLS_CONFIG = "input_urls_config.json"

BASE_URL = "base_url"

FILE_NAMES = "file_names"

DEFAULT_MEASUREMENT_METHOD = "NationalHouseholdTransportationSurveyEstimates"

ACS_SRUVEY_MEASUREMENT_METHOD = DEFAULT_MEASUREMENT_METHOD \
                                    + "_MarginOfErrorMoreThanACSSurvey"

DOWNLOAD_DIRECTORY = "input_files"

MELT_VAR_COL = "householdSize_numberOfVehicles"

MELT_OBV_COL = "observation"

_HOUSEHOLD_PV = "{person}"

_NUM_OF_VEHICLES_PV = "{vehicle}"

# pylint: disable=unnecessary-lambda-assignment
# pylint: disable=line-too-long
_PV_FORMAT = lambda prop_val: f'"{prop_val[0]}": "dcs:{prop_val[1]}"' if 'None' not in prop_val[
    1] else ""
_PV_FORMAT_NUMBERS = lambda prop_val: f'"{prop_val[0]}": "{prop_val[1]}"' if 'None' not in prop_val[
    1] else ""
SV_NODE_FORMAT = lambda prop_val: f'Node: dcid:{prop_val}'

_MEASURED_PROP = lambda prop: MEASUREDPROP_MAPPER[prop]

_HOUSEHOLD_PROP = lambda prop: _HOUSEHOLD_PV.format(person=prop)

_NOOFVEHICLES_PROP = lambda prop: _NUM_OF_VEHICLES_PV.format(vehicle=prop)

_DEFAULT_PROP = lambda prop: prop
# pylint: enable=unnecessary-lambda-assignment
# pylint: enable=line-too-long

URBAN_RURAL_MCF_NODE = (
    "Node: dcid:Place_Type_PlaceofResidenceClassification\n"
    "populationType: dcs:Place\n"
    "typeOf: dcs:StatisticalVariable\n"
    "statType: dcs:measurementResult\n"
    "measuredProperty: dcs:placeOfResidenceClassification\n")

TMCF_TEMPLATE = """Node: E:{filename}->E1
typeOf: dcs:StatVarObservation
variableMeasured: C:{filename}->sv
measurementMethod: C:{filename}->measurement_method
observationAbout: C:{filename}->location
observationDate: C:{filename}->year
value: C:{filename}->observation
"""

COMMON_COLS = [
    "ptrp_1mem_0veh", "ptrp_1mem_1veh", "ptrp_1mem_2veh", "ptrp_1mem_3veh",
    "ptrp_1mem_4veh", "ptrp_2mem_0veh", "ptrp_2mem_1veh", "ptrp_2mem_2veh",
    "ptrp_2mem_3veh", "ptrp_2mem_4veh", "ptrp_3mem_0veh", "ptrp_3mem_1veh",
    "ptrp_3mem_2veh", "ptrp_3mem_3veh", "ptrp_3mem_4veh", "ptrp_4mem_0veh",
    "ptrp_4mem_1veh", "ptrp_4mem_2veh", "ptrp_4mem_3veh", "ptrp_4mem_4veh",
    "pmiles_1mem_0veh", "pmiles_1mem_1veh", "pmiles_1mem_2veh",
    "pmiles_1mem_3veh", "pmiles_1mem_4veh", "pmiles_2mem_0veh",
    "pmiles_2mem_1veh", "pmiles_2mem_2veh", "pmiles_2mem_3veh",
    "pmiles_2mem_4veh", "pmiles_3mem_0veh", "pmiles_3mem_1veh",
    "pmiles_3mem_2veh", "pmiles_3mem_3veh", "pmiles_3mem_4veh",
    "pmiles_4mem_0veh", "pmiles_4mem_1veh", "pmiles_4mem_2veh",
    "pmiles_4mem_3veh", "pmiles_4mem_4veh", "vtrp_1mem_0veh", "vtrp_1mem_1veh",
    "vtrp_1mem_2veh", "vtrp_1mem_3veh", "vtrp_1mem_4veh", "vtrp_2mem_0veh",
    "vtrp_2mem_1veh", "vtrp_2mem_2veh", "vtrp_2mem_3veh", "vtrp_2mem_4veh",
    "vtrp_3mem_0veh", "vtrp_3mem_1veh", "vtrp_3mem_2veh", "vtrp_3mem_3veh",
    "vtrp_3mem_4veh", "vtrp_4mem_0veh", "vtrp_4mem_1veh", "vtrp_4mem_2veh",
    "vtrp_4mem_3veh", "vtrp_4mem_4veh", "vmiles_1mem_0veh", "vmiles_1mem_1veh",
    "vmiles_1mem_2veh", "vmiles_1mem_3veh", "vmiles_1mem_4veh",
    "vmiles_2mem_0veh", "vmiles_2mem_1veh", "vmiles_2mem_2veh",
    "vmiles_2mem_3veh", "vmiles_2mem_4veh", "vmiles_3mem_0veh",
    "vmiles_3mem_1veh", "vmiles_3mem_2veh", "vmiles_3mem_3veh",
    "vmiles_3mem_4veh", "vmiles_4mem_0veh", "vmiles_4mem_1veh",
    "vmiles_4mem_2veh", "vmiles_4mem_3veh", "vmiles_4mem_4veh"
]

ADDITIONAL_2009_FILE_COLS = [
    "ptrp_5mem_0veh", "ptrp_5mem_1veh", "ptrp_5mem_2veh", "ptrp_5mem_3veh",
    "ptrp_5mem_4veh", "pmiles_5mem_0veh", "pmiles_5mem_1veh",
    "pmiles_5mem_2veh", "pmiles_5mem_3veh", "pmiles_5mem_4veh",
    "vtrp_5mem_0veh", "vtrp_5mem_1veh", "vtrp_5mem_2veh", "vtrp_5mem_3veh",
    "vtrp_5mem_4veh", "vmiles_5mem_0veh", "vmiles_5mem_1veh",
    "vmiles_5mem_2veh", "vmiles_5mem_3veh", "vmiles_5mem_4veh"
]

FINAL_DATA_COLS = [
    "year", "location", "urban_group", "sv", "observation", "measurement_method"
]

MEASUREDPROP_MAPPER = {
    "pmiles": "personMilesTraveled",
    "ptrp": "personTrips",
    "vtrp": "vehicleTrips",
    "vmiles": "vehicleMilesTraveled",
}

ACS_LT_MOR = {0: '', 1: '_MarginOfErrorMoreThanACSSurvey'}

INCOMPLETE_ACS = {0: '', 1: '_IncompleteACSSurvey'}

URBAN = {1: "Urban", 2: "SemiUrban", 3: "Rural"}

RENAME_COLUMNS = {
    "geocode": "geoid",
    "pden_group_ua": "urban_group",
    "est_pmiles": "pmiles",
    "est_pmiles2007_11": "pmiles",
    "est_ptrp": "ptrp",
    "est_ptrp2007_11": "ptrp",
    "est_vtrp": "vtrp",
    "est_vtrp2007_11": "vtrp",
    "est_vmiles": "vmiles",
    "est_vmiles2007_11": "vmiles"
}

PADDING = {"width": 11, "side": "left", "fillchar": "0"}

CONF_2009_FILE = {
    "input_file_delimiter": ",",
    "basic_cols": ["geoid", "pden_group_ua"],
    "pop_cols": [
        "est_pmiles2007_11", "est_ptrp2007_11", "est_vmiles2007_11",
        "est_vtrp2007_11"
    ],
    "extra_cols": COMMON_COLS + ADDITIONAL_2009_FILE_COLS,
    "dtype_conv": {
        "urban_group": "int"
    },
    "col_values_mapper": {
        "urban_group": URBAN
    },
    "filters": {
        "dropna": ["urban_group"]
    },
    "year": 2009
}

CONF_2017_FILE = {
    "input_file_delimiter": ",",
    "basic_cols": [
        "geocode", "urban_group", "flag_acs_lt_moe", "flag_incomplete_acs",
        "flag_manhattan_trt"
    ],
    "pop_cols": ["est_pmiles", "est_ptrp", "est_vmiles", "est_vtrp"],
    "extra_cols": COMMON_COLS,
    "cols_for_measurement_method": ["flag_acs_lt_moe", "flag_incomplete_acs"],
    "dtype_conv": {
        "urban_group": "int"
    },
    "col_values_mapper": {
        "flag_acs_lt_moe": ACS_LT_MOR,
        "flag_incomplete_acs": INCOMPLETE_ACS,
        "urban_group": URBAN
    },
    "filters": {
        "equals": {
            "flag_manhattan_trt": 0
        },
        "dropna": ["urban_group"]
    },
    "additional_process": True,
    "year": 2017
}

DF_DEFAULT_MCF_PROP = [
    ('statType', 'meanValue', _PV_FORMAT),
    ('populationType', 'Household', _PV_FORMAT),
    ('typeOf', 'StatisticalVariable', _PV_FORMAT),
    ('measurementQualifier', 'EveryWeekday', _PV_FORMAT),
    ('transportationType', 'LocalAreaTransportation', _PV_FORMAT),
]

SV_PROP_ORDER = [
    "typeOf", "populationType", "statType", "measurementQualifier",
    "measuredProperty", "householdSize", "numberOfVehicles",
    "transportationType", "placeOfResidenceClassification"
]

FORM_STATVAR = {
    "placeOfResidenceClassification": {
        "column": "urban_group",
        "update_value": _DEFAULT_PROP,
        "pv_format": _PV_FORMAT
    },
    "numberOfVehicles": {
        "column": MELT_VAR_COL,
        "regex": {
            "pattern": r"(\d)(veh)",
            "position": 1
        },
        "update_value": _NOOFVEHICLES_PROP,
        "pv_format": _PV_FORMAT_NUMBERS
    },
    "householdSize": {
        "column": MELT_VAR_COL,
        "regex": {
            "pattern": r"(\d)(mem)",
            "position": 1
        },
        "update_value": _HOUSEHOLD_PROP,
        "pv_format": _PV_FORMAT_NUMBERS
    },
    "measuredProperty": {
        "column": MELT_VAR_COL,
        "regex": {
            "pattern": r"(pmiles|vtrp|ptrp|vmiles)",
            "position": 1
        },
        "update_value": _MEASURED_PROP,
        "pv_format": _PV_FORMAT
    }
}
