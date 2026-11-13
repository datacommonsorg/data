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
"""Downloads Sweden Census Category 2 (Health & Vital Statistics) from SCB PxWeb API.

Queries Statistics Sweden (SCB) across all 3 Health & Vital Statistics tables:
  1. Sub-National Deaths by Region, Age & Gender (1968-latest, 11 CSVs):
     - BE0101I/DodaFodelsearK (1968-2024)
     - BE0101I/DodaFodelsearKCKM (2025+)
     Aggregates individual ages into the 11 standard 10-year brackets + total,
     rolls up Swedish counties into NUTS3, NUTS2, and NUTS1, and writes the 11
     Death raw input CSVs.
  2. Municipal Total Fertility Rate by Gender (2000-latest, 1 CSV):
     - BE0101H/FruktsamhetSum (2000-2025+)
  3. Historical National Live Births by Gender & Total (1749-latest, 1 CSV):
     - BE0101G/BefUtvKon1749 (1749-2025+)
"""

import collections
import csv
import json
import os
import time

from absl import app
from absl import flags
from absl import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

FLAGS = flags.FLAGS

_DEFAULT_OUTPUT_DIR = os.path.join(_SCRIPT_DIR, 'input_files')

if 'output_dir' not in FLAGS:
    flags.DEFINE_string(
        'output_dir',
        _DEFAULT_OUTPUT_DIR,
        'Directory to save downloaded raw input CSV files.',
    )
if 'end_year' not in FLAGS:
    flags.DEFINE_integer(
        'end_year',
        None,
        'Optional end year. Defaults to None (automatically fetches up to the '
        'latest available year in SCB API, e.g. 2025+ in future runs).',
    )

# SCB PxWeb REST API endpoints for Category 2 (Health & Vital Statistics)
SCB_DEATHS_URL = (
    'https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101I/'
    'DodaFodelsearK')
SCB_DEATHS_CKM_URL = (
    'https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101I/'
    'DodaFodelsearKCKM')
SCB_FERTILITY_URL = (
    'https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101H/'
    'FruktsamhetSum')
SCB_LIVEBIRTH_URL = (
    'https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101G/'
    'BefUtvKon1749')

# Sex codes in SCB Deaths & Fertility tables
SEX_LEVELS: list[tuple[str, str]] = [
    ('1', 'män'),
    ('2', 'kvinnor'),
]

# 11 Age brackets used in Sweden Deaths by Age & Gender import
DEATH_AGE_GROUPS: list[tuple[str, list[str]]] = [
    ('0-4 år', [str(a) for a in range(5)]),
    ('5-14 år', [str(a) for a in range(5, 15)]),
    ('15-24 år', [str(a) for a in range(15, 25)]),
    ('25-34 år', [str(a) for a in range(25, 35)]),
    ('35-44 år', [str(a) for a in range(35, 45)]),
    ('45-54 år', [str(a) for a in range(45, 55)]),
    ('55-64 år', [str(a) for a in range(55, 65)]),
    ('65-74 år', [str(a) for a in range(65, 75)]),
    ('75-84 år', [str(a) for a in range(75, 85)]),
    ('85-94 år', [str(a) for a in range(85, 95)]),
    ('95+ år', [str(a) for a in range(95, 100)] + ['100+', '100+1']),
]
TOTAL_DEATH_AGE_LABEL = 'totalt ålder'

