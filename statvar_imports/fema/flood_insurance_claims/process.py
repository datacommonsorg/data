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

import multiprocessing
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

from absl import app
from absl import flags
from absl import logging
import numpy as np
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_IMPORTER_DIR = os.path.abspath(
    os.path.join(_SCRIPT_DIR, '../../../tools/statvar_importer'))
if _IMPORTER_DIR not in sys.path:
    sys.path.insert(0, _IMPORTER_DIR)


def _define_flag_if_not_exists(flag_type, name, default, help_str):
    if name not in flags.FLAGS:
        flag_type(name, default, help_str)


_define_flag_if_not_exists(flags.DEFINE_string, 'input_data',
                           'input_file/fema_nfip_claims.csv',
                           'Input CSV file containing FEMA claims data.')
_define_flag_if_not_exists(flags.DEFINE_string, 'output_path',
                           'output/nfip_output',
                           'Prefix path for output CSV and TMCF files.')
_define_flag_if_not_exists(flags.DEFINE_string, 'config_file', None,
                           'Optional config file for legacy processing.')
_define_flag_if_not_exists(flags.DEFINE_string, 'pv_map', None,
                           'Optional custom PV map files configuration.')
_define_flag_if_not_exists(flags.DEFINE_string, 'existing_statvar_mcf', None,
                           'Optional existing StatVar MCF file.')
_define_flag_if_not_exists(flags.DEFINE_string, 'output_counters',
                           'counters/counters.txt',
                           'Path to output counters summary file.')
_define_flag_if_not_exists(flags.DEFINE_integer, 'chunk_size', 250000,
                           'Number of rows per chunk for batched processing.')
_define_flag_if_not_exists(
    flags.DEFINE_integer, 'num_workers', None,
    'Number of parallel worker processes to use (defaults to CPU count).')
_define_flag_if_not_exists(
    flags.DEFINE_bool, 'use_legacy_processor', False,
    'If True, use the legacy StatVarDataProcessor interpreter.')

_FLAGS = flags.FLAGS

