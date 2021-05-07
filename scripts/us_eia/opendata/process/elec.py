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
"""EIA Electricity Dataset specific functions."""

import common
import logging
import re


def extract_place_statvar(series_id, counters):
    """Given the series_id, extract the raw place and stat-var ID.

    Args:
        series_id: EIA series ID
        counters: map for updating error statistics

    Returns a (place, raw-stat-var, is_us_place) tuple.
    """

    if series_id.startswith('ELEC.PLANT.'):
        counters['error_unimplemented_plant_series'] += 1
        return (None, None, None)

    # ELEC.{MEASURE}.{FUEL_TYPE}-{PLACE}-{PRODUCER_SECTOR}.{PERIOD}
    m = re.match(r"^ELEC\.([^.]+)\.([^-]+)-([^-]+)-([^.]+)\.([AQM])$",
                 series_id)
    if m:
        measure = m.group(1)
        fuel_type = m.group(2)
        place = m.group(3)
        producing_sector = m.group(4)
        period = m.group(5)
        sv_id = f'ELEC.{measure}.{fuel_type}-{producing_sector}.{period}'
    else:
        # ELEC.{MEASURE}.{PLACE}-{CONSUMER_SECTOR}.{PERIOD}
        m = re.match(r"^ELEC\.([^.]+)\.([^-]+)-([^.]+)\.([AQM])$", series_id)
        if not m:
            counters['error_unparsable_series'] += 1
            return (None, None)

        measure = m.group(1)
        place = m.group(2)
        consuming_sector = m.group(3)
        period = m.group(4)
        sv_id = f'ELEC.{measure}.{consuming_sector}.{period}'

    return (place, sv_id, True)


##
## Maps for Schema
##

_CONSUMING_SECTOR = {
    'COM': 'Commercial',
    'IND': 'Industrial',
    'OTH': 'OtherSector',
    'RES': 'Residential',
    'TRA': 'Transportation',
    'ALL': 'ALL',
}

_PRODUCING_SECTOR = {
    '1': 'ElectricUtility',
    '2': 'ElectricUtilityNonCogen',
    '3': 'ElectricUtilityCogen',
    '4': 'CommercialNonCogen',
    '5': 'CommercialCogen',
    '6': 'IndustrialNonCogen',
    '7': 'IndustrialCogen',
    '8': 'Residential',
    '94': 'IndependentPowerProducers',
    '96': 'Commercial',
    '97': 'Industrial',
    '98': 'ElectricPower',
    '99': 'ALL',  # Special handled ALL
}

_FUEL_TYPE = {
    'AOR': 'RenewableEnergy',
    'BIS': 'BituminousCoal',
    'BIT': 'BituminousCoal',
    'COL': 'Coal',
    'COW': 'Coal',
    'DPV': 'SmallScaleSolarPhotovoltaic',
    'GEO': 'Geothermal',
    'HPS': 'HydroelectricPumpedStorage',
    'HYC': 'ConventionalHydroelectric',
    'LIG': 'LigniteCoal',
    'NG': 'NaturalGas',
    'NUC': 'Nuclear',
    'OOG': 'OtherGases',
    'OTH': 'Other',
    'PC': 'PetroleumCoke',
    'PEL': 'PetroleumLiquids',
    'SPV': 'UtilityScalePhotovoltaic',
    'STH': 'UtilityScaleThermal',
    'SUB': 'SubbituminousCoal',
    'SUN': 'UtilityScaleSolar',
    'TSN': 'Solar',
    'WAS': 'OtherBiomass',
    'WND': 'Wind',
    'WWW': 'WoodAndWoodDerivedFuels',
    'ALL': 'ALL'
}

