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
"""Downloads Israel CBS datasets from apis.cbs.gov.il and boardsgenerator.cbs.gov.il into input_files/."""

import argparse
from concurrent import futures
import csv
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

# Official CBS Time-Series DataBank paths on apis.cbs.gov.il from the import spreadsheets:
# - 2,1,1,1: Population -> Population, by Population Group -> Population De Jure -> At End of Period
# - 2,3,1:   Population -> Live-Births and Deaths -> By Population Group
# - 4,2,1:   Health -> Mortality rates, by causes of death -> Data by select causes
CBS_SERIES_PATHS = (
    ('cbs_series_population_religion.csv', '2,1,1,1'),
    ('cbs_series_vital_statistics.csv', '2,3,1'),
    ('cbs_series_cause_of_death.csv', '4,2,1'),
)

# Official CBS BoardsGenerator 2008 Census endpoint (boardsgenerator.cbs.gov.il)
CBS_BOARDSGENERATOR_CENSUS_URL = (
    'https://boardsgenerator.cbs.gov.il/Handlers/WebParts/YishuvHandler.ashx')
CBS_CENSUS_2008_FILENAME = 'cbs_census_2008_regions.csv'
CBS_CENSUS_2008_FIELDS = (
    'region_code',
    'data_mode',
    'group_id',
    'group_name',
    'subject_id',
    'subject_name',
    'value',
)
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
            'User-Agent': 'DataCommons-IsraelCensus-Importer/1.0',
            'Accept': '*/*',
        })
        retry_strategy = retry.Retry(
            total=3,
            connect=0,
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


def _write_rows_atomically(
    dest_path: str,
    fieldnames: list[str] | tuple[str, ...],
    rows: list[dict[str, Any]],
) -> None:
    """Atomically writes a list of dictionaries to a CSV file."""
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=os.path.dirname(os.path.abspath(dest_path)),
        prefix='.tmp_cbs_',
        suffix='.csv',
    )
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as fp:
            writer = csv.DictWriter(
                fp,
                fieldnames=list(fieldnames),
                extrasaction='ignore',
                lineterminator='\n',
            )
            writer.writeheader()
            for rec in rows:
                clean_row = {
                    k: ('' if rec.get(k) is None else str(rec.get(k)).strip())
                    for k in fieldnames
                }
                writer.writerow(clean_row)
        os.replace(tmp_path, dest_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def fetch_cbs_series_path_csv_raw(
    path_id: str,
    dest_path: str,
    session: requests.Session | None = None,
    page_size: int = 100,
) -> int:
    """Downloads the direct raw CSV file from apis.cbs.gov.il/series/data/path."""
    sess = session or _get_session()
    params = {
        'id': path_id,
        'Page': 1,
        'PageSize': page_size,
        'format': 'csv',
        'download': 'true',
        'lang': 'en',
    }
    logging.info('HTTP GET %s params=%s', CBS_SERIES_API_URL, params)
    response = sess.get(
        CBS_SERIES_API_URL,
        params=params,
        timeout=(5, 30),
    )
    response.raise_for_status()
    content = response.content
    if (not content or content.lstrip().startswith((b'<!DOCTYPE', b'<html')) or
            b'obs_time_period' not in content.splitlines()[0]):
        raise RuntimeError(
            f'Invalid or empty CSV returned from {CBS_SERIES_API_URL} for id={path_id}'
        )
    _write_bytes_atomically(dest_path, content)
    return len(content)


def parse_cbs_boardsgenerator_census_payload(
    payload: dict[str, Any],
    region_code: str,
    data_mode: str,
) -> list[dict[str, str]]:
    """Extracts 2008 Census subject rows from a boardsgenerator.cbs.gov.il GetCensusData payload."""
    rows: list[dict[str, str]] = []
    for group in (payload or {}).get('Groups') or []:
        group_id = str(group.get('Id') or '').strip()
        group_name = str(group.get('Name') or '').strip()
        for subj in group.get('Subjects') or []:
            subject_id = str(subj.get('Id') or '').strip()
            subject_name = str(subj.get('Name') or '').strip()
            val = str(subj.get('Value') or '').strip()
            if not subject_id or not val:
                continue
            rows.append({
                'region_code': region_code,
                'data_mode': data_mode,
                'group_id': group_id,
                'group_name': group_name,
                'subject_id': subject_id,
                'subject_name': subject_name,
                'value': val,
            })
    return rows


def fetch_cbs_boardsgenerator_census_to_csv(
    dest_path: str,
    session: requests.Session | None = None,
) -> int:
    """Downloads 2008 Census regional data from boardsgenerator.cbs.gov.il to CSV."""
    sess = session or _get_session()
    all_rows: list[dict[str, str]] = []
    for region_code, data_mode in CBS_CENSUS_2008_REGIONS:
        params = {
            'mode': 'GetCensusData',
            'id': region_code,
            'dataMode': data_mode,
            'language': 'English',
            'rova': '',
            'tatRova': '',
        }
        logging.info('HTTP GET %s params=%s', CBS_BOARDSGENERATOR_CENSUS_URL,
                     params)
        response = sess.get(
            CBS_BOARDSGENERATOR_CENSUS_URL,
            params=params,
            timeout=(5, 30),
        )
        response.raise_for_status()
        payload = response.json()
        all_rows.extend(
            parse_cbs_boardsgenerator_census_payload(
                payload,
                region_code,
                data_mode,
            ))

    if not all_rows:
        raise RuntimeError(
            f'No 2008 Census rows returned from {CBS_BOARDSGENERATOR_CENSUS_URL}'
        )

    _write_rows_atomically(dest_path, CBS_CENSUS_2008_FIELDS, all_rows)
    return len(all_rows)


def fetch_cbs_mifkad_table_raw(
    xls_name: str,
    dest_path: str,
    session: requests.Session | None = None,
) -> int:
    """Downloads a raw 2008 Census Mifkad .xls table from boardsgenerator.cbs.gov.il."""
    sess = session or _get_session()
    remote_name = CBS_MIFKAD_2008_REMOTE_NAMES.get(xls_name, xls_name)
    url = f'{CBS_MIFKAD_BASE_URL}/{remote_name}'
    logging.info('HTTP GET %s', url)
    response = sess.get(url, headers={'Accept': '*/*'}, timeout=(5, 30))
    response.raise_for_status()
    content = response.content
    if not content or content.lstrip().startswith((b'<!DOCTYPE', b'<html')):
        raise RuntimeError(f'Downloaded invalid or empty XLS file from {url}')
    _write_bytes_atomically(dest_path, content)
    return len(content)


def download_all(output_dir: str, max_workers: int = 3) -> list[str]:
    """Downloads all CBS time-series CSV and 2008 Census CSV/XLS files into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    expected_filenames = ({filename for filename, _ in CBS_SERIES_PATHS} |
                          {CBS_CENSUS_2008_FILENAME} |
                          set(CBS_MIFKAD_2008_TABLES))

    downloaded_paths: list[str] = []
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        cbs_futures = {
            executor.submit(
                fetch_cbs_boardsgenerator_census_to_csv,
                os.path.join(output_dir, CBS_CENSUS_2008_FILENAME),
            ):
                CBS_CENSUS_2008_FILENAME
        }

        for xls_name in CBS_MIFKAD_2008_TABLES:
            cbs_futures[executor.submit(
                fetch_cbs_mifkad_table_raw,
                xls_name,
                os.path.join(output_dir, xls_name),
            )] = xls_name

        # Fetch CBS Series API direct CSVs sequentially to avoid concurrent ASP.NET session truncation
        for filename, path_id in CBS_SERIES_PATHS:
            dest_path = os.path.join(output_dir, filename)
            byte_count = fetch_cbs_series_path_csv_raw(path_id, dest_path)
            logging.info(
                'Downloaded CBS Series CSV %s (%d bytes) to %s',
                filename,
                byte_count,
                dest_path,
            )
            downloaded_paths.append(dest_path)

        for future in futures.as_completed(cbs_futures):
            filename = cbs_futures[future]
            dest_path = os.path.join(output_dir, filename)
            count = future.result()
            logging.info(
                'Downloaded CBS file %s (%d rows/bytes) to %s',
                filename,
                count,
                dest_path,
            )
            downloaded_paths.append(dest_path)

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
