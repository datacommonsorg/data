#!/usr/bin/env python3
# Copyright 2024 Google LLC
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
"""Download and preprocess US Census Gazetteer files for Surface Area."""

from contextlib import contextmanager
import os
import re
import shutil
import tempfile
from typing import Dict, List, Tuple
import zipfile

from absl import app
from absl import flags
from absl import logging
from bs4 import BeautifulSoup
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -----------------------------------------------------------------------------
# Configuration and Constants
# -----------------------------------------------------------------------------

INPUT_DIR = 'input_files'
OUTPUT_DIR = 'output_files'

OUTPUT_CSV = 'surface_area.csv'
OUTPUT_TMCF = 'surface_area.tmcf'

# Conversion factor: 1 Square Mile = 2,589,988.11 Square Meters
SQMI_FACTOR = 2589988.11

# URLs
CENSUS_BASE_URL = 'https://www2.census.gov/geo/docs/maps-data/data/gazetteer/'
STATE_AREA_URL = (
    'https://www.census.gov/geographies/reference-files/2010/geo/state-area.html'
)

DEFAULT_YEAR = '2018'

# Gazetteer file specifications: (file_pattern, dcid_prefix, geoid_column, description)
GAZETTEER_FILE_SPECS = [
    (r'.*_Gaz_counties_national\.(zip|txt)', 'geoId/', 'GEOID', 'Counties'),
    (r'.*_Gaz_.*CDs_national\.(zip|txt)', 'geoId/', 'GEOID',
     'Congressional Districts'),
    (r'.*_Gaz_cbsa_national\.(zip|txt)', 'geoId/C', 'GEOID',
     'Core Based Statistical Areas'),
    (r'.*_Gaz_place_national\.(zip|txt)', 'geoId/', 'GEOID', 'Places'),
    (r'.*_Gaz_cousubs_national\.(zip|txt)', 'geoId/', 'GEOID',
     'County Subdivisions'),
    (r'.*_Gaz_unsd_national\.(zip|txt)', 'geoId/sch', 'GEOID',
     'Unified School Districts'),
    (r'.*_Gaz_elsd_national\.(zip|txt)', 'geoId/sch', 'GEOID',
     'Elementary School Districts'),
    (r'.*_Gaz_scsd_national\.(zip|txt)', 'geoId/sch', 'GEOID',
     'Secondary School Districts'),
    (r'.*_Gaz_tracts_national\.(zip|txt)', 'geoId/', 'GEOID', 'Census Tracts'),
]

# File pattern for state gazetteer file (available in recent releases >= 2024)
STATE_GAZETTEER_PATTERN = r'.*_Gaz_state_national\.(zip|txt)'

# State name to 2-digit FIPS code mapping
STATE_FIPS_MAP = {
    'Alabama': '01',
    'Alaska': '02',
    'Arizona': '04',
    'Arkansas': '05',
    'California': '06',
    'Colorado': '08',
    'Connecticut': '09',
    'Delaware': '10',
    'District of Columbia': '11',
    'Florida': '12',
    'Georgia': '13',
    'Hawaii': '15',
    'Idaho': '16',
    'Illinois': '17',
    'Indiana': '18',
    'Iowa': '19',
    'Kansas': '20',
    'Kentucky': '21',
    'Louisiana': '22',
    'Maine': '23',
    'Maryland': '24',
    'Massachusetts': '25',
    'Michigan': '26',
    'Minnesota': '27',
    'Mississippi': '28',
    'Missouri': '29',
    'Montana': '30',
    'Nebraska': '31',
    'Nevada': '32',
    'New Hampshire': '33',
    'New Jersey': '34',
    'New Mexico': '35',
    'New York': '36',
    'North Carolina': '37',
    'North Dakota': '38',
    'Ohio': '39',
    'Oklahoma': '40',
    'Oregon': '41',
    'Pennsylvania': '42',
    'Rhode Island': '44',
    'South Carolina': '45',
    'South Dakota': '46',
    'Tennessee': '47',
    'Texas': '48',
    'Utah': '49',
    'Vermont': '50',
    'Virginia': '51',
    'Washington': '53',
    'West Virginia': '54',
    'Wisconsin': '55',
    'Wyoming': '56',
    'Puerto Rico': '72',
}

DEFAULT_YEARS = 'auto'

