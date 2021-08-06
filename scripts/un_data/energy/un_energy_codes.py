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

import re

# Map from UNData Energy commodity codes to EnergySourceEnum
UN_ENERGY_CODES = {
    'AO':  'AdditivesOxygenates',  # new
    'AW':  'AnimalWaste',  # new
    'AT':  'dcs:EIA_AnthraciteCoal',  # Anthracite
    'AV':  'AviationGasoline',  # new
    'BS':  'Bagasse',  # new
    'BJ':  'BioJetKerosene',  # new
    'BD':  'Biodiesel',  # new
    'BI':  'Biogases',  # new
    'AL':  'Biogasoline',  # new
    'BT':  'dcs:EIA_BituminousCoal',  # Bitumen
    'PU':  'BlackLiquor',  # new
    'BG':  'BlastFurnaceGas',  # new
    'LB':  'BrownCoal',  # new
    'BB':  'BrownCoalBriquettes',  # new
    'CH':  'Charcoal',  # new
    'CT':  'CoalTar',  # new
    'OK':  'CokeOvenCoke',  # new
    'OG':  'CokeOvenGas',  # new
    'CC':  'CokingCoal',  # new
    'CR':  'CrudeOil',  # new
    'DG':  'Geothermal',  # new
    'DS':  'SolarThermal',  # new
    'EC':  'ElectricityCapacity',  # new
    'EA':  'Ethane',  # new
    'WF':  'FallingWater',  # new
    'RF':  'FuelOil',  # new
    'FW':  'Fuelwood',  # new
    'GK':  'GasCoke',  # new
    'DL':  'DieselOil',  # new
    'GJ':  'GasolineJetFuel',  # new
    'GG':  'GasworksGas',  # new
    'EG': 'dcs:Geothermal',  # Geothermal
    'CL':  'HardCoal',  # new
    'ST':  'Heat',  # new
    'HF':  'HeatCombustibleFuels',  # new
    'EH': 'dcs:EIA_Water',  # Hydro
    'IW':  'IndustrialWaste',  # new
    'JF':  'KeroseneJetFuel',  # new
    'LN': 'dcs:LigniteCoal',  # Lignite
    'LP':  'Liquified Petroleum Gas',  # new
    'LU':  'Lubricants',  # new
    'MO':  'MotorGasoline',  # new
    'MW':  'MunicipalWastes',  # new
    'NP':  'Naphtha',  # new
    'NG': 'dcs:NaturalGas',  # Natural Gas (including LNG)
    'GL':  'NaturalGasLiquids',  # new
    'EN': 'dcs:Nuclear',  # Nuclear Electricity
    'ZJ':  'BioJetKerosene',  # new
    'ZD':  'Biodiesel',  # new
    'ZG':  'Biogasoline',  # new
    'OS':  'OilShale',  # new
    'OB':  'OtherBituminousCoal',  # new
    'CP':  'CoalProducts',  # new
    'OH':  'OtherHydrocarbons',  # new
    'KR':  'dcs:EIA_Kerosene',  # Other kerosene
    'OL':  'OtherLiquidBiofuels',  # new
    'PP':  'OtherOilProducts',  # new
    'BO':  'OtherRecoveredGases',  # new
    'VW':  'VegetalWaste',  # new
    'PW':  'ParaffinWaxes',  # new
    'BC':  'PatentFuel',  # new
    'PT':  'Peat',  # new
    'BP':  'PeatProducts',  # new
    'PK': 'dcs:PetroleumCoke',  # Petroleum Coke
    'FS':  'RefineryFeedstocks',  # new
    'RG':  'RefineryGas',  # new
    'ES': 'dcs:Solar',  # Solar Electricity
    'SB':  'dcs:EIA_SubbituminousCoal',  # Sub-bituminous coal
    'ET':  'ThermalElectricity',  # new
    'EO':  'OceanElectricity',  # new
    'EL':  'dcs:Electricity',  # Total Electricity
    'GR':  'TotalRefineryOutput',  # new
    'UR':  'Uranium',  # new
    'WS':  'White spirit and special boiling point industrial spirits',  # new
    'EW': 'dcs:Wind',  # Wind Electricity
}


def get_all_energy_source_codes() -> List[str]:
    return list(UN_ENERGY_CODES.keys())


def get_energy_source_dcid(fuel_type: str) -> str:
    if fuel_type in UN_ENERGY_CODES:
        return UN_ENERGY_CODES[fuel_type]
    return None


UN_ENERGY_ACTIVITY_CODE = {
    '01':  'dcs:Production',
    #  '02':  'dcs:receipt',
    #  '03':  'dcs:Imports',
    #  '04':  'dcs:Exports',
    #  '05':  'dcs:Bunkers',
    #  '06':  'dcs:Stock changes',
    #  '07':  'dcs:Transfers and recycled products',
    '08':  'dcs:Transformation',
    '09':  'dcs:Energy industry own use',
    '10':  'dcs:Losses',
    '11':  'dcs:Consumption',  # Consumption non-energy
    '12':  'dcs:Consumption',
    '13':  'dcs:Refinery capacity',
    #  '14:',
    '15':  'dcs:Total resources in place',
    '16':  'dcs:Reserves',
    '17':  'dcs:Total resources',
    'GA':  'dcs:Total energy supply',
    'NA':  'dcs:Final consumption',
}

