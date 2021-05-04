# Copyright 2021 Google LLC
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
"""Shared utilities for processing EIA Form-860"""
import os
import sys

import pandas as pd
import pandas.api.types as pd_types

# module_dir_ is the path to where this code is running from.
module_dir_ = os.path.dirname(__file__)

# For import util.alpha2_to_dcid
sys.path.insert(1, os.path.join(module_dir_, '../../../util'))
import alpha2_to_dcid


def state_alpha2_to_dcid(alpha2: str) -> str:
    if alpha2 == '':
        return ''

    # Special case for utility id 8862 in Canada
    if alpha2 == 'CN':
        return 'dcid:country/CAN'

    # Special case for utility id 23931 in Quebec
    if alpha2 == 'QB':
        alpha2 = 'QC'

    dcid = alpha2_to_dcid.USSTATE_MAP.get(alpha2, None)
    if dcid is None:
        dcid = alpha2_to_dcid.CAN_PROVINCE_MAP.get(alpha2, None)

    assert dcid is not None, f'state alpha2 "{alpha2}" not found'
    return f'dcid:{dcid}'


def zip_to_dcid(zip: str) -> str:
    if pd_types.is_number(zip):
        return f'dcid:zip/{zip:0>5}'
    return ''


def build_address(row: pd.Series) -> str:
    zip = row["Zip"]
    if pd_types.is_number(zip):
        zip = f'{zip:0>5}'
    return escape_value(
        f'{row["StreetAddress"]}, {row["City"]}, {row["State"]} {zip}')


def utility_id_to_dcid(utility_id: str) -> str:
    return f'eia/u/{utility_id}'


def plant_code_to_dcid(plant_code: str) -> str:
    return f'eia/pp/{plant_code}'


def naics_to_dcid(naics: str) -> str:
    return f'NAICS/{naics}'


def escape_value(value: str) -> str:
    """values that could include commas need to be escaped"""
    if value == '':
        return ''
    return f'\"{value}\"'