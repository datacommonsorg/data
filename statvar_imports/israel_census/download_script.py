# Copyright 2026 Google LLC
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
"""Downloads raw Israel CBS datasets from apis.cbs.gov.il and boardsgenerator.cbs.gov.il into input_files/."""

import argparse
from concurrent import futures
import csv
import io
import json
import math
import os
import re
import tempfile
import threading
import time
from typing import Any

from absl import logging
import requests
from requests import adapters

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CBS_SERIES_API_URL = 'https://apis.cbs.gov.il/series/data/path'

# Official CBS Time-Series DataBank paths on apis.cbs.gov.il:
# - 2,1,1,1: Population -> Population, by Population Group -> Population De Jure -> At End of Period
# - 2,3,1:   Population -> Live-Births and Deaths -> By Population Group
# - 4,2,1:   Health -> Mortality rates, by causes of death -> Data by select causes
CBS_SERIES_POPULATION_PATH_ID = '2,1,1,1'
CBS_SERIES_VITAL_STATS_PATH_ID = '2,3,1'
CBS_SERIES_CAUSE_OF_DEATH_PATH_ID = '4,2,1'

CBS_RAW_SERIES_FILES = {
    CBS_SERIES_POPULATION_PATH_ID: 'cbs_series_2_1_1_1.csv',
    CBS_SERIES_VITAL_STATS_PATH_ID: 'cbs_series_2_3_1.csv',
    CBS_SERIES_CAUSE_OF_DEATH_PATH_ID: 'cbs_series_4_2_1.csv',
}

CBS_SERIES_MIN_ANNUAL_ROWS: dict[str, dict[str, int]] = {
    CBS_SERIES_POPULATION_PATH_ID: {
        '3700': 75,
        '3701': 75,
        '3702': 40,
        '3703': 29,
        '3704': 29,
    },
    CBS_SERIES_VITAL_STATS_PATH_ID: {
        '3729': 28,
        '3747': 28,
        '3751': 28,
        '3752': 28,
        '3755': 15,
        '3759': 28,
        '3762': 28,
    },
    CBS_SERIES_CAUSE_OF_DEATH_PATH_ID: {
        **{
            str(sid): 70 for sid in (*range(70001, 70007), *range(70008, 70014))
        },
        **{
            str(sid): 50 for sid in (*range(70015, 70021), *range(70022, 70028))
        },
        # 24 is the exact historical floor (1998-2022 excluding empty 2019)
        # for the 12 Arab cause-of-death series.
        **{
            str(sid): 24 for sid in (*range(70136, 70142), *range(70143, 70149))
        },
    },
}

_CBS_SERIES_MIN_UNIQUE_IDS = {
    CBS_SERIES_POPULATION_PATH_ID: 5,
    CBS_SERIES_VITAL_STATS_PATH_ID: 7,
    CBS_SERIES_CAUSE_OF_DEATH_PATH_ID: 36,
}

# Official CBS BoardsGenerator 2008 Census endpoint (boardsgenerator.cbs.gov.il)
CBS_BOARDSGENERATOR_CENSUS_URL = (
    'https://boardsgenerator.cbs.gov.il/Handlers/WebParts/YishuvHandler.ashx')
CBS_RAW_YISHUV_CENSUS_JSON = 'cbs_yishuv_census_2008.json'

CBS_CENSUS_2008_REGIONS = (
    ('999', 'Machoz'),
    ('1', 'Machoz'),
    ('2', 'Machoz'),
    ('3', 'Machoz'),
    ('4', 'Machoz'),
    ('5', 'Machoz'),
    ('6', 'Machoz'),
    ('7', 'Machoz'),
    ('21', 'Nafa'),
    ('24', 'Nafa'),
    ('29', 'Nafa'),
    ('31', 'Nafa'),
    ('32', 'Nafa'),
    ('41', 'Nafa'),
    ('42', 'Nafa'),
    ('43', 'Nafa'),
    ('44', 'Nafa'),
    ('61', 'Nafa'),
    ('62', 'Nafa'),
)

# Official CBS 2008 Census Table Generator (Mifkad) tables on boardsgenerator.cbs.gov.il
CBS_MIFKAD_BASE_URL = (
    'https://boardsgenerator.cbs.gov.il/Resources/Mifkad/tables')
CBS_MIFKAD_2008_TABLES = (
    'dem1_2.xls',
    'dem1_14.xls',
    'lab4_14.xls',
    'lab4_14_1.xls',
    'lab4_14_2.xls',
)
CBS_MIFKAD_2008_REMOTE_NAMES = {
    'lab4_14_1.xls': 'lab4_14a.xls',
    'lab4_14_2.xls': 'lab4_14b.xls',
}

_THREAD_LOCAL = threading.local()
_SESSIONS_LOCK = threading.Lock()
_CREATED_SESSIONS: list[requests.Session] = []
_SESSION_GENERATION = 0


