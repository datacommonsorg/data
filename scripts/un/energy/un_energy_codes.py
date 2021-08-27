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
"""Utilities to map UNData Energy codes to StatVar properties and values"""

from typing import List

import re

# Map from UNData Energy commodity codes to EnergySourceEnum
UN_ENERGY_FUEL_CODES = {
    # StatVars with populationType: Fuel, property: fuelType
    'AO':  {'populationType': 'Fuel', 'fuelType': 'AdditivesOxygenates'},
    'AW':  {'populationType': 'Fuel', 'fuelType': 'AnimalWaste'},
    'AT':  {'populationType': 'Fuel', 'fuelType': 'dcs:EIA_AnthraciteCoal'},
    'AV':  {'populationType': 'Fuel', 'fuelType': 'AviationGasoline'},
    'BS':  {'populationType': 'Fuel', 'fuelType': 'Bagasse'},
    'BJ':  {'populationType': 'Fuel', 'fuelType': 'BioJetKerosene'},
    'BD':  {'populationType': 'Fuel', 'fuelType': 'BioDiesel'},
    'BI':  {'populationType': 'Fuel', 'fuelType': 'BioGas'},
    'AL':  {'populationType': 'Fuel', 'fuelType': 'BioGasoline'},
    'BT':  {'populationType': 'Fuel', 'fuelType': 'dcs:EIA_BituminousCoal'},
    'PU':  {'populationType': 'Fuel', 'fuelType': 'BlackLiquor'},
    'BG':  {'populationType': 'Fuel', 'fuelType': 'BlastFurnaceGas'},
    'LB':  {'populationType': 'Fuel', 'fuelType': 'BrownCoal'},
    'BB':  {'populationType': 'Fuel', 'fuelType': 'BrownCoalBriquettes'},
    'CH':  {'populationType': 'Fuel', 'fuelType': 'Charcoal'},
    'CT':  {'populationType': 'Fuel', 'fuelType': 'CoalTar'},
    'OK':  {'populationType': 'Fuel', 'fuelType': 'CokeOvenCoke'},
    'OG':  {'populationType': 'Fuel', 'fuelType': 'CokeOvenGas'},
    'CC':  {'populationType': 'Fuel', 'fuelType': 'CokingCoal'},
    'CR':  {'populationType': 'Fuel', 'fuelType': 'CrudeOil'},
    'EA':  {'populationType': 'Fuel', 'fuelType': 'Ethane'},
    'WF':  {'populationType': 'Fuel', 'fuelType': 'FallingWater'},
    'RF':  {'populationType': 'Fuel', 'fuelType': 'FuelOil'},
    'FW':  {'populationType': 'Fuel', 'fuelType': 'Fuelwood'},
    'GK':  {'populationType': 'Fuel', 'fuelType': 'GasCoke'},
    'DL':  {'populationType': 'Fuel', 'fuelType': 'DieselOil'},
    'GJ':  {'populationType': 'Fuel', 'fuelType': 'GasolineJetFuel'},
    'GG':  {'populationType': 'Fuel', 'fuelType': 'GasworksGas'},
    'CL':  {'populationType': 'Fuel', 'fuelType': 'HardCoal'},
    'IW':  {'populationType': 'Fuel', 'fuelType': 'IndustrialWaste'},
    'JF':  {'populationType': 'Fuel', 'fuelType': 'KeroseneJetFuel'},
    'LN':  {'populationType': 'Fuel', 'fuelType': 'dcs:LigniteCoal'},  # Lignite
    'LP':  {'populationType': 'Fuel', 'fuelType': 'LiquifiedPetroleumGas'},
    'LU':  {'populationType': 'Fuel', 'fuelType': 'Lubricants'},
    'MO':  {'populationType': 'Fuel', 'fuelType': 'MotorGasoline'},
    'MW':  {'populationType': 'Fuel', 'fuelType': 'MunicipalWaste'},
    'NP':  {'populationType': 'Fuel', 'fuelType': 'Naphtha'},
    'NG':  {'populationType': 'Fuel', 'fuelType': 'dcs:NaturalGas'},
    'GL':  {'populationType': 'Fuel', 'fuelType': 'NaturalGasLiquids'},
    'EN':  {'populationType': 'Fuel', 'fuelType': 'dcs:Nuclear'},
    'ZJ':  {'populationType': 'Fuel', 'fuelType': 'BioJetKerosene'},
    'ZD':  {'populationType': 'Fuel', 'fuelType': 'BioDiesel'},
    'ZG':  {'populationType': 'Fuel', 'fuelType': 'BioGasoline'},
    'OS':  {'populationType': 'Fuel', 'fuelType': 'OilShale'},
    'OB':  {'populationType': 'Fuel', 'fuelType': 'UN_OtherBituminousCoal'},
    'CP':  {'populationType': 'Fuel', 'fuelType': 'CoalProducts'},
    'OH':  {'populationType': 'Fuel', 'fuelType': 'UN_OtherHydrocarbons'},
    'KR':  {'populationType': 'Fuel', 'fuelType': 'dcs:EIA_Kerosene'},
    'OL':  {'populationType': 'Fuel', 'fuelType': 'UN_OtherLiquidBiofuels'},
    'PP':  {'populationType': 'Fuel', 'fuelType': 'UN_OtherOilProducts'},
    'BO':  {'populationType': 'Fuel', 'fuelType': 'UN_OtherRecoveredGases'},
    'VW':  {'populationType': 'Fuel', 'fuelType': 'VegetalWaste'},
    'PW':  {'populationType': 'Fuel', 'fuelType': 'ParaffinWaxes'},
    'BC':  {'populationType': 'Fuel', 'fuelType': 'PatentFuel'},
    'PT':  {'populationType': 'Fuel', 'fuelType': 'Peat'},
    'BP':  {'populationType': 'Fuel', 'fuelType': 'PeatProducts'},
    'PK':  {'populationType': 'Fuel', 'fuelType': 'dcs:PetroleumCoke'},
    'FS':  {'populationType': 'Fuel', 'fuelType': 'RefineryFeedstocks'},
    'RG':  {'populationType': 'Fuel', 'fuelType': 'RefineryGas'},
    'SB':  {'populationType': 'Fuel', 'fuelType': 'dcs:EIA_SubbituminousCoal'},
    'UR':  {'populationType': 'Fuel', 'fuelType': 'Uranium'},
    'WS':  {'populationType': 'Fuel', 'fuelType': 'WhiteSpirit'},

    # StatVars with populationType: Energy, property: energySource
    'DG':  {'populationType': 'Energy', 'energySource': 'Geothermal'},
    'DS':  {'populationType': 'Energy', 'energySource': 'SolarThermal'},
    'EG':  {'populationType': 'Energy', 'energySource': 'dcs:Geothermal'},
    'ST':  {'populationType': 'Energy', 'usedFor': 'Heat'},
    'HF':  {'populationType': 'Energy', 'energySource': 'HeatCombustibleFuels'},
    'EH':  {'populationType': 'Energy', 'energySource': 'dcs:EIA_Water'},  # Hydro
    # Solar Electricity
    'ES':  {'populationType': 'Energy', 'energySource': 'dcs:Solar'},

    'EW':  {'populationType': 'Electricity', 'energySource': 'dcs:Wind'},
    'ET':  {'populationType': 'Electricity', 'usedFor': 'ThermalElectricity'},
    'EO':  {'populationType': 'Electricity', 'energySource': 'OceanElectricity'},
    'EL':  {'populationType': 'Electricity'},  # Total Electricity
    'GR':  {'populationType': 'Energy', 'powerPlantSector': 'Refinery'},
    'EC':  {'populationType': 'Electricity', 'measuredProperty': 'capacity'},
}