# TMCF template
TMCF_TEMPLATE = ('Node: E:Data->E0\n'
                 'typeOf: schema:StatVarObservation\n'
                 'variableMeasured: dcs:SurfaceArea\n'
                 'observationAbout: C:Data->dcid\n'
                 'observationDate: C:Data->observationDate\n'
                 'value: C:Data->SurfaceArea\n'
                 'unit: dcs:SquareMile\n')

_USER_AGENT = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
               '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 DataCommons')

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

_FLAGS = flags.FLAGS

flags.DEFINE_enum('mode', 'all', ['download', 'process', 'all'],
                  'Mode of operation: download, process, or all.')
flags.DEFINE_string(
    'years', DEFAULT_YEARS,
    'Gazetteer release years to download and process. Defaults to "auto" '
    '(dynamically discovers all available years >= 2018 from census.gov).'
)
flags.DEFINE_string('year', '', 'Alias for --years.')
flags.DEFINE_string(
    'input_dir', '',
    'Directory to store/read raw input files. Defaults to input_files/ in module dir.'
)
flags.DEFINE_string(
    'output_dir', '',
    'Directory to store generated CSV and TMCF. Defaults to output_files/ in module dir.'
)


def get_requests_session() -> requests.Session:
    """Creates a requests.Session with connection pooling and exponential backoff retries."""
    session = requests.Session()
    session.headers.update({'User-Agent': _USER_AGENT})
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy,
                          pool_connections=10,
                          pool_maxsize=10)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def resolve_all_available_years(start_year: int = 2018,
                                session: requests.Session = None) -> List[str]:
    """Discovers all available release years >= start_year from census.gov."""
    if session is None:
        session = get_requests_session()
    logging.info('Discovering available gazetteer release years from %s...',
                 CENSUS_BASE_URL)
    try:
        index_html = fetch_url(CENSUS_BASE_URL, session).decode('utf-8',
                                                                errors='replace')
        years = sorted(set(re.findall(r'href="([0-9]{4})_Gazetteer/"', index_html)))
        available = [y for y in years if int(y) >= start_year]
        if available:
            logging.info('Found available gazetteer years: %s', ', '.join(available))
            return available
    except (requests.RequestException, ValueError, re.error) as e:
        logging.warning('Could not discover years dynamically (%s); falling back to 2018', e)
    return [str(start_year)]


def parse_years(year_spec: str,
                session: requests.Session = None) -> List[str]:
    """Parses year specification (e.g. 'auto', '2018', '2018-2025', '2018-latest')."""
    spec = str(year_spec).strip()
    if spec.lower() in ('auto', 'all'):
        return resolve_all_available_years(start_year=2018, session=session)
    if spec.lower() == 'latest':
        s = session or get_requests_session()
        return [resolve_latest_gazetteer_year(s)]
    if 'latest' in spec.lower():
        start = int(spec.lower().split('-', 1)[0].strip()) if '-' in spec else 2018
        return resolve_all_available_years(start_year=start, session=session)
    if '-' in spec:
        start, end = spec.split('-', 1)
        return [str(y) for y in range(int(start.strip()), int(end.strip()) + 1)]
    return [y.strip() for y in spec.split(',') if y.strip()]


def calc_surface_area(aland: float, awater: float) -> float:
    """Calculates surface area in Square Miles from land and water in Square Meters.

    Args:
        aland: Land area in Square Meters.
        awater: Water area in Square Meters.

    Returns:
        Surface area in Square Miles rounded to 4 decimal places.
    """
    return round((float(aland) + float(awater)) / SQMI_FACTOR, 4)


def _detect_separator(file_obj) -> str:
    """Detects whether a text stream is pipe-separated or tab-separated."""
    pos = file_obj.tell() if hasattr(file_obj, 'tell') else None
    first_line = file_obj.readline()
    if pos is not None and hasattr(file_obj, 'seek'):
        file_obj.seek(pos)
    if isinstance(first_line, bytes):
        return '|' if b'|' in first_line else '\t'
    return '|' if '|' in str(first_line) else '\t'


