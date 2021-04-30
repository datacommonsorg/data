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
"""
Processor for Schedule 1 of EIA Form 860 which includes Utility data.

To run this script as a standalone:
python3 -m utility <IN_EXCEL_FILENAME> <OUT_CSV_FILENAME>
"""
import csv
import io
import os
import sys

import pandas as pd
import pandas.api.types as pd_types
import numpy as np
from typing import Callable

# For import util.alpha2_to_dcid
sys.path.insert(1, '../../../util')
import alpha2_to_dcid

UTILITY_IMPORT_COLUMNS = [
    'UtilityId',
    'Name',
    'StreetAddress',
    'City',
    'State',
    'Zip',
    'IsOwner',
    'IsOperator',
    'IsAssetManager',
    'IsOther',
    'EntityType',
]

UTILITY_EXPORT_COLUMNS = [
    'UtilityId',
    'Dcid',
    'Name',
    'Address',
    'StateDcid',
    'ZipDcid',
    'EntityTypeEnum',
    'OwnerEnum',
    'OperatorEnum',
    'AssetManagerEnum',
    'OtherRelationshipEnum',
]

ENTITY_CODE_TO_ENUM = {
    'C': 'dcid:EIA_Cooperative',
    'I': 'dcid:EIA_InvestorOwned',
    'Q': 'dcid:EIA_Independent',
    'M': 'dcid:EIA_MunicipalityOwned',
    'P': 'dcid:EIA_PoliticalSubdivision',
    'F': 'dcid:EIA_FederallyOwned',
    'S': 'dcid:EIA_StateOwned',
    'IND': 'dcid:EIA_Industrial',
    'COM': 'dcid:EIA_Commercial',
}


def _state_alpha2_to_dcid(alpha2: str) -> str:
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


def _entity_type_to_enum(entity_code: str) -> str:
    enum = ENTITY_CODE_TO_ENUM.get(entity_code, None)
    assert enum is not None, f'utility entity code "{entity_code}" not found'
    return enum


def _to_assoc_enum(code: str, dcid) -> str:
    if code == 'Y':
        return dcid
    return ''


def _zip_to_dcid(zip: str) -> str:
    if pd_types.is_number(zip):
        return f'dcid:zip/{zip:0>5}'
    return ''


def _build_address(row: pd.Series) -> str:
    return _escape_value(
        f'{row["StreetAddress"]}, {row["City"]}, {row["State"]} {row["Zip"]}')


def _utility_id_to_dcid(utility_id: str) -> str:
    return f'eia/u/{utility_id}'


def _escape_value(value: str) -> str:
    """values that could include commas need to be escaped"""
    return f'\"{value}\"'


def _update_frames(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Updates data frame to include columns required for tmcf"""
    raw_df = raw_df.replace(np.nan, '')
    raw_df['Dcid'] = raw_df['UtilityId'].apply(_utility_id_to_dcid)
    raw_df['Name'] = raw_df['Name'].apply(_escape_value)
    raw_df['Address'] = raw_df.apply(_build_address, axis=1)
    raw_df['StateDcid'] = raw_df['State'].apply(_state_alpha2_to_dcid)
    raw_df['ZipDcid'] = raw_df['Zip'].apply(_zip_to_dcid)
    raw_df['EntityTypeEnum'] = raw_df['EntityType'].apply(_entity_type_to_enum)
    raw_df['OwnerEnum'] = raw_df['IsOwner'].apply(
        _to_assoc_enum, dcid='dcid:EIA_OwnerOfPowerPlants')
    raw_df['OperatorEnum'] = raw_df['IsOperator'].apply(
        _to_assoc_enum, dcid='dcid:EIA_OperatorOfPowerPlants')
    raw_df['AssetManagerEnum'] = raw_df['IsAssetManager'].apply(
        _to_assoc_enum, dcid='dcid:EIA_AssetManagerOfPowerPlants')
    raw_df['OtherRelationshipEnum'] = raw_df['IsOther'].apply(
        _to_assoc_enum, dcid='dcid:EIA_OtherRelationshipWithPowerPlants')
    print(raw_df)
    return raw_df


def process(in_path: str, out_path: str):
    """Read data from excel and create CSV required for DC import"""
    raw_df = pd.read_excel(in_path,
                           header=1,
                           dtype=object,
                           names=UTILITY_IMPORT_COLUMNS)
    df = _update_frames(raw_df)
    # To account for values with commas, we do a combination of: csv.QUOTE_ALL
    # and adding escaped quotes around such values (see _escape_value).
    df.to_csv(out_path,
              columns=UTILITY_EXPORT_COLUMNS,
              quoting=csv.QUOTE_ALL,
              escapechar='\\',
              doublequote=False,
              index=False)


if __name__ == '__main__':
    process(sys.argv[1], sys.argv[2])