# Types of EnergySourceEnum used in transaction code with other
# commodity codes like Electricity.
UN_ENERGY_SOURCE_TYPE = {
    'C': {'energySource': 'CombustibleFuel'},
    'EB': {'energySource': 'ElectricBoiler'},
    'G': {'energySource': 'Geothermal'},
    'HY': {'energySource': 'ConventionalHydroelectric'},
    'HP': {'energySource': 'HeatPump'},
    'H': {'energySource': 'ChemicalHeat'},
    'N': {'energySource': 'Nuclear'},
    'O': {'energySource': 'UN_OtherFuel'},
    'PH': {'energySource': 'PumpedHydro'},
    'S': {'energySource': 'Solar'},
    'SP': {'energySource': 'SolarPhotovoltaic'},
    'ST': {'energySource': 'SolarThermal'},
    'T': {'energySource': 'Tidal'},
    'W': {'energySource': 'Wind'},
    'BI': {'energySource': 'BioGas'},
    'BS': {'energySource': 'Bagasse'},
    'CL': {'energySource': 'Coal'},
    'CP': {'energySource': 'CoalProducts'},
    'DL': {'energySource': 'DieselOil'},
    'LB': {'energySource': 'BrownCoal'},
    'LBF': {'energySource': 'LiquidBioFuel'},
    'SBF': {'energySource': 'SolidBioFuel'},
    'MG': {'energySource': 'ManufacturedGas'},
    'NG': {'energySource': 'NaturalGas'},
    'NRW': {'energySource': 'NonRenewableWaste'},
    'OS': {'energySource': 'OilShale'},
    'PP': {'energySource': 'OilProducts'},
    'PT': {'energySource': 'Peat'},
    'RF': {'energySource': 'FuelOil'},
    'RW': {'energySource': 'MunicipalWaste'},
}


