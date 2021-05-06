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
"""EIA Coal Dataset specific functions."""

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
    # Pattern #1: COAL.{Measure}.{Region}-{Code}.{Period}
    # - Ignored: 3-leter region codes (e.g. MAT - Middle Atlantic)
    m = re.match(r"^COAL\.([^._]+_?[^._]+)\.([A-Z][A-Z])-([0-9]+)\.([AQM])$",
                 series_id)
    if m:
        measure = m.group(1)
        place = m.group(2)
        code = m.group(3)
        period = m.group(4)
        sv_id = f'COAL.{measure}.{code}.{period}'
        return (place, sv_id, True)
    # Pattern #2: COAL.{EXPORT|IMPORT}_{Measure}.{Type}-{CountryIso}-{UsPortIso}.{Period}
    # Pattern #3: COAL.{SHIPMENT}_{Submeasure}.{Source}-{Destination}-{Material}.{Period}
    m = re.match(r"^COAL\.([A-Z]+)_([A-Z]+)\.([^-]+)-([^-]+)-([^.]+)\.([AQM])$",
                 series_id)
    if m:
        activity = m.group(1)
        measure = m.group(2)
        if activity in ['EXPORT', 'IMPORT']:
            # Pattern #2
            # TODO: model destination / source port as well
            type = m.group(3)
            place = m.group(4)
            port = m.group(5)
            period = m.group(6)
            sv_id = f'COAL.{activity}_{measure}.{type}.{period}'
            return (place, sv_id, False)
        elif activity == 'SHIPMENT':
            # Pattern #3
            source = m.group(3)
            if source.isalpha() and len(source) == 2:  # US State
                destination_power_plant = m.group(4)
                material = m.group(5)
                period = m.group(6)
                sv_id = f'COAL.SHIPMENT_{measure}.{material}.{period}'
                return (source, sv_id, True)
            else:
                if source.isalpha():
                    # TODO: Handle remaining places - regions
                    counters[f'error_unknown_region SHIPMENT ({source})'] += 1
                    return (None, None, None)
                elif source.isnumeric():
                    # TODO: Handle remaining places - coal mines
                    counters[f'error_unknown_coal_mine SHIPMENT '] += 1
                    return (None, None, None)
        else:
            counters[f'unknown #2,3 activity ({activity})'] += 1
            return (None, None, None)

    # Pattern #4: COAL.{Measure}_{MINE|PLANT}_{ASH|HEAT|PRICE|QTY|SULFUR}.{Region}-{Material?}.{Period}
    return (None, None, None)


##
## Maps for Schema - more definitions at https://www.eia.gov/coal/data/browser/data/termsAndDefs.php?rseAvailable=false&showFilterValues=true&showDetail=true&showTransportationMode=true&showPrimeMovers=true&showPlantFuelTypes=true&showMineType=true&showMineStatus=true&topic=26
##

# Each value is a list where first entry is StatVar ID component, and the rest
# are StatVar PVs.
_MEASURE_MAP = {
    'ASH_CONTENT': [
        'AverageQuality_AshContent_ReceivedCoal',
        'populationType: dcs:Coal',
        'measuredProperty: dcs:ashContent',
        'statType: dcs:meanValue',
    ],
    'CONS_TOT': [
        'Consumption_Coal',
        'populationType: dcs:Coal',
        'measuredProperty: dcs:consumption',
        'statType: dcs:measuredValue',
    ],
    'COST': [
        'Average_Cost_Coal',
        'populationType: dcs:Coal',
        'measuredProperty: dcs:cost',
        'statType: dcs:meanValue',
    ],
    'HEAT_CONTENT': [
        'AverageQuality_HeatContent_ReceivedCoal',
        'populationType: dcs:Coal',
        'measuredProperty: dcs:heatContent',
        'statType: dcs:meanValue',
    ],
    'RECEIPTS': [
        'Receipt_Coal',
        'populationType: dcs:Coal',
        'measuredProperty: dcs:receipt',
        'statType: dcs:measuredValue',
    ],
    'STOCKS': [
        'Stock_Coal',
        'populationType: dcs:Coal',
        'measuredProperty: dcs:stock',
        'statType: dcs:measuredValue',
    ],
    'SULFUR_CONTENT': [
        'AverageQuality_SulfurContent_ReceivedCoal',
        'populationType: dcs:Coal',
        'measuredProperty: dcs:sulfurContent',
        'statType: dcs:meanValue',
    ],
}

_CONSUMING_SECTOR = {
    '1': 'ElectricUtility',
    '2': 'ElectricUtilityNonCogen',
    '3': 'ElectricUtilityCogen',
    '8': 'CommercialAndInstitutional',
    '9': 'CokePlants',
    '10': 'OtherIndustrial',
    '94': 'IndependentPowerProducers',
    '98': 'ElectricPower',
}

_UNIT_MAP = {
    'ASH_CONTENT': ('', '100'),
    'HEAT_CONTENT': ('BtuPerPound', ''),
    'SULFUR_CONTENT': ('', '100'),
    'CONS_TOT': ('ShortTon', ''),
    'RECEIPTS': ('ShortTon', ''),
    'STOCKS': ('ShortTon', ''),
    'COST': ('USDollarPerShortTon', ''),
}


def generate_statvar_schema(raw_sv, rows, sv_map, counters):
    """Generate StatVar with full schema.

    Args:
        raw_sv: Raw stat-var returned by extract_place_statvar()
        rows: List of dicts corresponding to CSV row. See common._COLUMNS.
        sv_map: Map from stat-var to its MCF content.
        counters: Map updated with error statistics.

    Returns True if schema was generated, False otherwise.
    """
    counters['generate_statvar_schema'] += 1

    # COAL.{Measure}.{ConsumingSector}.{Period}
    m = re.match(r"^COAL\.([^._]+_?[^._]+)\.([0-9]+)\.([AQM])$", raw_sv)
    if m:
        measure = m.group(1)
        consuming_sector = m.group(2)
        period = m.group(3)
    else:
        counters['error_unparsable_raw_statvar'] += 1
        return False
    counters[f'measure-{measure}'] += 1

    # Get popType and mprop based on measure.
    measure_pvs = _MEASURE_MAP.get(measure, None)
    if not measure_pvs:
        counters[f'error_missing_measure-{measure}'] += 1
        return False

    sv_id_parts = [common.PERIOD_MAP[period], measure_pvs[0]]
    sv_pvs = measure_pvs[1:] + [
        'typeOf: dcs:StatisticalVariable',
        # TODO(shanth): use new property in next iteration
        f'measurementQualifier: dcs:{common.PERIOD_MAP[period]}',
    ]

    if consuming_sector:
        cs = _CONSUMING_SECTOR.get(consuming_sector, None)
        if not cs:
            counters[f'error_missing_consuming_sector-{consumingSector}'] += 1
            return False
        sv_id_parts.append(cs)
        sv_pvs.append(f'consumingSector: dcs:{cs}')

    if measure not in _UNIT_MAP:
        counters[f'error_missing_unit-{measure}'] += 1
        return False
    (unit, sfactor) = _UNIT_MAP[measure]

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