# Mapping from 2-digit SCB County code -> (NUTS3 label, NUTS2 label, NUTS1 label)
COUNTY_TO_NUTS: dict[str, tuple[str, str, str]] = {
    '01': ('SE110 Stockholms län', 'SE11 Stockholm', 'SE1 Östra Sverige'),
    '03': (
        'SE121 Uppsala län',
        'SE12 Östra Mellansverige',
        'SE1 Östra Sverige',
    ),
    '04': (
        'SE122 Södermanlands län',
        'SE12 Östra Mellansverige',
        'SE1 Östra Sverige',
    ),
    '05': (
        'SE123 Östergötlands län',
        'SE12 Östra Mellansverige',
        'SE1 Östra Sverige',
    ),
    '18': ('SE124 Örebro län', 'SE12 Östra Mellansverige', 'SE1 Östra Sverige'),
    '19': (
        'SE125 Västmanlands län',
        'SE12 Östra Mellansverige',
        'SE1 Östra Sverige',
    ),
    '06': (
        'SE211 Jönköpings län',
        'SE21 Småland med öarna',
        'SE2 Södra Sverige',
    ),
    '07': (
        'SE212 Kronobergs län',
        'SE21 Småland med öarna',
        'SE2 Södra Sverige',
    ),
    '08': ('SE213 Kalmar län', 'SE21 Småland med öarna', 'SE2 Södra Sverige'),
    '09': ('SE214 Gotlands län', 'SE21 Småland med öarna', 'SE2 Södra Sverige'),
    '10': ('SE221 Blekinge län', 'SE22 Sydsverige', 'SE2 Södra Sverige'),
    '12': ('SE224 Skåne län', 'SE22 Sydsverige', 'SE2 Södra Sverige'),
    '13': ('SE231 Hallands län', 'SE23 Västsverige', 'SE2 Södra Sverige'),
    '14': (
        'SE232 Västra Götalands län',
        'SE23 Västsverige',
        'SE2 Södra Sverige',
    ),
    '17': (
        'SE311 Värmlands län',
        'SE31 Norra Mellansverige',
        'SE3 Norra Sverige',
    ),
    '20': (
        'SE312 Dalarnas län',
        'SE31 Norra Mellansverige',
        'SE3 Norra Sverige',
    ),
    '21': (
        'SE313 Gävleborgs län',
        'SE31 Norra Mellansverige',
        'SE3 Norra Sverige',
    ),
    '22': (
        'SE321 Västernorrlands län',
        'SE32 Mellersta Norrland',
        'SE3 Norra Sverige',
    ),
    '23': (
        'SE322 Jämtlands län',
        'SE32 Mellersta Norrland',
        'SE3 Norra Sverige',
    ),
    '24': (
        'SE331 Västerbottens län',
        'SE33 Övre Norrland',
        'SE3 Norra Sverige',
    ),
    '25': (
        'SE332 Norrbottens län',
        'SE33 Övre Norrland',
        'SE3 Norra Sverige',
    ),
}

NUTS1_ORDER: list[str] = [
    'SE1 Östra Sverige',
    'SE2 Södra Sverige',
    'SE3 Norra Sverige',
]

NUTS2_ORDER: list[str] = [
    'SE11 Stockholm',
    'SE12 Östra Mellansverige',
    'SE21 Småland med öarna',
    'SE22 Sydsverige',
    'SE23 Västsverige',
    'SE31 Norra Mellansverige',
    'SE32 Mellersta Norrland',
    'SE33 Övre Norrland',
]

NUTS3_ORDER: list[str] = [
    'SE110 Stockholms län',
    'SE121 Uppsala län',
    'SE122 Södermanlands län',
    'SE123 Östergötlands län',
    'SE124 Örebro län',
    'SE125 Västmanlands län',
    'SE211 Jönköpings län',
    'SE212 Kronobergs län',
    'SE213 Kalmar län',
    'SE214 Gotlands län',
    'SE221 Blekinge län',
    'SE224 Skåne län',
    'SE231 Hallands län',
    'SE232 Västra Götalands län',
    'SE311 Värmlands län',
    'SE312 Dalarnas län',
    'SE313 Gävleborgs län',
    'SE321 Västernorrlands län',
    'SE322 Jämtlands län',
    'SE331 Västerbottens län',
    'SE332 Norrbottens län',
]


