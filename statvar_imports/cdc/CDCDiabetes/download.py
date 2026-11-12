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
"""Downloads CDC US Diabetes Surveillance System (USDSS) county data."""

import csv
import math
import os
import re
import shutil
import subprocess
import sys
from typing import Any

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(_CODEDIR, '../../util/'))
sys.path.insert(1, os.path.join(_CODEDIR, '../../../util/'))

from absl import app
from absl import flags
from absl import logging
import file_util
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'output_dir',
    os.path.join(_CODEDIR, 'input_files'),
    'Directory path to save the downloaded input CSV file.',
)
flags.DEFINE_string(
    'historical_gcs_dir',
    'gs://unresolved_mcf/cdc/diabetes/historical',
    'GCS directory containing the consolidated 2004-2021 historical CSV file.',
)
flags.DEFINE_string(
    'historical_output_dir',
    os.path.join(_CODEDIR, 'output_files'),
    'Directory path to copy the historical CSV and TMCF files into.',
)
flags.DEFINE_string(
    'input_filename',
    'cdc_diabetes.csv',
    'Filename for the downloaded CDC Diabetes input CSV table.',
)
flags.DEFINE_integer(
    'start_year',
    2022,
    'Minimum observation year to include in the downloaded CSV file.',
)

USDSS_BASE_URL = 'https://usdss.cdc.gov'
USDSS_REFERER = 'https://usdss.cdc.gov/diabetes/surveillance.html'
USDSS_YEARS_URL = ('https://usdss.cdc.gov/diabetes/data/surveillance/'
                   'SurveillanceIndicatorsYearsList_Counties.json')
USDSS_COUNTY_DATA_URL = (
    'https://usdss.cdc.gov/webapi/Diabetes/AllCountiesDataOneYear')
USDSS_DEFAULT_INIT_APP_DATA = (
    'https://usdss.cdc.gov/diabetes/'
    'InitAppData_a76d04a7-0f44-4f44-9147-3be5354c46ba.json')

CONDITION_TO_INDICATOR_ID: dict[str, int] = {
    'diabetes': 151,  # Diagnosed Diabetes
    'obesity': 201,  # Obesity
    'inactivity': 202,  # Leisure-Time Physical Inactivity
}

SEX_GROUP_TO_ID: dict[str, int] = {
    'total': 591,
    'male': 592,
    'female': 593,
}

# Fixed stratification IDs for County Age-Adjusted Percentage (Adults 20+ Years).
USDSS_RACE_ID = 551  # Total
USDSS_AGE_ID = 635  # Age-Adjusted
USDSS_DATA_TYPE_ID = 1113  # Percentage
USDSS_EDUCATION_ID = 671  # Total
USDSS_MISC_ID = 701  # Total
USDSS_DATASET_ID = 1044  # Adults Aged 20+ Years
USDSS_PUBLISHED_STATUS = 100  # Published (not suppressed/missing)

