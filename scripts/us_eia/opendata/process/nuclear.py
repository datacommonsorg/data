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
"""EIA Nuclear Status Dataset specific functions."""

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
    m = re.match(r"^NUC_STATUS\.([^.]+)\.([^.]+)\.(D)$", series_id)
    if m:
        measure = m.group(1)
        place = m.group(2)
        if not place == 'US':
            place = f'dcid:eia/pp/{m.group(2)}'
        period = m.group(3)
        sv_id = f'NUC_STATUS.{measure}.{period}'
        return (place, sv_id, True)

    return (None, None, None)


##
## Maps for Schema
##

_SV_MAP = {
    'CAP': [
        'Daily_Capacity_Nuclear_ForEnergyGeneration',
        'typeOf: dcid:StatisticalVariable',
        'name: "Nuclear Power Plant generating capacity"',
        'description: \\""Nuclear generating capacity for a power plant. See https://www.eia.gov/nuclear/outages/.  For more information visit, Nuclear Regulatory Commission\'s Power Reactor Status Report\\""',
        'populationType: dcs:EnergyGeneration',
        'energySource: dcs:Nuclear',
        'measuredProperty: dcs:capacity',
        'statType: dcs:measuredValue',
        # TODO(shanth): use new property in next iteration
        'measurementQualifier: dcs:Daily',
    ],
    'OUT': [
        'Daily_CapacityOutage_Nuclear_ForEnergyGeneration',
        'typeOf: dcid:StatisticalVariable',
        'name: "Nuclear Power Plant generating capacity outage."',
        'description: \\""Nuclear generating capacity outage at a power plant. See https://www.eia.gov/nuclear/outages/.  For more information visit, Nuclear Regulatory Commission\'s Power Reactor Status Report\\""',
        'populationType: dcs:EnergyGeneration',
        'energySource: dcs:Nuclear',
        'measuredProperty: dcs:outage',
        'statType: dcs:measuredValue',
        # TODO(shanth): use new property in next iteration
        'measurementQualifier: dcs:Daily',
    ],
    'OUT_PCT': [
        'Daily_CapacityOutage_Nuclear_ForEnergyGeneration_AsAFractionOf_Capacity',
        'typeOf: dcid:StatisticalVariable',
        'description: \\""Nuclear generating capacity percent outage at a power plant. See https://www.eia.gov/nuclear/outages/.  For more information visit, Nuclear Regulatory Commission\'s Power Reactor Status Report\\""',
        'populationType: dcs:EnergyGeneration',
        'energySource: dcs:Nuclear',
        'measuredProperty: dcs:outage',
        'statType: dcs:measuredValue',
        'measurementDenominator: dcs:Daily_Capacity_Nuclear_ForEnergyGeneration',
        # TODO(shanth): use new property in next iteration
        'measurementQualifier: dcs:Daily',
    ],
}

_UNIT_MAP = {
    'CAP': ('Megawatt', None),
    'OUT': ('Megawatt', None),
    'OUT_PCT': (None, None),
}


def generate_statvar_schema(raw_sv, rows, sv_map, counters):
    """Generate StatVar with full schema.

    Args:
        raw_sv: Raw stat-var returned by extract_place_statvar()
        rows: List of dicts corresponding to CSV row. See common._COLUMNS.
        sv_map: Map from stat-var to its MCF content.
        counters: Map updated with error statistics.

    Returns schema-ful stat-var ID if schema was generated, None otherwise.
    """
    counters['generate_statvar_schema'] += 1

    # NUC_STATUS.{Measure}.{Period}
    m = re.match(r"^NUC_STATUS\.([^.]+)\.(D)$", raw_sv)
    if m:
        measure = m.group(1)
        period = m.group(2)
    else:
        counters['error_unparsable_raw_statvar'] += 1
        return None
    counters[f'measure-{measure}'] += 1

    # Get popType and mprop based on measure.
    measure_pvs = _SV_MAP.get(measure, None)
    if not measure_pvs:
        counters[f'error_missing_measure-{measure}'] += 1
        return None

    sv_id = measure_pvs[0]
    sv_pvs = measure_pvs[1:]

    if measure not in _UNIT_MAP:
        counters[f'error_missing_unit-{measure}'] += 1
        return None
    (unit, sfactor) = _UNIT_MAP[measure]

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

    return sv_id