# Each value is a list where first entry is StatVar ID component, and the rest
# are StatVar PVs.
_MEASURE_MAP = {
    'ASH_CONTENT': [
        'AshContent_Fuel_ForElectricityGeneration',
        'populationType: dcs:Fuel',
        'measuredProperty: dcs:ashContent',
        'usedFor: dcs:ElectricityGeneration',
        'statType: dcs:measuredValue',
    ],
    'CONS_EG': [
        'Consumption_Fuel_ForElectricityGeneration',
        'populationType: dcs:Fuel',
        'measuredProperty: dcs:consumption',
        'usedFor: dcs:ElectricityGeneration',
        'statType: dcs:measuredValue',
    ],
    'CONS_TOT': [
        'Consumption_Fuel_ForElectricityGenerationAndThermalOutput',
        'populationType: dcs:Fuel',
        'measuredProperty: dcs:consumption',
        'usedFor: dcs:ElectricityGenerationAndThermalOutput',
        'statType: dcs:measuredValue',
    ],
    'CONS_UTO': [
        'Consumption_Fuel_ForUsefulThermalOutput',
        'populationType: dcs:Fuel',
        'measuredProperty: dcs:consumption',
        'usedFor: dcs:UsefulThermalOutputInCHPSystem',
        'statType: dcs:measuredValue',
    ],
    'COST': [
        'Average_Cost_Fuel_ForElectricityGeneration',
        'populationType: dcs:Fuel',
        'measuredProperty: dcs:cost',
        'usedFor: dcs:ElectricityGeneration',
        'statType: dcs:meanValue',
    ],
    'CUSTOMERS': [
        'Count_ElectricityConsumer',
        'populationType: dcs:ElectricityConsumer',
        'measuredProperty: dcs:count',
        'statType: dcs:measuredValue',
    ],
    'GEN': [
        'Generation_Electricity',
        'populationType: dcs:Electricity',
        'measuredProperty: dcs:generation',
        'statType: dcs:measuredValue',
    ],
    'PRICE': [
        'Average_RetailPrice_Electricity',
        'populationType: dcs:Electricity',
        'measuredProperty: dcs:retailPrice',
        'statType: dcs:meanValue',
    ],
    'RECEIPTS': [
        'Receipt_Fuel_ForElectricityGeneration',
        'populationType: dcs:Fuel',
        'measuredProperty: dcs:receipt',
        'statType: dcs:measuredValue',
    ],
    'REV': [
        'SalesRevenue_Electricity',
        'populationType: dcs:Electricity',
        'measuredProperty: dcs:salesRevenue',
        'statType: dcs:measuredValue',
    ],
    'SALES': [
        'RetailSales_Electricity',
        'populationType: dcs:Electricity',
        'measuredProperty: dcs:retailSales',
        'statType: dcs:measuredValue',
    ],
    'STOCKS': [
        'Stock_Fuel_ForElectricityGeneration',
        'populationType: dcs:Fuel',
        'measuredProperty: dcs:stock',
        'statType: dcs:measuredValue',
    ],
    'SULFUR_CONTENT': [
        'SulfurContent_Fuel_ForElectricityGeneration',
        'populationType: dcs:Fuel',
        'measuredProperty: dcs:sulfurContent',
        'usedFor: dcs:ElectricityGeneration',
        'statType: dcs:measuredValue',
    ],
}

# The following measures are the same StatVar as another measure, but differ in
# units (see _UNIT_MAP).
_MEASURE_MAP['COST_BTU'] = _MEASURE_MAP['COST']
_MEASURE_MAP['CONS_EG_BTU'] = _MEASURE_MAP['CONS_EG']
_MEASURE_MAP['CONS_TOT_BTU'] = _MEASURE_MAP['CONS_TOT']
_MEASURE_MAP['CONS_UTO_BTU'] = _MEASURE_MAP['CONS_UTO']
_MEASURE_MAP['RECEIPTS_BTU'] = _MEASURE_MAP['RECEIPTS']

# Unit with this value is handled specially depending on the fuel type.
_PLACEHOLDER_FUEL_UNIT = '_XYZ_'

# The value is a pair of (unit, scalingFactor) for each measure.
_UNIT_MAP = {
    'ASH_CONTENT': ('', '100'),
    'CONS_EG': (_PLACEHOLDER_FUEL_UNIT, '1000'),
    'CONS_EG_BTU': ('MMBtu', '1000000'),
    'COST': (_PLACEHOLDER_FUEL_UNIT, ''),
    'COST_BTU': ('MMBtu', ''),
    'CUSTOMERS': ('', ''),
    'GEN': ('MegawattHour', '1000'),
    'PRICE': ('USCentPerKilowattHour', ''),
    'RECEIPTS': (_PLACEHOLDER_FUEL_UNIT, '1000'),
    'RECEIPTS_BTU': ('Btu', '1000000000'),
    'REV': ('USDollar', '1000000'),
    'SALES': ('KilowattHour', '1000000'),
    'STOCKS': (_PLACEHOLDER_FUEL_UNIT, '1000'),
    'SULFUR_CONTENT': ('', '100'),
}

_UNIT_MAP['CONS_TOT'] = _UNIT_MAP['CONS_EG']
_UNIT_MAP['CONS_UTO'] = _UNIT_MAP['CONS_EG']
_UNIT_MAP['CONS_TOT_BTU'] = _UNIT_MAP['CONS_EG_BTU']
_UNIT_MAP['CONS_UTO_BTU'] = _UNIT_MAP['CONS_EG_BTU']