# Built-in state postal and name mappings to Data Commons DCIDs
_DEFAULT_STATE_MAP = {
    'AL': 'dcid:geoId/01',
    'AK': 'dcid:geoId/02',
    'AZ': 'dcid:geoId/04',
    'AR': 'dcid:geoId/05',
    'CA': 'dcid:geoId/06',
    'CO': 'dcid:geoId/08',
    'CT': 'dcid:geoId/09',
    'DE': 'dcid:geoId/10',
    'DC': 'dcid:geoId/11',
    'FL': 'dcid:geoId/12',
    'GA': 'dcid:geoId/13',
    'HI': 'dcid:geoId/15',
    'ID': 'dcid:geoId/16',
    'IL': 'dcid:geoId/17',
    'IN': 'dcid:geoId/18',
    'IA': 'dcid:geoId/19',
    'KS': 'dcid:geoId/20',
    'KY': 'dcid:geoId/21',
    'LA': 'dcid:geoId/22',
    'ME': 'dcid:geoId/23',
    'MD': 'dcid:geoId/24',
    'MA': 'dcid:geoId/25',
    'MI': 'dcid:geoId/26',
    'MN': 'dcid:geoId/27',
    'MS': 'dcid:geoId/28',
    'MO': 'dcid:geoId/29',
    'MT': 'dcid:geoId/30',
    'NE': 'dcid:geoId/31',
    'NV': 'dcid:geoId/32',
    'NH': 'dcid:geoId/33',
    'NJ': 'dcid:geoId/34',
    'NM': 'dcid:geoId/35',
    'NY': 'dcid:geoId/36',
    'NC': 'dcid:geoId/37',
    'ND': 'dcid:geoId/38',
    'OH': 'dcid:geoId/39',
    'OK': 'dcid:geoId/40',
    'OR': 'dcid:geoId/41',
    'PA': 'dcid:geoId/42',
    'RI': 'dcid:geoId/44',
    'SC': 'dcid:geoId/45',
    'SD': 'dcid:geoId/46',
    'TN': 'dcid:geoId/47',
    'TX': 'dcid:geoId/48',
    'UT': 'dcid:geoId/49',
    'VT': 'dcid:geoId/50',
    'VA': 'dcid:geoId/51',
    'WA': 'dcid:geoId/53',
    'WV': 'dcid:geoId/54',
    'WI': 'dcid:geoId/55',
    'WY': 'dcid:geoId/56',
    'AS': 'dcid:geoId/60',
    'GU': 'dcid:geoId/66',
    'MP': 'dcid:geoId/69',
    'PR': 'dcid:geoId/72',
    'UM': 'dcid:geoId/74',
    'VI': 'dcid:geoId/78',
    'alabama': 'dcid:geoId/01',
    'alaska': 'dcid:geoId/02',
    'arizona': 'dcid:geoId/04',
    'arkansas': 'dcid:geoId/05',
    'california': 'dcid:geoId/06',
    'colorado': 'dcid:geoId/08',
    'connecticut': 'dcid:geoId/09',
    'delaware': 'dcid:geoId/10',
    'district of columbia': 'dcid:geoId/11',
    'florida': 'dcid:geoId/12',
    'georgia': 'dcid:geoId/13',
    'guam': 'dcid:geoId/66',
    'hawaii': 'dcid:geoId/15',
    'idaho': 'dcid:geoId/16',
    'illinois': 'dcid:geoId/17',
    'indiana': 'dcid:geoId/18',
    'iowa': 'dcid:geoId/19',
    'kansas': 'dcid:geoId/20',
    'kentucky': 'dcid:geoId/21',
    'louisiana': 'dcid:geoId/22',
    'maine': 'dcid:geoId/23',
    'maryland': 'dcid:geoId/24',
    'massachusetts': 'dcid:geoId/25',
    'michigan': 'dcid:geoId/26',
    'minnesota': 'dcid:geoId/27',
    'mississippi': 'dcid:geoId/28',
    'missouri': 'dcid:geoId/29',
    'montana': 'dcid:geoId/30',
    'nebraska': 'dcid:geoId/31',
    'nevada': 'dcid:geoId/32',
    'new hampshire': 'dcid:geoId/33',
    'new jersey': 'dcid:geoId/34',
    'new mexico': 'dcid:geoId/35',
    'new york': 'dcid:geoId/36',
    'north carolina': 'dcid:geoId/37',
    'north dakota': 'dcid:geoId/38',
    'ohio': 'dcid:geoId/39',
    'oklahoma': 'dcid:geoId/40',
    'oregon': 'dcid:geoId/41',
    'puerto rico': 'dcid:geoId/72',
    'pennsylvania': 'dcid:geoId/42',
    'rhode island': 'dcid:geoId/44',
    'south carolina': 'dcid:geoId/45',
    'south dakota': 'dcid:geoId/46',
    'tennessee': 'dcid:geoId/47',
    'texas': 'dcid:geoId/48',
    'utah': 'dcid:geoId/49',
    'vermont': 'dcid:geoId/50',
    'virginia': 'dcid:geoId/51',
    'washington': 'dcid:geoId/53',
    'west virginia': 'dcid:geoId/54',
    'wisconsin': 'dcid:geoId/55',
    'wyoming': 'dcid:geoId/56',
}