def _get_session() -> requests.Session:
    """Returns a thread-local HTTP session with inner retries disabled so outer retry loops control backoff and cookie clearing."""
    gen = getattr(_THREAD_LOCAL, 'generation', None)
    session = getattr(_THREAD_LOCAL, 'session', None)
    if session is None or gen != _SESSION_GENERATION:
        session = requests.Session()
        session.headers.update({
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/131.0.0.0 Safari/537.36'),
            'Accept': (
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            ),
            'Accept-Language': 'en-US,en;q=0.5',
        })
        adapter = adapters.HTTPAdapter(max_retries=0)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        with _SESSIONS_LOCK:
            _CREATED_SESSIONS.append(session)
            current_gen = _SESSION_GENERATION
        _THREAD_LOCAL.session = session
        _THREAD_LOCAL.generation = current_gen
    return session


def _close_sessions() -> None:
    """Closes all thread-local requests.Session instances created by _get_session()."""
    global _SESSION_GENERATION  # pylint: disable=global-statement
    with _SESSIONS_LOCK:
        sessions = list(_CREATED_SESSIONS)
        _CREATED_SESSIONS.clear()
        _SESSION_GENERATION += 1
    for sess in sessions:
        try:
            sess.close()
        except Exception as err:  # pylint: disable=broad-exception-caught
            logging.warning('Failed to close HTTP session: %s', err)
    if hasattr(_THREAD_LOCAL, 'session'):
        delattr(_THREAD_LOCAL, 'session')