SUPPRESSED_TOKENS: frozenset[str] = frozenset({
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

HISTORICAL_CSVS: tuple[str, ...] = ('cdc_diabetes_historical_2004_2021.csv',)

METRIC_COLUMNS: tuple[str, ...] = (
    'diabetes_total_pct',
    'diabetes_total_stderr',
    'diabetes_male_pct',
    'diabetes_male_stderr',
    'diabetes_female_pct',
    'diabetes_female_stderr',
    'obesity_total_pct',
    'obesity_total_stderr',
    'obesity_male_pct',
    'obesity_male_stderr',
    'obesity_female_pct',
    'obesity_female_stderr',
    'inactivity_total_pct',
    'inactivity_total_stderr',
    'inactivity_male_pct',
    'inactivity_male_stderr',
    'inactivity_female_pct',
    'inactivity_female_stderr',
)

INPUT_CSV_HEADERS: list[str] = [
    'observationAbout',
    'observationDate',
    *METRIC_COLUMNS,
]

COMMON_TMCF_CONTENT = ('Node: E:cdc_diabetes->E0\n'
                       'typeOf: dcs:StatVarObservation\n'
                       'observationAbout: C:cdc_diabetes->observationAbout\n'
                       'observationDate: C:cdc_diabetes->observationDate\n'
                       'variableMeasured: C:cdc_diabetes->variableMeasured\n'
                       'value: C:cdc_diabetes->value\n'
                       'measurementMethod: C:cdc_diabetes->measurementMethod\n'
                       'observationPeriod: C:cdc_diabetes->observationPeriod\n')


def format_number(val: float) -> str:
    """Formats a finite float rounded to up to 5 decimal places."""
    if not math.isfinite(val):
        return ''
    rounded = round(val, 5)
    if rounded == int(rounded):
        return f'{int(rounded)}'
    return f'{rounded:.5f}'.rstrip('0').rstrip('.')


def parse_estimate_and_stderr(raw_pct: Any,
                              raw_ul: Any) -> tuple[str, str] | None:
    """Validates percentage & 95% CI upper limit and computes (pct, std_error).

    Returns None if suppressed, non-finite, out of [0, 100], or ul < pct.
    """
    if raw_pct is None or raw_ul is None:
        return None
    pct_text = str(raw_pct).strip()
    ul_text = str(raw_ul).strip()
    if (pct_text.lower() in SUPPRESSED_TOKENS or
            ul_text.lower() in SUPPRESSED_TOKENS):
        return None
    try:
        pct_val = float(pct_text)
        ul_val = float(ul_text)
    except ValueError:
        return None
    if not (math.isfinite(pct_val) and math.isfinite(ul_val)):
        return None
    if not (0.0 <= pct_val <= 100.0) or ul_val < pct_val:
        return None
    std_error = (ul_val - pct_val) / 1.96
    pct_str = format_number(pct_val)
    stderr_str = format_number(std_error)
    if not pct_str or not stderr_str:
        return None
    return pct_str, stderr_str


def create_http_session() -> requests.Session:
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
        'Referer': USDSS_REFERER,
        'Accept': 'application/json, text/plain, */*',
    })
    return session


def discover_init_app_data_url(session: requests.Session) -> str:
    """Discovers the current InitAppData_*.json URL from the USDSS web app."""
    try:
        resp = session.get(USDSS_REFERER, timeout=30)
        resp.raise_for_status()
        bundle_match = re.search(
            r'([A-Za-z0-9_/\-]*surveillance_entry\.[a-f0-9]+\.app\.js)',
            resp.text,
        )
        if bundle_match:
            rel_path = bundle_match.group(1).lstrip('/')
            if not rel_path.startswith('diabetes/'):
                rel_path = f'diabetes/{rel_path}'
            bundle_url = f'{USDSS_BASE_URL}/{rel_path}'
            bundle_resp = session.get(bundle_url, timeout=30)
            if bundle_resp.ok:
                init_match = re.search(r'(InitAppData_[a-f0-9\-]+\.json)',
                                       bundle_resp.text)
                if init_match:
                    return f'{USDSS_BASE_URL}/diabetes/{init_match.group(1)}'
                logging.warning('InitAppData pattern not found in bundle JS.')
            else:
                logging.warning(
                    'Failed to fetch bundle JS from %s: %s',
                    bundle_url,
                    bundle_resp.status_code,
                )
        else:
            logging.warning(
                'surveillance_entry JS bundle match not found in referer HTML.')
    except requests.RequestException as exc:
        logging.warning(
            'Falling back to default InitAppData URL after discovery warning: %s',
            exc,
        )
    return USDSS_DEFAULT_INIT_APP_DATA


def parse_counties_by_geoid(init_data: dict[str, Any]) -> dict[int, str]:
    """Maps USDSS internal county GeoID (CDC) to 5-digit county FIPS code."""
    counties_by_geoid: dict[int, str] = {}
    for county in init_data.get('counties_list', []):
        if not isinstance(county, dict):
            continue
        geoid_raw = county.get('CDC')
        fips_raw = str(county.get('CC') or '').strip()
        if geoid_raw is None or not str(geoid_raw).strip().isdigit():
            continue
        if not fips_raw or not re.match(r'^\d+$', fips_raw):
            continue
        fips_int = int(fips_raw)
        if fips_int <= 0 or fips_int % 1000 == 0:
            continue
        counties_by_geoid[int(geoid_raw)] = f'{fips_int:05d}'
    return counties_by_geoid


