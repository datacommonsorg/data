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
# Used as values for property: energySource
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
    'LP':  'LiquifiedPetroleumGas',  # new
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
    'WS':  'WhiteSpirit',  # new
    'EW': 'dcs:Wind',  # Wind Electricity
}


def get_all_energy_source_codes() -> List[str]:
    return list(UN_ENERGY_CODES.keys())


def get_energy_source_dcid(fuel_type: str) -> str:
    if fuel_type in UN_ENERGY_CODES:
        return UN_ENERGY_CODES[fuel_type]
    return None

# Types of EnergyProducerEnum
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

# Types of EnergySourceEnum
# TODO(ajaits): should this be EnergySourceTypeEnum for energySourceType?
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
# Types for EnergyProducerEnum
# values for property: energyProducerType
UN_ENERGY_PLANT_TYPE = {
    'C': 'CombinedHeatPowerGeneratingPowerPlant',
    'H': 'HeatGeneratingPowerPlant',
    'E': 'ElectricityGeneratingPowerPlant',  # use dcid:ElectricUtility?
}

# TODO(ajaits): Add to ElectricityConsumer
# Types of EnergyConsumerEnum by industry type.
# values for property: energyConsumerType
UN_ENERGY_CONSUMING_INDUSTRY = {
    # Manufacturing industry
    '1': 'Manufacturing',  # new
    '11': 'IronSteel',  # new
    '13': 'ChemicalPetrochemicalIndustry',  # new
    '14': 'OtherIndustry',  # new
    '14a': 'NonferrousMetalsIndustry',  # new
    '14b': 'NonmetallicMineralsIndustry',  # new
    '14c': 'TransportEquipmentIndustry',  # new
    '14d': 'MachineryIndustry',  # new
    '14e': 'Mining',  # new
    '14f': 'FoodIndustry',  # new
    '14g': 'PaperIndustry',  # new
    '14h': 'WoodIndustry',  # new
    '14i': 'ConstructionIndustry',  # new
    '14j': 'TextileIndustry',  # new
    '14o': 'OtherManufacturingIndustry',  # new

    # Transport
    '2': 'TransportIndustry',  # new
    '22': 'RailTransport',  # new
    '23': 'DomesticAviation',  # new
    '24': 'DomesticNavigationTransport',  # new
    '25': 'OtherTransport',  # new
    '26': 'PipelineTransport',  # new
    '3': 'OtherIndustry',  # new
    '31': 'Households',  # new
    '32': 'Agriculture',  # new
    '35': 'Commerce_PublicServices',  # new
    '34': 'OtherIndustry',  # new

    # Other comsumption flows
    '051': 'InternationalMarineBunkers',  # new
    '052': 'InternationalAviationBunkers',  # new
}

# Types of EnergyConsumerEnum by industry type.
# values for property: energyConsumerType
UN_ENERGY_USAGE_CODES = {
    # Transfmation of energy
    '08': 'Transformation',  # new
    '081': 'CokeOvens',  # new
    '082': 'GasWorks',  # new
    '083': 'BriquettingPlants',  # new
    '084': 'BlastFurnaces',  # new
    '085CH': 'CharcoalPlants',  # new
    '085EP': 'ElectricityProduction',  # new
    '085GL': 'Gas_to_LiquidPlant',  # new
    '085LP': 'CoalLiquefactionPlant',  # new
    '085PP': 'PetrochemicalPlant',  # new
    '086': 'OilRefinery',  # new
    '087': 'NaturalGasBlendingPlants',  # new
    '0889E': 'ElectricBoilers',  # new
    '0889H': 'HeatPumps',  # new
    '088': 'ElectricityGeneration',  # new
    '08811': 'ElectricityMainActivityProducer',  # new
    '08812': 'ElectricityAutoproducer',  # new
    '08821': 'CombinedHeatPowerMainActivityProducers',  # new
    '08822': 'CombinedHeatPowerAutoproducer',  # new
    '08831': 'HeatPlantMainActivityProducer',  # new
    '08832': 'HeatPlantAutoproducer',  # new

    # Energy industry own use
    '09': 'EnergyIndustry',  # new
    '0911': 'CoalMines',  # new
    '0912': 'OilGasExtraction',  # new
    '0914': 'BiogasProduction',  # new
    '0915': 'NuclearFuelProcessing',  # new
    '0921': 'CokeOvens',  # new
    '0922': 'GasWorks',  # new
    '0923': 'BriquettingPlants',  # new
    '0924': 'BlastFurnaces',  # new
    '0925': 'OilRefineries',  # new
    '0926': 'PumpStoragePlants',  # new
    '0927': 'ElectricityGeneration',  # new
    '0928': 'Industry',  # new
    '0930': 'CoalLiquefactionPlants',  # new
    '0931': 'NaturalGasPlants',  # new
    '0932': 'GasToLiquidPlants',  # new
    '0933': 'CharcoalPlants',  # new
    '0934': 'LiquifiedNaturalGasPlants',  # new
}

