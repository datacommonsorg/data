# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https: #www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""UNData Energy codes to DCID and properties"""

from typing import List

# Map from UNData Energy commodity codes to EnergySourceEnum
UN_ENERGY_CODES = {
    #	'AO':  # Additives and Oxygenates
    #	'AW':  # Animal waste
    'AT':  'dcs:EIA_AnthraciteCoal',  # Anthracite
    #	'AV':  # Aviation Gasoline
    #	'BS':  # Bagasse
    #	'BJ':  # Bio jet kerosene
    #	'BD':  # Biodiesel
    #	'BI':  # Biogases
    #	'AL':  # Biogasoline
    'BT':  'dcs:EIA_BituminousCoal',  # Bitumen
    #	'PU':  # Black liquor
    #	'BG':  # Blast Furnace Gas
    #	'LB':  # Brown Coal
    #	'BB':  # Brown Coal Briquettes
    #	'CH':  # Charcoal
    #	'CT':  # Coal Tar
    #	'OK':  # Coke Oven Coke
    #	'OG':  # Coke Oven Gas
    #	'CC':  # Coking coal
    #	'CR':  # Conventional crude oil
    #	'DG':  # Direct use of geothermal heat
    #	'DS':  # Direct use of solar thermal heat
    #	'EC':  # Electricity, net installed capacity of electric power plants
    #	'EA':  # Ethane
    #	'WF':  # Falling Water
    #	'RF':  # Fuel Oil
    #	'FW':  # Fuelwood
    #	'GK':  # Gas Coke
    #	'DL':  # Gas Oil/ Diesel Oil
    #	'GJ':  # Gasoline-type jet fuel
    #	'GG':  # Gasworks Gas
    'EG': 'dcs:Geothermal',  # Geothermal
    #	'CL':  # Hard Coal
    #	'ST':  # Heat
    #	'HF':  # Heat from combustible fuels
    'EH': 'dcs:EIA_Water',  # Hydro
    #	'IW':  # Industrial Waste
    #	'JF':  # Kerosene-type Jet Fuel
    'LN': 'dcs:LigniteCoal',  # Lignite
    #	'LP':  # Liquified Petroleum Gas
    #	'LU':  # Lubricants
    #	'MO':  # Motor Gasoline
    #	'MW':  # Municipal Wastes
    #	'NP':  # Naphtha
    'NG': 'dcs:NaturalGas',  # Natural Gas (including LNG)
    #	'GL':  # Natural Gas Liquids
    'EN': 'dcs:Nuclear',  # Nuclear Electricity
    #	'ZJ':  # Of which: bio jet kerosene
    #	'ZD':  # Of which: biodiesel
    #	'ZG':  # Of which: biogasoline
    #	'OS':  # Oil Shale / Oil Sands
    #	'OB':  # Other bituminous coal
    #	'CP':  # Other coal products
    #	'OH':  # Other hydrocarbons
    'KR':  'dcs:EIA_Kerosene',  # Other kerosene
    #	'OL':  # Other liquid biofuels
    #	'PP':  # Other oil products n.e.c.
    #	'BO':  # Other recovered gases
    #	'VW':  # Other Vegetal Material and Residues
    #	'PW':  # Paraffin waxes
    #	'BC':  # Patent fuel
    #	'PT':  # Peat
    #	'BP':  # Peat Products
    'PK': 'dcs:PetroleumCoke',  # Petroleum Coke
    #	'FS':  # Refinery Feedstocks
    #	'RG':  # Refinery Gas
    'ES': 'dcs:Solar',  # Solar Electricity
    'SB':  'dcs:EIA_SubbituminousCoal',  # Sub-bituminous coal
    #	'ET':  # Thermal Electricity
    #	'EO':  # Tide, wave and ocean electricity
    'EL':  'dcs:Electricity',  # Total Electricity
    #	'GR':  # Total Refinery Output
    #	'UR':  # Uranium
    #	'WS':  # White spirit and special boiling point industrial spirits
    'EW': 'dcs:Wind',  # Wind Electricity
}


def get_all_energy_source_codes() -> List[str]:
    return list(UN_ENERGY_CODES.keys())


def get_energy_source_dcid(fuel_type: str) -> str:
    if UN_ENERGY_CODES.has_key(fuel_type):
        return UN_ENERGY_CODES[fuel_type]
    return None


UN_ENERGY_TRANSACTION_CODES = {
    '01':  'dcs:Production',
    #  '02':  'dcs:Receipt',
    #  '03':  'dcs:Imports',
    #  '04':  'dcs:Exports',
    #  '05':  'dcs:Bunkers',
    #  '06':  'dcs:Stock changes',
    #  '07':  'dcs:Transfers and recycled products',
    '08':  'dcs:Transformation',
    '09':  'dcs:Energy industry own use',
    '10':  'dcs:Losses',
    '11':  'dcs:Non-energy uses',
    '12':  'dcs:Consumption',
    '13':  'dcs:Refinery capacity',
    #  '14:',
    '15':  'dcs:Total resources in place',
    '16':  'dcs:Reserves',
    '17':  'dcs:Total resources',
    'GA':  'dcs:Total energy supply',
    'NA':  'dcs:Final consumption',
}