def parse_indicator_years(
    years_list: list[dict[str, Any]],
    start_year: int = 2022,
) -> dict[int, list[tuple[int, int]]]:
    """Maps IndicatorID to sorted list of (year_int, year_id) >= start_year."""
    indicator_years: dict[int, list[tuple[int, int]]] = {}
    for entry in years_list:
        if not isinstance(entry, dict):
            continue
        ind_raw = entry.get('IndicatorID')
        if ind_raw is None or not str(ind_raw).strip().isdigit():
            continue
        ind_id = int(ind_raw)
        valid_years: list[tuple[int, int]] = []
        for yr_obj in entry.get('YearsList', []):
            if not isinstance(yr_obj, dict):
                continue
            yr_str = str(yr_obj.get('Year') or '').strip()
            yr_id = yr_obj.get('YearID')
            if (yr_str.isdigit() and yr_id is not None and
                    str(yr_id).strip().isdigit()):
                yr_int = int(yr_str)
                if yr_int >= start_year:
                    valid_years.append((yr_int, int(yr_id)))
        valid_years.sort()
        indicator_years[ind_id] = valid_years
    return indicator_years


def fetch_usdss_metrics(
    start_year: int = 2022,
    session: requests.Session | None = None,
) -> dict[tuple[str, str], dict[str, str]]:
    """Fetches county estimates from CDC USDSS API for all years >= start_year.

    Returns:
      Dictionary mapping (fips_5digit, year_str) -> {metric_column: value_str}.
    """
    own_session = session is None
    if session is None:
        session = create_http_session()

    try:
        init_url = discover_init_app_data_url(session)
        logging.info('GET %s (fetching CDC USDSS county metadata)', init_url)
        init_resp = session.get(init_url, timeout=60)
        init_resp.raise_for_status()
        init_data = init_resp.json()

        counties_by_geoid = parse_counties_by_geoid(init_data)
        if not counties_by_geoid:
            raise RuntimeError(
                f'No counties found in CDC USDSS metadata at {init_url}')

        logging.info(
            'GET %s (fetching CDC USDSS available county years)',
            USDSS_YEARS_URL,
        )
        years_resp = session.get(USDSS_YEARS_URL, timeout=60)
        years_resp.raise_for_status()
        years_list = years_resp.json()

        indicator_years = parse_indicator_years(years_list,
                                                start_year=start_year)
        records_by_place_year: dict[tuple[str, str], dict[str, str]] = {}

        for condition, ind_id in sorted(CONDITION_TO_INDICATOR_ID.items()):
            years_for_ind = indicator_years.get(ind_id, [])
            if not years_for_ind:
                raise RuntimeError(
                    f'No years >= {start_year} found for condition={condition} '
                    f'(IndicatorID={ind_id})')
            for yr_int, yr_id in years_for_ind:
                year_str = str(yr_int)
                for sex_group, sex_id in sorted(SEX_GROUP_TO_ID.items()):
                    payload = {
                        'IndicatorID': ind_id,
                        'RaceID': USDSS_RACE_ID,
                        'SexID': sex_id,
                        'AgeID': USDSS_AGE_ID,
                        'DataTypeID': USDSS_DATA_TYPE_ID,
                        'EducationID': USDSS_EDUCATION_ID,
                        'MiscID': USDSS_MISC_ID,
                        'DatasetID': USDSS_DATASET_ID,
                        'YearID': yr_id,
                    }
                    logging.info(
                        'POST %s payload=%s (condition=%s, sex_group=%s, year=%d)',
                        USDSS_COUNTY_DATA_URL,
                        payload,
                        condition,
                        sex_group,
                        yr_int,
                    )
                    resp = session.post(USDSS_COUNTY_DATA_URL,
                                        json=payload,
                                        timeout=60)
                    resp.raise_for_status()
                    data = resp.json()
                    map_data = (data.get('MapData', []) if isinstance(
                        data, dict) else [])
                    if not map_data:
                        raise RuntimeError(
                            'Empty MapData from CDC USDSS API for '
                            f'condition={condition}, sex_group={sex_group}, '
                            f'year={yr_int}')

                    pct_col = f'{condition}_{sex_group}_pct'
                    stderr_col = f'{condition}_{sex_group}_stderr'
                    published_count = 0

                    for item in map_data:
                        if not isinstance(item, dict):
                            continue
                        geoid_raw = item.get('GeoID')
                        if (geoid_raw is None or
                                not str(geoid_raw).strip().isdigit()):
                            continue
                        geoid_int = int(geoid_raw)
                        fips = counties_by_geoid.get(geoid_int)
                        if not fips:
                            continue
                        if item.get('Sup') != USDSS_PUBLISHED_STATUS:
                            continue
                        parsed = parse_estimate_and_stderr(
                            item.get('Est'), item.get('UL'))
                        if parsed is None:
                            continue
                        pct_str, stderr_str = parsed
                        cell = records_by_place_year.setdefault(
                            (fips, year_str), {})
                        cell[pct_col] = pct_str
                        cell[stderr_col] = stderr_str
                        published_count += 1

                    if published_count == 0:
                        raise RuntimeError(
                            'Zero valid published county estimates returned from '
                            f'CDC USDSS API for condition={condition}, '
                            f'sex_group={sex_group}, year={yr_int}')
                    logging.info(
                        'Fetched %d published county records for %s / %s / %d',
                        published_count,
                        condition,
                        sex_group,
                        yr_int,
                    )

        return records_by_place_year
    finally:
        if own_session:
            session.close()


