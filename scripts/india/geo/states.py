# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = ["Thejesh GN (i@thejeshgn.com)"]

INDIA_STATES_ISO_CODES = {
    "ANDHRA PRADESH": "IN-AP",
    "ARUNACHAL PRADESH": "IN-AR",
    "ASSAM": "IN-AS",
    "BIHAR": "IN-BR",
    "CHATTISGARH": "IN-CT",
    "CHHATTISGARH": "IN-CT",
    "GOA": "IN-GA",
    "GUJARAT": "IN-GJ",
    "HARYANA": "IN-HR",
    "HIMACHAL PRADESH": "IN-HP",
    "JHARKHAND": "IN-JH",
    "JHARKHAND#": "IN-JH",
    "KARNATAKA": "IN-KA",
    "KERALA": "IN-KL",
    "MADHYA PRADESH": "IN-MP",
    "MADHYA PRADESH#": "IN-MP",
    "MAHARASHTRA": "IN-MH",
    "MANIPUR": "IN-MN",
    "MEGHALAYA": "IN-ML",
    "MIZORAM": "IN-MZ",
    "NAGALAND": "IN-NL",
    "NAGALAND#": "IN-NL",
    "ODISHA": "IN-OR",
    "PUNJAB": "IN-PB",
    "RAJASTHAN": "IN-RJ",
    "SIKKIM": "IN-SK",
    "TAMIL NADU": "IN-TN",
    "TELENGANA": "IN-TG",
    "TELANGANA": "IN-TG",
    "TRIPURA": "IN-TR",
    "UTTARAKHAND": "IN-UT",
    "UTTAR PRADESH": "IN-UP",
    "WEST BENGAL": "IN-WB",
    "ANDAMAN AND NICOBAR ISLANDS": "IN-AN",
    "ANDAMAN & NICOBAR ISLANDS": "IN-AN",
    "CHANDIGARH": "IN-CH",
    "DADRA AND NAGAR HAVELI": "IN-DN",
    "DADRA & NAGAR HAVELI": "IN-DN",
    "DADAR NAGAR HAVELI": "IN-DN",
    "DAMAN AND DIU": "IN-DD",
    "DAMAN & DIU": "IN-DD",
    "DELHI": "IN-DL",
    "JAMMU AND KASHMIR": "IN-JK",
    "JAMMU & KASHMIR": "IN-JK",
    "LADAKH": "IN-LA",
    "LAKSHADWEEP": "IN-LD",
    "LAKSHWADEEP": "IN-LD",
    "PONDICHERRY": "IN-PY",
    "PUDUCHERRY": "IN-PY",
    "DADRA AND NAGAR HAVELI AND DAMAN AND DIU": "IN-DH",
    "TELANGANA": "IN-TG",
    "ALL INDIA": "IN"
}

INDIA_STATES_CENSUS2001_CODES = {
    "JAMMU AND KASHMIR": "01",
    "HIMACHAL PRADESH": "02",
    "PUNJAB": "03",
    "CHANDIGARH": "04",
    "UTTARANCHAL": "05",
    "HARYANA": "06",
    "DELHI": "07",
    "RAJASTHAN": "08",
    "UTTAR PRADESH": "09",
    "BIHAR": "10",
    "SIKKIM": "11",
    "ARUNACHAL PRADESH": "12",
    "NAGALAND": "13",
    "MANIPUR": "14",
    "MIZORAM": "15",
    "TRIPURA": "16",
    "MEGHALAYA": "17",
    "ASSAM": "18",
    "WEST BENGAL": "19",
    "JHARKHAND": "20",
    "ODISHA": "21",
    "CHHATTISGARH": "22",
    "MADHYA PRADESH": "23",
    "GUJARAT": "24",
    "DAMAN & DIU": "25",
    "DAMAN AND DIU": "25",
    "DADRA & NAGAR HAVELI": "26",
    "DADRA AND NAGAR HAVELI": "26",
    "MAHARASTRA": "27",
    "MAHARASHTRA": "27",
    "ANDHRA PRADESH": "28",
    "KARNATAKA": "29",
    "GOA": "30",
    "LAKSHADWEEP": "31",
    "KERALA": "32",
    "TAMIL NADU": "33",
    "PUDUCHERRY": "34",
    "ANDAMAN & NICOBAR ISLANDS": "35",
    "ANDAMAN AND NICOBAR ISLANDS": "35"
}


class IndiaStatesMapper:
    """Class for resolving various mappings for Indian states and UTs """

    @staticmethod
    def get_state_name_to_iso_code_mapping(state_name):
        """
        Static function to get the ISO code for a given state or UT
        
        Args:
            state_name :  Indian State or UT name
        """
        state_name = state_name.upper().strip()
        if state_name in INDIA_STATES_ISO_CODES:
            return INDIA_STATES_ISO_CODES[state_name]
        else:
            raise Exception(
                "State name is not found in the INDIA_STATES_ISO_CODES mapping")

    @staticmethod
    def get_state_name_to_census2001_code_mapping(state_name,
                                                  district_name=None):
        """
        Static function to get the Census 2001 state code for a given state or UT
        
        Args:
            state_name :  Indian State or UT name
            district_name : District name, default is None
        """

        state_name = state_name.upper().strip()
        if district_name:
            district_name = district_name.upper().strip()

        # In 2001, LADAKH was part of JAMMU AND KASHMIR,
        # So it should return the code of JAMMU AND KASHMIR
        if state_name == "LADAKH":
            state_name = "JAMMU AND KASHMIR"
        # In 2001, TELANGANA was part of ANDHRA PRADESH,
        # So it should return the code of JAMMU AND KASHMIR
        elif state_name == "TELANGANA":
            state_name = "ANDHRA PRADESH"

        # In 2001, Uttarakhand was known as Uttaranchal
        elif state_name == "UTTARAKHAND":
            state_name = "UTTARANCHAL"

        # In 2001, DADRA AND NAGAR HAVELI, DAMAN AND DIU were
        # separate entities. We need to return the correct value
        # based on the district
        elif state_name == "THE DADRA AND NAGAR HAVELI AND DAMAN AND DIU" or state_name == "DADRA AND NAGAR HAVELI AND DAMAN AND DIU":
            if district_name == "DADRA AND NAGAR HAVELI":
                state_name = "DADRA AND NAGAR HAVELI"
            if district_name == "DAMAN":
                state_name = "DAMAN AND DIU"
            if district_name == "DIU":
                state_name = "DAMAN AND DIU"

        if state_name in INDIA_STATES_CENSUS2001_CODES:
            return INDIA_STATES_CENSUS2001_CODES[state_name]
        else:
            raise Exception(
                "State name is not found in the INDIA_STATES_CENSUS2001_CODES mapping"
            )
