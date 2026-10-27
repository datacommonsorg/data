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
"""Downloads and preprocesses CDC US Diabetes Surveillance System county data.

This script builds the unified `output/cdc_diabetes.csv` dataset covering:
1. Historical baseline county data (2004-2021) from GCS
   (`gs://unresolved_mcf/cdc/diabetes/20240112/`) or a local baseline directory.
2. Latest county data (2022+) from the CDC US Diabetes Surveillance System
   (USDSS) API (`https://usdss.cdc.gov/webapi/Diabetes/AllCountiesDataOneYear`)
   and/or raw CSVs in `input_files/`.

For each (condition, gender, county, year), two StatVarObservation rows are
emitted with `measurementMethod: dcid:AgeAdjustedPrevalence` and
`observationPeriod: P1Y`:
- Measured percentage (`statType: dcid:measuredValue`)
- Standard error derived from the 95% confidence interval upper bound:
  `stdError = round((Upper Limit - Percentage) / 1.96, 5)`
"""

import csv
import glob
import io
import os
import re
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple

from absl import app
from absl import flags
from absl import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

FLAGS = flags.FLAGS

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

flags.DEFINE_string(
    'baseline_dir',
    os.environ.get('CDC_DIABETES_BASELINE_DIR', ''),
    'Optional local directory containing historical 2004-2021 baseline CSVs.',
)
flags.DEFINE_string(
    'gcs_baseline_prefix',
    'gs://unresolved_mcf/cdc/diabetes/20240112/',
    'GCS prefix for historical 2004-2021 baseline CSVs.',
)
flags.DEFINE_string(
    'raw_input_dir',
    os.path.join(_MODULE_DIR, 'input_files'),
    'Directory containing raw CDC Diabetes Atlas CSV files (2022+).',
)
flags.DEFINE_string(
    'output_dir',
    os.path.join(_MODULE_DIR, 'output'),
    'Directory where processed output CSV and TMCF will be written.',
)
flags.DEFINE_boolean(
    'skip_baseline',
    False,
    'If True, skip loading the 2004-2021 baseline CSVs (used for unit tests).',
)
flags.DEFINE_boolean(
    'fetch_api',
    True,
    'If True, fetch 2022+ county data from the live CDC USDSS API into '
    'raw_input_dir before processing.',
)
flags.DEFINE_integer(
    'min_api_year',
    2022,
    'Minimum year to fetch from the CDC USDSS API.',
)

OUTPUT_COLUMNS = [
    'observationAbout',
    'observationDate',
    'variableMeasured',
    'value',
    'measurementMethod',
    'observationPeriod',
]

DEFAULT_MEASUREMENT_METHOD = 'dcid:AgeAdjustedPrevalence'
DEFAULT_OBSERVATION_PERIOD = 'P1Y'

# Exact 18 StatVar DCIDs verified against Data Commons production MCF
# (stat_vars.mcf) and the 20240112 baseline CSVs.
# Mapping: (condition, gender) -> (measuredValue_dcid, stdError_dcid)
STAT_VARS: Dict[Tuple[str, str], Tuple[str, str]] = {
    ('diabetes', 'total'): (
        'dcid:Percent_Person_20OrMoreYears_WithDiabetes',
        'dcid:dc/d4j16hnl53es2',  # stdError, WithDiabetes, Total
    ),
    ('diabetes', 'male'): (
        'dcid:dc/xmpy89x1nh8cg',  # measuredValue, WithDiabetes, Male
        'dcid:dc/xwtlmj1vg7618',  # stdError, WithDiabetes, Male
    ),
    ('diabetes', 'female'): (
        'dcid:dc/nh3s4skee5483',  # measuredValue, WithDiabetes, Female
        'dcid:dc/ryjdx30rfbfbb',  # stdError, WithDiabetes, Female
    ),
    ('obesity', 'total'): (
        'dcid:Percent_Person_20OrMoreYears_Obesity',
        'dcid:dc/bzfel0wfs6qhf',  # stdError, Obesity, Total
    ),
    ('obesity', 'male'): (
        'dcid:dc/x13tvt8jsgrm4',  # measuredValue, Obesity, Male
        'dcid:dc/73vt0flpsz26b',  # stdError, Obesity, Male
    ),
    ('obesity', 'female'): (
        'dcid:dc/4lvmzr1h1ylk1',  # measuredValue, Obesity, Female
        'dcid:dc/h3vxgc4gwl4c7',  # stdError, Obesity, Female
    ),
    ('inactivity', 'total'): (
        'dcid:Percent_Person_20OrMoreYears_PhysicalInactivity',
        'dcid:dc/1yfe8eezs4jbc',  # stdError, PhysicalInactivity, Total
    ),
    ('inactivity', 'male'): (
        'dcid:dc/ty7pq88d26963',  # measuredValue, PhysicalInactivity, Male
        'dcid:dc/bv6fv4et0d8pd',  # stdError, PhysicalInactivity, Male
    ),
    ('inactivity', 'female'): (
        'dcid:dc/tcqb49dvg7k53',  # measuredValue, PhysicalInactivity, Female
        'dcid:dc/t1hj2ymqdg5s6',  # stdError, PhysicalInactivity, Female
    ),
}