# Properties used as measuredProperty
UN_ENERGY_FLOW_CODES = {
    '01prop': 'generation',
    '02': 'receipt',  # new
    '03': 'imports',  # new
    '04': 'exports',  # new
    '06': 'stocks',  # new
    '07': 'productReclassification',  # new
    '11': 'nonEnergyConsumption',  # new
    'NA': 'consumption',  # new
    'GA': 'energySupply',  # new
    '21': 'energyStocksOpening',  # new
    '22': 'energyStocksClosing',  # new
    '15': 'energyReserve',  # new
    '16': 'energyReserve',  # new
    '10': 'energyLoss',  # new
}

# List of rangeIncludes for new properties.
UN_ENERGY_PROPERTY_RANGES = {
    'energySource': ['EnergySourceEnum'],
    'energyProducerType':  ['EnergyProducerEnum'],
    'energyConsumerType':  ['EnergyConsumerEnum'],
    'energyReserveType': ['EnergyConsumerEnum'],
    'energyLostAs': ['EnergyConsumerEnum'],
}

# energy capacity codes '13*' EnergySource
# TODO(ajaits): suffix of 1/2 for Main/Auto producer dropped
# Additional types for EnergySourceEnum
# used as property for energySource.
UN_ENERGY_CAPACITY_CODES = {
    '1': 'Refinery',  # new
    '3': 'ElectricityMainActivityAutoProducer',  # new
    '31': 'Nuclear',  # new
    '311': 'PublicNuclear',  # new
    '312': 'SelfProducerNuclear',  # new
    '32': 'dcs:EIA_Water',  # 'Hydro'
    '33': 'Geothermal',  # new
    '34': 'CombustibleFuel',  # new
    '35': 'dcs:Wind',
    '36': 'dcs:Solar',
    '37': 'Tide',  # new
    '39': 'Others',  # new
    'PH': 'PumpedHydro',
    'PV': 'SolarPV',  # new
    'ST': 'SolarThermal',  # new
}

# Energy Loss codes
# Prefixed with 10*
# Types of EnergyLossEnum
# Used as values for property energyLostAs
UN_ENERGY_LOSS_CODES = {
    '101': 'EnergyLost',  # new
    '103': 'EnergyReInjected',  # new
    '104': 'GasLostFlaredAndVented',  # new
    '104A': 'GasLostFlared',  # new
    '104B': 'GasLostVented',  # new
    '105': 'FuelLossDuringExtraction',  # new
}

# Energy reserves: prefixed with code 15* or 16*
# Types of EnergyReservesEnum
# Used as values for property type: energyReserveType
UN_ENERGY_RESERVE_CODES = {
    '15': 'EnergyResourcesInPlace',  # new
    '151': 'EnergyKnownReserves',  # new
    '1511': 'EnergyRecoverableReserves',  # new
    '152': 'EnergyAdditionalResources',  # new
    '161': 'EnergyReserves',  # new
    '162': 'EnergyReservesOilShaleTarSands',  # new
    '1621': 'EnergyReservesOilShale',  # new
    '1622': 'EnergyReservesTarSands',  # new
    '163': 'EnergyReservesOther',  # new
    '17': 'EnergyResources',  # new
    '181': 'EnergyReservesAssured',  # new
    '182': 'EnergyReservesAdditional',  # new
    '19': 'HydraulicResources',  # new
}

# If the value_code exists in the map code_map,
# the property is added with the mapped value into stat_var_pv


def add_pv_from_map(prop: str, value_code: str, code_map, stat_var_pv) -> bool:
    if value_code not in code_map:
        return False
    prop_value = code_map[value_code]
    if prop_value is None:
        return False
    if prop_value.find(':') == -1:
        prop_value = f'dcid:{prop_value}'
    stat_var_pv[prop] = prop_value
    return True


# If the value_code exists in the map code_map,
# the property is added with the mapped value into stat_var_pv
def add_pv_from_map_for_prefix(prop: str, value_code: str,
                               code_map, stat_var_pv) -> bool:
    # Look for codes in map from longest prefix to the shortest
    for l in reversed(range(1, len(value_code) + 1)):
        if add_pv_from_map(prop, value_code[:l], code_map, stat_var_pv):
            return True
    # No codes in map for any prefix length.
    return False


