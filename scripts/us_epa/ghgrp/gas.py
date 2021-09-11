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

GAS_COLUMNS = [
    'Total reported direct emissions',
    'CO2 emissions (non-biogenic)',
    'Methane (CH4) emissions',
    'Nitrous Oxide (N2O) emissions',
    'HFC emissions',
    'PFC emissions',
    'SF6 emissions',
    'NF3 emissions',
    'Other Fully Fluorinated GHG emissions',
    'HFE emissions',
    'Very Short-lived Compounds emissions',
    'Other GHGs (metric tons CO2e)',
    'Biogenic CO2 emissions (metric tons)',
    'Total reported emissions from Onshore Oil & Gas Production',
    'Total reported emissions from Gathering & Boosting',
    'Total reported direct emissions from Local Distribution Companies',
]

GAS_COL_TO_NAME = {
    'Methane (CH4)': 'Methane',
    'Nitrous Oxide (N2O)': 'Nitrous Oxide',
    'HFC': 'Hydrofluorocarbon',
    'PFC': 'Perfluorocarbon',
    'SF6': 'Sulfur Hexafluoride',
    'NF3': 'Nitrogen Trifluoride',
    'HFE': 'Hydrofluoroethers',
    'Very Short-lived Compounds': 'Very Short-lived Compounds',
    'Other Fully Fluorinated GHG': 'Other Fully Fluorinated Compounds',
    'Other GHGs (metric tons CO2e)': 'Other Greenhouse Gasses',
    'CO2 (non-biogenic)': 'Carbon Dioxide',
}

GAS_MCF_TEMPLATE = """
Node: dcid:{gas_dcid}
typeOf: dcs:GreenhouseGas
name: "{gas_name}"
"""


def is_gas_col(col):
    return col.strip() in GAS_COLUMNS


def col_to_sv(col):
    if not is_gas_col(col):
        return None
    dcid = col.strip().replace(' emissions', '')
    suffix = ''
    if dcid.startswith('Total'):
        suffix = 'GreenhouseGas'
    elif dcid.startswith('Biogenic CO2'):
        suffix = 'CarbonDioxide_Biogenic'
    elif dcid.startswith('CO2') and '(non-biogenic)' in dcid:
        suffix = 'CarbonDioxide_NonBiogenic'
    elif dcid in GAS_COL_TO_NAME:
        suffix = _name_to_dcid(dcid.strip())
    assert suffix != None
    return f'Annual_Emissions_{suffix}'


def _name_to_dcid(name):
    gas_dcid = name.replace(' ', '')
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


def append_mcf(fp):
    for gas_col, gas_name in GAS_COL_TO_NAME.items():
        fp.write(
            GAS_MCF_TEMPLATE.format(gas_dcid=_name_to_dcid(gas_name),
                                    gas_name=gas_name))


if __name__ == '__main__':
    with open('tmp_data/gas.mcf', 'w') as fp:
        append_mcf(fp)
