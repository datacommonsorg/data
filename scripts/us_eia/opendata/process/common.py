"""Process EIA datasets to produce TMCF and CSV."""

import csv
import json
import logging
from collections import defaultdict
from sys import path

# For import util.alpha2_to_dcid
path.insert(1, '../../../../')
import util.alpha2_to_dcid as alpha2_to_dcid

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

_QUARTER_MAP = {
    'Q1': '03',
    'Q2': '06',
    'Q3': '09',
    'Q4': '12',
}


def _parse_date(d):
    """Given a date from EIA JSON convert to DC compatible date."""

    if len(d) == 4:
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
        # PET has weekly https://www.eia.gov/opendata/qb.php?sdid=PET.WCESTUS1.W
        yr = d[:4]
        m = d[4:2]
        dt = d[6:2]
        return yr + '-' + m + '-' + dt

    return None


def _eia_dcid(raw_sv):
    return 'dcid:eia/' + raw_sv.lower()


def _enumify(in_str):
  return in_str.title().replace(' ', '')


def _print_counters(counters):
    print('\nSTATS:')
    for k, v in counters.items():
        print(f"\t{k} = {v}")
    print('')


def _find_dc_place(raw_place, is_us_place, counters):
    if is_us_place:
      if raw_place == 'US':
          return 'country/USA'
      if raw_place in alpha2_to_dcid.USSTATE_MAP:
          return alpha2_to_dcid.USSTATE_MAP[raw_place]
    else:
      if raw_place in alpha2_to_dcid.COUNTRY_MAP:
        return alpha2_to_dcid.COUNTRY_MAP[raw_place]
    # logging.error('ERROR: unsupported place %s %r', raw_place, is_us_place)
    counters['error_unsupported_places'] += 1
    return None


def _generate_default_statvar(raw_sv, sv_map):
    if raw_sv in sv_map:
        return
    raw_sv_id = _eia_dcid(raw_sv)
    sv_map[raw_sv] = '\n'.join([
        f"Node: {raw_sv_id}",
        'typeOf: dcs:StatisticalVariable',
        'populationType: schema:Thing',
        f"measuredProperty: {raw_sv_id}",
        'statType: dcs:measuredValue',
    ])


def process(in_json, out_csv, out_sv_mcf, out_tmcf, extract_place_statvar_fn,
            generate_statvar_schema_fn):
    """Process an EIA dataset and produce outputs using lambda functions.

    Args:
        in_json: Input JSON file
        out_csv: Output CSV file
        out_sv_mcf: Output StatisticalVariable MCF file
        out_tmcf: Output TMCF file

        extract_place_statvar_fn:
                            Required function to extract raw place and stat-var from series_id
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
                            Returns True if schema was generated, False otherwise.
                                On True, rows and sv-map are also updated.
    """
    assert extract_place_statvar_fn, 'Must provide extract_place_statvar_fn'

    counters = defaultdict(lambda: 0)
    sv_map = {}
    with open(in_json) as in_fp:
        with open(out_csv, 'w', newline='') as csv_fp:
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
                    counters['info_ignored_categories'] += 1
                    continue
                time_series = data.get('data', None)
                if not time_series:
                    counters['error_missing_time_series'] += 1
                    continue

                # Extract raw place and stat-var from series_id.
                (raw_place,
                 raw_sv,
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

                # TODO(shanth): Consider extracting stat-var name.

                # Add to rows.
                rows = []
                for k, v in time_series:

                    if not v:
                        counters['error_empty_values'] += 1
                        continue

                    dt = _parse_date(k)
                    if not dt:
                        logging.error('ERROR: failed to parse date "%s"', k)
                        counters['error_date_parsing'] += 1
                        continue

                    rows.append({
                        'place': f"dcid:{dc_place}",
                        'stat_var': _eia_dcid(raw_sv),
                        'date': dt,
                        'value': v,
                        'eia_series_id': series_id,
                        'unit': raw_unit,
                    })

                if not rows:
                    counters['error_empty_series'] += 1
                    continue

                if (generate_statvar_schema_fn and generate_statvar_schema_fn(
                        raw_sv, rows, sv_map, counters)):
                    counters['info_schemaful_series'] += 1
                else:
                    counters['info_schemaless_series'] += 1
                    _generate_default_statvar(raw_sv, sv_map)

                csvwriter.writerows(rows)
                counters['info_rows_output'] += len(rows)

    with open(out_sv_mcf, 'w') as out_fp:
        out_fp.write('\n\n'.join([v for k, v in sv_map.items()]))
        out_fp.write('\n')

    with open(out_tmcf, 'w') as out_fp:
        out_fp.write(_TMCF_STRING)

    _print_counters(counters)
