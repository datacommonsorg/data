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
import os
import tempfile
import threading
from typing import Any

from absl import logging
import requests
from requests import adapters
from urllib3.util import retry

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
            str(sid): 70 for sid in range(70001, 70013)
        },
        **{
            str(sid): 50 for sid in range(70015, 70027)
        },
        **{
            str(sid): 24 for sid in range(70136, 70148)
        },
    },
}

_CBS_SERIES_MIN_UNIQUE_IDS = {
    CBS_SERIES_POPULATION_PATH_ID: 5,
    CBS_SERIES_VITAL_STATS_PATH_ID: 7,
    CBS_SERIES_CAUSE_OF_DEATH_PATH_ID: 42,
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


def _get_session() -> requests.Session:
    """Returns a thread-local HTTP session configured with retry backoff."""
    session = getattr(_THREAD_LOCAL, 'session', None)
    if session is None:
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
        retry_strategy = retry.Retry(
            total=3,
            connect=3,
            backoff_factor=2.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=('GET',),
        )
        adapter = adapters.HTTPAdapter(max_retries=retry_strategy)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        _THREAD_LOCAL.session = session
    return session


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


def fetch_cbs_series_raw_csv(
    path_id: str,
    dest_path: str,
    session: requests.Session | None = None,
    page_size: int = 100,
    min_unique_series: int | None = None,
    min_annual_rows: dict[str, int] | None = None,
) -> int:
    """Downloads raw CSV data from apis.cbs.gov.il/series/data/path and writes it unmodified to dest_path."""
    sess = session or _get_session()
    expected_min = (min_unique_series if min_unique_series is not None else
                    _CBS_SERIES_MIN_UNIQUE_IDS.get(path_id, 1))
    req_annual_rows = (min_annual_rows if min_annual_rows is not None else
                       CBS_SERIES_MIN_ANNUAL_ROWS.get(path_id, {}))

    unique_sids: set[str] = set()
    annual_periods_by_sid: dict[str, set[str]] = {}
    header_line: bytes = b''
    raw_lines_by_key: dict[tuple[str, str, str], bytes] = {}
    incomplete_merged: dict[str, tuple[int, int]] = {}
    last_err: Exception | None = None
    max_attempts = 6 if session is None else 3
    for attempt in range(1, max_attempts + 1):
        if hasattr(sess, 'cookies') and hasattr(sess.cookies, 'clear'):
            sess.cookies.clear()
        page_contents: list[bytes] = []
        attempt_sids: set[str] = set()
        attempt_annual_by_sid: dict[str, set[str]] = {}
        page = 1
        while True:
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
            if (not content or content.lstrip().startswith(
                (b'<!DOCTYPE', b'<html')) or
                    b'obs_time_period' not in content.splitlines()[0]):
                if page == 1:
                    logging.warning(
                        'Invalid or empty CSV returned from %s for id=%s on attempt %d',
                        CBS_SERIES_API_URL,
                        path_id,
                        attempt,
                    )
                break
            raw_lines = content.splitlines(keepends=True)
            if not header_line and raw_lines:
                header_line = raw_lines[0]
            text = content.decode('utf-8-sig', errors='replace')
            page_sids: set[str] = set()
            for idx, row in enumerate(csv.DictReader(io.StringIO(text)),
                                      start=1):
                sid = (row.get('id') or row.get('series_id') or '').strip()
                t_name = (row.get('time_name') or row.get('time_unit') or
                          '').strip()
                t_period = (row.get('obs_time_period') or
                            row.get('time_period') or '').strip()
                if sid:
                    page_sids.add(sid)
                    if t_name in ('', 'Year') and t_period:
                        attempt_annual_by_sid.setdefault(sid,
                                                         set()).add(t_period)
                        annual_periods_by_sid.setdefault(sid,
                                                         set()).add(t_period)
                    if idx < len(raw_lines):
                        raw_lines_by_key.setdefault((sid, t_name, t_period),
                                                    raw_lines[idx])
            if not page_sids:
                if page == 1:
                    logging.warning(
                        'No series rows returned from %s for id=%s on attempt %d',
                        CBS_SERIES_API_URL,
                        path_id,
                        attempt,
                    )
                break
            attempt_sids.update(page_sids)
            unique_sids.update(page_sids)
            if page == 1:
                page_contents.append(content)
            else:
                if len(raw_lines) > 1:
                    page_contents.append(b''.join(raw_lines[1:]))
            if len(page_sids) < page_size:
                break
            page += 1

        incomplete_attempt = {
            sid: (len(attempt_annual_by_sid.get(sid, set())), req_cnt)
            for sid, req_cnt in req_annual_rows.items()
            if len(attempt_annual_by_sid.get(sid, set())) < req_cnt
        }
        if len(attempt_sids) >= expected_min and not incomplete_attempt:
            raw_bytes = b''.join(page_contents)
            _write_bytes_atomically(dest_path, raw_bytes)
            return len(raw_bytes)

        incomplete_merged = {
            sid: (len(annual_periods_by_sid.get(sid, set())), req_cnt)
            for sid, req_cnt in req_annual_rows.items()
            if len(annual_periods_by_sid.get(sid, set())) < req_cnt
        }
        if len(unique_sids) >= expected_min and not incomplete_merged:
            raw_bytes = header_line + b''.join(raw_lines_by_key.values())
            _write_bytes_atomically(dest_path, raw_bytes)
            return len(raw_bytes)

        logging.warning(
            'CBS Series CSV for id=%s returned %d/%d series (incomplete=%s) on attempt %d; retrying...',
            path_id,
            len(unique_sids),
            expected_min,
            incomplete_merged,
            attempt,
        )

    raise RuntimeError(
        f'CBS Series CSV for id={path_id} returned only {len(unique_sids)}/{expected_min} '
        f'series (incomplete={incomplete_merged}) after {max_attempts} attempts'
    ) from last_err


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
) -> str:
    """Downloads raw 2008 Census regional JSON payloads from boardsgenerator.cbs.gov.il."""
    sess = session or _get_session()
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
        for attempt in range(1, 4):
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
                if isinstance(candidate, dict) and candidate.get('Groups'):
                    payload = candidate
                    break
            except (ValueError, requests.RequestException) as err:
                last_err = err
                logging.warning(
                    'BoardsGenerator GetCensusData failed for region_code=%s on attempt %d: %s',
                    region_code,
                    attempt,
                    err,
                )
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
) -> int:
    """Downloads a raw 2008 Census Mifkad .xls table from boardsgenerator.cbs.gov.il."""
    sess = session or _get_session()
    remote_name = CBS_MIFKAD_2008_REMOTE_NAMES.get(xls_name, xls_name)
    url = f'{CBS_MIFKAD_BASE_URL}/{remote_name}'
    last_err: Exception | None = None
    for attempt in range(1, 4):
        logging.info('HTTP GET %s (attempt %d)', url, attempt)
        try:
            response = sess.get(url, timeout=(5, 30))
            response.raise_for_status()
            content = response.content
            if content and not content.lstrip().startswith(
                (b'<!DOCTYPE', b'<html')):
                _write_bytes_atomically(dest_path, content)
                return len(content)
        except requests.RequestException as err:
            last_err = err
            logging.warning('XLS request failed for %s on attempt %d: %s', url,
                            attempt, err)
        logging.warning('Invalid XLS response from %s on attempt %d', url,
                        attempt)
    raise RuntimeError(
        f'Downloaded invalid or empty XLS file from {url}') from last_err


def download_all(output_dir: str, max_workers: int = 3) -> list[str]:
    """Downloads all raw CBS Series CSVs, 2008 Census JSON, and 5 Mifkad XLS files into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    expected_filenames = (set(CBS_RAW_SERIES_FILES.values()) |
                          {CBS_RAW_YISHUV_CENSUS_JSON} |
                          set(CBS_MIFKAD_2008_TABLES))

    downloaded_paths: list[str] = []
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

    for existing_name in os.listdir(output_dir):
        existing_path = os.path.join(output_dir, existing_name)
        if (existing_name not in expected_filenames and
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
