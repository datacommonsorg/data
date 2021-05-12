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
"""Process EIA datasets to produce TMCF and CSV."""

import csv
import json
import logging
import re
from collections import defaultdict
from sys import path

# For import util.alpha2_to_dcid
path.insert(1, '../../../../')
import util.alpha2_to_dcid as alpha2_to_dcid
import util.name_to_alpha2 as name_to_alpha2

import category

PERIOD_MAP = {
    'A': 'Annual',
    'D': 'Daily',
    'M': 'Monthly',
    'Q': 'Quarterly',
}

_COLUMNS = [
    'place', 'stat_var', 'date', 'value', 'unit', 'scaling_factor',
    'eia_series_id'
]

_TMCF_STRING = """
Node: E:EIATable->E0
typeOf: dcs:StatVarObservation
observationAbout: C:EIATable->place
variableMeasured: C:EIATable->stat_var
observationDate: C:EIATable->date
value: C:EIATable->value
unit: C:EIATable->unit
scalingFactor: C:EIATable->scaling_factor
eiaSeriesId: C:EIATable->eia_series_id
"""

_DATE_RE = re.compile('[0-9WMQ]')

_QUARTER_MAP = {
    'Q1': '03',
    'Q2': '06',
    'Q3': '09',
    'Q4': '12',
}

_ALPHA3_COUNTRY_SET = frozenset(
    [v[len('country/'):] for k, v in alpha2_to_dcid.COUNTRY_MAP.items()])


def _parse_date(d):
    """Given a date from EIA JSON convert to DC compatible date."""

    if not _DATE_RE.match(d):
        return None

    if len(d) == 4:
        if not d.isnumeric():
            return None

        # Yearly
        return d

    if len(d) == 6:
        yr = d[:4]
        m_or_q = d[4:]

        if m_or_q.startswith('Q'):
            # Quarterly
            if m_or_q in _QUARTER_MAP:
                return yr + '-' + _QUARTER_MAP[m_or_q]
        else:
            # Monthly
            return yr + '-' + m_or_q

    if len(d) == 8:
        if not d.isnumeric():
            return None

        # PET has weekly https://www.eia.gov/opendata/qb.php?sdid=PET.WCESTUS1.W
        yr = d[:4]
        m = d[4:6]
        dt = d[6:8]
        return yr + '-' + m + '-' + dt

    return None


def _sv_dcid(raw_sv):
    return 'eia/' + raw_sv


def _enumify(in_str):
    return in_str.title().replace(' ', '')


def _print_counters(counters):
    print('\nSTATS:')
    for k in sorted(counters):
        print(f"\t{k} = {counters[k]}")
    print('')


def _find_dc_place(raw_place, is_us_place, counters):
    if raw_place.startswith('dcid:'):
        return raw_place
    if is_us_place:
        if raw_place == 'US' or raw_place == 'USA':
            return 'country/USA'
        if raw_place in alpha2_to_dcid.USSTATE_MAP:
            return alpha2_to_dcid.USSTATE_MAP[raw_place]
    else:
        if len(raw_place) == 2 and raw_place in alpha2_to_dcid.COUNTRY_MAP:
            return alpha2_to_dcid.COUNTRY_MAP[raw_place]
        elif len(raw_place) == 3 and raw_place in _ALPHA3_COUNTRY_SET:
            return f'country/{raw_place}'
        elif len(raw_place) > 3:
            # INTL dataset has 40 country aggregates
            # (https://user-images.githubusercontent.com/4375037/117168575-22206e00-ad7d-11eb-8f38-3a3003401464.png)
            # We map a subset that exists in DC.
            if raw_place == 'AFRC':
                return 'africa'
            if raw_place == 'EURO':
                return 'europe'
            if raw_place == 'NOAM':
                return 'northamerica'
            if raw_place == 'CSAM':
                # This includes central america though
                return 'southamerica'
            if raw_place == 'WORL':
                return 'Earth'

    # logging.error('ERROR: unsupported place %s %r', raw_place, is_us_place)
    counters[f'error_unsupported_places_{raw_place}'] += 1
    return None


