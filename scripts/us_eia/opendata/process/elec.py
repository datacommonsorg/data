"""EIA Electricity Dataset specific functions."""

import logging
import re


def extract_place_statvar(series_id, stats):
    """Given the series_id, extract the raw place and stat-var ID.

    Args:
        series_id: EIA series ID
        stats: map for updating error statistics

    Returns a (place, raw-stat-var) pair.
    """

    if series_id.startswith('ELEC.PLANT.'):
        stats['error_unimplemented_plant_series'] += 1
        return (None, None)

    # ELEC.{MEASURE}.{ENERGY_SOURCE}-{PLACE}-{PRODUCER_SECTOR}.{PERIOD}
    m = re.match(r"^ELEC\.([^.]+)\.([^-]+)-([^-]+)-([^.]+)\.([AQM])$",
                 series_id)
    if m:
        measure = m.group(1)
        energy_source = m.group(2)
        place = m.group(3)
        producing_sector = m.group(4)
        period = m.group(5)
        sv_id = f'ELEC.{measure}.{energy_source}-{producing_sector}.{period}'
    else:
        # ELEC.{MEASURE}.{PLACE}-{CONSUMER_SECTOR}.{PERIOD}
        m = re.match(r"^ELEC\.([^.]+)\.([^-]+)-([^.]+)\.([AQM])$", series_id)
        if not m:
            stats['error_unparsable_series'] += 1
            return (None, None)

        measure = m.group(1)
        place = m.group(2)
        consuming_sector = m.group(3)
        period = m.group(4)
        sv_id = f'ELEC.{measure}.{consuming_sector}.{period}'
    return (place, sv_id)


##
## Maps for Schema
##

_PERIOD_MAP = {
    'A': 'Annual',
    'M': 'Monthly',
    'Q': 'Quarterly',
}

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

_ENERGY_SOURCE = {
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
    'OOG': 'Other',
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

_MEASURE_MAP['COST_BTU'] = _MEASURE_MAP['COST']
_MEASURE_MAP['CONS_EG_BTU'] = _MEASURE_MAP['CONS_EG']
_MEASURE_MAP['CONS_TOT_BTU'] = _MEASURE_MAP['CONS_TOT']
_MEASURE_MAP['CONS_UTO_BTU'] = _MEASURE_MAP['CONS_UTO']
_MEASURE_MAP['RECEIPTS_BTU'] = _MEASURE_MAP['RECEIPTS']

_UNIT_MAP = {
    'ASH_CONTENT': ('', '100'),
    # TODO(shanth): This has ton/barrel too.
    'CONS_EG': ('Mcf', '1000'),
    'CONS_EG_BTU': ('MMBtu', '1000000'),
    'CONS_TOT': ('Mcf', '1000'),
    'CONS_TOT_BTU': ('MMBtu', '1000000'),
    'CONS_UTO': ('Mcf', '1000'),
    'CONS_UTO_BTU': ('MMBtu', '1000000'),
    # TODO(shanth): This has per ton/barrel too.
    'COST': ('USDollarPerMcf', ''),
    'COST_BTU': ('USDollarPerMMBtu', ''),
    'CUSTOMERS': ('', ''),
    'GEN': ('MegaWattHour', '1000'),
    'PRICE': ('USCentPerKiloWattHour', ''),
    # TODO(shanth): This has ton/barrel too.
    'RECEIPTS': ('Mcf', '1000'),
    'RECEIPTS_BTU': ('Btu', '1000000000'),
    'REV': ('USDollar', '1000000'),
    'SALES': ('KiloWattHour', '1000000'),
    # TODO(shanth): This has barrel too.
    'STOCKS': ('Ton', '1000'),
    'SULFUR_CONTENT': ('', '100'),
}


def generate_statvar_schema(raw_sv, rows, sv_map, stats):
    """Generate StatVar with full schema.

    Args:
        raw_sv: Raw stat-var returned by extract_place_statvar()
        rows: List of dicts corresponding to CSV row. See common._COLUMNS.
        sv_map: Map from stat-var to its MCF content.
        stats: Map updated with error statistics.

    Returns True if schema was generated, False otherwise.
    """

    # ELEC.{MEASURE}.{ENERGY_SOURCE}-{PRODUCER_SECTOR}.{PERIOD}
    m = re.match(r"^ELEC\.([^.]+)\.([^-]+)-([^.]+)\.([AQM])$", raw_sv)
    if m:
        measure = m.group(1)
        energy_source = m.group(2)
        producing_sector = m.group(3)
        period = m.group(4)
        consuming_sector = ''
    else:
        # ELEC.{MEASURE}.{CONSUMER_SECTOR}.{PERIOD}
        m = re.match(r"^ELEC\.([^.]+)\.([^.]+)\.([AQM])$", raw_sv)
        if not m:
            stats['error_unparsable_raw_statvar'] += 1
            return False
        measure = m.group(1)
        consuming_sector = m.group(2)
        period = m.group(3)
        energy_source = ''
        producing_sector = ''

    # Get popType and mprop based on measure.
    measure_pvs = _MEASURE_MAP.get(measure, None)
    if not measure_pvs:
        stats['error_missing_measure'] += 1
        return False

    sv_id_parts = [_PERIOD_MAP[period], measure_pvs[0]]
    sv_pvs = measure_pvs[1:] + [
        'typeOf: dcs:StatisticalVariable',
        # TODO(shanth): use new property in next iteration
        f'measurementQualifier: dcs:{_PERIOD_MAP[period]}',
    ]

    if energy_source:
        es = _ENERGY_SOURCE.get(energy_source, None)
        if not es:
            logging.error('Missing energy source: %s from %s', energy_source,
                          raw_sv)
            stats['error_missing_energy_source'] += 1
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
            stats['error_missing_producing_sector'] += 1
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
            stats['error_missing_consuming_sector'] += 1
            return False
        if cs != 'ALL':
            sv_id_parts.append(cs)
            sv_pvs.append(f'consumingSector: dcs:{cs}')

    if measure not in _UNIT_MAP:
        stats['error_missing_unit'] += 1
        return False
    (unit, sfactor) = _UNIT_MAP[measure]

    sv_id = '_'.join(sv_id_parts)

    # Update the rows with new StatVar ID value and additional properties.
    for row in rows:
        row['stat_var'] = f'dcid:{sv_id}'
        if unit:
            row['unit'] = f'dcid:{unit}'
        if sfactor:
            row['scaling_factor'] = sfactor

    if sv_id not in sv_map:
        node = f'Node: dcid:{sv_id}'
        sv_map[sv_id] = '\n'.join([node] + sv_pvs)

    return True
