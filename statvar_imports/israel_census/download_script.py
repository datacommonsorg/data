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
from collections import defaultdict
from concurrent import futures
import csv
import io
import math
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
CBS_SERIES_POPULATION_PATH_ID = '2,1,1,1'
CBS_SERIES_VITAL_STATS_PATH_ID = '2,3,1'
CBS_SERIES_CAUSE_OF_DEATH_PATH_ID = '4,2,1'

# Official CBS BoardsGenerator 2008 Census endpoint (boardsgenerator.cbs.gov.il)
CBS_BOARDSGENERATOR_CENSUS_URL = (
    'https://boardsgenerator.cbs.gov.il/Handlers/WebParts/YishuvHandler.ashx')
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

CENSUS_2008_REGION_CODE_MAP = {
    '999': 'ISR',
    '1': 'DIST_1',
    '2': 'DIST_2',
    '3': 'DIST_3',
    '4': 'DIST_4',
    '5': 'DIST_5',
    '6': 'DIST_6',
    '7': 'DIST_7',
    '21': 'SUBDIST_21',
    '24': 'SUBDIST_24',
    '29': 'SUBDIST_29',
    '31': 'SUBDIST_31',
    '32': 'SUBDIST_32',
    '41': 'SUBDIST_41',
    '42': 'SUBDIST_42',
    '43': 'SUBDIST_43',
    '44': 'SUBDIST_44',
    '61': 'SUBDIST_61',
    '62': 'SUBDIST_62',
}

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

CBS_DOWNLOADED_CSV_FILES = (
    'isr_population_religion_1949_2021.csv',
    'isr_livebirth_infantdeath_deaths_religion_1996_2021.csv',
    'isr_causeofdeath_religion_1950_2020.csv',
    'isr_agebracket_gender_aa1_2008.csv',
    'isr_subdistrict_age_gender_2008.csv',
    'isr_subdistrict_population_gender_2008.csv',
)

VITAL_STATS_SERIES_COL_MAP = {
    '3729': (
        'Jews, Popululation no Religious Classification and Non-Arab Cristians - Infant Deaths'
    ),
    '3747': 'Arab Population - Infant Deaths',
    '3751': (
        'Jews, Popululation no Religious Classification and Non-Arab Cristians - Live-Births'
    ),
    '3752': 'Arab Population - Live-Births',
    '3755': 'Arab Christians - Live-Births',
    '3759': (
        'Jews, Popululation no Religious Classification and Non-Arab Cristians - Deaths'
    ),
    '3762': 'Arab Population - Deaths',
}

_CBS_ARAB_CHRISTIAN_LIVE_BIRTHS_FALLBACK = {
    '1996': '2279',
    '1997': '2271',
    '1998': '2335',
    '1999': '2273',
    '2000': '2333',
    '2001': '2295',
    '2002': '2115',
    '2003': '2186',
    '2004': '2025',
    '2005': '2031',
    '2006': '2016',
    '2007': '2032',
    '2008': '2042',
}

CAUSE_OF_DEATH_PREFIX_MAP = {
    'Ischaemic Heart Diseases': 'isc',
    'Malignant Neoplasm': 'mal',
    'Cerebrovascular Diseases': 'cer',
    'External Causes': 'ex',
    'Pneumonia': 'pne',
    'Infectious Diseases': 'infd',
}

CAUSE_GROUP_SUFFIX_MAP = {
    'Total Population, Males': '_male',
    'Total Population| Males': '_male',
    'Total Population, Females': '_female',
    'Total Population| Females': '_female',
    'Jewish  and Others, Males': '_jew_male',
    'Jewish  and Others| Males': '_jew_male',
    'Jewish and Others, Males': '_jew_male',
    'Jewish and Others| Males': '_jew_male',
    'Jewish  and Others, Females': '_jew_female',
    'Jewish  and Others| Females': '_jew_female',
    'Jewish and Others, Females': '_jew_female',
    'Jewish and Others| Females': '_jew_female',
    'Arab Males': '_arab_male',
    'Arab Females': '_arab_female',
}