def _generate_default_statvar(raw_sv, sv_map):
    if raw_sv in sv_map:
        return
    raw_sv_id = _sv_dcid(raw_sv)
    sv_map[raw_sv] = '\n'.join([
        f"Node: dcid:{raw_sv_id}",
        'typeOf: dcs:StatisticalVariable',
        'populationType: schema:Thing',
        f"measuredProperty: dcid:{raw_sv_id}",
        'statType: dcs:measuredValue',
    ])


# Name patterns for US and US states.
_NAME_PATTERNS = {
    v: [k.lower()] for k, v in name_to_alpha2.USSTATE_MAP_SPACE.items()
}
_NAME_PATTERNS['US'] = [
    'united states of america', 'united states', 'u.s.a.', 'u.s.'
]
_NAME_PATTERNS['USA'] = _NAME_PATTERNS['US']


def cleanup_name(name):
    # Trim unnecessary whitespaces.
    name = name.strip()
    name = re.sub(r" +", ' ', name)

    # Trim any leading/trailing ',' or ':'.  To handle names like "Measure
    # Foo, California"
    name = re.sub(r"([,: ]+$|^[,: ]+)", '', name)

    # Replace ':' with ','.
    name = name.replace(':', ',')

    # Trim repeated ','s and have correct spaces. This can happen from:
    # "Stocks : California : electric utility : quarterly"
    parts = []
    for part in name.split(','):
        part = part.strip()
        if part:
            parts.append(part)
    name = ', '.join(parts)

    return name


def _maybe_parse_name(name, raw_place, is_us_place, counters):
    """Parsing stat-var name given a series name containing a place."""

    if not name or not is_us_place or raw_place not in _NAME_PATTERNS:
        return ''

    for p in _NAME_PATTERNS[raw_place]:
        idx = name.lower().find(p)
        if idx == -1:
            continue

        # Replace only the pattern, otherwise retaining the case of the name.
        name = name[0:idx] + name[idx + len(p):]

        return cleanup_name(name)

    # If we didn't find the name for the place, likely the name doesn't include
    # the place (e.g., TOTAL).
    counters['info_unmodified_names'] += 1
    return cleanup_name(name)


def _generate_sv_nodes(sv_map, sv_name_map, sv_membership_map, sv_schemaful2raw,
                       svg_info):
    nodes = []
    for sv, mcf in sv_map.items():
        raw_sv = sv_schemaful2raw[sv] if sv in sv_schemaful2raw else sv

        pvs = [mcf]
        if raw_sv in sv_name_map:
            pvs.append(f'name: "{sv_name_map[raw_sv]}"')

        if raw_sv in sv_membership_map:
            for svg in sorted(sv_membership_map[raw_sv]):
                if svg in svg_info:
                    pvs.append(f'memberOf: dcid:{svg}')

        nodes.append('\n'.join(pvs))

    return nodes