# Built-in FEMA rated flood zone to flood zone type mappings
_DEFAULT_RISK_ZONE_MAP = {
    'A': 'FEMAHighRiskFloodZone',
    'A01': 'FEMAHighRiskFloodZone',
    'A02': 'FEMAHighRiskFloodZone',
    'A03': 'FEMAHighRiskFloodZone',
    'A04': 'FEMAHighRiskFloodZone',
    'A05': 'FEMAHighRiskFloodZone',
    'A06': 'FEMAHighRiskFloodZone',
    'A07': 'FEMAHighRiskFloodZone',
    'A08': 'FEMAHighRiskFloodZone',
    'A09': 'FEMAHighRiskFloodZone',
    'A10': 'FEMAHighRiskFloodZone',
    'A11': 'FEMAHighRiskFloodZone',
    'A12': 'FEMAHighRiskFloodZone',
    'A13': 'FEMAHighRiskFloodZone',
    'A14': 'FEMAHighRiskFloodZone',
    'A15': 'FEMAHighRiskFloodZone',
    'A16': 'FEMAHighRiskFloodZone',
    'A17': 'FEMAHighRiskFloodZone',
    'A18': 'FEMAHighRiskFloodZone',
    'A19': 'FEMAHighRiskFloodZone',
    'A20': 'FEMAHighRiskFloodZone',
    'A21': 'FEMAHighRiskFloodZone',
    'A22': 'FEMAHighRiskFloodZone',
    'A23': 'FEMAHighRiskFloodZone',
    'A24': 'FEMAHighRiskFloodZone',
    'A25': 'FEMAHighRiskFloodZone',
    'A26': 'FEMAHighRiskFloodZone',
    'A27': 'FEMAHighRiskFloodZone',
    'A28': 'FEMAHighRiskFloodZone',
    'A29': 'FEMAHighRiskFloodZone',
    'A30': 'FEMAHighRiskFloodZone',
    'A99': 'FEMAHighRiskFloodZone',
    'AA': 'FEMAHighRiskFloodZone',
    'AE': 'FEMAHighRiskFloodZone',
    'AH': 'FEMAHighRiskFloodZone',
    'AHB': 'FEMAHighRiskFloodZone',
    'AO': 'FEMAHighRiskFloodZone',
    'AOB': 'FEMAHighRiskFloodZone',
    'AR': 'FEMAHighRiskFloodZone',
    'AS': 'FEMAHighRiskFloodZone',
    'V': 'FEMAHighRiskFloodZone',
    'V01': 'FEMAHighRiskFloodZone',
    'V02': 'FEMAHighRiskFloodZone',
    'V03': 'FEMAHighRiskFloodZone',
    'V04': 'FEMAHighRiskFloodZone',
    'V05': 'FEMAHighRiskFloodZone',
    'V06': 'FEMAHighRiskFloodZone',
    'V07': 'FEMAHighRiskFloodZone',
    'V08': 'FEMAHighRiskFloodZone',
    'V09': 'FEMAHighRiskFloodZone',
    'V10': 'FEMAHighRiskFloodZone',
    'V11': 'FEMAHighRiskFloodZone',
    'V12': 'FEMAHighRiskFloodZone',
    'V13': 'FEMAHighRiskFloodZone',
    'V14': 'FEMAHighRiskFloodZone',
    'V15': 'FEMAHighRiskFloodZone',
    'V16': 'FEMAHighRiskFloodZone',
    'V17': 'FEMAHighRiskFloodZone',
    'V18': 'FEMAHighRiskFloodZone',
    'V19': 'FEMAHighRiskFloodZone',
    'V20': 'FEMAHighRiskFloodZone',
    'V21': 'FEMAHighRiskFloodZone',
    'V22': 'FEMAHighRiskFloodZone',
    'V23': 'FEMAHighRiskFloodZone',
    'V24': 'FEMAHighRiskFloodZone',
    'V27': 'FEMAHighRiskFloodZone',
    'V30': 'FEMAHighRiskFloodZone',
    'VE': 'FEMAHighRiskFloodZone',
    'B': 'FEMAModerateRiskFloodZone',
    'C': 'FEMALowRiskFloodZone',
    'D': 'FEMALowRiskFloodZone',
    'X': 'FEMALowRiskFloodZone',
}

# Worker global caches for multiprocessing
_WORKER_STATE_MAP = None
_WORKER_RISK_ZONE_MAP = None