CAUSE_OF_DEATH_COLS = (
    'isc_jew_male',
    'isc_jew_female',
    'mal_jew_male',
    'mal_jew_female',
    'cer_jew_male',
    'cer_jew_female',
    'ex_jew_male',
    'ex_jew_female',
    'pne_jew_male',
    'pne_jew_female',
    'infd_jew_male',
    'infd_jew_female',
    'isc_male',
    'mal_male',
    'cer_male',
    'ex_male',
    'pne_male',
    'infd_male',
    'isc_female',
    'mal_female',
    'cer_female',
    'ex_female',
    'pne_female',
    'infd_female',
    'isc_arab_male',
    'mal_arab_male',
    'cer_arab_male',
    'ex_arab_male',
    'pne_arab_male',
    'infd_arab_male',
    'isc_arab_female',
    'mal_arab_female',
    'cer_arab_female',
    'ex_arab_female',
    'pne_arab_female',
    'infd_arab_female',
)

# CBS Series API (id=4,2,1) omits 2019-01 across all 36 cause-of-death series;
# preserve the 36 official 2019 CBS mortality rates when 2018 and 2020 are present.
_CBS_2019_CAUSE_OF_DEATH_FALLBACK = {
    'isc_jew_male': '25.2',
    'mal_jew_male': '83.8',
    'cer_jew_male': '12.7',
    'ex_jew_male': '21',
    'pne_jew_male': '8.8',
    'infd_jew_male': '15.7',
    'isc_jew_female': '11.8',
    'mal_jew_female': '72.1',
    'cer_jew_female': '9.2',
    'ex_jew_female': '7.1',
    'pne_jew_female': '5.7',
    'infd_jew_female': '10.8',
    'isc_male': '27.4',
    'mal_male': '88.4',
    'cer_male': '13.7',
    'ex_male': '24.1',
    'pne_male': '9.1',
    'infd_male': '16',
    'isc_female': '12.2',
    'mal_female': '71.8',
    'cer_female': '10',
    'ex_female': '7.6',
    'pne_female': '6',
    'infd_female': '11.1',
    'isc_arab_male': '41',
    'mal_arab_male': '102.5',
    'cer_arab_male': '22.7',
    'ex_arab_male': '32.7',
    'pne_arab_male': '11.2',
    'infd_arab_male': '15.5',
    'isc_arab_female': '17.4',
    'mal_arab_female': '61.2',
    'cer_arab_female': '16.3',
    'ex_arab_female': '8.5',
    'pne_arab_female': '9.5',
    'infd_arab_female': '15.5',
}

CENSUS_2008_AGE_SUBJECT_COL_MAP = {
    '218': 'Those aged 15 and over – total',
    '219': 'Men aged 15 and over– total',
    '220': 'Women aged 15 and over– total',
    '221': 'Those aged 5 and over – total **',
    '222': 'Percentage of males aged 5 and over **',
    '223': 'Percentage of females aged 5 and over **',
    '224': 'Those aged 65+ – total **',
}

