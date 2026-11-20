# Copyright 2026 Google LLC
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
"""Downloads NAEP input CSV files from the Nation's Report Card Data Service API.

Queries:
  https://www.nationsreportcard.gov/Dataservice/GetAdhocData.aspx

Optimizations in v2:
  - Uses single 55-state queries for fast indexed composite scales, 13-state
    pilot queries for Grade 12 Reading, and parallel 8-state batches directly
    for multi-year state content subscales (*RPS*) to avoid SQL full-table scan
    timeouts (>120s) and 3x retry penalties.
  - Warm-gates each content subscale (subject, grade, scale) with a single
    initial query before fanning out remaining queries for that subscale,
    preventing multi-thread cold-cache stampedes on NCES's backend SQL engine.
  - Uses single-attempt 60s probes with concurrent 7-batch fallback if any
    55-state composite query stalls, while preserving deterministic CSV order.

Generates the 16 input CSV files in input_files/:
  - 12 national files: naep_national_<subject>.csv
  - 4 state files: naep_state_<subject>.csv
"""

from concurrent import futures
import csv
import os
import random
import tempfile
import threading
import time
from typing import Dict, List, Optional, Tuple

from absl import app
from absl import flags
from absl import logging
import requests
from requests import adapters

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

FLAGS = flags.FLAGS

flags.DEFINE_string('output_dir',
                    os.path.join(MODULE_DIR, 'input_files'),
                    'Directory where downloaded NAEP CSV files will be saved.',
                    allow_override=True)
flags.DEFINE_list('files',
                  None,
                  'Optional comma-separated list of CSV filenames to download '
                  '(e.g. "naep_national_civ.csv,naep_state_wri.csv"). '
                  'If omitted, downloads all 16 files.',
                  allow_override=True)
flags.DEFINE_integer(
    'max_workers',
    8,
    'Maximum number of concurrent HTTP worker threads for NAEP API requests.',
    allow_override=True)
flags.DEFINE_integer('read_timeout',
                     120,
                     'HTTP read timeout in seconds per NAEP API request.',
                     allow_override=True)

NAEP_API_URL = 'https://www.nationsreportcard.gov/Dataservice/GetAdhocData.aspx'

# Exact 17 columns in the NAEP input CSVs (jurisLabel from the API is omitted).
CSV_COLUMNS = [
    'year',
    'sample',
    'yearSampleLabel',
    'Cohort',
    'CohortLabel',
    'stattype',
    'subject',
    'grade',
    'scale',
    'jurisdiction',
    'variable',
    'variableLabel',
    'varValue',
    'varValueLabel',
    'value',
    'isStatDisplayable',
    'errorFlag',
]

# Standard demographic/school variables in exact bucket order.
ALL_VARIABLES = [
    'TOTAL',
    'SRACE10',
    'GENDER',
    'SLUNCH3',
    'SCHTYPE',
    'CHRTRPT',
    'UTOL4',
    'IEP',
    'LEP',
]

# StatType batches in exact bucket order.
# Note: ALD:AD and ALC:AD must be queried in separate requests because the
# NAEP API deduplicates stattypes sharing the ":AD" suffix if combined.
STATTYPE_BATCHES_COMPOSITE = [
    'MN:MN,RP:RP',
    'ALD:BA,ALD:PR,ALD:AD',
    'ALC:BB,ALC:AB,ALC:AP,ALC:AD',
    'SD:SD,PC:P1,PC:P2,PC:P5,PC:P7,PC:P9',
]

# Content subscales do not have achievement levels (ALD / ALC).
STATTYPE_BATCHES_SUBSCALE = [
    'MN:MN,RP:RP',
    'SD:SD,PC:P1,PC:P2,PC:P5,PC:P7,PC:P9',
]

# Scales that include achievement levels (ALD:* and ALC:*).
COMPOSITE_SCALES = {
    'CIVRP',
    'ERPCM',
    'HRPCM',
    'MRPCM',
    'MWPCM',
    'RRPCM',
    'SRPUV',
    'TRPUN',
    'WRIRP',
}

# Indexed composite scales and fast single-scale national subjects that do not
# require per-subscale SQL cache warm-gating.
FAST_SCALES = COMPOSITE_SCALES | {'MUSRP', 'VISRP', 'VOCRP'}