def get_all_energy_source_codes() -> List[str]:
    return list(UN_ENERGY_FUEL_CODES.keys())


# Types of PowerPlantSectorEnum
# Values for property: powerPlantSector
UN_ENERGY_PRODUCER_TYPE = {
    '0': {'powerPlantSector': 'OffshorePlants'},
    '3': {'powerPlantSector': 'Refinery'},
    '4': {},  # Plants producing petroleum products
    '5': {'powerPlantSector': 'MainActivityProducer'},
    '6': {'powerPlantSector': 'AutoProducer'},
    '8': {},  # gross production
    '9': {},  # net production
    'C': {'powerPlantSector': 'CombinedHeatPowerPlants'},
    'H': {'powerPlantSector': 'HeatPlants'},
    'E': {'powerPlantSector': 'ElectricityPowerPlants'},
    '5C': {'powerPlantSector': 'MainActivityProducerCombinedHeatPowerPlants'},
    '5H': {'powerPlantSector': 'MainActivityProducerHeatPowerPlants'},
    '5E': {'powerPlantSector': 'MainActivityProducerElectricityPowerPlants'},
    '6C': {'powerPlantSector': 'AutoProducerCombinedHeatPowerPlants'},
    '6H': {'powerPlantSector': 'AutoProducerHeatPowerPlants'},
    '6E': {'powerPlantSector': 'AutoProducerElectricityPowerPlants'},
}

# Types for PowerPlantSectorEnum by the suffix code.
# values for property: powerPlantSector
UN_ENERGY_PLANT_TYPE = {
    'C': {'powerPlantSector': 'CombinedHeatPowerPlants'},
    'H': {'powerPlantSector': 'HeatPlants'},
    'E': {'powerPlantSector': 'ElectricityPowerPlants'},
}

# Types of EnergyConsumptionSectorEnum by industry type.
# values for property: consumingSector
UN_ENERGY_CONSUMING_INDUSTRY = {
    # Manufacturing industry
    '1': {'consumingSector': 'Manufacturing'},
    '11': {'consumingSector': 'IronSteel'},
    '13': {'consumingSector': 'ChemicalPetrochemicalIndustry'},
    '14': {'consumingSector': 'UN_OtherIndustry'},
    '14a': {'consumingSector': 'NonFerrousMetalsIndustry'},
    '14b': {'consumingSector': 'NonMetallicMineralsIndustry'},
    '14c': {'consumingSector': 'TransportEquipmentIndustry'},
    '14d': {'consumingSector': 'MachineryIndustry'},
    '14e': {'consumingSector': 'Mining'},
    '14f': {'consumingSector': 'FoodAndTobaccoIndustry'},
    '14g': {'consumingSector': 'PaperPulpPrintIndustry'},
    '14h': {'consumingSector': 'WoodAndWoodProductsIndustry'},
    '14i': {'consumingSector': 'ConstructionIndustry'},
    '14j': {'consumingSector': 'TextileAndLeatherIndustry'},
    '14o': {'consumingSector': 'UN_OtherManufacturingIndustry'},

    # Transport
    '2': {'consumingSector': 'TransportIndustry'},
    '22': {'consumingSector': 'RailTransport'},
    '23': {'consumingSector': 'DomesticAviationTransport'},
    '24': {'consumingSector': 'DomesticNavigationTransport'},
    '25': {'consumingSector': 'UN_OtherTransport'},
    '26': {'consumingSector': 'PipelineTransport'},
    '3': {'consumingSector': 'UN_OtherIndustry'},
    '31': {'consumingSector': 'Households'},
    '32': {'consumingSector': 'Agriculture'},
    '35': {'consumingSector': 'CommerceAndPublicServices'},
    '34': {'consumingSector': 'UN_OtherIndustry'},
}

