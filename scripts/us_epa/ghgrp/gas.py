# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Simple utility for gas-related operations, such as generating MCF."""

import os

GAS_COLUMNS_TO_NAME = {
    'Methane (CH4) emissions': 'Methane',
    'Nitrous Oxide (N2O) emissions': 'Nitrous Oxide',
    'HFC emissions': 'Hydrofluorocarbon',
    'PFC emissions': 'Perfluorocarbon',
    'SF6 emissions': 'Sulfur Hexafluoride',
    'NF3 emissions': 'Nitrogen Trifluoride',
    'HFE emissions': 'Hydrofluoroether',
    'CO2 emissions (non-biogenic)': 'Carbon Dioxide',
    'Other Fully Fluorinated GHG emissions': 'Other Fully Fluorinated Compound',
    'Very Short-lived Compounds emissions': 'Very Short-lived Compounds',
    'Other GHGs (metric tons CO2e)': 'Other Greenhouse Gas',
    'Biogenic CO2 emissions (metric tons)': 'Carbon Dioxide',
    'Total reported direct emissions': None,
    'Total reported emissions from Onshore Oil & Gas Production': None,
    'Total reported emissions from Gathering & Boosting': None,
    'Total reported direct emissions from Local Distribution Companies': None,
    'Total reported direct emissions from Electrical Equipment Use': None,
}

GAS_MCF_TEMPLATE = """
Node: dcid:{gas_dcid}
typeOf: dcs:GreenhouseGas
name: "{gas_name}"
"""

SV_MCF_TEMPLATE = """
Node: dcid:{sv_dcid}
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
measurementQualifier: dcs:Annual
emittedThing: dcs:{gas_dcid}
emissionSourceType: dcs:{source_type}
"""


def is_gas_col(col):
    return col.strip() in GAS_COLUMNS_TO_NAME


def col_to_sv(col):
    if not is_gas_col(col):
        return None
    dcid = col.strip()
    suffix = ''
    if dcid.startswith('Total'):
        suffix = 'GreenhouseGas_NonBiogenic'
    elif dcid.startswith('Biogenic CO2'):
        suffix = 'CarbonDioxide_Biogenic'
    elif dcid in GAS_COLUMNS_TO_NAME:
        suffix = f'{col_to_dcid(dcid.strip())}_NonBiogenic'
    assert suffix != None
    return f'Annual_Emissions_{suffix}'


def col_to_dcid(col):
    name = GAS_COLUMNS_TO_NAME[col]
    gas_dcid = name.replace(' emissions', '').replace(' ', '')
    if '-' in gas_dcid:
        idx = gas_dcid.rfind('-')
        if idx < len(gas_dcid) - 1:  # we don't expect a trailing '-'
            gas_dcid = gas_dcid[:idx] + gas_dcid[idx +
                                                 1].upper() + gas_dcid[idx + 2:]
    if '(' in gas_dcid:
        gas_dcid = gas_dcid.split('(', 1)[0]
    if 'Other' in gas_dcid:
        gas_dcid = f'EPA_{gas_dcid}'
    return gas_dcid


def append_gas_mcf(fp):
    for gas_col, gas_name in GAS_COLUMNS_TO_NAME.items():
        if not gas_name:
            continue
        fp.write(
            GAS_MCF_TEMPLATE.format(gas_dcid=col_to_dcid(gas_col),
                                    gas_name=gas_name))


def append_sv_mcf(fp):
    processed_total = False
    for col, name in GAS_COLUMNS_TO_NAME.items():
        if processed_total:
            continue
        if col.startswith('Total') and not processed_total:
            processed_total = True
        sv_dcid = col_to_sv(col)
        if name:
            gas_dcid = col_to_dcid(col)
        else:
            gas_dcid = 'GreenhouseGas'
        source_type = 'NonBiogenicEmissionSource'
        if col.startswith('Biogenic'):
            source_type = 'BiogenicEmissionSource'
        fp.write(
            SV_MCF_TEMPLATE.format(sv_dcid=sv_dcid,
                                   gas_dcid=gas_dcid,
                                   source_type=source_type))


if __name__ == '__main__':
    with open(os.path.join('import_data', 'gas_node.mcf'), 'w') as fp:
        append_gas_mcf(fp)
    with open(os.path.join('import_data', 'gas_sv.mcf'), 'w') as fp:
        append_sv_mcf(fp)
