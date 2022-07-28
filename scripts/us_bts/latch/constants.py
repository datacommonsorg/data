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
DEFAULT_SV_PROP = {
    "typeOf": "dcs:StatisticalVariable",
    "populationType": "dcs:Household",
    "statType": "dcs:meanValue",
    "measurementQualifier": "dcs:EveryWeekday"
}

MCF_TEMPLATE = ("Node: dcid:{dcid}\n"
                "typeOf: dcs:StatisticalVariable\n"
                "populationType: dcs:Household\n"
                "statType: dcs:meanValue\n"
                "measurementQualifier: dcs:EveryWeekday\n"
                "{xtra_pvs}\n")

TMCF_TEMPLATE = (
    "Node: E:us_transportation_household->E0\n"
    "typeOf: dcs:StatVarObservation\n"
    "variableMeasured: C:us_transportation_household->sv\n"
    "measurementMethod: C:us_transportation_household->measurement_method\n"
    "observationAbout: C:us_transportation_household->location\n"
    "observationDate: C:us_transportation_household->year\n"
    "value: C:us_transportation_household->observation\n")

HOUSEHOLD_PV = "[Person {person}]"
NUM_OF_VEHICLES_PV = "[AvailableVehicles {vehicle}]"
HEADERMAP = {
    "est_pmiles2007_11": "PersonMilesTraveled",
    "est_pmiles": "PersonMilesTraveled",
    "pmiles": "PersonMilesTraveled",
    "est_ptrp2007_11": "PersonTrips",
    "est_ptrp": "PersonTrips",
    "ptrp": "PersonTrips",
    "est_vtrp2007_11": "VehicleTrips",
    "est_vtrp": "VehicleTrips",
    "vtrp": "VehicleTrips",
    "est_vmiles2007_11": "VehicleMilesTraveled",
    "est_vmiles": "VehicleMilesTraveled",
    "vmiles": "VehicleMilesTraveled",
}
ACS_LT_MOR = {0: '', 1: '_MarginOfErrorMoreThanACSSurvey'}
INCOMPLETE_ACS = {0: '', 1: '_IncompleteACSSurvey'}
URBAN = {1: "Urban", 2: "SemiUrban", 3: "Rural"}

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

CONF_2009_FILE = {
    "input_file_delimiter": "\t",
    "basic_cols": ["geoid", "urban_group"],
    "pop_cols": [
        "est_pmiles2007_11", "est_ptrp2007_11", "est_vmiles2007_11",
        "est_vtrp2007_11"
    ],
    "extra_cols": COMMON_COLS + ADDITIONAL_2009_FILE_COLS,
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
    "year": 2017,
    "additional_process": True
}