# Types of EnergyConsumptionSectorEnum by industry type.
# values for property: consumingSector and usedFor
UN_ENERGY_USAGE_CODES = {
    # Transfmation of energy
    '08': {'consumingSector': 'FuelTransformationIndustry', 'usedFor': 'FuelTransformation'},
    '081': {'consumingSector': 'CokeOvens', 'usedFor': 'FuelTransformation'},
    '082': {'consumingSector': 'GasWorks', 'usedFor': 'FuelTransformation'},
    '083': {'consumingSector': 'BriquettingPlants', 'usedFor': 'FuelTransformation'},
    '084': {'consumingSector': 'BlastFurnaces', 'usedFor': 'FuelTransformation'},
    '085CH': {'consumingSector': 'CharcoalPlants', 'usedFor': 'FuelTransformation'},
    '085EP': {'consumingSector': 'ElectricityGeneration', 'usedFor': 'FuelTransformation'},
    '085GL': {'consumingSector': 'GasToLiquidPlants', 'usedFor': 'FuelTransformation'},
    '085LP': {'consumingSector': 'CoalLiquefactionPlants', 'usedFor': 'FuelTransformation'},
    '085PP': {'consumingSector': 'PetrochemicalPlants', 'usedFor': 'FuelTransformation'},
    '086': {'consumingSector': 'OilRefineries', 'usedFor': 'FuelTransformation'},
    '087': {'consumingSector': 'NaturalGasPlants', 'usedFor': 'FuelTransformation'},
    '089': {'consumingSector': 'UN_OtherIndustry', 'usedFor': 'FuelTransformation'},
    '0889E': {'consumingSector': 'ElectricBoilers', 'usedFor': 'FuelTransformation'},
    '0889H': {'consumingSector': 'HeatPumps', 'usedFor': 'FuelTransformation'},
    '088': {'consumingSector': 'ElectricityGeneration', 'usedFor': 'FuelTransformation'},
    '08811': {'consumingSector': 'MainActivityProducerElectricityPowerPlants', 'usedFor': 'FuelTransformation'},
    '08812': {'consumingSector': 'AutoProducerElectricityPowerPlants', 'usedFor': 'FuelTransformation'},
    '08821': {'consumingSector': 'MainActivityProducerCombinedHeatPowerPlants', 'usedFor': 'FuelTransformation'},
    '08822': {'consumingSector': 'AutoProducerCombinedHeatPowerPlants', 'usedFor': 'FuelTransformation'},
    '08831': {'consumingSector': 'MainActivityProducerHeatPowerPlants', 'usedFor': 'FuelTransformation'},
    '08832': {'consumingSector': 'AutoProducerHeatPowerPlants', 'usedFor': 'FuelTransformation'},

    # Energy industry own use
    '09': {'consumingSector': 'EnergyIndustry', 'usedFor': 'EnergyIndustryOwnUse'},
    '0911': {'consumingSector': 'CoalMines', 'usedFor': 'EnergyIndustryOwnUse'},
    '0912': {'consumingSector': 'OilGasExtraction', 'usedFor': 'EnergyIndustryOwnUse'},
    '0914': {'consumingSector': 'BiogasProduction', 'usedFor': 'EnergyIndustryOwnUse'},
    '0915': {'consumingSector': 'NuclearFuelProcessing', 'usedFor': 'EnergyIndustryOwnUse'},
    '0921': {'consumingSector': 'CokeOvens', 'usedFor': 'EnergyIndustryOwnUse'},
    '0922': {'consumingSector': 'GasWorks', 'usedFor': 'EnergyIndustryOwnUse'},
    '0923': {'consumingSector': 'BriquettingPlants', 'usedFor': 'EnergyIndustryOwnUse'},
    '0924': {'consumingSector': 'BlastFurnaces', 'usedFor': 'EnergyIndustryOwnUse'},
    '0925': {'consumingSector': 'OilRefineries', 'usedFor': 'EnergyIndustryOwnUse'},
    '0926': {'consumingSector': 'PumpStoragePlants', 'usedFor': 'EnergyIndustryOwnUse'},
    '0927': {'consumingSector': 'ElectricityGeneration', 'usedFor': 'EnergyIndustryOwnUse'},
    '0928': {'consumingSector': 'Industry', 'usedFor': 'EnergyIndustryOwnUse'},
    '0930': {'consumingSector': 'CoalLiquefactionPlants', 'usedFor': 'EnergyIndustryOwnUse'},
    '0931': {'consumingSector': 'NaturalGasPlants', 'usedFor': 'EnergyIndustryOwnUse'},
    '0932': {'consumingSector': 'GasToLiquidPlants', 'usedFor': 'EnergyIndustryOwnUse'},
    '0933': {'consumingSector': 'CharcoalPlants', 'usedFor': 'EnergyIndustryOwnUse'},
    '0934': {'consumingSector': 'LiquifiedNaturalGasPlants', 'usedFor': 'EnergyIndustryOwnUse'},
}

