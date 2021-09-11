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
"""Simple utility for emission source-related operations, such as generating MCF."""

SOURCE_COLS = [
    'Stationary Combustion',
    'Electricity Generation',
    'Adipic Acid Production',
    'Aluminum Production',
    'Ammonia Manufacturing',
    'Cement Production',
    'Electronics Manufacture',
    'Ferroalloy Production',
    'Fluorinated GHG Production',
    'Glass Production',
    'HCFC–22 Production from HFC–23 Destruction',
    'Hydrogen Production',
    'Iron and Steel Production',
    'Lead Production',
    'Lime Production',
    'Magnesium Production',
    'Miscellaneous Use of Carbonates',
    'Nitric Acid Production',
    'Petroleum and Natural Gas Systems – Offshore Production',
    'Petroleum and Natural Gas Systems – Processing',
    'Petroleum and Natural Gas Systems – Transmission/Compression',
    'Petroleum and Natural Gas Systems – Underground Storage',
    'Petroleum and Natural Gas Systems – LNG Storage',
    'Petroleum and Natural Gas Systems – LNG Import/Export',
    'Petrochemical Production',
    'Petroleum Refining',
    'Phosphoric Acid Production',
    'Pulp and Paper Manufacturing',
    'Silicon Carbide Production',
    'Soda Ash Manufacturing',
    'Titanium Dioxide Production',
    'Underground Coal Mines',
    'Zinc Production',
    'Municipal Landfills',
    'Industrial Wastewater Treatment',
    'Manufacture of Electric Transmission and Distribution Equipment',
    'Industrial Waste Landfills',
]

SOURCE_MCF_TEMPLATE = """
Node: dcid:{dcid}
typeOf: dcs:EmissionSourceEnum
name: "{name}"
"""


def is_source_col(col):
    return col.strip() in SOURCE_COLS


def col_to_sv(col):
    if not is_source_col(col):
        return None
    return f'Annual_Emissions_{_name_to_dcid(col)}'


def _name_to_dcid(name):
    dcid = name.replace(' and ', 'And')
    dcid = dcid.replace(' from ', 'From')
    dcid = dcid.replace(' of ', 'Of')
    dcid = dcid.replace(' – ', '_')
    dcid = dcid.replace('–', '')
    dcid = dcid.replace('/', 'Or')
    dcid = dcid.replace(' ', '')
    return dcid


def append_mcf(fp):
    for source in SOURCE_COLS:
        fp.write(
            SOURCE_MCF_TEMPLATE.format(dcid=_name_to_dcid(source), name=source))


if __name__ == '__main__':
    with open('tmp_data/sources.mcf', 'w') as fp:
        append_mcf(fp)