def parse_gazetteer_data(file_obj,
                         dcid_prefix: str,
                         geoid_col: str = 'GEOID') -> Dict[str, float]:
    """Parses a gazetteer text stream and computes surface area for each entity.

    Args:
        file_obj: A file-like object or file path containing tab-separated values.
        dcid_prefix: Prefix to prepend to GEOID (e.g. 'geoId/', 'geoId/C', 'geoId/sch').
        geoid_col: Column name containing the GEOID.

    Returns:
        Dictionary mapping dcid -> SurfaceArea.
    """
    sep = _detect_separator(file_obj)
    df = pd.read_csv(file_obj, sep=sep, dtype=str, encoding='latin1')
    df.columns = [c.strip() for c in df.columns]

    if geoid_col not in df.columns:
        raise ValueError(
            f'Column {geoid_col} not found in gazetteer file columns: {df.columns}'
        )
    if 'ALAND' not in df.columns or 'AWATER' not in df.columns:
        raise ValueError(
            f'ALAND or AWATER column missing in gazetteer file columns: {df.columns}'
        )

    aland = pd.to_numeric(df['ALAND'].str.strip(), errors='coerce').fillna(0.0)
    awater = pd.to_numeric(df['AWATER'].str.strip(),
                           errors='coerce').fillna(0.0)
    surface_area = ((aland + awater) / SQMI_FACTOR).round(4)

    dcids = dcid_prefix + df[geoid_col].str.strip()
    return dict(zip(dcids, surface_area))