# Properties used as measuredProperty
UN_ENERGY_FLOW_CODES = {
    '01': {'measuredProperty': 'generation'},
    '02': {'measuredProperty': 'receipts'},
    '03': {'measuredProperty': 'imports'},
    '04': {'measuredProperty': 'exports'},
    '06': {'measuredProperty': 'stocks'},
    '07': {'measuredProperty': 'productReclassification'},
    '11': {'measuredProperty': 'consumption', 'usedFor': 'NonEnergyUse'},
    'NA': {'measuredProperty': 'consumption'},
    'GA': {'measuredProperty': 'generation'},
    # 'measurementQualifier: 'OpeningStocks'
    '21': {'measuredProperty': 'stocks'},
    # 'measurementQualifier': 'ClosingStocks'
    '22': {'measuredProperty': 'stocks'},
    '15': {'measuredProperty': 'reserves'},
    '16': {'measuredProperty': 'reserves'},
    '10': {'measuredProperty': 'loss'},

    # Other capacity codes
    'CP': {'measuredProperty': 'capacity', 'powerPlantSector': 'MainActivityProducer'},
    'CS': {'measuredProperty': 'capacity', 'powerPlantSector': 'AutoProducer'},

    # Other production codes
    'EP': {'measuredProperty': 'generation', 'powerPlantSector': 'MainActivityProducer'},
    'SP': {'measuredProperty': 'generation', 'powerPlantSector': 'AutoProducer'},
    'O': {'measuredProperty': 'generation', 'powerPlantSector': 'Refinery'},

    # Other comsumption flows
    '051': {'measuredProperty': 'consumption', 'consumingSector': 'InternationalMarineBunkers'},
    '052': {'measuredProperty': 'consumption', 'consumingSector': 'InternationalAviationBunkers'},
}

# energy capacity codes '13*' EnergySource
# TODO(ajaits): suffix of 1/2 for Main/Auto producer dropped
#
# Suffix for Power Plant properties for measuredProperty: capacity
# Additional types for EnergySourceEnum
# used as property for energySource with
# additional property powerPlantSector.
UN_ENERGY_CAPACITY_CODES = {
    '1': {'powerPlantSector': 'Refinery'},
    '3': {'powerPlantSector': 'ElectricityPowerPlants'},
    '31': {'energySource': 'Nuclear', 'powerPlantSector': 'ElectricityPowerPlants'},
    # '311': {'energySource': 'PublicNuclear'},
    # '312': {'energySource': 'SelfProducerNuclear'},
    '32': {'energySource': 'dcs:EIA_Water', 'powerPlantSector': 'ElectricityPowerPlants'},
    '33': {'energySource': 'Geothermal', 'powerPlantSector': 'ElectricityPowerPlants'},
    '34': {'energySource': 'CombustibleFuel', 'powerPlantSector': 'ElectricityPowerPlants'},
    '35': {'energySource': 'Wind', 'powerPlantSector': 'ElectricityPowerPlants'},
    '36': {'energySource': 'Solar', 'powerPlantSector': 'ElectricityPowerPlants'},
    '37': {'energySource': 'Tidal', 'powerPlantSector': 'ElectricityPowerPlants'},
    '39': {'energySource': 'UN_OtherFuel'},
    'PH': {'energySource': 'PumpedHydro'},
    'PV': {'energySource': 'SolarPhotovoltaic'},
    'ST': {'energySource': 'SolarThermal'},
}

# Suffix for powerPlant sector for measuredProperty: capacity
UN_ENERGY_CAPACITY_PLANT_CODE = {
    '1': {'powerPlantSector': 'MainActivityProducer'},
    '2': {'powerPlantSector': 'AutoProducer'}
}

# Energy Loss codes
# Prefixed with 10*
# Types of EnergyLossEnum
# Used as values for property energyLostAs
UN_ENERGY_LOSS_CODES = {
    '101': {'measuredProperty': 'dcid:loss'},  # EnergyLost
    '103': {'lossReason': 'EnergyReInjected'},
    '104': {'lossReason': 'GasLostFlaredAndVented'},
    '104A': {'lossReason': 'GasLostFlared'},
    '104B': {'lossReason': 'GasLostVented'},
    '105': {'lossReason': 'FuelLossDuringExtraction'},
}