# CDC USDSS API constants for County Age-Adjusted Percentage (Adults 20+ Years).
_USDSS_BASE_URL = 'https://usdss.cdc.gov'
_USDSS_REFERER = 'https://usdss.cdc.gov/diabetes/surveillance.html'
_USDSS_YEARS_URL = ('https://usdss.cdc.gov/diabetes/data/surveillance/'
                    'SurveillanceIndicatorsYearsList_Counties.json')
_USDSS_COUNTY_DATA_URL = (
    'https://usdss.cdc.gov/webapi/Diabetes/AllCountiesDataOneYear')
_USDSS_DEFAULT_INIT_APP_DATA = (
    'https://usdss.cdc.gov/diabetes/'
    'InitAppData_a76d04a7-0f44-4f44-9147-3be5354c46ba.json')

# IndicatorID mapping in CDC USDSS API.
_CONDITION_TO_INDICATOR_ID: Dict[str, int] = {
    'diabetes': 151,  # Diagnosed Diabetes
    'obesity': 201,  # Obesity
    'inactivity': 202,  # Leisure-Time Physical Inactivity
}

# SexID mapping in CDC USDSS API.
_GENDER_TO_SEX_ID: Dict[str, int] = {
    'total': 591,
    'male': 592,
    'female': 593,
}

# Fixed stratification IDs for County Age-Adjusted Percentage (Adults 20+ Years).
_USDSS_RACE_ID = 551  # Total
_USDSS_AGE_ID = 635  # Age-Adjusted
_USDSS_DATA_TYPE_ID = 1113  # Percentage
_USDSS_EDUCATION_ID = 671  # Total
_USDSS_MISC_ID = 701  # Total
_USDSS_DATASET_ID = 1044  # Adults Aged 20+ Years
_USDSS_PUBLISHED_STATUS = 100  # Published (not suppressed/missing)

_SUPPRESSED_TOKENS = frozenset({
    '',
    'no data',
    'suppressed',
    'data suppressed',
    'na',
    'n/a',
    'null',
    'none',
    '.',
    '-',
})


def _ensure_dcid_prefix(val: str) -> str:
    """Ensures a DCID string starts with 'dcid:'."""
    val = val.strip()
    if not val:
        return ''
    if val.startswith('dcid:'):
        return val
    if val.startswith('dcs:'):
        return 'dcid:' + val[len('dcs:'):]
    return f'dcid:{val}'


def _create_http_session() -> requests.Session:
    """Creates an HTTP session with retry and required USDSS headers."""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(['GET', 'POST']),
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    session.headers.update({
        'User-Agent': 'DataCommons-Import/1.0',
        'Referer': _USDSS_REFERER,
        'Accept': 'application/json, text/plain, */*',
    })
    return session


def _discover_init_app_data_url(session: requests.Session) -> str:
    """Discovers the current InitAppData_*.json URL from the USDSS web app."""
    try:
        resp = session.get(_USDSS_REFERER, timeout=30)
        resp.raise_for_status()
        bundle_match = re.search(
            r'([A-Za-z0-9_/\-]*surveillance_entry\.[a-f0-9]+\.app\.js)',
            resp.text,
        )
        if bundle_match:
            rel_path = bundle_match.group(1).lstrip('/')
            if not rel_path.startswith('diabetes/'):
                rel_path = f'diabetes/{rel_path}'
            bundle_url = f'{_USDSS_BASE_URL}/{rel_path}'
            bundle_resp = session.get(bundle_url, timeout=30)
            if bundle_resp.ok:
                init_match = re.search(r'(InitAppData_[a-f0-9\-]+\.json)',
                                       bundle_resp.text)
                if init_match:
                    return f'{_USDSS_BASE_URL}/diabetes/{init_match.group(1)}'
    except Exception as exc:  # pylint: disable=broad-except
        logging.warning(
            'Falling back to default InitAppData URL after discovery warning: %s',
            exc,
        )
    return _USDSS_DEFAULT_INIT_APP_DATA