def _write_bytes_atomically(dest_path: str, content: bytes) -> None:
    """Atomically writes raw bytes to dest_path."""
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=os.path.dirname(os.path.abspath(dest_path)),
        prefix='.tmp_cbs_',
    )
    try:
        with os.fdopen(fd, 'wb') as fp:
            fp.write(content)
        os.replace(tmp_path, dest_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _strip_trailing_blank_lines(chunk: bytes) -> bytes:
    """Removes trailing blank lines while ensuring a single trailing newline."""
    lines = chunk.splitlines(keepends=True)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return b''
    out = b''.join(lines)
    if not out.endswith(b'\n'):
        out += b'\n'
    return out


_EXCEL_MAGIC_PREFIXES = (b'\xd0\xcf\x11\xe0', b'PK\x03\x04')


def _is_non_retryable_http_error(err: requests.HTTPError) -> bool:
    """Returns True for permanent 4xx client errors that should fail fast."""
    response = err.response
    if response is None:
        return False
    status_code = response.status_code
    return 400 <= status_code < 500 and status_code not in (403, 408, 429)


_CBS_MISSING_TOKENS = frozenset({'-', '..', '...', '*'})
_ANNUAL_TIME_PERIOD_RE = re.compile(r'^[0-9]{4}(?:-01)?$')
_CENSUS_EXPECTED_SUBJECT_IDS: dict[str, frozenset[str]] = {
    'Machoz':
        frozenset({'218', '219', '220', '221', '222', '223', '224'}),
    'Nafa':
        frozenset(
            {'18', '19', '20', '218', '219', '220', '221', '222', '223',
             '224'}),
}
_ALL_CENSUS_EXPECTED_SUBJECT_IDS = frozenset().union(
    *_CENSUS_EXPECTED_SUBJECT_IDS.values())


def _is_ascii_digits(value: str) -> bool:
    """Returns True if value consists solely of ASCII decimal digits."""
    return bool(value) and value.isascii() and value.isdigit()


def _parse_annual_year(time_period: str) -> str | None:
    """Returns 4-digit ASCII year if time_period matches YYYY or YYYY-01, else None."""
    if _ANNUAL_TIME_PERIOD_RE.fullmatch(time_period):
        return time_period[:4]
    return None


def _is_subannual_period(time_period: str) -> bool:
    """Returns True if time_period is YYYY-<suffix> with suffix != '01' (e.g., 2024-02, 2024-Q2)."""
    return (len(time_period) >= 6 and _is_ascii_digits(time_period[:4]) and
            time_period[4] == '-' and time_period[5:] != '01')


def _effective_annual_count(
    sid: str,
    explicit_by_sid: dict[str, set[str]],
    blank_by_sid: dict[str, set[str]],
    subannual_blank_sids: set[str],
) -> int:
    """Counts distinct annual years for sid, excluding blank-unit rows if sid has sub-annual periods."""
    years = set(explicit_by_sid.get(sid, ()))
    if sid not in subannual_blank_sids:
        years |= blank_by_sid.get(sid, set())
    return len(years)


def _is_valid_numeric_obs(val: str) -> bool:
    """Returns True if val parses as a finite non-negative numeric observation."""
    cleaned = val.replace(',', '').strip()
    if not cleaned or cleaned in _CBS_MISSING_TOKENS:
        return False
    try:
        parsed = float(cleaned)
    except ValueError:
        return False
    return math.isfinite(parsed) and parsed >= 0


def _is_valid_census_groups_payload(
    candidate: Any,
    data_mode: str | None = None,
) -> bool:
    """Returns True if payload has a non-empty list of dict Groups containing all expected census subject IDs with finite non-negative numeric Values."""
    if not isinstance(candidate, dict):
        return False
    groups = candidate.get('Groups')
    if not isinstance(groups, list) or not groups:
        return False
    required_ids = _CENSUS_EXPECTED_SUBJECT_IDS.get(
        data_mode or '', _CENSUS_EXPECTED_SUBJECT_IDS['Machoz'])
    valid_ids: set[str] = set()
    for group in groups:
        if not isinstance(group, dict):
            return False
        subjects = group.get('Subjects')
        if subjects is None:
            continue
        if not isinstance(subjects, list) or not all(
                isinstance(s, dict) for s in subjects):
            return False
        for subj in subjects:
            raw_id = subj.get('Id')
            raw_val = subj.get('Value')
            if raw_id is None or raw_val is None:
                continue
            sid = str(raw_id).strip()
            if (sid in _ALL_CENSUS_EXPECTED_SUBJECT_IDS and
                    _is_valid_numeric_obs(str(raw_val))):
                valid_ids.add(sid)
    return valid_ids >= required_ids


def _extend_header_columns(
    target_header: list[str],
    target_names: list[str],
    incoming_header: list[str],
    incoming_names: list[str],
) -> int:
    """Appends any newly seen columns to target_header and returns count added."""
    existing = set(target_names)
    added = 0
    for raw_col, norm_col in zip(incoming_header, incoming_names, strict=True):
        if norm_col not in existing:
            target_header.append(raw_col)
            target_names.append(norm_col)
            existing.add(norm_col)
            added += 1
    return added


def _align_row_to_header(
    row: list[str],
    source_names: list[str],
    target_names: list[str],
) -> list[str]:
    """Aligns a parsed CSV row from source_names order into target_names order."""
    if source_names == target_names and len(row) == len(target_names):
        return list(row)
    col_map = {
        name: (row[i] if i < len(row) else '')
        for i, name in enumerate(source_names)
    }
    return [col_map.get(name, '') for name in target_names]


def _serialize_csv_rows(header_row: list[str], rows: list[list[str]]) -> bytes:
    """Serializes parsed CSV header and rows using csv.writer."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator='\n')
    writer.writerow(header_row)
    writer.writerows(rows)
    return buf.getvalue().encode('utf-8')


def fetch_cbs_series_raw_csv(
    path_id: str,
    dest_path: str,
    session: requests.Session | None = None,
    page_size: int = 100,
    min_unique_series: int | None = None,
    min_annual_rows: dict[str, int] | None = None,
    max_pages: int = 50,
    retry_delay: float | None = None,
) -> int:
    """Downloads raw CSV data from apis.cbs.gov.il/series/data/path and writes it unmodified to dest_path."""
    sess = session or _get_session()
    expected_min = (min_unique_series if min_unique_series is not None else
                    _CBS_SERIES_MIN_UNIQUE_IDS.get(path_id, 1))
    req_annual_rows = (min_annual_rows if min_annual_rows is not None else
                       CBS_SERIES_MIN_ANNUAL_ROWS.get(path_id, {}))
    delay = (retry_delay if retry_delay is not None else
             (2.0 if session is None else 0.0))

    unique_sids: set[str] = set()
    explicit_annual_by_sid: dict[str, set[str]] = {}
    blank_annual_by_sid: dict[str, set[str]] = {}
    subannual_blank_sids: set[str] = set()
    merged_header: list[str] = []
    merged_header_names: list[str] = []
    merged_rows_by_key: dict[tuple[str, str, str], tuple[list[str], bool]] = {}
    incomplete_merged: dict[str, tuple[int, int]] = {}
    completed_pages: set[int] = set()
    known_last_page: int | None = None
    min_required_pages = 1
    saw_unbounded_end = False
    has_unclosed_unbounded_attempt = False
    effective_page_target: int | None = None
    last_err: Exception | None = None
    max_attempts = 6 if session is None else 3
    for attempt in range(1, max_attempts + 1):
        if hasattr(sess, 'cookies') and hasattr(sess.cookies, 'clear'):
            sess.cookies.clear()
        page_contents: list[bytes] = []
        attempt_header: list[str] = []
        attempt_header_names: list[str] = []
        attempt_headers_match = True
        attempt_had_key_upgrade = False
        attempt_rows: list[list[str]] = []
        attempt_row_index_by_key: dict[tuple[str, str, str], int] = {}
        attempt_sids: set[str] = set()
        attempt_explicit_annual: dict[str, set[str]] = {}
        attempt_blank_annual: dict[str, set[str]] = {}
        attempt_subannual_blank_sids: set[str] = set()
        attempt_key_has_val: dict[tuple[str, str, str], bool] = {}
        attempt_last_page: int | None = None
        attempt_committed_unbounded = False
        attempt_complete = False
        page = 1
        while page <= max_pages:
            params = {
                'id': path_id,
                'Page': page,
                'PageSize': page_size,
                'format': 'csv',
                'download': 'true',
                'lang': 'en',
            }
            logging.info(
                'HTTP GET %s params=%s (attempt %d)',
                CBS_SERIES_API_URL,
                params,
                attempt,
            )
            try:
                response = sess.get(
                    CBS_SERIES_API_URL,
                    params=params,
                    timeout=(5, 30),
                )
                response.raise_for_status()
            except requests.HTTPError as err:
                if _is_non_retryable_http_error(err):
                    logging.error(
                        'Permanent HTTP error for id=%s page=%d: %s',
                        path_id,
                        page,
                        err,
                    )
                    raise
                last_err = err
                logging.warning(
                    'CBS Series CSV request failed for id=%s page=%d on attempt %d: %s',
                    path_id,
                    page,
                    attempt,
                    err,
                )
                break
            except requests.RequestException as err:
                last_err = err
                logging.warning(
                    'CBS Series CSV request failed for id=%s page=%d on attempt %d: %s',
                    path_id,
                    page,
                    attempt,
                    err,
                )
                break
            content = response.content
            prefix = content.lstrip()[:16].lower()
            if (not content or prefix.startswith((b'<!doctype', b'<html')) or
                    b'obs_time_period' not in content.splitlines()[0]):
                logging.warning(
                    'Invalid or empty CSV returned from %s for id=%s page=%d on attempt %d',
                    CBS_SERIES_API_URL,
                    path_id,
                    page,
                    attempt,
                )
                break
            text = content.decode('utf-8-sig', errors='replace')
            reader = csv.reader(io.StringIO(text))
            header_row = next(reader, None)
            if not header_row:
                logging.warning(
                    'Empty CSV header from %s for id=%s page=%d on attempt %d',
                    CBS_SERIES_API_URL,
                    path_id,
                    page,
                    attempt,
                )
                break
            header_names = [name.strip() for name in header_row]
            col_index = {name: i for i, name in enumerate(header_names)}
            sid_idx = col_index.get('id', col_index.get('series_id'))
            tname_idx = col_index.get('time_name')
            tunit_idx = col_index.get('time_unit')
            tperiod_idx = col_index.get('obs_time_period')
            obs_val_idx = col_index.get('obs_value')
            cur_idx = col_index.get('page_current_page')
            last_idx = col_index.get('page_last_page')

            def _cell(r: list[str], idx: int | None) -> str:
                if idx is None or idx >= len(r):
                    return ''
                return r[idx].strip()

            # Buffer parsed page data locally so rejected pages cannot pollute
            # attempt-level or cross-attempt state.
            page_sids: set[str] = set()
            page_explicit_annual: dict[str, set[str]] = {}
            page_blank_annual: dict[str, set[str]] = {}
            page_subannual_blank_sids: set[str] = set()
            page_rows_by_key: dict[tuple[str, str, str], tuple[list[str],
                                                               bool]] = {}
            page_unkeyed_rows: list[list[str]] = []
            page_currents: set[int] = set()
            page_last_values: set[int] = set()
            saw_nonempty_cur = False
            saw_blank_cur = False
            saw_nonempty_last = False
            saw_blank_last = False
            invalid_page_current = False
            invalid_page_last = False
            for row in reader:
                if not row or not any(cell.strip() for cell in row):
                    continue
                sid = _cell(row, sid_idx)
                t_name = _cell(row, tname_idx) or _cell(row, tunit_idx)
                t_period = _cell(row, tperiod_idx)
                obs_val = _cell(row, obs_val_idx)
                cur_str = _cell(row, cur_idx)
                last_str = _cell(row, last_idx)
                if cur_idx is not None:
                    if cur_str:
                        saw_nonempty_cur = True
                        if _is_ascii_digits(cur_str) and int(cur_str) >= 1:
                            page_currents.add(int(cur_str))
                        else:
                            invalid_page_current = True
                    else:
                        saw_blank_cur = True
                if last_idx is not None:
                    if last_str:
                        saw_nonempty_last = True
                        if _is_ascii_digits(last_str) and int(last_str) >= 1:
                            page_last_values.add(int(last_str))
                        else:
                            invalid_page_last = True
                    else:
                        saw_blank_last = True
                if sid:
                    page_sids.add(sid)
                    row_key = (sid, t_name, t_period)
                    has_val = _is_valid_numeric_obs(obs_val)
                    if t_name == '' and _is_subannual_period(t_period):
                        page_subannual_blank_sids.add(sid)
                    year = _parse_annual_year(t_period)
                    if year is not None and has_val:
                        if t_name == 'Year':
                            page_explicit_annual.setdefault(sid,
                                                            set()).add(year)
                        elif t_name == '':
                            page_blank_annual.setdefault(sid, set()).add(year)
                    existing_page = page_rows_by_key.get(row_key)
                    if existing_page is None or has_val:
                        page_rows_by_key[row_key] = (list(row), has_val)
                else:
                    page_unkeyed_rows.append(list(row))

            if len(page_last_values) > 1 or (saw_nonempty_last and
                                             saw_blank_last):
                invalid_page_last = True
            if len(page_currents) > 1 or (saw_nonempty_cur and saw_blank_cur):
                invalid_page_current = True

            if invalid_page_last:
                logging.warning(
                    'Invalid or conflicting page_last_page for id=%s page=%d on attempt %d',
                    path_id,
                    page,
                    attempt,
                )
                break
            if invalid_page_current:
                logging.warning(
                    'Invalid or conflicting page_current_page for id=%s page=%d on attempt %d',
                    path_id,
                    page,
                    attempt,
                )
                break
            if not page_sids:
                logging.warning(
                    'No series rows returned from %s for id=%s page=%d on attempt %d',
                    CBS_SERIES_API_URL,
                    path_id,
                    page,
                    attempt,
                )
                break
            has_page_current = bool(page_currents)
            page_current = next(
                iter(page_currents)) if has_page_current else page
            page_last = (next(iter(page_last_values))
                         if page_last_values else None)
            if has_page_current and page_current != page:
                logging.warning(
                    'CBS Series CSV pagination mismatch for id=%s: requested page=%d got page_current_page=%d (attempt %d)',
                    path_id,
                    page,
                    page_current,
                    attempt,
                )
                break
            if page_last is not None and page_current > page_last:
                logging.warning(
                    'CBS Series CSV pagination invalid for id=%s: page_current_page=%d > page_last_page=%d (attempt %d)',
                    path_id,
                    page_current,
                    page_last,
                    attempt,
                )
                break
            if attempt_last_page is not None and page_last != attempt_last_page:
                logging.warning(
                    'CBS Series CSV page_last_page changed mid-attempt for id=%s: '
                    'expected %d got %s on page=%d (attempt %d)',
                    path_id,
                    attempt_last_page,
                    page_last,
                    page,
                    attempt,
                )
                break
            if (page_last is not None and known_last_page is not None and
                    page_last < known_last_page):
                logging.warning(
                    'CBS Series CSV page_last_page shrank below prior known_last_page '
                    'for id=%s: got %d < %d on page=%d (attempt %d)',
                    path_id,
                    page_last,
                    known_last_page,
                    page,
                    attempt,
                )
                break
            page_has_new_or_upgraded = any(
                rk not in attempt_key_has_val or
                (hv and not attempt_key_has_val[rk])
                for rk, (_, hv) in page_rows_by_key.items())
            if page > 1 and not page_has_new_or_upgraded:
                logging.warning(
                    'CBS Series CSV pagination returned 0 new rows for id=%s page=%d (attempt %d)',
                    path_id,
                    page,
                    attempt,
                )
                break
            expected_min_pages = max(known_last_page or 1, min_required_pages)
            if (page_last is None and len(page_sids) < page_size and
                    page < expected_min_pages):
                logging.warning(
                    'CBS Series CSV returned short page %d (< %d series) without '
                    'page_last_page while expecting at least %d pages for id=%s (attempt %d)',
                    page,
                    page_size,
                    expected_min_pages,
                    path_id,
                    attempt,
                )
                break

            # Page passed all validation guards; commit buffered data.
            if page_last is not None:
                if attempt_last_page is None:
                    attempt_last_page = page_last
                known_last_page = (max(known_last_page, page_last) if
                                   known_last_page is not None else page_last)
                min_required_pages = max(min_required_pages, known_last_page)
            else:
                attempt_committed_unbounded = True

            attempt_sids.update(page_sids)
            unique_sids.update(page_sids)
            attempt_subannual_blank_sids.update(page_subannual_blank_sids)
            subannual_blank_sids.update(page_subannual_blank_sids)
            for sid, periods in page_explicit_annual.items():
                attempt_explicit_annual.setdefault(sid, set()).update(periods)
                explicit_annual_by_sid.setdefault(sid, set()).update(periods)
            for sid, periods in page_blank_annual.items():
                attempt_blank_annual.setdefault(sid, set()).update(periods)
                blank_annual_by_sid.setdefault(sid, set()).update(periods)

            if not merged_header:
                merged_header = list(header_row)
                merged_header_names = list(header_names)
            elif header_names != merged_header_names:
                added = _extend_header_columns(
                    merged_header,
                    merged_header_names,
                    header_row,
                    header_names,
                )
                if added:
                    for existing_row, _ in merged_rows_by_key.values():
                        existing_row.extend([''] * added)
            merged_obs_idx = (merged_header_names.index('obs_value')
                              if 'obs_value' in merged_header_names else None)
            for row_key, (page_row, has_val) in page_rows_by_key.items():
                existing = merged_rows_by_key.get(row_key)
                aligned_row = _align_row_to_header(
                    page_row,
                    header_names,
                    merged_header_names,
                )
                if existing is None:
                    merged_rows_by_key[row_key] = (aligned_row, has_val)
                elif has_val:
                    prev_row, prev_has_val = existing
                    prev_obs = _cell(prev_row, merged_obs_idx)
                    new_obs = _cell(page_row, obs_val_idx)
                    if prev_has_val and prev_obs != new_obs:
                        logging.warning(
                            'Updating CBS Series row %s across retry attempts: %r -> %r',
                            row_key,
                            prev_obs,
                            new_obs,
                        )
                    merged_rows_by_key[row_key] = (aligned_row, True)

            if not attempt_header:
                attempt_header = list(header_row)
                attempt_header_names = list(header_names)
            elif header_names != attempt_header_names:
                attempt_headers_match = False
                added = _extend_header_columns(
                    attempt_header,
                    attempt_header_names,
                    header_row,
                    header_names,
                )
                if added:
                    for existing_row in attempt_rows:
                        existing_row.extend([''] * added)
            for row_key, (page_row, has_val) in page_rows_by_key.items():
                aligned_attempt_row = _align_row_to_header(
                    page_row, header_names, attempt_header_names)
                if row_key not in attempt_key_has_val:
                    attempt_key_has_val[row_key] = has_val
                    attempt_row_index_by_key[row_key] = len(attempt_rows)
                    attempt_rows.append(aligned_attempt_row)
                elif has_val:
                    attempt_had_key_upgrade = True
                    attempt_key_has_val[row_key] = True
                    attempt_rows[
                        attempt_row_index_by_key[row_key]] = aligned_attempt_row
            for unkeyed_row in page_unkeyed_rows:
                attempt_rows.append(
                    _align_row_to_header(unkeyed_row, header_names,
                                         attempt_header_names))

            completed_pages.add(page)
            if page == 1:
                page_contents.append(content)
            else:
                raw_lines = content.splitlines(keepends=True)
                if len(raw_lines) > 1:
                    page_contents.append(b''.join(raw_lines[1:]))
            if page_last is not None:
                effective_last = max(page_last, known_last_page or page_last,
                                     min_required_pages)
                if page >= effective_last:
                    attempt_complete = True
                    break
                saw_unbounded_end = False
            elif len(page_sids) < page_size:
                attempt_complete = True
                saw_unbounded_end = True
                break
            else:
                saw_unbounded_end = False
                min_required_pages = max(min_required_pages, page + 1)
            page += 1
        else:
            logging.warning(
                'CBS Series CSV pagination exceeded max_pages=%d for id=%s (attempt %d)',
                max_pages,
                path_id,
                attempt,
            )

        if attempt_complete:
            has_unclosed_unbounded_attempt = False
        elif attempt_committed_unbounded:
            has_unclosed_unbounded_attempt = True

        incomplete_attempt = {
            sid:
                (_effective_annual_count(sid, attempt_explicit_annual,
                                         attempt_blank_annual,
                                         attempt_subannual_blank_sids), req_cnt)
            for sid, req_cnt in req_annual_rows.items()
            if _effective_annual_count(sid, attempt_explicit_annual,
                                       attempt_blank_annual,
                                       attempt_subannual_blank_sids) < req_cnt
        }
        if (attempt_complete and len(attempt_sids) >= expected_min and
                not incomplete_attempt):
            if len(page_contents) == 1 and not attempt_had_key_upgrade:
                raw_bytes = page_contents[0]
            elif attempt_headers_match and not attempt_had_key_upgrade:
                raw_bytes = b''.join(
                    _strip_trailing_blank_lines(c) for c in page_contents)
            else:
                raw_bytes = _serialize_csv_rows(attempt_header, attempt_rows)
            _write_bytes_atomically(dest_path, raw_bytes)
            return len(raw_bytes)

        incomplete_merged = {
            sid: (_effective_annual_count(sid, explicit_annual_by_sid,
                                          blank_annual_by_sid,
                                          subannual_blank_sids), req_cnt)
            for sid, req_cnt in req_annual_rows.items()
            if _effective_annual_count(sid, explicit_annual_by_sid,
                                       blank_annual_by_sid,
                                       subannual_blank_sids) < req_cnt
        }
        target_last_page = max(known_last_page or 0, min_required_pages)
        effective_page_target = (
            known_last_page if (known_last_page is not None and
                                min_required_pages <= known_last_page) else
            (min_required_pages if min_required_pages > 1 else
             (1 if saw_unbounded_end else None)))
        if has_unclosed_unbounded_attempt:
            merged_pages_complete = False
        elif (known_last_page is not None and
              min_required_pages <= known_last_page):
            merged_pages_complete = all(
                p in completed_pages for p in range(1, target_last_page + 1))
        else:
            merged_pages_complete = (saw_unbounded_end and all(
                p in completed_pages for p in range(1, target_last_page + 1)))
        if (merged_pages_complete and len(unique_sids) >= expected_min and
                not incomplete_merged):
            raw_bytes = _serialize_csv_rows(
                merged_header,
                [row for row, _ in merged_rows_by_key.values()],
            )
            _write_bytes_atomically(dest_path, raw_bytes)
            return len(raw_bytes)

        logging.warning(
            'CBS Series CSV for id=%s returned %d/%d series (incomplete=%s, complete_pages=%s/%s) on attempt %d; retrying...',
            path_id,
            len(unique_sids),
            expected_min,
            incomplete_merged,
            sorted(completed_pages),
            effective_page_target,
            attempt,
        )
        if attempt < max_attempts and delay > 0:
            time.sleep(min(delay * (2**(attempt - 1)), 16.0))

    reason = (f'returned only {len(unique_sids)}/{expected_min} series'
              if len(unique_sids) < expected_min else
              f'incomplete ({len(unique_sids)}/{expected_min} series)')
    raise RuntimeError(
        f'CBS Series CSV for id={path_id} {reason} '
        f'(incomplete={incomplete_merged}, complete_pages={sorted(completed_pages)}/{effective_page_target}) '
        f'after {max_attempts} attempts') from last_err


def fetch_cbs_series_datasets_raw(
    output_dir: str,
    session: requests.Session | None = None,
) -> list[str]:
    """Downloads all 3 raw CBS Series API CSV datasets into output_dir."""
    paths: list[str] = []
    for path_id, filename in CBS_RAW_SERIES_FILES.items():
        dest_path = os.path.join(output_dir, filename)
        byte_count = fetch_cbs_series_raw_csv(
            path_id=path_id,
            dest_path=dest_path,
            session=session,
        )
        logging.info(
            'Downloaded raw CBS Series CSV id=%s (%d bytes) to %s',
            path_id,
            byte_count,
            dest_path,
        )
        paths.append(dest_path)
    return paths


def fetch_cbs_boardsgenerator_census_raw_json(
    output_dir: str,
    session: requests.Session | None = None,
    retry_delay: float | None = None,
) -> str:
    """Downloads raw 2008 Census regional JSON payloads from boardsgenerator.cbs.gov.il."""
    sess = session or _get_session()
    delay = (retry_delay if retry_delay is not None else
             (2.0 if session is None else 0.0))
    records: list[dict[str, Any]] = []
    for region_code, data_mode in CBS_CENSUS_2008_REGIONS:
        params = {
            'mode': 'GetCensusData',
            'id': region_code,
            'dataMode': data_mode,
            'language': 'English',
            'rova': '',
            'tatRova': '',
        }
        payload: dict[str, Any] | None = None
        last_err: Exception | None = None
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            if hasattr(sess, 'cookies') and hasattr(sess.cookies, 'clear'):
                sess.cookies.clear()
            logging.info(
                'HTTP GET %s params=%s (attempt %d)',
                CBS_BOARDSGENERATOR_CENSUS_URL,
                params,
                attempt,
            )
            try:
                response = sess.get(
                    CBS_BOARDSGENERATOR_CENSUS_URL,
                    params=params,
                    timeout=(5, 30),
                )
                response.raise_for_status()
                candidate = response.json()
                if _is_valid_census_groups_payload(candidate,
                                                   data_mode=data_mode):
                    payload = candidate
                    break
                logging.warning(
                    'BoardsGenerator GetCensusData returned empty or malformed '
                    'Groups for region_code=%s on attempt %d',
                    region_code,
                    attempt,
                )
            except requests.HTTPError as err:
                if _is_non_retryable_http_error(err):
                    logging.error(
                        'Permanent HTTP error for region_code=%s: %s',
                        region_code,
                        err,
                    )
                    raise
                last_err = err
                logging.warning(
                    'BoardsGenerator GetCensusData failed for region_code=%s on attempt %d: %s',
                    region_code,
                    attempt,
                    err,
                )
            except (ValueError, requests.RequestException) as err:
                last_err = err
                logging.warning(
                    'BoardsGenerator GetCensusData failed for region_code=%s on attempt %d: %s',
                    region_code,
                    attempt,
                    err,
                )
            if attempt < max_attempts and delay > 0:
                time.sleep(min(delay * (2**(attempt - 1)), 16.0))
        if payload is None:
            raise RuntimeError(
                f'No valid 2008 Census JSON returned from {CBS_BOARDSGENERATOR_CENSUS_URL} '
                f'for region_code={region_code} data_mode={data_mode}'
            ) from last_err
        records.append({
            'region_code': region_code,
            'data_mode': data_mode,
            'payload': payload,
        })

    dest_path = os.path.join(output_dir, CBS_RAW_YISHUV_CENSUS_JSON)
    raw_json_bytes = json.dumps(records, ensure_ascii=False,
                                indent=2).encode('utf-8')
    _write_bytes_atomically(dest_path, raw_json_bytes)
    logging.info(
        'Downloaded raw 2008 Census regional JSON (%d bytes) to %s',
        len(raw_json_bytes),
        dest_path,
    )
    return dest_path


def fetch_cbs_mifkad_table_raw(
    xls_name: str,
    dest_path: str,
    session: requests.Session | None = None,
    retry_delay: float | None = None,
) -> int:
    """Downloads a raw 2008 Census Mifkad .xls table from boardsgenerator.cbs.gov.il."""
    sess = session or _get_session()
    delay = (retry_delay if retry_delay is not None else
             (2.0 if session is None else 0.0))
    remote_name = CBS_MIFKAD_2008_REMOTE_NAMES.get(xls_name, xls_name)
    url = f'{CBS_MIFKAD_BASE_URL}/{remote_name}'
    last_err: Exception | None = None
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        if hasattr(sess, 'cookies') and hasattr(sess.cookies, 'clear'):
            sess.cookies.clear()
        logging.info('HTTP GET %s (attempt %d)', url, attempt)
        try:
            response = sess.get(url, timeout=(5, 30))
            response.raise_for_status()
            content = response.content
            if content and content.startswith(_EXCEL_MAGIC_PREFIXES):
                _write_bytes_atomically(dest_path, content)
                return len(content)
            logging.warning(
                'Invalid XLS response (missing Excel magic bytes) from %s on attempt %d',
                url,
                attempt,
            )
        except requests.HTTPError as err:
            if _is_non_retryable_http_error(err):
                logging.error('Permanent HTTP error for %s: %s', url, err)
                raise
            last_err = err
            logging.warning('XLS request failed for %s on attempt %d: %s', url,
                            attempt, err)
        except requests.RequestException as err:
            last_err = err
            logging.warning('XLS request failed for %s on attempt %d: %s', url,
                            attempt, err)
        if attempt < max_attempts and delay > 0:
            time.sleep(min(delay * (2**(attempt - 1)), 16.0))
    raise RuntimeError(
        f'Downloaded invalid or empty XLS file from {url}') from last_err


def _is_managed_raw_input_filename(filename: str) -> bool:
    """Returns True if filename matches CBS raw input naming patterns managed by download_all."""
    return ((filename.startswith('cbs_') and filename.endswith(
        ('.csv', '.json'))) or filename.endswith(('.xls', '.xlsx')))


def download_all(output_dir: str, max_workers: int = 3) -> list[str]:
    """Downloads all raw CBS Series CSVs, 2008 Census JSON, and 5 Mifkad XLS files into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    expected_filenames = (set(CBS_RAW_SERIES_FILES.values()) |
                          {CBS_RAW_YISHUV_CENSUS_JSON} |
                          set(CBS_MIFKAD_2008_TABLES))

    downloaded_paths: list[str] = []
    try:
        downloaded_paths.extend(fetch_cbs_series_datasets_raw(output_dir))

        with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            xls_futures = {
                executor.submit(
                    fetch_cbs_mifkad_table_raw,
                    xls_name,
                    os.path.join(output_dir, xls_name),
                ):
                    xls_name for xls_name in CBS_MIFKAD_2008_TABLES
            }

            for future in futures.as_completed(xls_futures):
                xls_name = xls_futures[future]
                dest_path = os.path.join(output_dir, xls_name)
                byte_count = future.result()
                logging.info(
                    'Downloaded CBS Mifkad XLS %s (%d bytes) to %s',
                    xls_name,
                    byte_count,
                    dest_path,
                )
                downloaded_paths.append(dest_path)

        downloaded_paths.append(
            fetch_cbs_boardsgenerator_census_raw_json(output_dir))
    finally:
        _close_sessions()

    if os.path.realpath(output_dir) == os.path.realpath(_SCRIPT_DIR):
        logging.warning(
            'Refusing to run stale-file cleanup in script directory: %s',
            output_dir,
        )
    else:
        for existing_name in os.listdir(output_dir):
            existing_path = os.path.join(output_dir, existing_name)
            if (existing_name not in expected_filenames and
                    _is_managed_raw_input_filename(existing_name) and
                    os.path.isfile(existing_path)):
                logging.info('Removing stale input file: %s', existing_path)
                os.remove(existing_path)

    return sorted(downloaded_paths)


def main(argv: list[str] | None = None) -> None:
    logging.set_verbosity(logging.INFO)
    parser = argparse.ArgumentParser(
        description='Downloads raw Israel CBS files into input_files/.')
    parser.add_argument(
        '--output_dir',
        default=os.path.join(_SCRIPT_DIR, 'input_files'),
        help='Directory where raw CBS input files will be downloaded.',
    )
    parser.add_argument(
        '--max_workers',
        type=int,
        default=3,
        help='Maximum number of concurrent download threads.',
    )
    args = parser.parse_args(argv)
    download_all(args.output_dir, max_workers=args.max_workers)


if __name__ == '__main__':
    main()