# Energy reserves: prefixed with code 15* or 16*
# Types of EnergyReservesEnum
# Used as values for property type: energyReserveType
UN_ENERGY_RESERVE_CODES = {
    '15': {'measuredProperty': 'reserves'},
    '151': {'reserveType': 'EnergyKnownReserves'},
    '1511': {'reserveType': 'EnergyRecoverableReserves'},
    '152': {'reserveType': 'EnergyAdditionalResources'},
    '161': {'measuredProperty': 'reserves'},
    '162': {'measuredProperty': 'reserves', 'energySource': 'OilShaleAndTarSands'},
    '1621': {'measuredProperty': 'reserves', 'energySource': 'OilShale'},
    '1622': {'measuredProperty': 'reserves', 'energySource': 'TarSands'},
    '163': {'reserveType': 'EnergyAdditionalResources'},
    '17': {'measuredProperty': 'reserves'},
    '181': {'reserveType': 'EnergyReservesAssured'},
    '182': {'reserveType': 'EnergyAdditionalResources'},
    '19': {'reserveType': 'HydraulicResources'},
}


# Set of property enum values that are a combination of other values.
# The key is the sorted set of values to be merged, with an _ delimiter.
UN_ENERGY_MERGED_CODES = {
  'CombinedHeatPowerPlants_MainActivityProducer': 'MainActivityProducerCombinedHeatPowerPlants',
  'HeatPlants_MainActivityProducer':  'MainActivityProducerHeatPowerPlants',
  'ElectricityPowerPlants_MainActivityProducer': 'MainActivityProducerElectricityPowerPlants',
  'AutoProducer_CombinedHeatPowerPlants': 'AutoProducerCombinedHeatPowerPlants',
  'AutoProducer_HeatPlants':  'AutoProducerHeatPowerPlants',
  'AutoProducer_ElectricityPowerPlants': 'AutoProducerElectricityPowerPlants',
}


def _add_error_counter(counter_name: str, error_msg: str, counters):
    if counters is None:
        return
    mod_lines = 1
    if 'debug_lines' in counters and counters['debug_lines'] > 0:
        mod_lines = counters['debug_lines']
    if counters[counter_name] % mod_lines == 0:
        print("Error: ", counter_name, ": ", error_msg)
    counters[counter_name] += 1

def remove_namespace_prefix(value: str) -> str:
    """Returns the string without the 'namespace:' prefix
    """
    delim = value.find(':')
    return value[delim + 1:]

def get_merged_values(values: list) -> str:
    """Returns a merged string for the given list of values
       by removing prefix, sorting alphabetically and joining with '_'
    """
    merge_values = []
    for v in values:
       merge_values.append(remove_namespace_prefix(v))
    return '_'.join(sorted(merge_values))

def add_pv_to_stat_var(prop: str, value: str, stat_var_pv, counters=None):
    """Add a property with value to the statVar.
       If the property already exists, the value is overridden.
    """
    if prop in stat_var_pv:
        old_value = remove_namespace_prefix(stat_var_pv[prop])
        current_value = remove_namespace_prefix(value)
        if current_value != old_value:
            # Check if there is specific merged value
            merged_value  = get_merged_values([old_value, current_value])
            if merged_value in UN_ENERGY_MERGED_CODES:
                value = UN_ENERGY_MERGED_CODES[merged_value]
            else:
                _add_error_counter(f'warning_overwriten_property_{prop}',
                                   f'Overwriting value for property:{prop} from {old_value} to {value}', counters)
    if value.find(':') == -1:
        value = f'dcid:{value}'
    stat_var_pv[prop] = value


# If the key exists in the map code_map,
# the set of mapped properties and their values are added into stat_var_pv
# and returns True
def add_pv_from_map(key: str, code_map, stat_var_pv, counters=None) -> bool:
    if key not in code_map:
        return False
    prop_value = code_map[key]
    if prop_value is None:
        return False
    for p in prop_value:
        add_pv_to_stat_var(p, prop_value[p], stat_var_pv, counters)
    return True


# If the value_code exists in the map code_map,
# the property is added with the mapped value into stat_var_pv
# Returns the prefix of value_code which was found.
def add_pv_from_map_for_prefix(value_code: str,
                               code_map, stat_var_pv, counters=None) -> str:
    # Look for codes in map from longest prefix to the shortest
    for l in reversed(range(1, len(value_code) + 1)):
        prefix = value_code[:l]
        if add_pv_from_map(prefix, code_map, stat_var_pv, counters):
            return prefix
    # No codes in map for any prefix length.
    return None