NATIONAL_JURISDICTION = 'NP,NR,NT'

# All 55 valid NAEP state/territory jurisdictions from jurisdiction_map.py
# (excludes MP and UM which return HTTP 400 on the NAEP API).
# Fallback batches are structured so every batch contains at least one state
# from every assessment if a full 55-state request ever times out.
STATE_JURISDICTION_BATCHES = [
    'AL,AK,AZ,AR,CA,CO,CT,DE',
    'DC,FL,GA,HI,ID,IL,IN,NY',
    'KS,KY,LA,ME,MD,MA,MI,MN',
    'MS,MO,MT,NE,NV,NH,NJ,NM',
    'IA,NC,ND,OH,OK,OR,PA,RI',
    'SC,SD,TN,TX,UT,VT,VA,WA',
    'WV,WI,WY,AS,GU,PR,VI',
]

ALL_STATE_JURISDICTIONS = ','.join(STATE_JURISDICTION_BATCHES)

# The 15 states participating in Grade 12 state-level Reading pilot assessments.
RED_G12_PILOT_STATES = 'AR,CT,FL,IA,ID,IL,KY,MA,MI,NH,NJ,SD,TN,WV,WI'

# Download query specifications for all 16 NAEP CSV files.
# All years are fetched automatically by omitting the 'Year' parameter.
FILE_SPECS: Dict[str, List[Dict]] = {
    'naep_national_civ.csv': [
        {
            'subject': 'CIV',
            'grade': 4,
            'scales': ['CIVRP'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'CIV',
            'grade': 8,
            'scales': ['CIVRP'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'CIV',
            'grade': 12,
            'scales': ['CIVRP'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
    ],
    'naep_national_ecn.csv': [{
        'subject': 'ECN',
        'grade': 12,
        'scales': ['ERPCM', 'ERPS1', 'ERPS2', 'ERPS3'],
        'jurisdiction_batches': [NATIONAL_JURISDICTION],
    },],
    'naep_national_geo.csv': [
        {
            'subject': 'GEO',
            'grade': 4,
            'scales': ['GRPS1', 'GRPS2', 'GRPS3'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'GEO',
            'grade': 8,
            'scales': ['GRPS1', 'GRPS2', 'GRPS3'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'GEO',
            'grade': 12,
            'scales': ['GRPS1', 'GRPS2', 'GRPS3'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
    ],
    'naep_national_his.csv': [
        {
            'subject': 'HIS',
            'grade': 4,
            'scales': ['HRPCM', 'HRPS1', 'HRPS2', 'HRPS3', 'HRPS4'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'HIS',
            'grade': 8,
            'scales': ['HRPCM', 'HRPS1', 'HRPS2', 'HRPS3', 'HRPS4'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'HIS',
            'grade': 12,
            'scales': ['HRPCM', 'HRPS1', 'HRPS2', 'HRPS3', 'HRPS4'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
    ],
    'naep_national_mat.csv': [
        {
            'subject': 'MAT',
            'grade': 4,
            'scales': ['MRPCM', 'MRPS1', 'MRPS2', 'MRPS3', 'MRPS4', 'MRPS5'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'MAT',
            'grade': 8,
            'scales': ['MRPCM', 'MRPS1', 'MRPS2', 'MRPS3', 'MRPS4', 'MRPS5'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
    ],
    'naep_national_mus.csv': [{
        'subject': 'MUS',
        'grade': 8,
        'scales': ['MUSRP'],
        'jurisdiction_batches': [NATIONAL_JURISDICTION],
    },],
    'naep_national_red.csv': [
        {
            'subject': 'RED',
            'grade': 4,
            'scales': ['RRPCM', 'RRPS1', 'RRPS2'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'RED',
            'grade': 8,
            'scales': ['RRPCM', 'RRPS1', 'RRPS2', 'RRPS3'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'RED',
            'grade': 12,
            'scales': ['RRPCM', 'RRPS1', 'RRPS2', 'RRPS3', 'RRPS4'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
    ],
    'naep_national_sci.csv': [
        {
            'subject': 'SCI',
            'grade': 4,
            'scales': ['SRPUV', 'SRPS2', 'SRPS3', 'SRPS1'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'SCI',
            'grade': 8,
            'scales': ['SRPUV', 'SRPS2', 'SRPS3', 'SRPS1'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
    ],
    'naep_national_tel.csv': [{
        'subject': 'TEL',
        'grade': 8,
        'scales': ['TRPUN', 'TRPP1', 'TRPP2', 'TRPP3'],
        'jurisdiction_batches': [NATIONAL_JURISDICTION],
    },],
    'naep_national_vis.csv': [{
        'subject': 'VIS',
        'grade': 8,
        'scales': ['VISRP'],
        'jurisdiction_batches': [NATIONAL_JURISDICTION],
    },],
    'naep_national_voc.csv': [
        {
            'subject': 'VOC',
            'grade': 4,
            'scales': ['VOCRP'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'VOC',
            'grade': 8,
            'scales': ['VOCRP'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'VOC',
            'grade': 12,
            'scales': ['VOCRP'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
    ],
    'naep_national_wri.csv': [
        {
            'subject': 'WRI',
            'grade': 4,
            'scales': ['WRIRP'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'WRI',
            'grade': 8,
            'scales': ['WRIRP'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
        {
            'subject': 'WRI',
            'grade': 12,
            'scales': ['WRIRP'],
            'jurisdiction_batches': [NATIONAL_JURISDICTION],
        },
    ],
    'naep_state_mat.csv': [{
        'subject': 'MAT',
        'grades_and_scales': [
            (4, ['MRPCM', 'MRPS1', 'MRPS2', 'MRPS3', 'MRPS4', 'MRPS5']),
            (8, ['MRPCM', 'MRPS1', 'MRPS2', 'MRPS3', 'MRPS4', 'MRPS5']),
        ],
        'jurisdiction_batches': [ALL_STATE_JURISDICTIONS],
        'subscale_jurisdiction_batches': STATE_JURISDICTION_BATCHES,
    },],
    'naep_state_red.csv': [
        {
            'subject': 'RED',
            'grades_and_scales': [
                (4, ['RRPCM', 'RRPS1', 'RRPS2']),
                (8, ['RRPCM', 'RRPS1', 'RRPS2', 'RRPS3']),
            ],
            'jurisdiction_batches': [ALL_STATE_JURISDICTIONS],
            'subscale_jurisdiction_batches': STATE_JURISDICTION_BATCHES,
        },
        {
            'subject': 'RED',
            'grades_and_scales': [(12, ['RRPCM', 'RRPS1', 'RRPS4']),],
            'jurisdiction_batches': [ALL_STATE_JURISDICTIONS],
        },
    ],
    'naep_state_sci.csv': [{
        'subject': 'SCI',
        'grades_and_scales': [
            (4, ['SRPUV', 'SRPS2', 'SRPS3', 'SRPS1']),
            (8, ['SRPUV', 'SRPS2', 'SRPS3', 'SRPS1']),
        ],
        'jurisdiction_batches': [ALL_STATE_JURISDICTIONS],
        'subscale_jurisdiction_batches': STATE_JURISDICTION_BATCHES,
    },],
    'naep_state_wri.csv': [{
        'subject': 'WRI',
        'grades_and_scales': [(4, ['WRIRP']),],
        'jurisdiction_batches': [ALL_STATE_JURISDICTIONS],
    },],
}

QueryTask = Tuple[str, int, str, str, str, str]
ScaleKey = Tuple[str, int, str]
WarmKey = Tuple[str, int, str, str]

_THREAD_LOCAL = threading.local()
_CONNECT_TIMEOUT_SECS = 15
_ALL_STATES_PROBE_TIMEOUT_SECS = 60
_FALLBACK_WORKERS = 4

# Primary composite/first scale per subject used to discover valid assessment
# years when a subscale triggers NCES's GetDependentInfo() HTTP 400 bug on
# legacy R2 cycles when 'Year' is omitted.
_PRIMARY_SCALE_BY_SUBJECT: Dict[str, str] = {
    'CIV': 'CIVRP',
    'ECN': 'ERPCM',
    'GEO': 'GRPS1',
    'HIS': 'HRPCM',
    'MAT': 'MRPCM',
    'MUS': 'MUSRP',
    'RED': 'RRPCM',
    'SCI': 'SRPUV',
    'TEL': 'TRPUN',
    'VIS': 'VISRP',
    'VOC': 'VOCRP',
    'WRI': 'WRIRP',
}

_YEAR_CACHE_LOCK = threading.Lock()
_DESCENDING_YEARS_CACHE: Dict[Tuple[str, int, str], str] = {}
_EXPLICIT_YEAR_SCALE_LOCKS: Dict[ScaleKey, threading.Lock] = {}
# Scales known to fail in NCES GetDependentInfo() when 'Year' is omitted because
# their earliest cycle in the NCES database is an R2 sample without that scale.
_SCALES_REQUIRING_EXPLICIT_YEARS = {
    ('MAT', 4, 'MRPS4'),
    ('RED', 12, 'RRPS4'),
}


def _get_session() -> requests.Session:
    """Returns a thread-local requests.Session with keep-alive pooling."""
    session = getattr(_THREAD_LOCAL, 'session', None)
    if session is None:
        session = requests.Session()
        adapter = adapters.HTTPAdapter(pool_connections=16, pool_maxsize=16)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        session.headers.update({
            'Accept': 'application/json',
            'Connection': 'keep-alive',
        })
        _THREAD_LOCAL.session = session
    return session


def _filter_r3_rows(raw_rows: List[Dict]) -> List[Dict]:
    """Filters NAEP API rows to standard R3 sample rows with numeric values."""
    rows = []
    for r in raw_rows:
        if r.get('sample') != 'R3' or r.get('yearSampleLabel') == 'XXXX':
            continue
        if 'value' in r and r['value'] is not None:
            try:
                r['value'] = float(r['value'])
            except (TypeError, ValueError):
                logging.debug('Skipping NAEP row with non-numeric value: %s', r)
                continue
        rows.append(r)
    return rows


def _query_naep_once(
    params: Dict[str, str],
    read_timeout: int,
    max_attempts: int = 3,
) -> Tuple[List[Dict], str]:
    """Executes one NAEP API query with fast-fail on 4xx and retry on 5xx/timeout.

    Returns:
        Tuple of (filtered_rows, status_tag) where status_tag is one of:
        'ok', 'client_error', 'dependent_info_error', or 'transient_error'.
    """
    session = _get_session()
    for attempt in range(max_attempts):
        try:
            resp = session.get(
                NAEP_API_URL,
                params=params,
                timeout=(_CONNECT_TIMEOUT_SECS, read_timeout),
            )
            if resp.status_code == 200:
                payload = resp.json()
                if isinstance(payload, dict):
                    api_status = payload.get('status')
                    if api_status == 200:
                        return _filter_r3_rows(payload.get('result', [])), 'ok'
                    if api_status in (400, 404):
                        if 'GetDependentInfo' in resp.text:
                            return [], 'dependent_info_error'
                        logging.debug(
                            'NAEP API returned non-retriable status %s for %s',
                            api_status, params)
                        return [], 'client_error'
                logging.warning(
                    'Unexpected NAEP JSON payload (attempt %d/%d) for %s: %s',
                    attempt + 1, max_attempts, params,
                    str(payload)[:200])
            elif resp.status_code in (400, 404):
                if 'GetDependentInfo' in resp.text:
                    return [], 'dependent_info_error'
                # Unsupported assessment/variable/scale combination; do not retry.
                logging.debug('NAEP API HTTP %d (non-retriable) for %s',
                              resp.status_code, params)
                return [], 'client_error'
            else:
                logging.warning('NAEP API HTTP %d (attempt %d/%d) for %s',
                                resp.status_code, attempt + 1, max_attempts,
                                params)
        except requests.RequestException as e:
            logging.warning('NAEP API request error (attempt %d/%d) for %s: %s',
                            attempt + 1, max_attempts, params, e)
        except ValueError as e:
            logging.warning(
                'Invalid JSON from NAEP API (attempt %d/%d) for %s: %s',
                attempt + 1, max_attempts, params, e)

        if attempt + 1 < max_attempts:
            time.sleep(2 * (attempt + 1) + random.uniform(0.5, 2.5))

    return [], 'transient_error'


def _get_scale_lock(scale_key: ScaleKey) -> threading.Lock:
    """Returns a per-scale Lock to serialize explicit-Year subscale queries."""
    with _YEAR_CACHE_LOCK:
        lock = _EXPLICIT_YEAR_SCALE_LOCKS.get(scale_key)
        if lock is None:
            lock = threading.Lock()
            _EXPLICIT_YEAR_SCALE_LOCKS[scale_key] = lock
        return lock


def _get_descending_years(subject: str, grade: int, jurisdiction: str,
                          read_timeout: int, max_attempts: int) -> str:
    """Discovers and caches all valid descending R3 years per scope."""
    is_national = jurisdiction == NATIONAL_JURISDICTION
    scope_key = NATIONAL_JURISDICTION if is_national else 'STATE'
    cache_key = (subject, grade, scope_key)
    with _YEAR_CACHE_LOCK:
        cached = _DESCENDING_YEARS_CACHE.get(cache_key)
    if cached:
        return cached

    primary_scale = _PRIMARY_SCALE_BY_SUBJECT.get(subject)
    if not primary_scale:
        return ''

    probe_jurisdiction = (NATIONAL_JURISDICTION
                          if is_national else ALL_STATE_JURISDICTIONS)
    probe_params = {
        'type': 'data',
        'subject': subject,
        'grade': str(grade),
        'subscale': primary_scale,
        'variable': 'TOTAL',
        'jurisdiction': probe_jurisdiction,
        'stattype': 'MN:MN',
    }
    rows, status = _query_naep_once(probe_params,
                                    read_timeout=read_timeout,
                                    max_attempts=max_attempts)
    if (status == 'client_error' and not is_national and subject == 'RED' and
            grade == 12):
        pilot_probe = dict(probe_params, jurisdiction=RED_G12_PILOT_STATES)
        rows, status = _query_naep_once(pilot_probe,
                                        read_timeout=read_timeout,
                                        max_attempts=max_attempts)

    if status == 'transient_error':
        raise RuntimeError(
            f'Transient failure discovering assessment years for {subject} '
            f'grade {grade}: {probe_params}')
    if status != 'ok' or not rows:
        logging.error(
            'Failed to discover valid assessment years for %s grade %d '
            '(status=%s): %s', subject, grade, status, probe_params)
        return ''

    sorted_years = sorted({int(r['year']) for r in rows if 'year' in r},
                          reverse=True)
    years_desc = ','.join(str(y) for y in sorted_years)
    with _YEAR_CACHE_LOCK:
        _DESCENDING_YEARS_CACHE[cache_key] = years_desc
    logging.info('Discovered descending R3 years for %s grade %d (%s): %s',
                 subject, grade, scope_key, years_desc)
    return years_desc


def _fetch_state_batches_fallback(params: Dict[str, str], read_timeout: int,
                                  max_attempts: int) -> List[Dict]:
    """Splits a failed 55-state query concurrently across 7 state batches."""
    logging.info(
        'Falling back to 7 state batches after multi-state failure for %s',
        params)

    def _run_batch(batch: str) -> List[Dict]:
        batch_params = dict(params, jurisdiction=batch)
        batch_rows, batch_status = _query_naep_once(batch_params,
                                                    read_timeout=read_timeout,
                                                    max_attempts=max_attempts)
        if batch_status == 'transient_error':
            raise RuntimeError(
                f'Failed fallback batch after {max_attempts} attempts for '
                f'NAEP query: {batch_params}')
        return batch_rows

    combined_rows: List[Dict] = []
    with futures.ThreadPoolExecutor(max_workers=_FALLBACK_WORKERS) as pool:
        for batch_rows in pool.map(_run_batch, STATE_JURISDICTION_BATCHES):
            combined_rows.extend(batch_rows)
    return combined_rows


def _query_explicit_years(
    scale_key: ScaleKey,
    params: Dict[str, str],
    years_desc: str,
    read_timeout: int,
    max_attempts: int,
) -> Tuple[List[Dict], str]:
    """Queries explicit years serialized per scale to prevent SQL stampedes."""
    year_params = dict(params, Year=years_desc)
    with _get_scale_lock(scale_key):
        return _query_naep_once(year_params,
                                read_timeout=read_timeout,
                                max_attempts=max_attempts)


# pylint: disable=too-many-arguments,too-many-positional-arguments
def fetch_naep_rows(subject: str,
                    grade: int,
                    scale: str,
                    variable: str,
                    jurisdiction: str,
                    stattype: str,
                    max_attempts: int = 3,
                    read_timeout: Optional[int] = None) -> List[Dict]:
    """Queries the NAEP API for all years with smart multi-state fallbacks."""
    timeout_secs = read_timeout if read_timeout is not None else (
        FLAGS.read_timeout if FLAGS.is_parsed() else 120)
    params = {
        'type': 'data',
        'subject': subject,
        'grade': str(grade),
        'subscale': scale,
        'variable': variable,
        'jurisdiction': jurisdiction,
        'stattype': stattype,
    }
    scale_key = (subject, grade, scale)
    with _YEAR_CACHE_LOCK:
        needs_explicit_years = scale_key in _SCALES_REQUIRING_EXPLICIT_YEARS
    if needs_explicit_years and jurisdiction == NATIONAL_JURISDICTION:
        years_desc = _get_descending_years(subject, grade, jurisdiction,
                                           timeout_secs, max_attempts)
        if years_desc:
            rows, status = _query_explicit_years(scale_key, params, years_desc,
                                                 timeout_secs, max_attempts)
            if status == 'transient_error':
                raise RuntimeError(
                    f'Failed to fetch NAEP data after {max_attempts} attempts: '
                    f'{dict(params, Year=years_desc)}')
            return rows

    # Probe 55-state queries at most once (capped at 60s) before splitting into
    # the 7 smaller state batches so slow multi-state scans never burn 3x120s.
    is_all_states = jurisdiction == ALL_STATE_JURISDICTIONS
    initial_timeout = (min(timeout_secs, _ALL_STATES_PROBE_TIMEOUT_SECS)
                       if is_all_states else timeout_secs)
    initial_attempts = 1 if is_all_states else max_attempts

    rows, status = _query_naep_once(params,
                                    read_timeout=initial_timeout,
                                    max_attempts=initial_attempts)
    if status == 'ok':
        return rows

    # If omitting 'Year' triggered NCES's GetDependentInfo() HTTP 400 bug on a
    # legacy R2 cycle, retry with all discovered descending R3 years.
    if status == 'dependent_info_error' and 'Year' not in params:
        if jurisdiction == NATIONAL_JURISDICTION:
            with _YEAR_CACHE_LOCK:
                _SCALES_REQUIRING_EXPLICIT_YEARS.add(scale_key)
        years_desc = _get_descending_years(subject, grade, jurisdiction,
                                           timeout_secs, max_attempts)
        if years_desc:
            rows, status = _query_explicit_years(scale_key, params, years_desc,
                                                 timeout_secs, max_attempts)
            if status == 'ok':
                return rows

    # If a 55-state Grade 12 Reading query returned HTTP 400 due to non-pilot
    # states, retry with the Grade 12 Reading pilot states before batch split.
    if (status == 'client_error' and is_all_states and subject == 'RED' and
            grade == 12):
        pilot_params = dict(params, jurisdiction=RED_G12_PILOT_STATES)
        pilot_rows, pilot_status = _query_naep_once(pilot_params,
                                                    read_timeout=timeout_secs,
                                                    max_attempts=max_attempts)
        if pilot_status == 'ok':
            return pilot_rows
        if pilot_status == 'transient_error':
            raise RuntimeError(
                f'Failed to fetch NAEP pilot data after {max_attempts} '
                f'attempts: {pilot_params}')

    # If a full 55-state query timed out, hit 5xx, or hit HTTP 400 due to an
    # unsupported jurisdiction in the 55-state list, split across 7 batches.
    if status in ('transient_error', 'client_error') and is_all_states:
        return _fetch_state_batches_fallback(params, timeout_secs, max_attempts)

    if status == 'transient_error':
        raise RuntimeError(
            f'Failed to fetch NAEP data after {max_attempts} attempts: {params}'
        )
    return []


# pylint: enable=too-many-arguments,too-many-positional-arguments


def _expand_spec_tasks(spec: Dict) -> List[QueryTask]:
    """Expands one file spec dict into ordered API query tuples."""
    subject = spec['subject']
    variables = spec.get('variables', ALL_VARIABLES)
    grade_scale_pairs = (spec['grades_and_scales'] if 'grades_and_scales'
                         in spec else [(spec['grade'], spec['scales'])])
    default_juris_batches = spec['jurisdiction_batches']
    subscale_juris_batches = spec.get('subscale_jurisdiction_batches',
                                      default_juris_batches)
    spec_tasks: List[QueryTask] = []
    for grade, scales in grade_scale_pairs:
        for scale in scales:
            is_composite = scale in COMPOSITE_SCALES
            stattypes = (STATTYPE_BATCHES_COMPOSITE
                         if is_composite else STATTYPE_BATCHES_SUBSCALE)
            juris_batches = (default_juris_batches
                             if is_composite else subscale_juris_batches)
            for variable in variables:
                for stattype in stattypes:
                    for juris_batch in juris_batches:
                        spec_tasks.append((subject, grade, scale, variable,
                                           juris_batch, stattype))
    return spec_tasks


def build_query_tasks(spec_list: List[Dict]) -> List[QueryTask]:
    """Builds ordered API query task tuples from file specifications."""
    tasks: List[QueryTask] = []
    for spec in spec_list:
        tasks.extend(_expand_spec_tasks(spec))
    return tasks


def _partition_warm_gated_tasks(
    tasks: List[QueryTask],
) -> Tuple[
        List[Tuple[int, QueryTask]],
        Dict[int, WarmKey],
        Dict[WarmKey, List[Tuple[int, QueryTask]]],
]:
    """Splits tasks into initial (warmers + fast scales) and deferred tasks.

    For each content subscale (not in FAST_SCALES), only its first task per
    (subject, grade, scale, stattype) is submitted initially to warm NCES's
    backend SQL cache for both MN/RP and SD/PC tables; remaining tasks for
    that key are held until the warmer finishes so worker threads never
    stampede an uncached subscale/stattype table simultaneously.
    """
    warmer_tasks: List[Tuple[int, QueryTask]] = []
    fast_tasks: List[Tuple[int, QueryTask]] = []
    warmer_idx_to_key: Dict[int, WarmKey] = {}
    deferred_by_key: Dict[WarmKey, List[Tuple[int, QueryTask]]] = {}

    for idx, task in enumerate(tasks):
        subject, grade, scale, _, _, stattype = task
        if scale in FAST_SCALES:
            fast_tasks.append((idx, task))
            continue
        warm_key = (subject, grade, scale, stattype)
        if warm_key not in deferred_by_key:
            warmer_tasks.append((idx, task))
            warmer_idx_to_key[idx] = warm_key
            deferred_by_key[warm_key] = []
        else:
            deferred_by_key[warm_key].append((idx, task))

    return warmer_tasks + fast_tasks, warmer_idx_to_key, deferred_by_key


def _flush_ready_rows(writer: csv.DictWriter, pending: Dict[int, List[Dict]],
                      next_idx: int) -> Tuple[int, int]:
    """Writes contiguous completed task buffers starting at next_idx."""
    written_rows = 0
    while next_idx in pending:
        rows = pending.pop(next_idx)
        writer.writerows(rows)
        written_rows += len(rows)
        next_idx += 1
    return next_idx, written_rows


# pylint: disable=too-many-locals
def _write_ordered_results(filename: str, writer: csv.DictWriter,
                           tasks: List[QueryTask], workers: int,
                           timeout_secs: int) -> int:
    """Executes warm-gated tasks concurrently in deterministic CSV order."""
    start_time = time.monotonic()
    total_tasks = len(tasks)
    if total_tasks == 0:
        return 0

    # Pre-warm explicit-Year cache before launching worker threads so warmers
    # for MRPS4 / RRPS4 start immediately alongside other scales.
    for subject, grade, scale, _, jurisdiction, _ in tasks:
        if ((subject, grade, scale) in _SCALES_REQUIRING_EXPLICIT_YEARS and
                jurisdiction == NATIONAL_JURISDICTION):
            _get_descending_years(subject,
                                  grade,
                                  jurisdiction,
                                  timeout_secs,
                                  max_attempts=3)

    initial_tasks, warmer_idx_to_key, deferred_by_key = (
        _partition_warm_gated_tasks(tasks))
    total_rows = 0
    completed = 0
    next_idx = 0
    pending: Dict[int, List[Dict]] = {}

    with futures.ThreadPoolExecutor(max_workers=workers) as executor:
        in_flight: Dict[futures.Future, int] = {
            executor.submit(fetch_naep_rows, *task, read_timeout=timeout_secs):
                idx for idx, task in initial_tasks
        }
        while in_flight:
            done, _ = futures.wait(in_flight.keys(),
                                   return_when=futures.FIRST_COMPLETED)
            for future in done:
                idx = in_flight.pop(future)
                pending[idx] = future.result()
                completed += 1

                warm_key = warmer_idx_to_key.pop(idx, None)
                if warm_key is not None:
                    for def_idx, def_task in deferred_by_key.pop(warm_key, ()):
                        fut = executor.submit(fetch_naep_rows,
                                              *def_task,
                                              read_timeout=timeout_secs)
                        in_flight[fut] = def_idx

                next_idx, flushed = _flush_ready_rows(writer, pending, next_idx)
                total_rows += flushed

                if completed % 25 == 0 or completed == total_tasks:
                    logging.info(
                        'Progress %s: %d/%d queries completed '
                        '(%.1fs elapsed, %d rows written)', filename, completed,
                        total_tasks,
                        time.monotonic() - start_time, total_rows)
    return total_rows


# pylint: enable=too-many-locals


def download_file(filename: str,
                  spec_list: List[Dict],
                  output_dir: str,
                  max_workers: Optional[int] = None,
                  read_timeout: Optional[int] = None) -> int:
    """Downloads a single NAEP CSV file concurrently and returns row count."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    tasks = build_query_tasks(spec_list)
    workers = max(
        1, max_workers if max_workers is not None else
        (FLAGS.max_workers if FLAGS.is_parsed() else 8))
    timeout_secs = read_timeout if read_timeout is not None else (
        FLAGS.read_timeout if FLAGS.is_parsed() else 120)

    start_time = time.monotonic()
    logging.info(
        'Starting download for %s -> %s (%d API queries, max_workers=%d)',
        filename, output_path, len(tasks), workers)

    fd, tmp_path = tempfile.mkstemp(prefix=f'.{filename}.',
                                    suffix='.tmp',
                                    dir=output_dir)
    fd_owned_by_file = False
    try:
        csv_file = os.fdopen(fd, 'w', newline='', encoding='utf-8')
        fd_owned_by_file = True
        with csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=CSV_COLUMNS,
                                    extrasaction='ignore',
                                    lineterminator='\n')
            writer.writeheader()
            total_rows = _write_ordered_results(filename, writer, tasks,
                                                workers, timeout_secs)
        os.replace(tmp_path, output_path)
    except Exception:
        if not fd_owned_by_file:
            try:
                os.close(fd)
            except OSError:
                pass
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    logging.info('Finished %s in %.1fs: wrote %d data rows.', filename,
                 time.monotonic() - start_time, total_rows)
    return total_rows


def main(_):
    """CLI entry point to download configured NAEP input CSV files."""
    target_files = FLAGS.files if FLAGS.files else list(FILE_SPECS.keys())
    unknown_files = [f for f in target_files if f not in FILE_SPECS]
    if unknown_files:
        raise ValueError(
            f'Unknown target file(s): {unknown_files}. Valid files: '
            f'{list(FILE_SPECS.keys())}')

    overall_start = time.monotonic()
    for filename in target_files:
        download_file(filename,
                      FILE_SPECS[filename],
                      FLAGS.output_dir,
                      max_workers=FLAGS.max_workers,
                      read_timeout=FLAGS.read_timeout)

    logging.info('All downloads completed in %.1fs.',
                 time.monotonic() - overall_start)


if __name__ == '__main__':
    app.run(main)