# Values for property: energyProducerType
UN_ENERGY_PRODUCER_TYPE = {
    '0': 'OffShore',
    '3': 'Refinery',
    '4': None,  # Plants producing petroleum products
    '5': 'EnergyProducerMainActivity',
    '6': 'EnergyProducerAutoProducer',
    '8': None,  # gross production
    '9': None,  # net production
}

# Values for property: energySource
UN_ENERGY_FUEL_TYPE = {
    'C': 'CombustibleFuel',
    'EB': 'ElectricBoiler',
    'G': 'Geothermal',
    'HY': 'ConventionalHydroelectric',
    'HP': 'HeatPump',
    'H': 'ChemicalHeat',
    'N': 'Nuclear',
    'O': 'OtherFuel',
    'PH': 'PumpedHydro',
    'S': 'Solar',
    'SP': 'SolarPhotovoltaic',
    'ST': 'SolarThermal',
    'T': 'Tidal',
    'W': 'Wind',
    'BI': 'Biogas',
    'BS': 'Bagasse',
    'CL': 'Coal',
    'CP': 'CoalProducts',
    'DL': 'DieselOil',
    'LB': 'BrownCoal',
    'LBF': 'LiquidBioFuel',
    'SBF': 'SolidBioFuel',
    'MG': 'ManufaturedGas',
    'NG': 'NaturalGas',
    'NRW': 'NonRenewableWaste',
    'OS': 'OilShale',
    'PP': 'OilProducts',
    'PT': 'Peat',
    'RF': 'FuelOil',
    'RW': 'MunicipalWaste',
}

# TODO(ajaits): extent dcid:PowerPlantSectorEnum
# values for property: energyGeneratingPlantType
UN_ENERGY_PLANT_TYPE = {
    'C': 'CHPGeneratingPowerPlant',
    'H': 'HeatGeneratingPowerPlant',
    'E': 'ElectricityGeneratingPowerPlant',  # use dcid:ElectricUtility?
}

# If the value_code exists in the map code_map,
# the property is added with the mapped value into stat_var_pv


def add_pv_from_map(prop: str, value_code: str, code_map, stat_var_pv) -> bool:
    if value_code not in code_map:
        return False
    prop_value = code_map[value_code]
    if prop_value is None:
        return False
    stat_var_pv[prop] = 'dcid:' + prop_value
    return True


def get_pv_for_production_code(code: str, counters=None) -> {str: str}:
    """The production code is roughly formatted as:
       01<ProducerType><FuelType><PlantType> where
       ProducerType is:
          '5': Main activity
          '6': Auto producer
       FuelType:
          1 or 2 letter code
       PlantType:
          C: CHP plant
          E: Electricity plant
          H: Heat plant 
    """
    pv = {}
    if not code.startswith('01'):
        return pv
    code = code.removeprefix('01')
    # Add default production variables.
    pv['measuredProperty'] = 'Production'

    # Add an optional producer type.
    if add_pv_from_map('energyProducerType', code[:1], UN_ENERGY_PRODUCER_TYPE, pv):
        code = code[1:]

    # Add fuel type as energySource which could be a 1-3 letter prefix.
    for l in [3, 2, 1]:
        value_code = code[:l]
        if add_pv_from_map('energySource', code[:l], UN_ENERGY_FUEL_TYPE, pv):
            code = code[l:]
            break

    # Add plant type from the remaining code
    if add_pv_from_map('energyProducerType', code[:1], UN_ENERGY_PLANT_TYPE, pv):
        code = code[1:]

    if len(code) > 0 and counters is not None:
        counters['error_ignored_producer_code'] += 1
    return pv


def get_pv_for_energy_code(code: str, counters=None) -> {str: str}:
    """Get the property values for the given transaction code.
       The prefix of the transaction code indicates the activity.
       Based on the activity the transaction code is further split to
       get constriants for the activity.
    """
    if code.startswith('01'):
        return get_pv_for_production_code(code, counters)

    if len(code) > 0 and counters is not None:
        counters['error_ignored_energy_code'] += 1
    return {}


# TODO(ajaits): define new entities in the KG schema
UN_ENERGY_UNITS = {
    'cubicmetres': 'dcid:CubicMeter',  # new
    'kilowatthours': 'dcid:KilowattHour',
    'kilowatthour': 'dcid:KilowattHour',
    'kwh': 'dcid:KilowattHour',
    'kilowatts': 'dcid:Kilowatt',  # new
    'kilowatt': 'dcid:Kilowatt',  # new
    'kw': 'dcid:Kilowatt',  # new
    'metrictons': 'dcid:MetricTon',
    'metricton': 'dcid:MetricTon',
    'terajoules': 'dcid:Terajoule',  # new
    'terajoule': 'dcid:Terajoule',  # new
    'tj': 'dcid:Terajoule',  # new
}

UN_ENERGY_UNITS_MULTIPLIER = {
    'thousand': 1000,
    'million': 1000000,
}


def get_unit_dcid_scale(units_scale: str) -> (str, str):
    units = re.sub('[^a-z,]', '', units_scale.lower())
    multiplier = None
    if ',' in units:
        units, multiplier = units.split(',', 2)

    units_dcid = None
    if units in UN_ENERGY_UNITS:
        units_dcid = UN_ENERGY_UNITS[units]

    multiplier_num = 1
    if multiplier is not None and multiplier in UN_ENERGY_UNITS_MULTIPLIER:
        multiplier_num = UN_ENERGY_UNITS_MULTIPLIER[multiplier]
    return (units_dcid, multiplier_num)