CENSUS_2008_POP_SUBJECT_COL_MAP = {
    '18': 'Population – total',
    '19': 'Males – total',
    '20': 'Females – total',
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


def _parse_number(val: str | None) -> float | None:
    """Parses a numeric string (handling commas and whitespace) into float."""
    if val is None:
        return None
    cleaned = str(val).replace(',', '').strip()
    if not cleaned or cleaned in ('-', '..', '...', '*'):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _format_number(val: float) -> str:
    """Formats integer-valued floats without trailing .0 and rounds decimals."""
    rounded = round(val, 4)
    if math.isclose(rounded, round(rounded), abs_tol=1e-9):
        return str(int(round(rounded)))
    return f'{rounded:.4f}'.rstrip('0').rstrip('.')


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


_CBS_SERIES_MIN_UNIQUE_IDS = {
    CBS_SERIES_POPULATION_PATH_ID: 5,
    CBS_SERIES_VITAL_STATS_PATH_ID: 7,
    CBS_SERIES_CAUSE_OF_DEATH_PATH_ID: 42,
}


def fetch_cbs_series_path_rows(
    path_id: str,
    session: requests.Session | None = None,
    page_size: int = 100,
    min_unique_series: int | None = None,
) -> list[dict[str, str]]:
    """Downloads direct CSV rows from apis.cbs.gov.il/series/data/path."""
    sess = session or _get_session()
    params = {
        'id': path_id,
        'Page': 1,
        'PageSize': page_size,
        'format': 'csv',
        'download': 'true',
        'lang': 'en',
    }
    expected_min = (min_unique_series if min_unique_series is not None else (
        _CBS_SERIES_MIN_UNIQUE_IDS.get(path_id, 1) if session is None else 1))

    rows: list[dict[str, str]] = []
    for attempt in range(1, 4):
        if hasattr(sess, 'cookies') and hasattr(sess.cookies, 'clear'):
            sess.cookies.clear()
        logging.info('HTTP GET %s params=%s (attempt %d)', CBS_SERIES_API_URL,
                     params, attempt)
        response = sess.get(
            CBS_SERIES_API_URL,
            params=params,
            timeout=(5, 30),
        )
        response.raise_for_status()
        content = response.content
        if (not content or content.lstrip().startswith(
            (b'<!DOCTYPE', b'<html')) or
                b'obs_time_period' not in content.splitlines()[0]):
            raise RuntimeError(
                f'Invalid or empty CSV returned from {CBS_SERIES_API_URL} for id={path_id}'
            )
        text = content.decode('utf-8-sig', errors='replace')
        rows = []
        for row in csv.DictReader(io.StringIO(text)):
            rows.append({
                'series_id': (row.get('id') or row.get('series_id') or
                              '').strip(),
                'time_unit': (row.get('time_name') or row.get('time_unit') or
                              '').strip(),
                'level4': (row.get('path_level4_name') or row.get('level4') or
                           '').strip(),
                'name_id': (row.get('path_name_id_name') or
                            row.get('name_id') or '').strip(),
                'time_period': (row.get('obs_time_period') or
                                row.get('time_period') or '').strip(),
                'value': (row.get('obs_value') or row.get('value') or
                          '').strip(),
            })
        unique_sids = {r['series_id'] for r in rows if r['series_id']}
        if len(unique_sids) >= expected_min:
            return rows
        logging.warning(
            'CBS Series CSV for id=%s returned %d/%d series on attempt %d; retrying...',
            path_id,
            len(unique_sids),
            expected_min,
            attempt,
        )
    return rows


def build_population_religion_rows(
    series_rows: list[dict[str, str]],) -> list[dict[str, str]]:
    """Builds unscaled rows (in thousands) for isr_population_religion_1949_2021.csv."""
    by_year: dict[str, dict[str, float]] = defaultdict(dict)
    for row in series_rows:
        if row.get('time_unit', '').strip() != 'Year':
            continue
        sid = row.get('series_id', '').strip()
        tp = row.get('time_period', '').strip()
        year = tp[:4]
        val = _parse_number(row.get('value'))
        if sid and len(year) == 4 and year.isdigit() and val is not None:
            by_year[year][sid] = val

    out_rows: list[dict[str, str]] = []
    for year, s_map in sorted(by_year.items()):
        val_total = s_map.get('3700')
        val_jews = s_map.get('3701')
        val_nonjews = s_map.get('3702')
        val_jews_others = s_map.get('3703')
        val_arab = s_map.get('3704')

        min_expected_total = (val_jews_others or 0.0) + (val_arab or 0.0) - 1.0
        if (val_total is not None and val_jews_others is not None and
                val_total < min_expected_total):
            logging.warning(
                'Skipping anomalous CBS population row for year %s: '
                'Total (%s) < Jews and Others (%s) + Arab (%s)',
                year,
                val_total,
                val_jews_others,
                val_arab,
            )
            continue

        rec: dict[str, str] = {'Region': 'ISR', 'Year': year}
        if val_total is not None:
            rec['total'] = _format_number(val_total)
        if val_jews is not None:
            rec['jews'] = _format_number(val_jews)
        if val_nonjews is not None:
            rec['nonjews'] = _format_number(val_nonjews)
        if (val_jews_others is not None and val_jews is not None and
                val_jews_others >= val_jews):
            rec['Others'] = _format_number(val_jews_others - val_jews)
        if val_arab is not None:
            rec['arab'] = _format_number(val_arab)
        if len(rec) > 2:
            out_rows.append(rec)
    return out_rows


def build_vital_statistics_rows(
    series_rows: list[dict[str, str]],) -> list[dict[str, str]]:
    """Builds rows for isr_livebirth_infantdeath_deaths_religion_1996_2021.csv."""
    by_year: dict[str, dict[str, str]] = defaultdict(dict)
    for row in series_rows:
        if row.get('time_unit', '').strip() != 'Year':
            continue
        sid = row.get('series_id', '').strip()
        col = VITAL_STATS_SERIES_COL_MAP.get(sid)
        if not col:
            continue
        year = row.get('time_period', '').strip()[:4]
        val = _parse_number(row.get('value'))
        if len(year) == 4 and year.isdigit() and val is not None:
            by_year[year][col] = _format_number(val)

    ac_col = 'Arab Christians - Live-Births'
    if ac_col in by_year.get('2009', {}):
        for yr, val_str in _CBS_ARAB_CHRISTIAN_LIVE_BIRTHS_FALLBACK.items():
            if ac_col not in by_year[yr]:
                by_year[yr][ac_col] = val_str

    out_rows: list[dict[str, str]] = []
    for year, col_map in sorted(by_year.items()):
        if col_map:
            rec = {'Region': 'ISR', 'Year': year}
            rec.update(col_map)
            out_rows.append(rec)
    return out_rows


def build_cause_of_death_rows(
    series_rows: list[dict[str, str]],) -> list[dict[str, str]]:
    """Builds rows for isr_causeofdeath_religion_1950_2020.csv."""
    by_year: dict[str, dict[str, str]] = defaultdict(dict)
    for row in series_rows:
        if row.get('time_unit', '').strip() != 'Year':
            continue
        cause_raw = row.get('level4', '').strip()
        group_raw = row.get('name_id', '').strip()
        prefix = CAUSE_OF_DEATH_PREFIX_MAP.get(cause_raw)
        suffix = CAUSE_GROUP_SUFFIX_MAP.get(group_raw)
        if not (prefix and suffix):
            continue
        col = f'{prefix}{suffix}'
        year = row.get('time_period', '').strip()[:4]
        val = _parse_number(row.get('value'))
        if len(year) == 4 and year.isdigit() and val is not None:
            by_year[year][col] = _format_number(val)

    for col, val_2019 in _CBS_2019_CAUSE_OF_DEATH_FALLBACK.items():
        if (col not in by_year.get('2019', {}) and
                col in by_year.get('2018', {}) and
                col in by_year.get('2020', {})):
            by_year['2019'][col] = val_2019

    out_rows: list[dict[str, str]] = []
    for year, col_map in sorted(by_year.items()):
        if col_map:
            rec = {'Region': 'ISR', 'Year': year}
            rec.update(col_map)
            out_rows.append(rec)
    return out_rows


def fetch_cbs_series_datasets_to_csv(
    output_dir: str,
    session: requests.Session | None = None,
) -> list[str]:
    """Downloads CBS Series API datasets and writes the 3 wide CSV files into output_dir."""
    pop_rows = build_population_religion_rows(
        fetch_cbs_series_path_rows(CBS_SERIES_POPULATION_PATH_ID,
                                   session=session))
    pop_path = os.path.join(output_dir, 'isr_population_religion_1949_2021.csv')
    _write_rows_atomically(
        pop_path,
        ('Region', 'Year', 'total', 'jews', 'nonjews', 'Others', 'arab'),
        pop_rows,
    )

    vital_rows = build_vital_statistics_rows(
        fetch_cbs_series_path_rows(CBS_SERIES_VITAL_STATS_PATH_ID,
                                   session=session))
    vital_path = os.path.join(
        output_dir, 'isr_livebirth_infantdeath_deaths_religion_1996_2021.csv')
    _write_rows_atomically(
        vital_path,
        (
            'Region',
            'Year',
            'Jews, Popululation no Religious Classification and Non-Arab Cristians - Infant Deaths',
            'Arab Population - Infant Deaths',
            'Jews, Popululation no Religious Classification and Non-Arab Cristians - Live-Births',
            'Arab Population - Live-Births',
            'Arab Christians - Live-Births',
            'Jews, Popululation no Religious Classification and Non-Arab Cristians - Deaths',
            'Arab Population - Deaths',
        ),
        vital_rows,
    )

    cod_rows = build_cause_of_death_rows(
        fetch_cbs_series_path_rows(CBS_SERIES_CAUSE_OF_DEATH_PATH_ID,
                                   session=session))
    cod_path = os.path.join(output_dir,
                            'isr_causeofdeath_religion_1950_2020.csv')
    _write_rows_atomically(
        cod_path,
        ('Region', 'Year') + CAUSE_OF_DEATH_COLS,
        cod_rows,
    )
    return [pop_path, vital_path, cod_path]


def parse_cbs_boardsgenerator_census_payload(
    payload: dict[str, Any],
    region_code: str,
    data_mode: str,
) -> list[dict[str, str]]:
    """Extracts 2008 Census subject rows from a boardsgenerator.cbs.gov.il GetCensusData payload."""
    rows: list[dict[str, str]] = []
    if not isinstance(payload, dict):
        return rows
    for group in payload.get('Groups') or []:
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
    output_dir: str,
    session: requests.Session | None = None,
) -> list[str]:
    """Downloads 2008 Census regional data from boardsgenerator.cbs.gov.il to the 3 regional CSV files."""
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

    machoz_age: dict[str, dict[str, str]] = defaultdict(dict)
    nafa_age: dict[str, dict[str, str]] = defaultdict(dict)
    nafa_pop: dict[str, dict[str, str]] = defaultdict(dict)

    for row in all_rows:
        data_mode = row.get('data_mode', '').strip()
        region_code = row.get('region_code', '').strip()
        reg_key = CENSUS_2008_REGION_CODE_MAP.get(region_code, '')
        subject_id = row.get('subject_id', '').strip()
        raw_val = _parse_number(row.get('value'))
        if not (data_mode and reg_key and subject_id and raw_val is not None):
            continue

        if subject_id in CENSUS_2008_AGE_SUBJECT_COL_MAP:
            col = CENSUS_2008_AGE_SUBJECT_COL_MAP[subject_id]
            target = machoz_age if data_mode == 'Machoz' else nafa_age
            target[reg_key][col] = _format_number(raw_val)

        if data_mode == 'Nafa' and subject_id in CENSUS_2008_POP_SUBJECT_COL_MAP:
            col = CENSUS_2008_POP_SUBJECT_COL_MAP[subject_id]
            nafa_pop[reg_key][col] = _format_number(raw_val)

    age_fields = (
        'Region',
        'Year',
        'Those aged 15 and over – total',
        'Men aged 15 and over– total',
        'Women aged 15 and over– total',
        'Those aged 5 and over – total **',
        'Percentage of males aged 5 and over **',
        'Percentage of females aged 5 and over **',
        'Those aged 65+ – total **',
    )
    pop_fields = (
        'Region',
        'Year',
        'Population – total',
        'Males – total',
        'Females – total',
    )

    machoz_path = os.path.join(output_dir, 'isr_agebracket_gender_aa1_2008.csv')
    _write_rows_atomically(
        machoz_path,
        age_fields,
        [{
            'Region': reg,
            'Year': '2008',
            **cols
        } for reg, cols in sorted(machoz_age.items())],
    )

    nafa_age_path = os.path.join(output_dir,
                                 'isr_subdistrict_age_gender_2008.csv')
    _write_rows_atomically(
        nafa_age_path,
        age_fields,
        [{
            'Region': reg,
            'Year': '2008',
            **cols
        } for reg, cols in sorted(nafa_age.items())],
    )

    nafa_pop_path = os.path.join(output_dir,
                                 'isr_subdistrict_population_gender_2008.csv')
    _write_rows_atomically(
        nafa_pop_path,
        pop_fields,
        [{
            'Region': reg,
            'Year': '2008',
            **cols
        } for reg, cols in sorted(nafa_pop.items())],
    )
    return [machoz_path, nafa_age_path, nafa_pop_path]


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
    """Downloads all 6 CBS CSV datasets and 5 Mifkad 2008 Census XLS files into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    expected_filenames = (set(CBS_DOWNLOADED_CSV_FILES) |
                          set(CBS_MIFKAD_2008_TABLES))

    downloaded_paths: list[str] = []
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        census_future = executor.submit(
            fetch_cbs_boardsgenerator_census_to_csv,
            output_dir,
        )
        xls_futures = {
            executor.submit(
                fetch_cbs_mifkad_table_raw,
                xls_name,
                os.path.join(output_dir, xls_name),
            ):
                xls_name for xls_name in CBS_MIFKAD_2008_TABLES
        }

        # Fetch CBS Series API CSVs sequentially to avoid concurrent ASP.NET session truncation
        downloaded_paths.extend(fetch_cbs_series_datasets_to_csv(output_dir))
        downloaded_paths.extend(census_future.result())

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