def process(dataset, dataset_name, in_json, out_csv, out_sv_mcf, out_svg_mcf,
            out_tmcf, extract_place_statvar_fn, generate_statvar_schema_fn):
    """Process an EIA dataset and produce outputs using lambda functions.

    Args:
        dataset: Dataset code
        dataset_name: Name of the dataset
        in_json: Input JSON file
        out_csv: Output CSV file
        out_sv_mcf: Output StatisticalVariable MCF file
        out_svg_mcf: Ouytput StatVarGroups MCF file
        out_tmcf: Output TMCF file

        extract_place_statvar_fn:
                            Required function to extract raw place and stat-var from series_id.
                            raw-place-id could be a code that is resolvable
                            by _find_dc_place, or a specified dcid (prefixed with 'dcid:').
                            Args:
                                series_id: series_id field from EIA
                                counters: map of counters with frequency
                            Returns (raw-place-id, raw-stat-var-id, is_us_place)

        generate_statvar_schema_fn:
                            Optional function to generate stat-var schema.
                            Args:
                                raw-stat-var: the value returned by extract_place_statvar_fn
                                rows: list of dicts representing rows with _COLUMNS as keys
                                sv-map: map from stat-var-id to MCF content
                                counters: map of counters with frequency
                            Returns schema-ful stat-var ID if schema was generated,
                                None otherwise. If stat-var is returned,
                                rows and sv-map are also updated.
    """
    assert extract_place_statvar_fn, 'Must provide extract_place_statvar_fn'

    # SVG ID -> (parent SVG, name)
    svg_info = {}
    # Raw SV -> set(SVGs)
    sv_membership_map = {}
    # Schema-ful SV -> Raw SV
    sv_schemaful2raw = {}
    counters = defaultdict(lambda: 0)
    sv_map = {}
    sv_name_map = {}
    with open(in_json) as in_fp, open(out_csv, 'w', newline='') as csv_fp:
        csvwriter = csv.DictWriter(csv_fp, fieldnames=_COLUMNS)
        csvwriter.writeheader()

        for line in in_fp:
            counters['info_lines_processed'] += 1
            if counters['info_lines_processed'] % 100000 == 99999:
                _print_counters(counters)

            data = json.loads(line)

            # Preliminary checks
            series_id = data.get('series_id', None)
            if not series_id:
                category.process_category(dataset, data,
                                          extract_place_statvar_fn, svg_info,
                                          sv_membership_map, counters)
                counters['info_categories_processed'] += 1
                continue

            time_series = data.get('data', None)
            if not time_series:
                counters['error_missing_time_series'] += 1
                continue

            # Extract raw place and stat-var from series_id.
            (raw_place, raw_sv,
             is_us_place) = extract_place_statvar_fn(series_id, counters)
            if not raw_place or not raw_sv:
                counters['error_extract_place_sv'] += 1
                continue

            # Map raw place to DC place
            dc_place = _find_dc_place(raw_place, is_us_place, counters)
            if not dc_place:
                counters['error_place_mapping'] += 1
                continue

            raw_unit = _enumify(data.get('units', ''))

            if raw_sv not in sv_name_map:
                name = _maybe_parse_name(data.get('name', ''), raw_place,
                                         is_us_place, counters)
                if name:
                    sv_name_map[raw_sv] = name

            # Add to rows.
            rows = []
            for k, v in time_series:

                try:
                    # The following non-numeric values exist:
                    #  -- = Not applicable
                    #   - = No data reported
                    # (s) = Value too small for number of decimal places shown
                    #  NA = Not available
                    #   W = Data withheld to avoid disclosure
                    #   * = Conversion Factor Unavailable
                    #  se = EIA estimates based on time series analysis
                    #  st = EIA forecasts (Short-Term Energy Outlook)
                    # - - = Not applicable.
                    #   W = Withdrawn
                    #
                    # TODO: Handle some these better.
                    _ = float(v)
                except Exception:
                    counters['error_non_numeric_values'] += 1
                    continue

                dt = _parse_date(k)
                if not dt:
                    logging.error('ERROR: failed to parse date "%s"', k)
                    counters['error_date_parsing'] += 1
                    continue

                rows.append({
                    'place': f"dcid:{dc_place}",
                    'stat_var': f"dcid:{_sv_dcid(raw_sv)}",
                    'date': dt,
                    'value': v,
                    'eia_series_id': series_id,
                    'unit': raw_unit,
                })

            if not rows:
                counters['error_empty_series'] += 1
                continue

            schema_sv = None
            if generate_statvar_schema_fn:
                schema_sv = generate_statvar_schema_fn(raw_sv, rows, sv_map,
                                                       counters)
            if schema_sv:
                sv_schemaful2raw[schema_sv] = raw_sv
                counters['info_schemaful_series'] += 1
            else:
                counters['info_schemaless_series'] += 1
                _generate_default_statvar(raw_sv, sv_map)

            csvwriter.writerows(rows)
            counters['info_rows_output'] += len(rows)

    category.trim_area_categories(svg_info, counters)

    with open(out_sv_mcf, 'w') as out_fp:
        nodes = _generate_sv_nodes(sv_map, sv_name_map, sv_membership_map,
                                   sv_schemaful2raw, svg_info)

        out_fp.write('\n\n'.join(nodes))
        out_fp.write('\n')

    with open(out_svg_mcf, 'w') as out_fp:
        nodes = category.generate_svg_nodes(dataset, dataset_name, svg_info)

        out_fp.write('\n\n'.join(nodes))
        out_fp.write('\n')

    with open(out_tmcf, 'w') as out_fp:
        out_fp.write(_TMCF_STRING)

    print('=== FINAL COUNTERS ===')
    _print_counters(counters)