def fetch_usdss_county_data(raw_input_dir: str,
                            min_year: int = 2022) -> List[str]:
    """Fetches county surveillance data from CDC USDSS API and writes raw CSVs.

    Args:
      raw_input_dir: Directory where raw CSV files will be written.
      min_year: Minimum calendar year to fetch (inclusive).

    Returns:
      List of file paths written to `raw_input_dir`.
    """
    os.makedirs(raw_input_dir, exist_ok=True)
    session = _create_http_session()

    init_url = _discover_init_app_data_url(session)
    logging.info('Fetching CDC USDSS county metadata from %s', init_url)
    init_resp = session.get(init_url, timeout=60)
    init_resp.raise_for_status()
    init_data = init_resp.json()

    states_by_id: Dict[int, str] = {}
    for st in init_data.get('states_list', []):
        if 'LookupID' in st and 'Description' in st:
            states_by_id[int(st['LookupID'])] = str(st['Description']).strip()

    # Map internal GeoID (CDC) -> (fips_5digit, county_name, state_name)
    counties_by_geoid: Dict[int, Tuple[str, str, str]] = {}
    for county in init_data.get('counties_list', []):
        geoid = county.get('CDC')
        fips = str(county.get('CC', '')).strip()
        if geoid is None or not fips:
            continue
        county_name = str(county.get('CD', '')).strip()
        state_name = states_by_id.get(int(county.get('STC', -1)), '')
        counties_by_geoid[int(geoid)] = (fips, county_name, state_name)

    if not counties_by_geoid:
        raise RuntimeError(
            f'No counties found in CDC USDSS metadata at {init_url}')

    logging.info('Fetching CDC USDSS available county years from %s',
                 _USDSS_YEARS_URL)
    years_resp = session.get(_USDSS_YEARS_URL, timeout=60)
    years_resp.raise_for_status()
    years_list = years_resp.json()

    # Map IndicatorID -> list of (year_int, year_id)
    indicator_years: Dict[int, List[Tuple[int, int]]] = {}
    for entry in years_list:
        ind_id = int(entry.get('IndicatorID', -1))
        valid_years: List[Tuple[int, int]] = []
        for yr_obj in entry.get('YearsList', []):
            yr_str = str(yr_obj.get('Year', '')).strip()
            yr_id = yr_obj.get('YearID')
            if yr_str.isdigit() and yr_id is not None:
                yr_int = int(yr_str)
                if yr_int >= min_year:
                    valid_years.append((yr_int, int(yr_id)))
        valid_years.sort()
        indicator_years[ind_id] = valid_years

    written_files: List[str] = []
    for condition, ind_id in sorted(_CONDITION_TO_INDICATOR_ID.items()):
        years_for_ind = indicator_years.get(ind_id, [])
        if not years_for_ind:
            raise RuntimeError(
                f'No years >= {min_year} found for condition {condition} '
                f'(IndicatorID={ind_id})')
        for yr_int, yr_id in years_for_ind:
            for gender, sex_id in sorted(_GENDER_TO_SEX_ID.items()):
                payload = {
                    'IndicatorID': ind_id,
                    'RaceID': _USDSS_RACE_ID,
                    'SexID': sex_id,
                    'AgeID': _USDSS_AGE_ID,
                    'DataTypeID': _USDSS_DATA_TYPE_ID,
                    'EducationID': _USDSS_EDUCATION_ID,
                    'MiscID': _USDSS_MISC_ID,
                    'DatasetID': _USDSS_DATASET_ID,
                    'YearID': yr_id,
                }
                resp = session.post(_USDSS_COUNTY_DATA_URL,
                                    json=payload,
                                    timeout=60)
                resp.raise_for_status()
                data = resp.json()
                map_data = data.get('MapData', [])
                if not map_data:
                    raise RuntimeError(
                        f'Empty MapData from CDC USDSS API for '
                        f'condition={condition}, gender={gender}, year={yr_int}'
                    )

                out_filename = (
                    f'DiabetesAtlasCountyData_{condition}_{gender}_{yr_int}.csv'
                )
                out_path = os.path.join(raw_input_dir, out_filename)
                tmp_path = f'{out_path}.tmp'
                with open(tmp_path, 'w', encoding='utf-8', newline='') as f:
                    f.write('U.S. Diabetes Surveillance System '
                            '(https://gis.cdc.gov/grasp/diabetes/'
                            'DiabetesAtlas.html)\n')
                    f.write(f'Diagnosed/Surveillance {condition.capitalize()}, '
                            f'Age-Adjusted Percentage, Adults Aged 20+ Years, '
                            f'{gender.capitalize()}, {yr_int}\n')
                    writer = csv.writer(f, lineterminator='\n')
                    writer.writerow([
                        'County',
                        'State',
                        'CountyFIPS',
                        'Percentage',
                        'Lower Limit',
                        'Upper Limit',
                    ])
                    rows_to_write = []
                    for item in map_data:
                        geoid = item.get('GeoID')
                        if geoid is None or int(geoid) not in counties_by_geoid:
                            continue
                        fips, county_name, state_name = counties_by_geoid[int(
                            geoid)]
                        if item.get('Sup') == _USDSS_PUBLISHED_STATUS and (
                                item.get('Est') is not None and
                                item.get('UL') is not None):
                            pct_str = str(item['Est'])
                            ll_str = (str(item['LL'])
                                      if item.get('LL') is not None else '')
                            ul_str = str(item['UL'])
                        else:
                            pct_str = 'No Data'
                            ll_str = 'No Data'
                            ul_str = 'No Data'
                        rows_to_write.append((fips, county_name, state_name,
                                              pct_str, ll_str, ul_str))
                    rows_to_write.sort(key=lambda r: r[0])
                    for (
                            fips,
                            county_name,
                            state_name,
                            pct_str,
                            ll_str,
                            ul_str,
                    ) in rows_to_write:
                        writer.writerow([
                            county_name,
                            state_name,
                            fips,
                            pct_str,
                            ll_str,
                            ul_str,
                        ])
                os.replace(tmp_path, out_path)
                written_files.append(out_path)
                logging.info(
                    'Saved %s (%d county records)',
                    out_filename,
                    len(rows_to_write),
                )
    return written_files