def write_input_csv(
    output_path: str,
    records_by_place_year: dict[tuple[str, str], dict[str, str]],
) -> int:
    """Writes input_files/cdc_diabetes.csv matching cdc_diabetes_pvmap.csv."""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    tmp_path = f'{output_path}.tmp'
    row_count = 0
    with open(tmp_path, 'w', newline='', encoding='utf-8') as fp:
        writer = csv.writer(fp, lineterminator='\n')
        writer.writerow(INPUT_CSV_HEADERS)
        for fips, year_str in sorted(records_by_place_year.keys()):
            metrics = records_by_place_year[(fips, year_str)]
            if not any(metrics.get(col, '') for col in METRIC_COLUMNS):
                continue
            row = [
                fips,
                year_str,
                *[metrics.get(col, '') for col in METRIC_COLUMNS],
            ]
            writer.writerow(row)
            row_count += 1
    os.replace(tmp_path, output_path)
    logging.info('Wrote %d county-year rows to %s', row_count, output_path)
    return row_count


def download_cdc_diabetes_data(
    output_dir: str,
    input_filename: str = 'cdc_diabetes.csv',
    start_year: int = 2022,
    session: requests.Session | None = None,
) -> str:
    """Downloads CDC USDSS county estimates and writes the input CSV file."""
    records_by_place_year = fetch_usdss_metrics(start_year=start_year,
                                                session=session)
    output_path = os.path.join(output_dir, input_filename)
    row_count = write_input_csv(output_path, records_by_place_year)
    if row_count == 0:
        raise RuntimeError('No county rows written to input CSV; aborting.')
    return output_path


def copy_historical_files_from_gcs(
    historical_gcs_dir: str,
    historical_output_dir: str,
) -> None:
    """Copies consolidated historical CSV from GCS and writes common_tmcf.tmcf into output_files."""
    if not historical_gcs_dir:
        return
    os.makedirs(historical_output_dir, exist_ok=True)
    dst_tmcf = os.path.join(historical_output_dir, 'common_tmcf.tmcf')
    with open(dst_tmcf, mode='w', encoding='utf-8') as tmcf_f:
        tmcf_f.write(COMMON_TMCF_CONTENT)
    logging.info('Wrote historical TMCF to %s', dst_tmcf)

    gcs_base = historical_gcs_dir.rstrip('/')
    for fname in HISTORICAL_CSVS:
        src_gcs = f'{gcs_base}/{fname}'
        dst_local = os.path.join(historical_output_dir, fname)
        logging.info('Copying historical CSV from %s to %s', src_gcs, dst_local)
        try:
            file_util.file_copy(src_gcs, dst_local)
        except Exception as exc:  # pylint: disable=broad-except
            local_fallback = os.path.join(_CODEDIR, 'historical', fname)
            if os.path.exists(local_fallback) and os.path.getsize(
                    local_fallback) > 0:
                logging.warning(
                    'file_util.file_copy(%s) failed (%s); copying from local %s',
                    src_gcs,
                    exc,
                    local_fallback,
                )
                shutil.copyfile(local_fallback, dst_local)
            else:
                logging.warning(
                    'file_util.file_copy(%s) failed (%s); falling back to gsutil cp',
                    src_gcs,
                    exc,
                )
                subprocess.run(['gsutil', 'cp', src_gcs, dst_local], check=True)


def main(_) -> None:
    logging.set_verbosity(logging.INFO)
    copy_historical_files_from_gcs(
        historical_gcs_dir=_FLAGS.historical_gcs_dir,
        historical_output_dir=_FLAGS.historical_output_dir,
    )
    download_cdc_diabetes_data(
        output_dir=_FLAGS.output_dir,
        input_filename=_FLAGS.input_filename,
        start_year=_FLAGS.start_year,
    )


if __name__ == '__main__':
    app.run(main)
