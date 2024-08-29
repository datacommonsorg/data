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
Processor for Schedule 2 of EIA Form 860 which includes Power Plant data.

To run this script as a standalone:
python3 -m power_plant <IN_EXCEL_FILENAME> <OUT_CSV_FILENAME>
"""
import csv
import io
import os
import sys

import pandas as pd
import pandas.api.types as pd_types
import numpy as np
import typing

from us_eia.eia_860 import utils

IMPORT_COLUMNS = [
    'UtilityId',
    'UtilityName',
    'PlantCode',
    'PlantName',
    'StreetAddress',
    'City',
    'State',
    'Zip',
    'County',
    'Latitude',
    'Longitude',
    'NERC Region',  # Not imported
    'Balancing Authority Code',  # Not imported
    'Balancing Authority Name',  # Not imported
    'Name of Water Source',  # Not imported
    'NAICSCode',
    'RegulatoryStatus',
    'Sector',
    'Sector Name',
    'FERC Cogeneration Status',
    'FercCogenerationDocketNumber',
    'FERC Small Power Producer Status',
    'FercSmallPowerProducerDocketNumber',
    'FERC Exempt Wholesale Generator Status',
    'FercExemptWholesaleGeneratorDocketNumber',
    'Ash Impoundment?',
    'Ash Impoundment Lined?',
    'Ash Impoundment Status',
    'Transmission or Distribution System Owner',  # Not imported
    'Transmission or Distribution System Owner ID',  # Not imported
    'Transmission or Distribution System Owner State',  # Not imported
    'Grid Voltage 1',
    'Grid Voltage 2',
    'Grid Voltage 3',
    'Energy Storage',
    'Natural Gas LDC Name',  # Not imported
    'Natural Gas Pipeline Name 1',  # Not imported
    'Natural Gas Pipeline Name 2',  # Not imported
    'Natural Gas Pipeline Name 3',  # Not imported
    'Pipeline Notes',  # Not imported
    'Natural Gas Storage',
    'Liquefied Natural Gas Storage',
]

EXPORT_COLUMNS = [
    'Dcid',
    'Name',
    'Address',
    'StateDcid',
    'ZipDcid',
    'Latitude',
    'Longitude',
    'Naics',
    'PlantCode',
    'UtilityDcid',
    'RegulatoryStatusEnum',
    'PowerPlantSector',
    'FercCogenerationStatus',
    'FercCogenerationDocketNumber',
    'FercSmallPowerProducerStatus',
    'FercSmallPowerProducerDocketNumber',
    'FercExemptWholesaleGeneratorStatus',
    'FercExemptWholesaleGeneratorDocketNumber',
    'IsAshImpounded',
    'IsAshLined',
    'AshImpoundmentStatusEnum',
    'GridVoltage1',
    'GridVoltage2',
    'GridVoltage3',
    'IsEnergyStored',
    'IsNaturalGasStored',
    'IsLiquefiedNaturalGasStored',
]

REGULATORY_STATUS_ENUM = {
    'NR': 'dcid:Regulated',
    'RE': 'dcid:NonRegulated',
}

SECTOR_CODE_ENUM = {
    1: 'dcid:EIA_ElectricUtility',
    2: 'dcid:EIA_IndependentPowerProducer_NonCombinedHeatPower',
    3: 'dcid:EIA_IndependentPowerProducer_CombinedHeatPower',
    4: 'dcid:EIA_Commercial_NonCombinedHeatPower',
    5: 'dcid:EIA_Commercial_CombinedHeatPower',
    6: 'dcid:EIA_Industrial_NonCombinedHeatPower',
    7: 'dcid:EIA_Industrial_CombinedHeatPower',
}

FERC_COGENERATION_STATUS_ENUM = {
    'Y': 'dcid:FERC_QualifiedCogenerator',
    'N': 'dcid:FERC_NonQualifiedCogenerator',
}

FERC_SMALL_PRODUCER_ENUM = {
    'Y': 'dcid:FERC_QualifiedSmallPowerProducer',
    'N': 'dcid:FERC_NonQualifiedSmallPowerProducer',
}

FERC_EXEMPT_GEN_ENUM = {
    'Y': 'dcid:FERC_QualifiedExemptWholesaleGenerator',
    'N': 'dcid:FERC_NonQualifiedExemptWholesaleGenerator',
}

ASH_IMPOUNDMENT_STATUS_ENUM = {
    'OP': 'dcid:EIA_Operating',
    'SB': 'dcid:EIA_StandbyBackup',
    'OA': 'dcid:EIA_OutOfService_Temporary',
    'OS': 'dcid:EIA_OutOfService_Permanent',
}

ASH_IMPOUNDED_ENUM = {
    'Y': '',
    'N': 'dcid:EIA_NotImpounded',
    '': 'dcid:EIA_NotImpounded',
}

ASH_LINED_ENUM = {
    'Y': 'dcid:EIA_Impoundment_Lined',
    'N': 'dcid:EIA_Impoundment_NotLined',
    'X': '',
    '': '',
}


def _to_enum(value: object, enum: typing.Dict) -> str:
    dcid = enum.get(value, None)
    assert enum is not None, f'code "{value}" not found in {enum}'
    return dcid


def _to_kv_quantity(value: object) -> str:
    if pd_types.is_number(value):
        return f'[{value} KiloVolt]'
    return ''


def _to_boolean(value: object) -> str:
    if value == 'Y':
        return 'dcid:True'
    return 'dcid:False'


def _update_frames(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Updates data frame to include columns required for tmcf"""
    raw_df = raw_df.replace(np.nan, '')
    raw_df['PlantCode'] = raw_df['PlantCode'].apply(utils.plant_code_to_str)
    raw_df['Dcid'] = raw_df['PlantCode'].apply(utils.plant_code_to_dcid)
    raw_df['Name'] = raw_df['PlantName'].apply(utils.escape_value)
    raw_df['Address'] = raw_df.apply(utils.build_address, axis=1)
    raw_df['StateDcid'] = raw_df['State'].apply(utils.state_alpha2_to_dcid)
    raw_df['ZipDcid'] = raw_df['Zip'].apply(utils.zip_to_dcid)
    raw_df['Naics'] = raw_df['NAICSCode'].apply(utils.naics_to_dcid)
    raw_df['UtilityDcid'] = raw_df['UtilityId'].apply(utils.utility_id_to_dcid,
                                                      prefix_dcid=True)
    raw_df['RegulatoryStatusEnum'] = raw_df['RegulatoryStatus'].apply(
        _to_enum, enum=REGULATORY_STATUS_ENUM)
    raw_df['PowerPlantSector'] = raw_df['Sector'].apply(_to_enum,
                                                        enum=SECTOR_CODE_ENUM)
    raw_df['FercCogenerationStatus'] = raw_df['FERC Cogeneration Status'].apply(
        _to_enum, enum=FERC_COGENERATION_STATUS_ENUM)
    raw_df['FercCogenerationDocketNumber'] = raw_df[
        'FercCogenerationDocketNumber'].apply(utils.escape_value)
    raw_df['FercSmallPowerProducerStatus'] = raw_df[
        'FERC Small Power Producer Status'].apply(_to_enum,
                                                  enum=FERC_SMALL_PRODUCER_ENUM)
    raw_df['FercSmallPowerProducerDocketNumber'] = raw_df[
        'FercSmallPowerProducerDocketNumber'].apply(utils.escape_value)
    raw_df['FercExemptWholesaleGeneratorStatus'] = raw_df[
        'FERC Exempt Wholesale Generator Status'].apply(
            _to_enum, enum=FERC_EXEMPT_GEN_ENUM)
    raw_df['FercExemptWholesaleGeneratorDocketNumber'] = raw_df[
        'FercExemptWholesaleGeneratorDocketNumber'].apply(utils.escape_value)
    raw_df['IsAshImpounded'] = raw_df['Ash Impoundment?'].apply(
        _to_enum, enum=ASH_IMPOUNDMENT_STATUS_ENUM)
    raw_df['IsAshLined'] = raw_df['Ash Impoundment Lined?'].apply(
        _to_enum, enum=ASH_IMPOUNDMENT_STATUS_ENUM)
    raw_df['AshImpoundmentStatusEnum'] = raw_df['Ash Impoundment Status'].apply(
        _to_enum, enum=ASH_IMPOUNDMENT_STATUS_ENUM)
    raw_df['GridVoltage1'] = raw_df['Grid Voltage 1'].apply(_to_kv_quantity)
    raw_df['GridVoltage2'] = raw_df['Grid Voltage 2'].apply(_to_kv_quantity)
    raw_df['GridVoltage3'] = raw_df['Grid Voltage 3'].apply(_to_kv_quantity)
    raw_df['IsEnergyStored'] = raw_df['Energy Storage'].apply(_to_boolean)
    raw_df['IsNaturalGasStored'] = raw_df['Natural Gas Storage'].apply(
        _to_boolean)
    raw_df['IsLiquefiedNaturalGasStored'] = raw_df[
        'Liquefied Natural Gas Storage'].apply(_to_boolean)
    print(raw_df)
    return raw_df


def process(in_path: str, out_path: str):
    """Read data from excel and create CSV required for DC import"""
    raw_df = pd.read_excel(in_path,
                           header=1,
                           dtype=object,
                           names=IMPORT_COLUMNS)
    print(raw_df)
    df = _update_frames(raw_df)
    # To account for values with commas, we do a combination of: csv.QUOTE_ALL
    # and adding escaped quotes around such values (see utils.escape_value).
    df.to_csv(out_path,
              columns=EXPORT_COLUMNS,
              quoting=csv.QUOTE_ALL,
              escapechar='\\',
              doublequote=False,
              index=False)


if __name__ == '__main__':
    process(sys.argv[1], sys.argv[2])
