"""Process EIA datasets to produce TMCF and CSV."""

from sys import path
# For import util.alpha2_to_dcid
path.insert(1, '../../../../')

import csv
import elec
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


def extract_place_stat_var(series_id, stats):
  if series_id.startswith('ELEC.'):
    return elec.extract_place_stat_var(series_id, stats)
  else:
    stats['error_unimplemented_dataset'] += 1
    return (None, None)


def find_dc_place(raw_place, stats):
  # At the moment, we only support states and US.
  if raw_place == 'US':
    return 'country/usa'
  elif raw_place in alpha2_to_dcid.USSTATE_MAP:
    return alpha2_to_dcid.USSTATE_MAP[raw_place]

  stats['error_unsupported_places'] += 1
  return None


def generate_schema_statvar(raw_sv, rows, sv_map, stats):
  if raw_sv.startswith('ELEC'):
    return elec.generate_schema_statvar(raw_sv, rows, sv_map, stats)
  else:
    return False


def eia_dcid(raw_sv):
  return 'dcid:eia/' + raw_sv.lower()


def generate_default_statvar(raw_sv, sv_map):
  if raw_sv in sv_map:
    return
  raw_sv_id = eia_dcid(raw_sv)
  sv_map[raw_sv] = '\n'.join([
      f"Node: {raw_sv_id}",
      'typeOf: dcs:StatisticalVariable',
      'populationType: schema:Thing',
      f"measuredProperty: {raw_sv_id}",
      'statType: dcs:measuredValue',
  ])


def print_stats(stats):
  print('\nSTATS:')
  for k, v in stats.items():
    print(f"\t{k} = {v}")
  print('')


def process(in_json, out_csv, out_sv_mcf, out_tmcf):
  """
    Produces CSV with schema:
        place, stat_var, date, value, unit, scaling_factor, eia_series_id
  """
  stats = defaultdict(lambda: 0)
  sv_map = {}
  with open(in_json) as in_fp:
    with open(out_csv, 'w', newline='') as csv_fp:
      csvwriter = csv.DictWriter(csv_fp, fieldnames=_COLUMNS)
      csvwriter.writeheader()

      for line in in_fp:
        stats['info_lines_processed'] += 1
        if stats['info_lines_processed'] % 100000 == 99999:
          print_stats(stats)

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
        (raw_place, raw_sv) = extract_place_stat_var(series_id, stats)
        if not raw_place or not raw_sv:
          # Stats updated by extract_place_stat_var()
          continue

        # Map raw place to DC place
        dc_place = find_dc_place(raw_place, stats)
        if not dc_place:
          stats['error_place_mapping'] += 1
          continue

        # Add to rows.
        rows = []
        for k, v in time_series:
          rows.append({
            'place': f"dcid:{dc_place}",
            'stat_var': eia_dcid(raw_sv),
            # TODO(shanth): Format date correctly
            'date': k,
            'value': v,
            'eia_series_id': series_id,
          })

        if generate_schema_statvar(raw_sv, rows, sv_map, stats):
          stats['info_schemaful_series'] += 1
        else:
          stats['info_schemaless_series'] += 1
          generate_default_statvar(raw_sv, sv_map)

        csvwriter.writerows(rows)
        stats['info_rows_output'] += len(rows)

  with open(out_sv_mcf, 'w') as out_fp:
    out_fp.write('\n\n'.join([v for k, v in sv_map.items()]))
    out_fp.write('\n')

  with open(out_tmcf, 'w') as out_fp:
    out_fp.write(_TMCF_STRING)

  print_stats(stats)