def add_pv_for_production_code(code: str, pv, counters=None) -> bool:
    """The production code is roughly formatted as:
       01<ProducerType><FuelType><PlantType> where
       ProducerType is:
          '5': Main activity
          '6': Auto producer
       FuelType:
          1 or 2 letter code
       PlantType:
          C: CombinedHeatPower plant
          E: Electricity plant
          H: Heat plant
    """
    orig_code = code
    if not code.startswith('01'):
        return False
    code = code.removeprefix('01')
    # Add default production variables.
    pv['measuredProperty'] = 'dcs:generation'
    producer_code = ''
    # Add an optional producer type.
    if add_pv_from_map(code[:1], UN_ENERGY_PRODUCER_TYPE, pv, counters):
        producer_code = code[:1]
        code = code[1:]

    # Add fuel type as energySource which could be a 1-3 letter prefix.
    energy_source = None
    if 'energySource' in pv:
        energy_source = pv['energySource']
    for l in [3, 2, 1]:
        value_code = code[:l]
        if add_pv_from_map(code[:l], UN_ENERGY_SOURCE_TYPE, pv, counters):
            code = code[l:]
            if energy_source is not None and energy_source != pv['energySource']:
                if energy_source == 'Electricity':
                    pv['producedThing'] = 'dcid:Electricity'
                else:
                    new_energy_source = pv['energySource']
                    _add_error_counter('warning_energy_source_change',
                                       f'Fuel changed {energy_source}->{new_energy_source}',
                                       counters)
            break

    # Add plant type from the remaining code
    producer_code += code[:1]
    if add_pv_from_map(producer_code, UN_ENERGY_PLANT_TYPE, pv, counters) or add_pv_from_map(code[:1], UN_ENERGY_PLANT_TYPE, pv, counters):
        code = code[1:]

    if len(code) > 0:
        _add_error_counter(f'warning_ignored_producer_code_{code}',
                           f'Ignored producer code sufffix: {code} in {orig_code}', counters)
    return pv


def add_pv_for_consumption_code(code: str, pv, counters=None) -> bool:
    """Consumption code is formatted as follows:
         '1': Manufacturing
         '2': Transport
         '3': others
    """
    if not code.startswith('12'):
        return False
    code = code.removeprefix('12')
    pv['measuredProperty'] = 'dcs:consumption'
    if len(code) > 0 and not add_pv_from_map_for_prefix(code,
                                                        UN_ENERGY_CONSUMING_INDUSTRY, pv, counters):
        _add_error_counter('error_ignored_consumer_code',
                           f'Ignored consumption code: {code}', counters)
    return True


def add_pv_for_capacity_code(code: str, pv, counters=None) -> bool:
    if not code.startswith('13'):
        return False
    code = code.removeprefix('13')
    pv['measuredProperty'] = 'dcs:generation'
    prefix = add_pv_from_map_for_prefix(
        code, UN_ENERGY_CAPACITY_CODES, pv, counters)
    if prefix is None:
        _add_error_counter('error_ignored_capacity_code',
                           f'Ignored energy capacity code {code}', counters)
        return False
    code = code.removeprefix(prefix)
    if len(code) > 0:
        # Add plant type
        add_pv_from_map_for_prefix(
            code, UN_ENERGY_CAPACITY_PLANT_CODE, pv, counters)
    return True


def get_pv_for_energy_code(energy_source: str, code: str, counters=None) -> {str: str}:
    """Get the property values for the given transaction code.
       The prefix of the transaction code indicates the activity.
       Based on the activity the transaction code is further split to
       get constriants for the activity.
    """
    pv = {}
    if not add_pv_from_map(energy_source, UN_ENERGY_FUEL_CODES, pv, counters):
        _add_error_counter(f'error_unknown_energy_code_{energy_source}',
                           f'Unknown energy source: {energy_source} with transaction: {code}',
                           counters)

    if code.startswith('01'):
        add_pv_for_production_code(code, pv, counters)
        return pv

    if code.startswith('12'):
        add_pv_for_consumption_code(code, pv, counters)
        return pv

    if code.startswith('13'):
        add_pv_for_capacity_code(code, pv, counters)
        return pv

    if add_pv_from_map_for_prefix(code, UN_ENERGY_USAGE_CODES, pv, counters):
        pv['measuredProperty'] = 'dcs:consumption'
        return pv

    if code.startswith('10'):
        if add_pv_from_map_for_prefix(code, UN_ENERGY_LOSS_CODES, pv, counters):
            pv['measuredProperty'] = 'dcs:loss'
        return pv

    if add_pv_from_map_for_prefix(code, UN_ENERGY_RESERVE_CODES, pv, counters):
        pv['measuredProperty'] = 'dcs:reserves'
        return pv

    if add_pv_from_map_for_prefix(code, UN_ENERGY_FLOW_CODES, pv, counters):
        return pv

    if len(code) > 0:
        _add_error_counter(f'error_ignored_energy_code_{code}',
                           f'Ignored energy transaction code {code}', counters)
    return pv


