# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Script to process flood insurance claims data from US FEMA's
National Flood Insurance Program using an optimized multi-core vectorized pipeline.'''

import ast
import concurrent.futures
import multiprocessing
import os
import sys
import time
from typing import Any, Optional, Tuple

from absl import app
from absl import flags
from absl import logging
import numpy as np
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _define_flag_if_not_exists(flag_type, name, default, help_str):
    if name not in flags.FLAGS:
        flag_type(name, default, help_str)


_define_flag_if_not_exists(flags.DEFINE_string, 'input_data',
                           'input_file/fema_nfip_claims.csv',
                           'Input CSV file containing FEMA claims data.')
_define_flag_if_not_exists(flags.DEFINE_string, 'output_path',
                           'output/nfip_output',
                           'Prefix path for output CSV and TMCF files.')
_define_flag_if_not_exists(flags.DEFINE_string, 'config_file',
                           'us_flood_nfip_config.py', 'Config file.')
_define_flag_if_not_exists(
    flags.DEFINE_string, 'pv_map',
    'us_flood_nfip_pv_map_floodzone.py,ratedFloodZone:us_flood_nfip_floodzone_pv_map.py,observationAbout:us_state_codes.py',
    'PV map files configuration.')
_define_flag_if_not_exists(flags.DEFINE_string, 'output_counters',
                           'counters/counters.txt',
                           'Path to output counters summary file.')
_define_flag_if_not_exists(flags.DEFINE_integer, 'chunk_size', 250000,
                           'Number of rows per chunk for batched processing.')
_define_flag_if_not_exists(
    flags.DEFINE_integer, 'num_workers', None,
    'Number of parallel worker processes to use (defaults to CPU count).')

_FLAGS = flags.FLAGS

_WORKER_STATE_MAP = None
_WORKER_RISK_ZONE_MAP = None


def _resolve_map_path(pv_map_arg: Optional[str],
                      prefix: str,
                      default_name: Optional[str] = None) -> Optional[str]:
    """Finds mapping file path from pv_map flag or defaults to script directory."""
    if pv_map_arg:
        items = pv_map_arg if isinstance(pv_map_arg,
                                         list) else pv_map_arg.split(',')
        for item in items:
            if item.startswith(f"{prefix}:"):
                path = item.split(':', 1)[1].strip()
                if os.path.exists(path):
                    return path
                script_dir_path = os.path.join(_SCRIPT_DIR, path)
                if os.path.exists(script_dir_path):
                    return script_dir_path
    return os.path.join(_SCRIPT_DIR, default_name) if default_name else None


def _load_mappings(pv_map_arg: Optional[str] = None) -> Tuple[dict, dict]:
    """Loads state and floodzone mappings from pv_map or default files."""
    state_file = _resolve_map_path(pv_map_arg, 'observationAbout',
                                   'us_state_codes.py')
    zone_file = _resolve_map_path(pv_map_arg, 'ratedFloodZone',
                                  'us_flood_nfip_floodzone_pv_map.py')

    state_map = {}
    if state_file and os.path.exists(state_file):
        logging.info("Loading state codes from: %s", state_file)
        with open(state_file, 'r', encoding='utf-8') as f:
            state_map = ast.literal_eval(f.read())

    risk_zone_map = {}
    if zone_file and os.path.exists(zone_file):
        logging.info("Loading flood zone mappings from: %s", zone_file)
        with open(zone_file, 'r', encoding='utf-8') as f:
            raw_map = ast.literal_eval(f.read())
        risk_zone_map = {
            k: v.get('floodZoneType', '').replace('dcid:', '')
            for k, v in raw_map.items()
        }

    return state_map, risk_zone_map


def _init_worker(state_map: dict, risk_zone_map: dict):
    """Initializes worker process global mappings to avoid IPC overhead."""
    global _WORKER_STATE_MAP, _WORKER_RISK_ZONE_MAP
    _WORKER_STATE_MAP = state_map
    _WORKER_RISK_ZONE_MAP = risk_zone_map


def _pad_code(val: Any, target_len: int, min_len: int) -> Any:
    """Pads numeric FIPS codes with leading zeroes if length is within expected bounds."""
    if not isinstance(val, str):
        return val
    s = val.strip()
    if s.isdigit() and min_len <= len(s) <= target_len:
        return s.zfill(target_len)
    return s


def _process_chunk_worker(chunk: pd.DataFrame) -> Tuple[int, pd.DataFrame]:
    """Worker entrypoint executing _process_chunk with worker global maps."""
    agg = _process_chunk(chunk, _WORKER_STATE_MAP, _WORKER_RISK_ZONE_MAP)
    return len(chunk), agg


def _process_chunk(df: pd.DataFrame, state_map: dict,
                   risk_zone_map: dict) -> pd.DataFrame:
    """Processes a single DataFrame chunk into intermediate aggregations."""
    b_val = pd.to_numeric(df['amountPaidOnBuildingClaim'], errors='coerce')
    c_val = pd.to_numeric(df['amountPaidOnContentsClaim'], errors='coerce')

    df['b_val'] = b_val
    df['c_val'] = c_val

    bc_val = b_val.fillna(0.0) + c_val.fillna(0.0)
    bc_val[b_val.isna() & c_val.isna()] = np.nan
    df['bc_val'] = bc_val

    # Each non-empty policyCount row adds 1 to claim count
    df['claim_count'] = np.where(
        df['policyCount'].notna() &
        (df['policyCount'].astype(str).str.strip() != ''), 1.0, np.nan)

    # Geographic entities with zero-padding
    tract_clean = (df['censusTract'].astype(str).str.strip().str.replace(
        r'\.0$', '',
        regex=True).apply(_pad_code, target_len=11,
                          min_len=10).str.extract(r'([0-9]{11,})')[0])
    df['tract_place'] = tract_clean.apply(lambda x: f"dcid:geoId/{x[:11]}"
                                          if pd.notna(x) else None)

    county_clean = (df['countyCode'].astype(str).str.strip().str.replace(
        r'\.0$', '',
        regex=True).apply(_pad_code, target_len=5,
                          min_len=4).str.extract(r'(^[0-9]{5}$)')[0])
    df['county_place'] = county_clean.apply(lambda x: f"dcid:geoId/{x}"
                                            if pd.notna(x) else None)

    df['state_place'] = df['state'].astype(str).str.strip().map(state_map)
    df['country_place'] = 'dcid:country/USA'

    # Temporal entities
    df['month_date'] = df['dateOfLoss'].astype(str).str.extract(
        r'(^[0-9]{4}-[0-9]{2})')[0]
    df['year_date'] = pd.to_numeric(
        df['yearOfLoss'],
        errors='coerce').apply(lambda x: f"{int(x)}" if pd.notna(x) else None)

    # Flood zone categories (pre-computed dictionary mapping)
    unique_zones = df['ratedFloodZone'].dropna().unique()
    zone_dict = {
        z:
        f"FEMAFloodZone{str(z).strip()}" if str(z).strip().lower()
        not in ('nan', 'none', '') else "FEMAFloodZone"
        for z in unique_zones
    }
    df['specific_zone'] = df['ratedFloodZone'].map(zone_dict).fillna(
        "FEMAFloodZone")
    df['risk_zone'] = df['ratedFloodZone'].astype(str).str.strip().map(
        risk_zone_map)
    df['all_zone'] = ""

    place_cols = [
        'tract_place', 'county_place', 'state_place', 'country_place'
    ]
    date_configs = [('month_date', 'P1M'), ('year_date', 'P1Y')]
    zone_cols = ['specific_zone', 'risk_zone', 'all_zone']

    chunk_aggregates = []
    for p_col in place_cols:
        for d_col, period in date_configs:
            for z_col in zone_cols:
                valid_mask = df[p_col].notna() & df[d_col].notna()
                if z_col == 'risk_zone':
                    valid_mask = valid_mask & df[z_col].notna()

                sub = df[valid_mask]
                if len(sub) == 0:
                    continue

                grp = sub.groupby([d_col, p_col, z_col], as_index=False)[[
                    'claim_count', 'b_val', 'c_val', 'bc_val'
                ]].sum(min_count=1)

                grp['period'] = period
                grp = grp.rename(columns={
                    d_col: 'date',
                    p_col: 'place',
                    z_col: 'zone'
                })
                chunk_aggregates.append(grp[[
                    'date', 'place', 'zone', 'period', 'claim_count', 'b_val',
                    'c_val', 'bc_val'
                ]])

    if chunk_aggregates:
        return pd.concat(chunk_aggregates, ignore_index=True)
    return pd.DataFrame()


def _make_statvar_name(zone_val: str, metric: str, thing: str) -> str:
    """Constructs the StatVar DCID name."""
    prefix = f"_{zone_val}" if zone_val else ""
    return f"dcid:{metric}_NaturalHazardInsurance{prefix}_{thing}_FloodEvent"


def _write_tmcf(output_path: str):
    """Writes the template MCF file atomically."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    tmcf_path = f"{output_path}.tmcf"
    temp_tmcf = f"{tmcf_path}.tmp.{os.getpid()}"
    content = ("Node: E:nfip_output->E0\n"
               "observationDate: C:nfip_output->observationDate\n"
               "observationAbout: C:nfip_output->observationAbout\n"
               "value: C:nfip_output->value\n"
               "observationPeriod: C:nfip_output->observationPeriod\n"
               "unit: C:nfip_output->unit\n"
               "variableMeasured: C:nfip_output->variableMeasured\n"
               "typeOf: dcs:StatVarObservation\n"
               "measurementMethod: dcs:dcAggregate/NFIPInsuranceClaims\n"
               "#Aggregate: sum\n")
    with open(temp_tmcf, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(temp_tmcf, tmcf_path)
    logging.info("Wrote template MCF to: %s", tmcf_path)


def _write_node_mcf(output_path: str):
    """Writes the node MCF file atomically."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    mcf_path = f"{output_path}.mcf"
    temp_mcf = f"{mcf_path}.tmp.{os.getpid()}"
    with open(temp_mcf, 'w', encoding='utf-8') as f:
        f.write("# Generated node MCF for USFEMA_FloodInsuranceClaims\n")
    os.replace(temp_mcf, mcf_path)
    logging.info("Wrote node MCF to: %s", mcf_path)


def _write_counters(counters_path: str, num_input_rows: int,
                    num_cleaned_obs: int):
    """Writes job counters to a text file atomically."""
    output_dir = os.path.dirname(counters_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    temp_counters = f"{counters_path}.tmp.{os.getpid()}"
    with open(temp_counters, 'w', encoding='utf-8') as f:
        f.write(f"num_input_rows={num_input_rows}\n")
        f.write(f"num_cleaned_observations={num_cleaned_obs}\n")
    os.replace(temp_counters, counters_path)
    logging.info("Wrote counters to: %s", counters_path)


def process_data_vectorized(
        input_data: str,
        output_path: str,
        pv_map_arg: Optional[str] = None,
        chunk_size: int = 250000,
        num_workers: Optional[int] = None,
        output_counters: Optional[str] = 'counters/counters.txt'):
    """Executes the high-performance multi-process vectorized aggregation pipeline."""
    start_time = time.time()
    state_map, risk_zone_map = _load_mappings(pv_map_arg)

    usecols = [
        'dateOfLoss', 'yearOfLoss', 'censusTract', 'countyCode', 'state',
        'ratedFloodZone', 'amountPaidOnBuildingClaim',
        'amountPaidOnContentsClaim', 'policyCount'
    ]

    max_cpus = os.cpu_count() or 1
    workers = num_workers if num_workers is not None else max(1, max_cpus)
    if chunk_size == 250000 and workers > 8:
        chunk_size = max(50000, 2750000 // (workers * 2))

    logging.info(
        "Starting parallel processing for: %s (chunk_size=%s, workers=%s)",
        input_data, chunk_size, workers)

    reader = pd.read_csv(input_data,
                         usecols=usecols,
                         dtype=str,
                         chunksize=chunk_size,
                         low_memory=False)

    chunk_results = []
    total_rows = 0

    if workers > 1:
        mp_ctx = multiprocessing.get_context('spawn')
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=workers,
                mp_context=mp_ctx,
                initializer=_init_worker,
                initargs=(state_map, risk_zone_map)) as executor:
            for chunk_idx, (c_len, agg) in enumerate(
                    executor.map(_process_chunk_worker, reader), 1):
                total_rows += c_len
                if len(agg) > 0:
                    chunk_results.append(agg)
                logging.info(
                    "Processed chunk %s in parallel pool (rows read: %s)",
                    chunk_idx, total_rows)
    else:
        for chunk_idx, chunk in enumerate(reader, 1):
            total_rows += len(chunk)
            agg = _process_chunk(chunk, state_map, risk_zone_map)
            if len(agg) > 0:
                chunk_results.append(agg)
            logging.info("Processed chunk %s (rows read: %s)", chunk_idx,
                         total_rows)

    if not chunk_results:
        logging.error("No data found to aggregate from input: %s", input_data)
        raise RuntimeError(
            f"Process failed: No valid data aggregated from {input_data}")

    logging.info("Aggregating intermediate chunks...")
    combined = pd.concat(chunk_results, ignore_index=True)
    final_agg = combined.groupby(['date', 'place', 'zone', 'period'],
                                 as_index=False)[[
                                     'claim_count', 'b_val', 'c_val', 'bc_val'
                                 ]].sum(min_count=1)

    logging.info("Vectorized generation of observations for %s groups...",
                 len(final_agg))

    statvar_specs = [
        ('claim_count', 'CountOfClaims', 'BuildingStructureAndContents', '',
         0),
        ('b_val', 'SettlementAmount', 'BuildingStructure', 'dcs:USDollar', 2),
        ('c_val', 'SettlementAmount', 'BuildingContents', 'dcs:USDollar', 2),
        ('bc_val', 'SettlementAmount', 'BuildingStructureAndContents',
         'dcs:USDollar', 2),
    ]

    dfs_to_concat = []
    for col, metric, thing, unit, round_digits in statvar_specs:
        sub = final_agg[final_agg[col].notna()].copy()
        if len(sub) > 0:
            sub['variableMeasured'] = [
                _make_statvar_name(z, metric, thing) for z in sub['zone']
            ]
            sub['value'] = sub[col].round(
                round_digits) if round_digits else sub[col]
            sub['unit'] = unit
            dfs_to_concat.append(sub[[
                'date', 'place', 'value', 'period', 'unit', 'variableMeasured'
            ]])

    if dfs_to_concat:
        out_df = pd.concat(dfs_to_concat, ignore_index=True)
    else:
        out_df = pd.DataFrame(columns=[
            'observationDate', 'observationAbout', 'value',
            'observationPeriod', 'unit', 'variableMeasured'
        ])

    out_df = out_df.rename(
        columns={
            'date': 'observationDate',
            'place': 'observationAbout',
            'period': 'observationPeriod'
        })

    logging.info("Sorting %s output observation rows...", len(out_df))
    out_df = out_df.sort_values(
        by=['observationDate', 'observationAbout', 'variableMeasured'],
        na_position='first')

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    csv_path = f"{output_path}.csv"
    temp_csv = f"{csv_path}.tmp.{os.getpid()}"
    out_df.to_csv(temp_csv, index=False)
    os.replace(temp_csv, csv_path)
    logging.info("Wrote cleaned observations to: %s", csv_path)

    _write_tmcf(output_path)
    _write_node_mcf(output_path)

    if output_counters:
        _write_counters(output_counters, total_rows, len(out_df))

    elapsed = time.time() - start_time
    logging.info(
        "Successfully completed processing into %s observations in %.2f seconds.",
        len(out_df), elapsed)


def process_data():
    input_data = _FLAGS.input_data
    if isinstance(input_data, list):
        input_data = input_data[
            0] if input_data else 'input_file/fema_nfip_claims.csv'

    process_data_vectorized(input_data=input_data,
                            output_path=_FLAGS.output_path,
                            pv_map_arg=_FLAGS.pv_map,
                            chunk_size=_FLAGS.chunk_size,
                            num_workers=_FLAGS.num_workers,
                            output_counters=_FLAGS.output_counters)


def main(_):
    process_data()


if __name__ == '__main__':
    app.run(main)