def _init_worker(state_map: dict, risk_zone_map: dict):
    """Initializes worker process global mappings to avoid IPC overhead."""
    global _WORKER_STATE_MAP, _WORKER_RISK_ZONE_MAP
    _WORKER_STATE_MAP = state_map
    _WORKER_RISK_ZONE_MAP = risk_zone_map


def _resolve_map_path(pv_map_arg: Optional[str], prefix: str) -> Optional[str]:
    """Finds the mapping file path from pv_map flag if specified and exists."""
    if pv_map_arg:
        items = pv_map_arg if isinstance(pv_map_arg,
                                         list) else pv_map_arg.split(',')
        for item in items:
            if item.startswith(f"{prefix}:"):
                path = item.split(':', 1)[1].strip()
                if os.path.exists(path):
                    return path
    return None


def _load_mappings(pv_map_arg: Optional[str] = None) -> Tuple[dict, dict]:
    """Loads state and floodzone mappings from embedded defaults or optional custom file."""
    state_map = _DEFAULT_STATE_MAP
    risk_zone_map = _DEFAULT_RISK_ZONE_MAP

    if pv_map_arg:
        state_map_file = _resolve_map_path(pv_map_arg, 'observationAbout')
        if state_map_file and os.path.exists(state_map_file):
            logging.info("Loading custom state codes from: %s", state_map_file)
            with open(state_map_file, 'r', encoding='utf-8') as f:
                state_map = eval(f.read())

        floodzone_map_file = _resolve_map_path(pv_map_arg, 'ratedFloodZone')
        if floodzone_map_file and os.path.exists(floodzone_map_file):
            logging.info("Loading custom flood zone mappings from: %s",
                         floodzone_map_file)
            with open(floodzone_map_file, 'r', encoding='utf-8') as f:
                raw_map = eval(f.read())
            risk_zone_map = {
                k: v.get('floodZoneType', '').replace('dcid:', '')
                for k, v in raw_map.items()
            }

    return state_map, risk_zone_map


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

    # Geographic entities
    tract_clean = df['censusTract'].astype(str).str.extract(r'([0-9]{11,})')[0]
    df['tract_place'] = tract_clean.apply(lambda x: f"dcid:geoId/{x[:11]}"
                                          if pd.notna(x) else None)

    county_clean = df['countyCode'].astype(str).str.extract(r'(^[0-9]{5}$)')[0]
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

    # Flood zone categories
    df['specific_zone'] = df['ratedFloodZone'].apply(
        lambda x: f"FEMAFloodZone{str(x).strip()}" if pd.notna(x) and str(
            x).strip().lower() not in ('nan', 'none', '') else "FEMAFloodZone")
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
    """Writes the template MCF file."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(output_path)
    tmcf_path = f"{output_path}.tmcf"

    content = f"""Node: E:{base_name}->E0