def _get_fuel_unit(fuel_type):
    if fuel_type == 'NG' or fuel_type == 'OOG':
        # Gas
        return 'Mcf'
    if fuel_type == 'PEL':
        # Liquid
        return 'Barrel'
    return 'ShortTon'


def generate_statvar_schema(raw_sv, rows, sv_map, counters):
    """Generate StatVar with full schema.

    Args:
        raw_sv: Raw stat-var returned by extract_place_statvar()
        rows: List of dicts corresponding to CSV row. See common._COLUMNS.
        sv_map: Map from stat-var to its MCF content.
        counters: Map updated with error statistics.

    Returns True if schema was generated, False otherwise.
    """

    # ELEC.{MEASURE}.{FUEL_TYPE}-{PRODUCER_SECTOR}.{PERIOD}
    m = re.match(r"^ELEC\.([^.]+)\.([^-]+)-([^.]+)\.([AQM])$", raw_sv)
    if m:
        measure = m.group(1)
        fuel_type = m.group(2)
        producing_sector = m.group(3)
        period = m.group(4)
        consuming_sector = ''
    else:
        # ELEC.{MEASURE}.{CONSUMER_SECTOR}.{PERIOD}
        m = re.match(r"^ELEC\.([^.]+)\.([^.]+)\.([AQM])$", raw_sv)
        if not m:
            counters['error_unparsable_raw_statvar'] += 1
            return False
        measure = m.group(1)
        consuming_sector = m.group(2)
        period = m.group(3)
        fuel_type = ''
        producing_sector = ''

    # Get popType and mprop based on measure.
    measure_pvs = _MEASURE_MAP.get(measure, None)
    if not measure_pvs:
        counters['error_missing_measure'] += 1
        return False

    sv_id_parts = [common.PERIOD_MAP[period], measure_pvs[0]]
    sv_pvs = measure_pvs[1:] + [
        'typeOf: dcs:StatisticalVariable',
        # TODO(shanth): use new property in next iteration
        f'measurementQualifier: dcs:{common.PERIOD_MAP[period]}',
    ]

    if fuel_type:
        es = _FUEL_TYPE.get(fuel_type, None)
        if not es:
            logging.error('Missing energy source: %s from %s', fuel_type,
                          raw_sv)
            counters['error_missing_fuel_type'] += 1
            return False
        if es != 'ALL':
            sv_id_parts.append(es)
            if '_Fuel_' in measure_pvs[0]:
                sv_pvs.append(f'fuelType: dcs:{es}')
            else:
                sv_pvs.append(f'energySource: dcs:{es}')

    if producing_sector:
        ps = _PRODUCING_SECTOR.get(producing_sector, None)
        if not ps:
            counters['error_missing_producing_sector'] += 1
            return False
        if ps != 'ALL':
            sv_id_parts.append(ps)
            if '_Fuel_' in measure_pvs[0]:
                sv_pvs.append(f'electricityProducingSector: dcs:{ps}')
            else:
                sv_pvs.append(f'producingSector: dcs:{ps}')

    if consuming_sector:
        cs = _CONSUMING_SECTOR.get(consuming_sector, None)
        if not cs:
            counters['error_missing_consuming_sector'] += 1
            return False
        if cs != 'ALL':
            sv_id_parts.append(cs)
            sv_pvs.append(f'consumingSector: dcs:{cs}')

    if measure not in _UNIT_MAP:
        counters['error_missing_unit'] += 1
        return False
    (unit, sfactor) = _UNIT_MAP[measure]

    if unit == _PLACEHOLDER_FUEL_UNIT:
        if not fuel_type:
            counters['error_missing_unit_fuel_type'] += 1
            return False
        unit = _get_fuel_unit(fuel_type)
        if measure == 'COST':
            unit = 'USDollarPer' + unit

    sv_id = '_'.join(sv_id_parts)

    # Update the rows with new StatVar ID value and additional properties.
    for row in rows:
        row['stat_var'] = f'dcid:{sv_id}'
        if unit:
            row['unit'] = f'dcid:{unit}'
        else:
            # Reset unit to empty to clear the raw unit value.
            row['unit'] = ''
        if sfactor:
            row['scaling_factor'] = sfactor

    if sv_id not in sv_map:
        node = f'Node: dcid:{sv_id}'
        sv_map[sv_id] = '\n'.join([node] + sv_pvs)

    return True