def _extract_preprocessed_row(row: Dict[str, str]) -> Optional[List[str]]:
    """Extracts a 6-column output row from a pre-processed baseline CSV row."""
    obs_about = str(row.get('observationAbout') or row.get('location') or
                    '').strip()
    obs_date = str(row.get('observationDate') or row.get('year') or '').strip()
    var_measured = str(row.get('variableMeasured', '')).strip()
    value = str(row.get('value', '')).strip()
    method = str(row.get('measurementMethod', '')).strip()
    period = str(row.get('observationPeriod', '')).strip()

    if not obs_about or not obs_date or not var_measured or value == '':
        return None

    obs_about = _ensure_dcid_prefix(obs_about)
    var_measured = _ensure_dcid_prefix(var_measured)
    method = (_ensure_dcid_prefix(method)
              if method else DEFAULT_MEASUREMENT_METHOD)
    period = period if period else DEFAULT_OBSERVATION_PERIOD
    return [obs_about, obs_date, var_measured, value, method, period]


def _load_baseline_from_directory(baseline_dir: str) -> List[List[str]]:
    """Loads pre-processed 2004-2021 baseline CSVs from a local directory."""
    csv_files = sorted(
        glob.glob(os.path.join(baseline_dir, 'DiabetesAtlasCountyData_*.csv')))
    if not csv_files:
        raise FileNotFoundError(
            f'No DiabetesAtlasCountyData_*.csv files found in {baseline_dir}')
    rows: List[List[str]] = []
    for path in csv_files:
        with open(path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                extracted = _extract_preprocessed_row(row)
                if extracted:
                    rows.append(extracted)
    logging.info(
        'Loaded %d baseline rows from %d files in %s',
        len(rows),
        len(csv_files),
        baseline_dir,
    )
    return rows


def _load_baseline_from_gcs(gcs_prefix: str) -> List[List[str]]:
    """Loads pre-processed 2004-2021 baseline CSVs from GCS."""
    match = re.match(r'^gs://([^/]+)/(.*)$', gcs_prefix)
    if not match:
        raise ValueError(f'Invalid GCS prefix: {gcs_prefix}')
    bucket_name, prefix = match.group(1), match.group(2)

    try:
        from google.cloud import storage  # pylint: disable=import-outside-toplevel

        try:
            client = storage.Client.create_anonymous_client()
            blobs = list(client.list_blobs(bucket_name, prefix=prefix))
        except Exception:  # pylint: disable=broad-except
            client = storage.Client()
            blobs = list(client.list_blobs(bucket_name, prefix=prefix))

        csv_blobs = sorted(
            [b for b in blobs if b.name.endswith('.csv')],
            key=lambda b: b.name,
        )
        if csv_blobs:
            rows: List[List[str]] = []
            for blob in csv_blobs:
                content = blob.download_as_text(encoding='utf-8-sig')
                reader = csv.DictReader(io.StringIO(content))
                for row in reader:
                    extracted = _extract_preprocessed_row(row)
                    if extracted:
                        rows.append(extracted)
            logging.info(
                'Loaded %d baseline rows from %d GCS blobs under %s',
                len(rows),
                len(csv_blobs),
                gcs_prefix,
            )
            return rows
    except Exception as exc:  # pylint: disable=broad-except
        logging.warning(
            'google-cloud-storage fetch failed (%s); trying gsutil fallback.',
            exc,
        )

    tmp_dir = os.path.join(_MODULE_DIR, '_tmp_baseline_gcs')
    os.makedirs(tmp_dir, exist_ok=True)
    try:
        subprocess.run(
            ['gsutil', '-m', 'cp', f'{gcs_prefix.rstrip("/")}/*.csv', tmp_dir],
            check=True,
        )
        return _load_baseline_from_directory(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _normalize_condition(raw_text: str) -> Optional[str]:
    """Maps a condition label or filename token to a canonical condition key."""
    text = raw_text.strip().lower()
    if 'diabetes' in text:
        return 'diabetes'
    if 'obesity' in text:
        return 'obesity'
    if 'inactivity' in text or 'physical' in text:
        return 'inactivity'
    return None


def _normalize_gender(raw_text: str) -> Optional[str]:
    """Maps a gender/sex label or filename token to a canonical gender key."""
    text = raw_text.strip().lower()
    if text in ('female', 'females', 'women'):
        return 'female'
    if text in ('male', 'males', 'men'):
        return 'male'
    if text in ('total', 'overall', 'both', 'all'):
        return 'total'
    return None


def _parse_filename_metadata(
        filepath: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extracts (condition, gender, year) from a standard filename if present."""
    basename = os.path.basename(filepath)
    match = re.match(
        r'^DiabetesAtlasCountyData_([A-Za-z]+)_([A-Za-z]+)_(\d{4})\.csv$',
        basename,
        re.IGNORECASE,
    )
    if match:
        cond = _normalize_condition(match.group(1))
        gender = _normalize_gender(match.group(2))
        year = match.group(3)
        return cond, gender, year
    return None, None, None


def _parse_metadata_banner(
        lines: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extracts (condition, gender, year) from CDC Diabetes Atlas banner lines."""
    banner = ' '.join(lines[:5])
    cond = _normalize_condition(banner)
    gender = None
    for token in re.split(r'[,\s]+', banner):
        maybe_gender = _normalize_gender(token)
        if maybe_gender:
            gender = maybe_gender
            break
    if gender is None:
        gender = 'total'
    years = re.findall(r'\b((?:19|20)\d{2})\b', banner)
    year = years[-1] if years else None
    return cond, gender, year


def _format_number(val: float) -> str:
    """Formats a rounded float to up to 5 decimal places."""
    rounded = round(val, 5)
    if rounded == int(rounded):
        return f'{int(rounded)}'
    return f'{rounded:.5f}'.rstrip('0').rstrip('.')


def parse_raw_csv_file(filepath: str) -> List[List[str]]:
    """Parses a raw CDC Diabetes Atlas CSV file into output rows.

    Supports both:
    - Standard CDC GRASP/USDSS per-series CSVs (with 0-5 banner lines above a
      header containing `CountyFIPS`, `Percentage`, `Upper Limit`, plus
      optional `Year`, `Indicator`/`Condition`, `Gender`/`Sex` columns).
    - Pre-formatted Data Commons CSVs containing `observationAbout,observationDate,variableMeasured,value`.

    Args:
      filepath: Path to the CSV file.

    Returns:
      List of `[observationAbout, observationDate, variableMeasured, value, measurementMethod, observationPeriod]` rows.
    """
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        raw_lines = f.read().splitlines()

    if not raw_lines:
        return []

    first_non_empty = next((ln for ln in raw_lines if ln.strip()), '')
    first_cols = {c.strip() for c in next(csv.reader([first_non_empty]))}
    if {'variableMeasured', 'value'
       }.issubset(first_cols) and ('observationAbout' in first_cols or
                                   'location' in first_cols):
        rows: List[List[str]] = []
        reader = csv.DictReader(raw_lines)
        for row in reader:
            extracted = _extract_preprocessed_row(row)
            if extracted:
                rows.append(extracted)
        return rows

    file_cond, file_gender, file_year = _parse_filename_metadata(filepath)

    header_idx: Optional[int] = None
    header_cols: List[str] = []
    for idx, line in enumerate(raw_lines[:15]):
        if not line.strip():
            continue
        cols = [c.strip() for c in next(csv.reader([line]))]
        lower_cols = {c.lower() for c in cols}
        if ('countyfips' in lower_cols or 'county_fips' in lower_cols or
                'fips' in lower_cols) and ('percentage' in lower_cols or
                                           'median' in lower_cols or
                                           'estimate' in lower_cols):
            header_idx = idx
            header_cols = cols
            break

    if header_idx is None:
        logging.warning('Skipping %s: could not find CountyFIPS header row.',
                        filepath)
        return []

    banner_cond, banner_gender, banner_year = _parse_metadata_banner(
        raw_lines[:header_idx])
    default_cond = file_cond or banner_cond
    default_gender = file_gender or banner_gender or 'total'
    default_year = file_year or banner_year

    col_map = {c.strip().lower(): c for c in header_cols}
    fips_col = (col_map.get('countyfips') or col_map.get('county_fips') or
                col_map.get('fips'))
    pct_col = (col_map.get('percentage') or col_map.get('estimate') or
               col_map.get('median'))
    ul_col = None
    for candidate in (
            'upper limit',
            'upperlimit',
            'upper_limit',
            'ul',
            '95% ci upper limit',
    ):
        if candidate in col_map:
            ul_col = col_map[candidate]
            break
    if ul_col is None:
        for k, orig in col_map.items():
            if 'upper' in k:
                ul_col = orig
                break

    year_col = col_map.get('year') or col_map.get('timeperiod')
    cond_col = (col_map.get('condition') or col_map.get('indicator') or
                col_map.get('metric'))
    gender_col = col_map.get('gender') or col_map.get('sex')

    output_rows: List[List[str]] = []
    reader = csv.DictReader(raw_lines[header_idx:])
    for row in reader:
        if not row:
            continue
        raw_fips = str(row.get(fips_col, '') or '').strip()
        if not raw_fips or not re.match(r'^\d+$', raw_fips):
            continue
        fips_int = int(raw_fips)
        if fips_int <= 0 or fips_int % 1000 == 0:
            # Skip invalid or state-level summary FIPS codes (e.g., 01000).
            continue
        fips_5 = f'{fips_int:05d}'
        obs_about = f'dcid:geoId/{fips_5}'

        raw_pct = str(row.get(pct_col, '') or '').strip()
        raw_ul = str(row.get(ul_col, '') or '').strip() if ul_col else ''
        if (raw_pct.lower() in _SUPPRESSED_TOKENS or
                raw_ul.lower() in _SUPPRESSED_TOKENS):
            continue
        try:
            pct_val = float(raw_pct)
            ul_val = float(raw_ul)
        except ValueError:
            continue

        row_year = (str(row.get(year_col, '') or '').strip()
                    if year_col else default_year)
        if not row_year or not re.match(r'^\d{4}$', str(row_year)):
            continue

        row_cond = (_normalize_condition(str(row.get(cond_col, '') or ''))
                    if cond_col else default_cond)
        row_gender = (_normalize_gender(str(row.get(gender_col, '') or ''))
                      if gender_col else default_gender)
        if not row_cond or not row_gender:
            continue

        sv_key = (row_cond, row_gender)
        if sv_key not in STAT_VARS:
            continue
        sv_measured, sv_stderr = STAT_VARS[sv_key]

        std_error = (ul_val - pct_val) / 1.96
        pct_str = _format_number(pct_val)
        stderr_str = _format_number(std_error)

        output_rows.append([
            obs_about,
            str(row_year),
            sv_measured,
            pct_str,
            DEFAULT_MEASUREMENT_METHOD,
            DEFAULT_OBSERVATION_PERIOD,
        ])
        output_rows.append([
            obs_about,
            str(row_year),
            sv_stderr,
            stderr_str,
            DEFAULT_MEASUREMENT_METHOD,
            DEFAULT_OBSERVATION_PERIOD,
        ])

    return output_rows


def process_all(
    baseline_dir: str,
    gcs_baseline_prefix: str,
    raw_input_dir: str,
    output_dir: str,
    skip_baseline: bool = False,
    fetch_api: bool = False,
    min_api_year: int = 2022,
) -> str:
    """Runs the end-to-end preprocessing pipeline and writes `cdc_diabetes.csv`.

    Args:
      baseline_dir: Optional local path to 2004-2021 baseline CSVs.
      gcs_baseline_prefix: GCS prefix for 2004-2021 baseline CSVs.
      raw_input_dir: Directory containing 2022+ raw CSVs.
      output_dir: Output directory for `cdc_diabetes.csv` and `cdc_diabetes.tmcf`.
      skip_baseline: Whether to skip loading 2004-2021 baseline CSVs.
      fetch_api: Whether to fetch 2022+ data from the live CDC USDSS API.
      min_api_year: Minimum year to fetch from the CDC USDSS API.

    Returns:
      Path to the generated `cdc_diabetes.csv`.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Keyed by (observationDate, observationAbout, variableMeasured) -> full row.
    deduped_rows: Dict[Tuple[str, str, str], List[str]] = {}

    if not skip_baseline:
        if baseline_dir and os.path.isdir(baseline_dir):
            baseline_rows = _load_baseline_from_directory(baseline_dir)
        else:
            baseline_rows = _load_baseline_from_gcs(gcs_baseline_prefix)
        for row in baseline_rows:
            deduped_rows[(row[1], row[0], row[2])] = row

    if fetch_api:
        fetch_usdss_county_data(raw_input_dir=raw_input_dir,
                                min_year=min_api_year)

    raw_csv_files = sorted(glob.glob(os.path.join(raw_input_dir, '*.csv')))
    raw_row_count = 0
    for csv_path in raw_csv_files:
        parsed = parse_raw_csv_file(csv_path)
        raw_row_count += len(parsed)
        for row in parsed:
            deduped_rows[(row[1], row[0], row[2])] = row

    logging.info(
        'Processed %d raw rows from %d files in %s (total unique rows: %d)',
        raw_row_count,
        len(raw_csv_files),
        raw_input_dir,
        len(deduped_rows),
    )

    if not deduped_rows:
        raise RuntimeError('No observation rows produced; aborting.')

    sorted_keys = sorted(deduped_rows.keys())
    output_csv_path = os.path.join(output_dir, 'cdc_diabetes.csv')
    tmp_csv_path = f'{output_csv_path}.tmp'
    with open(tmp_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(OUTPUT_COLUMNS)
        for key in sorted_keys:
            writer.writerow(deduped_rows[key])
    os.replace(tmp_csv_path, output_csv_path)

    src_tmcf = os.path.join(_MODULE_DIR, 'cdc_diabetes.tmcf')
    dst_tmcf = os.path.join(output_dir, 'cdc_diabetes.tmcf')
    if os.path.exists(src_tmcf) and os.path.abspath(
            src_tmcf) != os.path.abspath(dst_tmcf):
        shutil.copyfile(src_tmcf, dst_tmcf)

    logging.info('Successfully wrote %d rows to %s', len(sorted_keys),
                 output_csv_path)
    return output_csv_path


def main(argv: List[str]) -> None:
    if len(argv) > 1:
        logging.fatal('Too many command-line arguments: %s', argv[1:])
    try:
        process_all(
            baseline_dir=FLAGS.baseline_dir,
            gcs_baseline_prefix=FLAGS.gcs_baseline_prefix,
            raw_input_dir=FLAGS.raw_input_dir,
            output_dir=FLAGS.output_dir,
            skip_baseline=FLAGS.skip_baseline,
            fetch_api=FLAGS.fetch_api,
            min_api_year=FLAGS.min_api_year,
        )
    except Exception as exc:  # pylint: disable=broad-except
        logging.fatal(
            'Failed to download and preprocess CDC Diabetes data: %s', exc)


if __name__ == '__main__':
    app.run(main)
