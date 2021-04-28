"""Process EIA datasets to produce TMCF and CSV."""

from sys import path
# For import util.alpha2_to_dcid
path.insert(1, '../../../../')

import csv
import json
import logging
import pandas as pd
import util.alpha2_to_dcid as alpha2_to_dcid
from collections import defaultdict


_COLUMNS = ['place', 'stat_var', 'date', 'value', 'unit', 'scaling_factor',
            'eia_series_id']

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

  return None


def _eia_dcid(raw_sv):
  return 'dcid:eia/' + raw_sv.lower()


def _print_stats(stats):
  print('\nSTATS:')
  for k, v in stats.items():
    print(f"\t{k} = {v}")
  print('')


def _find_dc_place(raw_place, stats):
  # At the moment, we only support states and US.
  if raw_place == 'US':
    return 'country/usa'
  elif raw_place in alpha2_to_dcid.USSTATE_MAP:
    return alpha2_to_dcid.USSTATE_MAP[raw_place]

  stats['error_unsupported_places'] += 1
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
  """
  """
  assert extract_place_statvar_fn, 'Must provide extract_place_statvar_fn'

  stats = defaultdict(lambda: 0)
  sv_map = {}
  with open(in_json) as in_fp:
    with open(out_csv, 'w', newline='') as csv_fp:
      csvwriter = csv.DictWriter(csv_fp, fieldnames=_COLUMNS)
      csvwriter.writeheader()

      for line in in_fp:
        stats['info_lines_processed'] += 1
        if stats['info_lines_processed'] % 100000 == 99999:
          _print_stats(stats)

        data = json.loads(line)

        # Preliminary checks
        series_id = data.get('series_id', None)
        if not series_id:
          stats['error_missing_series'] += 1
          continue
        time_series = data.get('data', None)
        if not time_series:
          stats['error_missing_time_series'] += 1
          continue

        # Extract raw place and stat-var from series_id.
        (raw_place, raw_sv) = extract_place_statvar_fn(series_id, stats)
        if not raw_place or not raw_sv:
          # Stats updated by extract_place_statvar_fn()
          continue

        # Map raw place to DC place
        dc_place = _find_dc_place(raw_place, stats)
        if not dc_place:
          stats['error_place_mapping'] += 1
          continue

        # Add to rows.
        rows = []
        for k, v in time_series:
          dt = _parse_date(k)
          if not dt:
            stats['error_date_parsing'] += 1
            continue
          rows.append({
            'place': f"dcid:{dc_place}",
            'stat_var': _eia_dcid(raw_sv),
            'date': dt,
            'value': v,
            'eia_series_id': series_id,
          })

        if (generate_statvar_schema_fn and
            generate_statvar_schema_fn(raw_sv, rows, sv_map, stats)):
          stats['info_schemaful_series'] += 1
        else:
          stats['info_schemaless_series'] += 1
          _generate_default_statvar(raw_sv, sv_map)

        csvwriter.writerows(rows)
        stats['info_rows_output'] += len(rows)

  with open(out_sv_mcf, 'w') as out_fp:
    out_fp.write('\n\n'.join([v for k, v in sv_map.items()]))
    out_fp.write('\n')

  with open(out_tmcf, 'w') as out_fp:
    out_fp.write(_TMCF_STRING)

  _print_stats(stats)