# TODO(ajaits): define new entities in the KG schema
UN_ENERGY_UNITS = {
    'cubicmetres': 'dcid:CubicMeter',
    'kilowatthours': 'dcid:KilowattHour',
    'kilowatthour': 'dcid:KilowattHour',
    'kwh': 'dcid:KilowattHour',
    'kilowatts': 'dcid:Kilowatt',
    'kilowatt': 'dcid:Kilowatt',
    'kw': 'dcid:Kilowatt',
    'metrictons': 'dcid:MetricTon',
    'metricton': 'dcid:MetricTon',
    'terajoules': 'dcid:Terajoule',
    'terajoule': 'dcid:Terajoule',
    'tj': 'dcid:Terajoule',
}

UN_ENERGY_UNITS_MULTIPLIER = {
    'thousand': 1000,
    'million': 1000000,
}


def get_unit_dcid_scale(units_scale: str) -> (str, int):
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


def get_name_from_id(dcid_str: str) -> str:
    """Converts the camel case into a space separated name """
    if dcid_str is None:
        return None
    # Strip any namespace prefix
    dcid = dcid_str[dcid_str.find(':') + 1:]

    if len(dcid) < 2:
        return dcid

    # Find all case changes
    dcid = dcid[0].upper() + dcid[1:]
    start_idx = [i for i, e in enumerate(dcid)
                 if e.isupper() or e == '_'] + [len(dcid)]

    # Insert spaces at positions where case changes
    words = [dcid[x: y]
             for x, y in zip(start_idx, start_idx[1:]) if dcid[x: y] != '_']
    return ' '.join(words)


def get_unique_list(list_elements):
    """Return a list of unique elements
    """
    list_set = set(list_elements)
    return list(list_set)


def generate_property_mcf_node(prop: str, rangeIncludes):
    """Generate a property node mcf for the given property
       with the list of range includes.
    """
    node_mcf = []
    node_mcf.append(f'Node: {prop}')
    node_mcf.append(f'typeOf: dcs:Property')
    if rangeIncludes is not None:
        node_mcf.append(f'rangeIncludes: {",".join(rangeIncludes)}')
    # TODO(ajaits): check if name is needed as
    #               dc-import requires this to start with lower case
    # name = get_name_from_id(prop)
    # node_mcf.append(f'name: "{name}"')
    return node_mcf


def generate_property_mcf_for_list(prop_list, prop_range_map, default_ranges, node_id_map):
    """Generate property node mcfs for each property in the list
    """
    mcf_nodes = []
    unique_props = get_unique_list(prop_list)
    for prop in unique_props:
        if prop not in node_id_map:
            range_props = default_ranges
            if prop_range_map is not None and prop in prop_range_map:
                range_props = prop_range_map[prop]
            node_mcf = generate_property_mcf_node(prop, range_props)
            mcf_nodes.append(node_mcf)
        node_id_map[prop] += 1

    return mcf_nodes


# TODO(ajaits): declare return of list of list
def generate_enum_mcf_for_list(enum_dcid: str, enum_list, node_id_map):
    """Given a map with property values, returns enum MCF nodes for each value.
    """
    mcf_nodes = []
    if enum_dcid is None:
        return None
    if enum_dcid not in node_id_map:
        # Add a node for the enum itself.
        node_mcf = []
        node_mcf.append(f'Node: dcid:{enum_dcid}')
        node_mcf.append(f'typeOf: schema:Class')
        node_mcf.append(f'subClassOf: schema.Enumeration')
        name = get_name_from_id(enum_dcid)
        if name is not None:
            node_mcf.append(f'name: "{name}"')
        node_id_map[enum_dcid] += 1

    for code in get_unique_list(enum_list):
        if code is not None:
            if code not in node_id_map:
                node_mcf = []
                node_mcf.append(f'Node: dcid:{code}')
                node_mcf.append(f'typeOf: dcid:{enum_dcid}')
                name = get_name_from_id(code)
                if name is not None:
                    node_mcf.append(f'name: "{name}"')
                mcf_nodes.append(node_mcf)
                node_id_map[enum_dcid] += 1
            node_id_map[code] += 1

    return mcf_nodes