def _create_retry_session(retries: int = 5,
                          backoff_factor: float = 1.0) -> requests.Session:
    """Creates a requests.Session configured with standard Data Commons retry logic."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['HEAD', 'GET', 'POST', 'OPTIONS'],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def fetch_metadata(session: requests.Session, url: str) -> dict:
    """Fetches table metadata from SCB PxWeb API."""
    logging.info('Fetching metadata from %s', url)
    response = session.get(url, timeout=60)
    response.raise_for_status()
    return json.loads(response.content.decode('utf-8-sig'))


def post_scb_query(
    session: requests.Session,
    url: str,
    query_items: list[dict],
) -> list[dict]:
    """Executes a JSON-POST query against SCB PxWeb API using session retry."""
    payload = {
        'query': query_items,
        'response': {
            'format': 'json'
        },
    }
    query_summary = ', '.join(
        f"{item.get('code')}={len(item.get('selection', {}).get('values', []))}"
        for item in query_items)
    logging.info('POST %s [%s]', url, query_summary)
    resp = session.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    text = resp.content.decode('utf-8-sig')
    data = json.loads(text).get('data', [])
    if not data:
        raise RuntimeError(
            f'Empty data returned from {url} for query [{query_summary}]')
    logging.info('Received %d records from %s.', len(data), url)
    return data


def write_deaths_wide_csv(
    filepath: str,
    title: str,
    include_gender: bool,
    regions: list[str],
    age_labels: list[str],
    years: list[str],
    data_store: dict,
) -> int:
    """Writes a raw wide-format CSV matching the Sweden Deaths PVMaps."""
    if not data_store:
        raise RuntimeError(f'Cannot write {filepath} from an empty data_store.')
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    tmp_filepath = f'{filepath}.tmp'
    rows_written = 0
    with open(tmp_filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([title])
        writer.writerow([])
        if include_gender:
            writer.writerow(['region', 'ålder', 'kön'] + years)
        else:
            writer.writerow(['region', 'ålder'] + years)

        for reg in regions:
            for age_label in age_labels:
                if include_gender:
                    for sex_code, sex_text in SEX_LEVELS:
                        year_vals = []
                        for yr in years:
                            key = (reg, age_label, sex_code, yr)
                            if key not in data_store:
                                raise RuntimeError(
                                    f'Missing death observation for {key}')
                            year_vals.append(data_store[key])
                        writer.writerow([reg, age_label, sex_text] + year_vals)
                        rows_written += 1
                else:
                    year_vals = []
                    for yr in years:
                        key = (reg, age_label, 'TOT', yr)
                        if key not in data_store:
                            raise RuntimeError(
                                f'Missing total death observation for {key}')
                        year_vals.append(data_store[key])
                    writer.writerow([reg, age_label] + year_vals)
                    rows_written += 1

    if (rows_written == 0 or not os.path.exists(tmp_filepath) or
            os.path.getsize(tmp_filepath) == 0):
        raise RuntimeError(f'Generated empty CSV file: {tmp_filepath}')
    os.replace(tmp_filepath, filepath)
    logging.info('Wrote %d data rows to %s', rows_written, filepath)
    return rows_written


def download_deaths(session: requests.Session, out_dir: str) -> None:
    """Downloads 1968-latest Deaths data and writes all 11 Death CSVs."""
    meta_hist = fetch_metadata(session, SCB_DEATHS_URL)
    var_hist = {v['code']: v for v in meta_hist['variables']}

    hist_years = sorted(
        [
            y for y in var_hist['Tid']['values'] if int(y) >= 1968 and
            (FLAGS.end_year is None or int(y) <= FLAGS.end_year)
        ],
        key=int,
    )
    hist_contents = var_hist['ContentsCode']['values'][0]

    # Discover additional years (e.g. 2025+) in the companion CKM table
    meta_ckm = fetch_metadata(session, SCB_DEATHS_CKM_URL)
    var_ckm = {v['code']: v for v in meta_ckm['variables']}
    ckm_years = sorted(
        [
            y for y in var_ckm['Tid']['values']
            if y not in hist_years and int(y) >= 1968 and
            (FLAGS.end_year is None or int(y) <= FLAGS.end_year)
        ],
        key=int,
    )
    ckm_contents = (var_ckm['ContentsCode']['values'][0] if ckm_years and
                    var_ckm['ContentsCode']['values'] else None)

    all_years = sorted(hist_years + ckm_years, key=int)
    if not all_years:
        raise RuntimeError('No Deaths years discovered from SCB API.')
    logging.info(
        'Deaths years discovered: %s..%s (%d years: %d historical + %d CKM)',
        all_years[0],
        all_years[-1],
        len(all_years),
        len(hist_years),
        len(ckm_years),
    )

    # Separate 21 counties and 290 municipalities
    reg_values = var_hist['Region']['values']
    reg_texts = var_hist['Region']['valueTexts']
    county_codes: list[str] = []
    muni_codes: list[str] = []
    muni_code_to_label: dict[str, str] = {}
    for code, text in zip(reg_values, reg_texts):
        if code == '00':
            continue
        elif len(code) == 2 and code in COUNTY_TO_NUTS:
            county_codes.append(code)
        elif len(code) == 4:
            muni_codes.append(code)
            muni_code_to_label[code] = f'{code} {text}'

    age_to_bracket: dict[str, str] = {}
    for bracket_label, ages in DEATH_AGE_GROUPS:
        for a in ages:
            age_to_bracket[a] = bracket_label

    hist_ages = [str(a) for a in range(100)] + ['100+', 'tot']
    ckm_ages = [str(a) for a in range(100)] + ['100+1', 'TotSA']
    sex_codes = [code for code, _ in SEX_LEVELS]

    # Data store: (region_label, age_label, sex_code_or_TOT, year) -> int count
    data_store: dict[tuple[str, str, str, str],
                     int] = collections.defaultdict(int)

    # 1A. Fetch County-level data from DodaFodelsearK (1968-2024) in 15-year chunks
    year_chunk_size = 15
    for i in range(0, len(hist_years), year_chunk_size):
        yr_chunk = hist_years[i:i + year_chunk_size]
        rows = post_scb_query(
            session,
            SCB_DEATHS_URL,
            [
                {
                    'code': 'Region',
                    'selection': {
                        'filter': 'item',
                        'values': county_codes
                    },
                },
                {
                    'code': 'Alder',
                    'selection': {
                        'filter': 'item',
                        'values': hist_ages
                    },
                },
                {
                    'code': 'Kon',
                    'selection': {
                        'filter': 'item',
                        'values': sex_codes
                    },
                },
                {
                    'code': 'ContentsCode',
                    'selection': {
                        'filter': 'item',
                        'values': [hist_contents]
                    },
                },
                {
                    'code': 'Tid',
                    'selection': {
                        'filter': 'item',
                        'values': yr_chunk
                    },
                },
            ],
        )
        for row in rows:
            reg_code, age_code, sex_code, yr = row['key']
            val_str = row['values'][0]
            # Legacy CNS parity: SCB returns '..' when an age/region cell was
            # not yet established; convert '..'/'.'/'-'/'' to 0 to match
            # historical CNS raw input tables.
            val = int(val_str) if val_str not in ('..', '.', '-', '') else 0
            nuts3_label, nuts2_label, nuts1_label = COUNTY_TO_NUTS[reg_code]
            target_age = (TOTAL_DEATH_AGE_LABEL
                          if age_code == 'tot' else age_to_bracket[age_code])
            for nuts_label in (nuts1_label, nuts2_label, nuts3_label):
                data_store[(nuts_label, target_age, sex_code, yr)] += val
                data_store[(nuts_label, target_age, 'TOT', yr)] += val
        time.sleep(1.2)

    # 1B. Fetch County-level data from DodaFodelsearKCKM (2025+)
    if ckm_years and ckm_contents:
        rows = post_scb_query(
            session,
            SCB_DEATHS_CKM_URL,
            [
                {
                    'code': 'Region',
                    'selection': {
                        'filter': 'item',
                        'values': county_codes
                    },
                },
                {
                    'code': 'Alder',
                    'selection': {
                        'filter': 'item',
                        'values': ckm_ages
                    },
                },
                {
                    'code': 'Kon',
                    'selection': {
                        'filter': 'item',
                        'values': sex_codes
                    },
                },
                {
                    'code': 'ContentsCode',
                    'selection': {
                        'filter': 'item',
                        'values': [ckm_contents]
                    },
                },
                {
                    'code': 'Tid',
                    'selection': {
                        'filter': 'item',
                        'values': ckm_years
                    },
                },
            ],
        )
        for row in rows:
            reg_code, age_code, sex_code, yr = row['key']
            val_str = row['values'][0]
            # Legacy CNS parity: convert SCB missing markers ('..', '.', '-', '') to 0.
            val = int(val_str) if val_str not in ('..', '.', '-', '') else 0
            nuts3_label, nuts2_label, nuts1_label = COUNTY_TO_NUTS[reg_code]
            target_age = (TOTAL_DEATH_AGE_LABEL
                          if age_code == 'TotSA' else age_to_bracket[age_code])
            for nuts_label in (nuts1_label, nuts2_label, nuts3_label):
                data_store[(nuts_label, target_age, sex_code, yr)] += val
                data_store[(nuts_label, target_age, 'TOT', yr)] += val
        time.sleep(1.2)

    # 2A. Fetch Municipality-level total-age data from DodaFodelsearK (1968-2024)
    if hist_years:
        rows = post_scb_query(
            session,
            SCB_DEATHS_URL,
            [
                {
                    'code': 'Region',
                    'selection': {
                        'filter': 'item',
                        'values': muni_codes
                    },
                },
                {
                    'code': 'Alder',
                    'selection': {
                        'filter': 'item',
                        'values': ['tot']
                    },
                },
                {
                    'code': 'Kon',
                    'selection': {
                        'filter': 'item',
                        'values': sex_codes
                    },
                },
                {
                    'code': 'ContentsCode',
                    'selection': {
                        'filter': 'item',
                        'values': [hist_contents]
                    },
                },
                {
                    'code': 'Tid',
                    'selection': {
                        'filter': 'item',
                        'values': hist_years
                    },
                },
            ],
        )
        for row in rows:
            reg_code, _, sex_code, yr = row['key']
            val_str = row['values'][0]
            # Legacy CNS parity: SCB returns '..' for municipalities in years
            # prior to their municipal split (e.g., Nykvarn before 1999,
            # Knivsta before 2003). Convert '..' to 0 to match legacy CNS inputs.
            val = int(val_str) if val_str not in ('..', '.', '-', '') else 0
            muni_label = muni_code_to_label[reg_code]
            data_store[(muni_label, TOTAL_DEATH_AGE_LABEL, sex_code, yr)] += val
            data_store[(muni_label, TOTAL_DEATH_AGE_LABEL, 'TOT', yr)] += val
        time.sleep(1.2)

    # 2B. Fetch Municipality-level total-age data from DodaFodelsearKCKM (2025+)
    if ckm_years and ckm_contents:
        rows = post_scb_query(
            session,
            SCB_DEATHS_CKM_URL,
            [
                {
                    'code': 'Region',
                    'selection': {
                        'filter': 'item',
                        'values': muni_codes
                    },
                },
                {
                    'code': 'Alder',
                    'selection': {
                        'filter': 'item',
                        'values': ['TotSA']
                    },
                },
                {
                    'code': 'Kon',
                    'selection': {
                        'filter': 'item',
                        'values': sex_codes
                    },
                },
                {
                    'code': 'ContentsCode',
                    'selection': {
                        'filter': 'item',
                        'values': [ckm_contents]
                    },
                },
                {
                    'code': 'Tid',
                    'selection': {
                        'filter': 'item',
                        'values': ckm_years
                    },
                },
            ],
        )
        for row in rows:
            reg_code, _, sex_code, yr = row['key']
            val_str = row['values'][0]
            # Legacy CNS parity: convert SCB missing markers ('..', '.', '-', '') to 0.
            val = int(val_str) if val_str not in ('..', '.', '-', '') else 0
            muni_label = muni_code_to_label[reg_code]
            data_store[(muni_label, TOTAL_DEATH_AGE_LABEL, sex_code, yr)] += val
            data_store[(muni_label, TOTAL_DEATH_AGE_LABEL, 'TOT', yr)] += val
        time.sleep(1.2)

    muni_labels_sorted = [muni_code_to_label[c] for c in muni_codes]
    age_bracket_labels = [label for label, _ in DEATH_AGE_GROUPS]

    title_no_sex = 'Döda efter region, ålder och år'
    title_with_sex = 'Döda efter region, ålder, kön och år'

    # Write Group 1: Total Deaths (4 files)
    write_deaths_wide_csv(
        os.path.join(out_dir, 'Death_NUTS1.csv'),
        title_no_sex,
        False,
        NUTS1_ORDER,
        [TOTAL_DEATH_AGE_LABEL],
        all_years,
        data_store,
    )
    write_deaths_wide_csv(
        os.path.join(out_dir, 'Death_NUTS2.csv'),
        title_no_sex,
        False,
        NUTS2_ORDER,
        [TOTAL_DEATH_AGE_LABEL],
        all_years,
        data_store,
    )
    write_deaths_wide_csv(
        os.path.join(out_dir, 'Death_NUTS3.csv'),
        title_no_sex,
        False,
        NUTS3_ORDER,
        [TOTAL_DEATH_AGE_LABEL],
        all_years,
        data_store,
    )
    write_deaths_wide_csv(
        os.path.join(out_dir, 'Death_Muncipality.csv'),
        title_no_sex,
        False,
        muni_labels_sorted,
        [TOTAL_DEATH_AGE_LABEL],
        all_years,
        data_store,
    )

    # Write Group 2: Deaths by Gender (4 files)
    write_deaths_wide_csv(
        os.path.join(out_dir, 'Death_gender_NUTS1.csv'),
        title_with_sex,
        True,
        NUTS1_ORDER,
        [TOTAL_DEATH_AGE_LABEL],
        all_years,
        data_store,
    )
    write_deaths_wide_csv(
        os.path.join(out_dir, 'Death_gender_NUTS2.csv'),
        title_with_sex,
        True,
        NUTS2_ORDER,
        [TOTAL_DEATH_AGE_LABEL],
        all_years,
        data_store,
    )
    write_deaths_wide_csv(
        os.path.join(out_dir, 'Death_gender_NUTS3.csv'),
        title_with_sex,
        True,
        NUTS3_ORDER,
        [TOTAL_DEATH_AGE_LABEL],
        all_years,
        data_store,
    )
    write_deaths_wide_csv(
        os.path.join(out_dir, 'Death_gender_Muncipality.csv'),
        title_with_sex,
        True,
        muni_labels_sorted,
        [TOTAL_DEATH_AGE_LABEL],
        all_years,
        data_store,
    )

    # Write Group 3: Deaths by Age & Gender (3 files)
    write_deaths_wide_csv(
        os.path.join(out_dir, 'Death_age_gender_NUTS1.csv'),
        title_with_sex,
        True,
        NUTS1_ORDER,
        age_bracket_labels,
        all_years,
        data_store,
    )
    write_deaths_wide_csv(
        os.path.join(out_dir, 'Death_age_gender_NUTS2.csv'),
        title_with_sex,
        True,
        NUTS2_ORDER,
        age_bracket_labels,
        all_years,
        data_store,
    )
    write_deaths_wide_csv(
        os.path.join(out_dir, 'Death_age_gender_NUTS3.csv'),
        title_with_sex,
        True,
        NUTS3_ORDER,
        age_bracket_labels,
        all_years,
        data_store,
    )


def _format_fertility_val(val_str: str) -> str:
    """Formats SCB fertility float string matching historical CNS representation."""
    val_str = val_str.strip()
    if val_str in ('..', '.', '-', ''):
        return '..'
    try:
        fval = float(val_str)
        return f'{fval:g}'
    except ValueError:
        return val_str


def download_fertility(session: requests.Session, out_dir: str) -> None:
    """Downloads 2000-latest Municipal Fertility Rate and writes 1 raw CSV."""
    meta = fetch_metadata(session, SCB_FERTILITY_URL)
    var_map = {v['code']: v for v in meta['variables']}
    all_years = sorted(
        [
            y for y in var_map['Tid']['values'] if int(y) >= 2000 and
            (FLAGS.end_year is None or int(y) <= FLAGS.end_year)
        ],
        key=int,
    )
    if not all_years:
        raise RuntimeError('No Fertility years discovered from SCB API.')
    contents_code = var_map['ContentsCode']['values'][0]
    muni_codes = [c for c in var_map['Region']['values'] if len(c) == 4]
    muni_code_to_label = {
        c: f'{c} {t}'
        for c, t in zip(var_map['Region']['values'], var_map['Region']
                        ['valueTexts'])
        if len(c) == 4
    }
    sex_codes = [code for code, _ in SEX_LEVELS]

    rows = post_scb_query(
        session,
        SCB_FERTILITY_URL,
        [
            {
                'code': 'Region',
                'selection': {
                    'filter': 'item',
                    'values': muni_codes
                },
            },
            {
                'code': 'Kon',
                'selection': {
                    'filter': 'item',
                    'values': sex_codes
                },
            },
            {
                'code': 'ContentsCode',
                'selection': {
                    'filter': 'item',
                    'values': [contents_code]
                },
            },
            {
                'code': 'Tid',
                'selection': {
                    'filter': 'item',
                    'values': all_years
                },
            },
        ],
    )
    store: dict[tuple[str, str, str], str] = {}
    for row in rows:
        reg_code, sex_code, yr = row['key']
        muni_label = muni_code_to_label[reg_code]
        store[(muni_label, sex_code,
               yr)] = _format_fertility_val(row['values'][0])
    time.sleep(1.2)

    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, 'FertilityRate_gender_Muncipality.csv')
    tmp_filepath = f'{filepath}.tmp'
    rows_written = 0
    with open(tmp_filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Summerad fruktsamhet efter region, kön och år'])
        writer.writerow([])
        writer.writerow(['region', 'kön'] + all_years)
        for c in muni_codes:
            reg_label = muni_code_to_label[c]
            for sex_code, sex_text in SEX_LEVELS:
                vals = [
                    store.get((reg_label, sex_code, yr), '..')
                    for yr in all_years
                ]
                writer.writerow([reg_label, sex_text] + vals)
                rows_written += 1

    if (rows_written == 0 or not os.path.exists(tmp_filepath) or
            os.path.getsize(tmp_filepath) == 0):
        raise RuntimeError(f'Generated empty CSV file: {tmp_filepath}')
    os.replace(tmp_filepath, filepath)
    logging.info('Wrote %d data rows to %s', rows_written, filepath)


def download_livebirths(session: requests.Session, out_dir: str) -> None:
    """Downloads 1749-latest National Live Births and writes 1 raw CSV."""
    meta = fetch_metadata(session, SCB_LIVEBIRTH_URL)
    var_map = {v['code']: v for v in meta['variables']}
    all_years = sorted(
        [
            y for y in var_map['Tid']['values'] if int(y) >= 1749 and
            (FLAGS.end_year is None or int(y) <= FLAGS.end_year)
        ],
        key=int,
    )
    if not all_years:
        raise RuntimeError('No LiveBirth years discovered from SCB API.')
    # '0000001H' is 'Födda' (Live Births) in BE0101G/BefUtvKon1749
    rows = post_scb_query(
        session,
        SCB_LIVEBIRTH_URL,
        [
            {
                'code': 'Kon',
                'selection': {
                    'filter': 'item',
                    'values': ['1+2', '1', '2']
                },
            },
            {
                'code': 'ContentsCode',
                'selection': {
                    'filter': 'item',
                    'values': ['0000001H']
                },
            },
            {
                'code': 'Tid',
                'selection': {
                    'filter': 'item',
                    'values': all_years
                },
            },
        ],
    )
    store: dict[tuple[str, str], str] = {}
    for row in rows:
        sex_code, yr = row['key']
        store[(sex_code, yr)] = row['values'][0]

    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, 'LiveBirth_gender_total_country.csv')
    tmp_filepath = f'{filepath}.tmp'
    rows_written = 0
    sex_rows = [
        ('1+2', 'båda könen'),
        ('1', 'pojkar'),
        ('2', 'flickor'),
    ]
    with open(tmp_filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Levande födda  efter kön och år'])
        writer.writerow([])
        writer.writerow(['kön'] + all_years)
        for sex_code, sex_label in sex_rows:
            vals: list[str] = []
            for yr in all_years:
                if (sex_code, yr) not in store:
                    raise RuntimeError(
                        f'Missing LiveBirth observation for sex={sex_code}, year={yr}'
                    )
                vals.append(store[(sex_code, yr)])
            writer.writerow([sex_label] + vals)
            rows_written += 1

    if (rows_written == 0 or not os.path.exists(tmp_filepath) or
            os.path.getsize(tmp_filepath) == 0):
        raise RuntimeError(f'Generated empty CSV file: {tmp_filepath}')
    os.replace(tmp_filepath, filepath)
    logging.info('Wrote %d data rows to %s', rows_written, filepath)


def main(argv):
    del argv
    out_dir = FLAGS.output_dir
    os.makedirs(out_dir, exist_ok=True)
    for existing_file in os.listdir(out_dir):
        if existing_file.endswith(('.csv', '.tmp')):
            os.remove(os.path.join(out_dir, existing_file))

    session = _create_retry_session()
    download_deaths(session, out_dir)
    download_fertility(session, out_dir)
    download_livebirths(session, out_dir)
    logging.info(
        'Successfully generated all 13 Sweden Health & Vital Statistics raw CSVs'
        ' in %s',
        out_dir,
    )


if __name__ == '__main__':
    app.run(main)