observationDate: C:{base_name}->observationDate
observationAbout: C:{base_name}->observationAbout
value: C:{base_name}->value
observationPeriod: C:{base_name}->observationPeriod
unit: C:{base_name}->unit
variableMeasured: C:{base_name}->variableMeasured
typeOf: dcs:StatVarObservation
measurementMethod: dcs:dcAggregate/NFIPInsuranceClaims
#Aggregate: sum
"""
    with open(tmcf_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info("Wrote template MCF to: %s", tmcf_path)


def _write_node_mcf(output_path: str):
    """Writes an empty node MCF to satisfy manifest import_inputs."""
    mcf_path = f"{output_path}.mcf"
    with open(mcf_path, 'w', encoding='utf-8') as f:
        f.write("# Generated node MCF for USFEMA_FloodInsuranceClaims\n")
    logging.info("Wrote node MCF to: %s", mcf_path)


def _write_counters(output_counters_path: Optional[str], total_rows: int,
                    total_observations: int):
    """Writes import counters if output path is configured."""
    if not output_counters_path:
        return
    counters_dir = os.path.dirname(output_counters_path)
    if counters_dir:
        os.makedirs(counters_dir, exist_ok=True)
    with open(output_counters_path, 'w', encoding='utf-8') as f:
        f.write(f"num_input_rows={total_rows}\n")
        f.write(f"num_cleaned_observations={total_observations}\n")
    logging.info("Wrote counters to: %s", output_counters_path)


def process_data_vectorized(input_data: str,
                            output_path: str,
                            pv_map_arg: Optional[str] = None,
                            chunk_size: int = 250000,
                            num_workers: Optional[int] = None,
                            output_counters: Optional[str] = None):
    """
    Processes FEMA NFIP claims CSV using an optimized parallel chunked pipeline.
    """
    start_time = time.perf_counter()

    state_map, risk_zone_map = _load_mappings(pv_map_arg)

    usecols = [
        'censusTract', 'countyCode', 'state', 'dateOfLoss', 'yearOfLoss',
        'ratedFloodZone', 'amountPaidOnBuildingClaim',
        'amountPaidOnContentsClaim', 'policyCount'
    ]

    max_cpus = os.cpu_count() or 4
    if num_workers is None or num_workers <= 0:
        workers = min(max_cpus, 32)
    else:
        workers = min(num_workers, max_cpus)

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
        with multiprocessing.Pool(processes=workers,
                                  initializer=_init_worker,
                                  initargs=(state_map, risk_zone_map)) as pool:
            for chunk_idx, (c_len, agg) in enumerate(
                    pool.imap(_process_chunk_worker, reader), 1):
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
        logging.warning("No data found to aggregate.")
        return

    logging.info("Aggregating intermediate chunks...")
    combined = pd.concat(chunk_results, ignore_index=True)
    final_grp = combined.groupby(['date', 'place', 'zone', 'period'],
                                 as_index=False)[[
                                     'claim_count', 'b_val', 'c_val', 'bc_val'
                                 ]].sum(min_count=1)

    logging.info("Vectorized generation of observations for %s groups...",
                 len(final_grp))

    zone_sv_claim = final_grp['zone'].apply(lambda z: _make_statvar_name(
        z, 'CountOfClaims', 'BuildingStructureAndContents'))
    zone_sv_b = final_grp['zone'].apply(lambda z: _make_statvar_name(
        z, 'SettlementAmount', 'BuildingStructure'))
    zone_sv_c = final_grp['zone'].apply(lambda z: _make_statvar_name(
        z, 'SettlementAmount', 'BuildingContents'))
    zone_sv_bc = final_grp['zone'].apply(lambda z: _make_statvar_name(
        z, 'SettlementAmount', 'BuildingStructureAndContents'))

    parts = []

    mask_cnt = final_grp['claim_count'].notna()
    if mask_cnt.any():
        parts.append(
            pd.DataFrame({
                'observationDate':
                final_grp.loc[mask_cnt, 'date'],
                'observationAbout':
                final_grp.loc[mask_cnt, 'place'],
                'value':
                final_grp.loc[mask_cnt, 'claim_count'].astype(int),
                'observationPeriod':
                final_grp.loc[mask_cnt, 'period'],
                'unit':
                '',
                'variableMeasured':
                zone_sv_claim[mask_cnt]
            }))

    mask_b = final_grp['b_val'].notna()
    if mask_b.any():
        parts.append(
            pd.DataFrame({
                'observationDate': final_grp.loc[mask_b, 'date'],
                'observationAbout': final_grp.loc[mask_b, 'place'],
                'value': final_grp.loc[mask_b, 'b_val'].round(2),
                'observationPeriod': final_grp.loc[mask_b, 'period'],
                'unit': 'dcs:USDollar',
                'variableMeasured': zone_sv_b[mask_b]
            }))

    mask_c = final_grp['c_val'].notna()
    if mask_c.any():
        parts.append(
            pd.DataFrame({
                'observationDate': final_grp.loc[mask_c, 'date'],
                'observationAbout': final_grp.loc[mask_c, 'place'],
                'value': final_grp.loc[mask_c, 'c_val'].round(2),
                'observationPeriod': final_grp.loc[mask_c, 'period'],
                'unit': 'dcs:USDollar',
                'variableMeasured': zone_sv_c[mask_c]
            }))

    mask_bc = final_grp['bc_val'].notna()
    if mask_bc.any():
        parts.append(
            pd.DataFrame({
                'observationDate': final_grp.loc[mask_bc, 'date'],
                'observationAbout': final_grp.loc[mask_bc, 'place'],
                'value': final_grp.loc[mask_bc, 'bc_val'].round(2),
                'observationPeriod': final_grp.loc[mask_bc, 'period'],
                'unit': 'dcs:USDollar',
                'variableMeasured': zone_sv_bc[mask_bc]
            }))

    out_df = pd.concat(parts, ignore_index=True)
    logging.info("Sorting %s output observation rows...", len(out_df))
    out_df = out_df.sort_values(by=[
        'observationDate', 'observationAbout', 'variableMeasured',
        'observationPeriod'
    ])

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    csv_path = f"{output_path}.csv"
    out_df[[
        'observationDate', 'observationAbout', 'value', 'observationPeriod',
        'unit', 'variableMeasured'
    ]].to_csv(csv_path, index=False)
    logging.info("Wrote cleaned observations to: %s", csv_path)

    _write_tmcf(output_path)
    _write_node_mcf(output_path)
    _write_counters(output_counters, total_rows, len(out_df))

    elapsed = time.perf_counter() - start_time
    logging.info(
        "Successfully completed processing into %s observations in %.2f seconds.",
        len(out_df), elapsed)


def _process_data_legacy():
    """Runs data processing using the legacy StatVarDataProcessor."""
    from stat_var_processor import StatVarDataProcessor, process
    from mcf_file_util import strip_namespace

    class NFIPStatVarDataProcessor(StatVarDataProcessor):

        def preprocess_stat_var_obs_pvs(self, pvs: dict) -> list:
            if 'observationPeriod' not in pvs:
                date = pvs.get('observationDate', '')
                if date:
                    if len(date) == len('YYYY'):
                        pvs['observationPeriod'] = 'P1Y'
                    elif len(date) == len('YYYY-MM'):
                        pvs['observationPeriod'] = 'P1M'
            svobs_pvs_list = [pvs]
            if strip_namespace(pvs.get('floodZoneType',
                                       '')).startswith('FEMAFloodZone'):
                agg_pvs = dict(pvs)
                agg_pvs.pop('floodZoneType')
                svobs_pvs_list.append(agg_pvs)
                self._counters.add_counter('additional-count-svobs', 1)

            new_settlement_svobs = []
            for svobs_pvs in svobs_pvs_list:
                if strip_namespace(svobs_pvs.get('measuredProperty',
                                                 '')) == 'settlementAmount':
                    if strip_namespace(svobs_pvs.get('insuredThing', '')) in [
                            'BuildingStructure', 'BuildingContents'
                    ]:
                        settlement_pvs = dict(svobs_pvs)
                        settlement_pvs[
                            'insuredThing'] = 'dcs:BuildingStructureAndContents'
                        new_settlement_svobs.append(settlement_pvs)
                        self._counters.add_counter(
                            'additional-settlement-svobs', 1)
            svobs_pvs_list.extend(new_settlement_svobs)
            return svobs_pvs_list

    process(data_processor_class=NFIPStatVarDataProcessor,
            input_data=_FLAGS.input_data,
            output_path=_FLAGS.output_path,
            config=_FLAGS.config_file,
            pv_map_files=_FLAGS.pv_map,
            parallelism=os.cpu_count())


def process_data():
    if _FLAGS.use_legacy_processor:
        _process_data_legacy()
        return

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