def get_pv_for_production_code(code: str, counters=None) -> {str: str}:
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
    pv = {}
    if not code.startswith('01'):
        return pv
    code = code.removeprefix('01')
    # Add default production variables.
    pv['measuredProperty'] = 'dcs:generation'

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


def get_pv_for_consumption_code(code: str, counters=None) -> {str: str}:
    """Consumption code is formatted as follows:
       12<1-digit-ConsumingSector><sub-sector>
       ConsumingSectors are:
         '1': Manufacturing
         '2': Transport
         '3': others
    """
    pv = {}
    if not code.startswith('12'):
        return pv
    code = code.removeprefix('12')
    pv['measuredProperty'] = 'dcs:consumption'  # new
    if not add_pv_from_map_for_prefix('energyConsumerType', code,
                                      UN_ENERGY_CONSUMING_INDUSTRY, pv):
        counters['error_ignored_consumer_code'] += 1
    return pv


def get_pv_for_capacity_code(code: str, counters=None) -> {str: str}:
    pv = {}
    if not code.startswith('13'):
        return pv
    code = code.removeprefix('13')
    # TODO(ajaits): create a new code for capacity?
    pv['measuredProperty'] = 'dcs:generation'
    if not add_pv_from_map_for_prefix('energySource', code, UN_ENERGY_CAPACITY_CODES, pv):
        counters['error_ignored_capacity_code'] += 1
    return pv


def get_pv_for_energy_code(code: str, counters=None) -> {str: str}:
    """Get the property values for the given transaction code.
       The prefix of the transaction code indicates the activity.
       Based on the activity the transaction code is further split to
       get constriants for the activity.
    """
    if code.startswith('01'):
        return get_pv_for_production_code(code, counters)

    if code.startswith('12'):
        return get_pv_for_consumption_code(code, counters)

    if code.startswith('13'):
        return get_pv_for_capacity_code(code, counters)

    pv = {}
    if add_pv_from_map_for_prefix('energyConsumerType', code, UN_ENERGY_USAGE_CODES, pv):
        pv['measuredProperty'] = 'dcs:consumption'  # new
        return pv

    if code.startswith('10'):
        if add_pv_from_map_for_prefix('energyLostAs', code, UN_ENERGY_LOSS_CODES, pv):
            pv['measuredProperty'] = 'dcs:energyLoss'  # new
        return pv

    if add_pv_from_map_for_prefix('energyReserveType', code,
                                  UN_ENERGY_RESERVE_CODES, pv):
        pv['measuredProperty'] = 'dcs:energyReserves'  # new
        return pv

    if add_pv_from_map_for_prefix('measuredProperty', code, UN_ENERGY_FLOW_CODES, pv):
        return pv

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


def generate_un_energy_code_enums(node_id_map):
    """Generate a set of MCF nodes for all UN energy code enums."""
    mcf_nodes = []
    mcf_nodes += generate_enum_mcf_for_list('EnergySourceEnum', UN_ENERGY_CODES.values(),
                                            node_id_map)
    mcf_nodes += generate_enum_mcf_for_list('EnergySourceEnum', UN_ENERGY_FUEL_TYPE.values(),
                                            node_id_map)

    mcf_nodes += generate_enum_mcf_for_list('EnergyProducerEnum', UN_ENERGY_PRODUCER_TYPE.values(),
                                            node_id_map)
    mcf_nodes += generate_enum_mcf_for_list('EnergyProducerEnum', UN_ENERGY_PLANT_TYPE.values(),
                                            node_id_map)
    mcf_nodes += generate_enum_mcf_for_list('EnergyConsumerEnum', UN_ENERGY_CONSUMING_INDUSTRY.values(),
                                            node_id_map)
    mcf_nodes += generate_enum_mcf_for_list('EnergyConsumerEnum', UN_ENERGY_USAGE_CODES.values(),
                                            node_id_map)
    mcf_nodes += generate_enum_mcf_for_list('EnergySourceEnum', UN_ENERGY_CAPACITY_CODES.values(),
                                            node_id_map)
    mcf_nodes += generate_enum_mcf_for_list('EnergyLossEnum', UN_ENERGY_LOSS_CODES.values(),
                                            node_id_map)
    mcf_nodes += generate_enum_mcf_for_list('EnergyReservesEnum', UN_ENERGY_RESERVE_CODES.values(),
                                            node_id_map)
    mcf_nodes += generate_property_mcf_for_list(
        UN_ENERGY_FLOW_CODES.values(), {}, ['Number'], node_id_map)

    mcf_nodes += generate_property_mcf_for_list(
        UN_ENERGY_PROPERTY_RANGES.keys(), UN_ENERGY_PROPERTY_RANGES, None, node_id_map)
    return mcf_nodes