def parse_state_area_html(html_content: str) -> Dict[str, float]:
    """Parses US Census State Area Measurements HTML table.

    Args:
        html_content: HTML content of the state area reference page.

    Returns:
        Dictionary mapping state dcid (e.g. 'geoId/01') -> SurfaceArea.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    records = {}

    for tr in soup.find_all('tr'):
        tds = [td.get_text(strip=True) for td in tr.find_all('td')]
        if len(tds) >= 6 and tds[0] in STATE_FIPS_MAP:
            state_name = tds[0]
            fips = STATE_FIPS_MAP[state_name]
            dcid = f'geoId/{fips}'
            try:
                # Column 3: Land area (sq mi), Column 5: Water area (sq mi)
                land_sqmi = float(tds[3].replace(',', ''))
                water_sqmi = float(tds[5].replace(',', ''))
                records[dcid] = land_sqmi + water_sqmi
            except ValueError:
                logging.warning('Could not parse area for state %s', state_name)

    return records


def parse_state_gazetteer(file_obj) -> Dict[str, float]:
    """Parses a modern state gazetteer file (2024+).

    Args:
        file_obj: File-like object with state gazetteer table.

    Returns:
        Dictionary mapping state dcid -> SurfaceArea.
    """
    sep = _detect_separator(file_obj)
    df = pd.read_csv(file_obj, sep=sep, dtype=str, encoding='latin1')
    df.columns = [c.strip() for c in df.columns]

    geoid_col = 'GEOID'
    if geoid_col not in df.columns:
        raise ValueError('GEOID column not found in state gazetteer file.')

    aland = pd.to_numeric(df['ALAND'].str.strip(), errors='coerce').fillna(0.0)
    awater = pd.to_numeric(df['AWATER'].str.strip(),
                           errors='coerce').fillna(0.0)
    surface_area = ((aland + awater) / SQMI_FACTOR).round(4)

    dcids = 'geoId/' + df[geoid_col].str.strip().str.zfill(2)
    return dict(zip(dcids, surface_area))


def fetch_url(url: str, session: requests.Session, timeout: int = 60) -> bytes:
    """Fetches URL contents using a shared session with retries."""
    logging.info('HTTP GET %s', url)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    logging.info('HTTP GET %s succeeded (%d bytes)', url, len(response.content))
    return response.content


def download_file_atomic(url: str,
                         dest_path: str,
                         session: requests.Session,
                         timeout: int = 60) -> None:
    """Downloads a file atomically to a temp file, verifies size, and moves."""
    dest_dir = os.path.dirname(dest_path)
    os.makedirs(dest_dir, exist_ok=True)
    logging.info('HTTP GET %s -> %s', url, dest_path)

    with tempfile.NamedTemporaryFile(dir=dest_dir, delete=False) as tmp_file:
        tmp_path = tmp_file.name
        try:
            with session.get(url, stream=True, timeout=timeout) as response:
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        tmp_file.write(chunk)
            tmp_file.flush()
            size = os.path.getsize(tmp_path)
            if size == 0:
                raise RuntimeError(f'Downloaded file {url} is empty (0 bytes)')
            shutil.move(tmp_path, dest_path)
            logging.info('Successfully downloaded %s (%d bytes)', dest_path, size)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise


def resolve_latest_gazetteer_year(session: requests.Session) -> str:
    """Resolves the latest available gazetteer year from census.gov."""
    logging.info('Resolving latest gazetteer year from census.gov...')
    index_html = fetch_url(CENSUS_BASE_URL, session).decode('utf-8',
                                                            errors='replace')
    years = re.findall(r'href="([0-9]{4})_Gazetteer/"', index_html)
    if not years:
        logging.warning('Could not discover years; falling back to %s',
                        DEFAULT_YEAR)
        return DEFAULT_YEAR

    latest_year = max(years)
    logging.info('Resolved latest gazetteer year: %s', latest_year)
    return latest_year


def get_gazetteer_year_file_list(year: str,
                                 session: requests.Session) -> List[str]:
    """Retrieves file listing for the specified gazetteer year directory."""
    year_url = f'{CENSUS_BASE_URL}{year}_Gazetteer/'
    html = fetch_url(year_url, session).decode('utf-8', errors='replace')
    files = re.findall(r'href="([^"]*Gaz_[^"]*)"', html)
    return files


def download_files(input_dir: str, year_spec: str = DEFAULT_YEARS) -> List[str]:
    """Downloads required gazetteer files and state area table into input_dir for all years.

    Args:
        input_dir: Directory where downloaded files are stored.
        year_spec: Year range or specification (e.g. '2018-2025' or 'latest').

    Returns:
        List of paths to downloaded files.
    """
    os.makedirs(input_dir, exist_ok=True)
    session = get_requests_session()
    if str(year_spec).strip().lower() == 'latest':
        years = [resolve_latest_gazetteer_year(session)]
    else:
        years = parse_years(year_spec)
    downloaded_paths = []

    for year in years:
        year_url = f'{CENSUS_BASE_URL}{year}_Gazetteer/'
        logging.info('Discovering files for year %s from %s...', year, year_url)
        try:
            available_files = get_gazetteer_year_file_list(year, session)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logging.warning(
                    'Year %s gazetteer directory not found (HTTP 404). Stopping early.',
                    year)
                break
            raise

        for pattern, _, _, desc in GAZETTEER_FILE_SPECS:
            matched_filename = None
            for filename in available_files:
                if re.match(pattern, filename):
                    matched_filename = filename
                    break

            if not matched_filename:
                logging.warning('No gazetteer file found for %s %s (pattern: %s)',
                                year, desc, pattern)
                continue

            target_url = f'{year_url}{matched_filename}'
            dest_path = os.path.join(input_dir, matched_filename)

            if not (os.path.exists(dest_path) and os.path.getsize(dest_path) > 0):
                logging.info('Downloading %s (%s) from %s...', matched_filename, desc,
                             target_url)
                download_file_atomic(target_url, dest_path, session)
            downloaded_paths.append(dest_path)

        # State file for modern years (2024+)
        state_gaz_file = None
        for filename in available_files:
            if re.match(STATE_GAZETTEER_PATTERN, filename):
                state_gaz_file = filename
                break

        if state_gaz_file:
            dest_path = os.path.join(input_dir, state_gaz_file)
            if not (os.path.exists(dest_path) and os.path.getsize(dest_path) > 0):
                target_url = f'{year_url}{state_gaz_file}'
                logging.info('Downloading state gazetteer %s from %s...', state_gaz_file,
                             target_url)
                download_file_atomic(target_url, dest_path, session)
            downloaded_paths.append(dest_path)

    # State area reference table (for 2018-2023)
    html_dest = os.path.join(input_dir, 'state_area.html')
    if not (os.path.exists(html_dest) and os.path.getsize(html_dest) > 0):
        logging.info('Downloading state area reference table from %s...',
                     STATE_AREA_URL)
        download_file_atomic(STATE_AREA_URL, html_dest, session)
    downloaded_paths.append(html_dest)

    return downloaded_paths


@contextmanager
def _open_input_stream(filepath: str):
    """Context manager to stream-read a plain text file or the first file in a zip archive."""
    if filepath.endswith('.zip'):
        with zipfile.ZipFile(filepath) as zf:
            inner_names = [n for n in zf.namelist() if not n.startswith('__MACOSX')]
            with zf.open(inner_names[0]) as f:
                yield f
    else:
        with open(filepath, 'r', encoding='latin1') as f:
            yield f


def process(input_dir: str,
            output_dir: str,
            year_spec: str = DEFAULT_YEARS) -> Tuple[str, str]:
    """Processes gazetteer raw files into final CSV and TMCF across specified years.

    Args:
        input_dir: Directory containing downloaded raw files.
        output_dir: Directory where surface_area.csv and surface_area.tmcf will be saved.
        year_spec: Year range or specification (e.g. '2018-2025' or '2018').

    Returns:
        Tuple of (csv_path, tmcf_path).
    """
    os.makedirs(output_dir, exist_ok=True)
    files_in_input = os.listdir(input_dir) if os.path.exists(input_dir) else []

    if str(year_spec).strip().lower() in ('auto', 'all'):
        input_years = set()
        for filename in files_in_input:
            m = re.match(r'^([0-9]{4})_', filename)
            if m and int(m.group(1)) >= 2018:
                input_years.add(m.group(1))
        if input_years:
            years = sorted(input_years)
        else:
            years = parse_years(year_spec)
    else:
        years = parse_years(year_spec)

    all_rows = []

    for year in years:
        logging.info('Processing data for year %s...', year)
        year_records: Dict[str, float] = {}

        # 1. Process States
        state_gaz_found = False
        for filename in files_in_input:
            if filename.startswith(f'{year}_') and re.match(
                    STATE_GAZETTEER_PATTERN, filename):
                filepath = os.path.join(input_dir, filename)
                logging.info('Processing state gazetteer: %s', filename)
                with _open_input_stream(filepath) as f:
                    year_records.update(parse_state_gazetteer(f))
                state_gaz_found = True
                break

        if not state_gaz_found:
            html_path = os.path.join(input_dir, 'state_area.html')
            if os.path.exists(html_path):
                logging.info('Processing state area reference table for %s: %s',
                             year, html_path)
                with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
                    year_records.update(parse_state_area_html(f.read()))
            else:
                logging.warning('No state data file found in %s', input_dir)

        logging.info('Year %s states loaded: %d', year, len(year_records))

        # 2. Process Gazetteer specs
        for pattern, prefix, geoid_col, desc in GAZETTEER_FILE_SPECS:
            matched_file = None
            for filename in files_in_input:
                if filename.startswith(f'{year}_') and re.match(pattern, filename):
                    matched_file = filename
                    break
            # Fallback for test datasets without year prefix
            if not matched_file and len(years) == 1:
                for filename in files_in_input:
                    if re.match(pattern, filename):
                        matched_file = filename
                        break

            if not matched_file:
                logging.warning('No file found for %s %s (pattern: %s)',
                                year, desc, pattern)
                continue

            filepath = os.path.join(input_dir, matched_file)
            logging.info('Processing %s (%s)...', matched_file, desc)
            with _open_input_stream(filepath) as f:
                records = parse_gazetteer_data(f, prefix, geoid_col)
                logging.info('  Loaded %d records for %s %s', len(records), year, desc)
                year_records.update(records)

        logging.info('Year %s total unique entities: %d', year, len(year_records))
        for dcid, area in year_records.items():
            all_rows.append((dcid, str(year), area))

    logging.info('Total observations across all years: %d', len(all_rows))

    # 3. Create sorted DataFrame
    all_rows.sort(key=lambda r: (r[0], r[1]))
    output_df = pd.DataFrame(
        all_rows, columns=['dcid', 'observationDate', 'SurfaceArea'])

    # 4. Write CSV
    csv_path = os.path.join(output_dir, OUTPUT_CSV)
    output_df.to_csv(csv_path, index=False)
    logging.info('Cleaned CSV successfully written to %s (%d rows)', csv_path,
                 len(output_df))

    # 5. Write TMCF
    tmcf_path = os.path.join(output_dir, OUTPUT_TMCF)
    with open(tmcf_path, 'w', encoding='utf-8') as f:
        f.write(TMCF_TEMPLATE)
    logging.info('Template MCF successfully written to %s', tmcf_path)

    return csv_path, tmcf_path


def main(argv):
    """Main entry point for command-line execution."""
    del argv  # Unused
    input_dir = _FLAGS.input_dir or os.path.join(_MODULE_DIR, INPUT_DIR)
    output_dir = _FLAGS.output_dir or os.path.join(_MODULE_DIR, OUTPUT_DIR)
    year_spec = _FLAGS.year or _FLAGS.years or DEFAULT_YEARS

    if _FLAGS.mode in ('download', 'all'):
        logging.info('Running download mode...')
        download_files(input_dir, year_spec)

    if _FLAGS.mode in ('process', 'all'):
        logging.info('Running process mode...')
        process(input_dir, output_dir, year_spec)


if __name__ == '__main__':
    app.run(main)
