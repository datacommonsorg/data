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
"""Transforms raw CBS Series CSVs, 2008 Census JSON, and Mifkad .xls files in input_files/ into the 11 staged CSV tables in staged_inputs/."""

import argparse
from collections import defaultdict
import csv
import json
import math
import os
import re
import tempfile
from typing import Any

from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

VITAL_STATS_SERIES_COL_MAP = {
    '3729': 'infant_deaths_jews_others',
    '3747': 'infant_deaths_arab',
    '3751': 'live_births_jews_others',
    '3752': 'live_births_arab',
    '3755': 'live_births_arab_christian',
    '3759': 'deaths_jews_others',
    '3762': 'deaths_arab',
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

# Exact CBS Series API numeric IDs for path id=4,2,1 (36 ingested cause-of-death
# mortality rate series, excluding the 6 unused "All Causes" total series).
CAUSE_OF_DEATH_SERIES_COL_MAP = {
    '70001': 'isc_jew_male',
    '70002': 'mal_jew_male',
    '70003': 'cer_jew_male',
    '70004': 'ex_jew_male',
    '70005': 'pne_jew_male',
    '70006': 'infd_jew_male',
    '70008': 'isc_jew_female',
    '70009': 'mal_jew_female',
    '70010': 'cer_jew_female',
    '70011': 'ex_jew_female',
    '70012': 'pne_jew_female',
    '70013': 'infd_jew_female',
    '70015': 'isc_male',
    '70016': 'mal_male',
    '70017': 'cer_male',
    '70018': 'ex_male',
    '70019': 'pne_male',
    '70020': 'infd_male',
    '70022': 'isc_female',
    '70023': 'mal_female',
    '70024': 'cer_female',
    '70025': 'ex_female',
    '70026': 'pne_female',
    '70027': 'infd_female',
    '70136': 'isc_arab_male',
    '70137': 'mal_arab_male',
    '70138': 'cer_arab_male',
    '70139': 'ex_arab_male',
    '70140': 'pne_arab_male',
    '70141': 'infd_arab_male',
    '70143': 'isc_arab_female',
    '70144': 'mal_arab_female',
    '70145': 'cer_arab_female',
    '70146': 'ex_arab_female',
    '70147': 'pne_arab_female',
    '70148': 'infd_arab_female',
}

_CAUSE_OF_DEATH_IGNORED_SERIES_IDS = frozenset({
    '70007',
    '70014',
    '70021',
    '70028',
    '70142',
    '70149',
})

# Normalized (lowercase, punctuation stripped, whitespace collapsed) fallback maps
# for synthetic inputs or renumbered CBS series without known numeric series_id.
CAUSE_OF_DEATH_PREFIX_MAP = {
    'ischaemic heart diseases': 'isc',
    'malignant neoplasm': 'mal',
    'cerebrovascular diseases': 'cer',
    'external causes': 'ex',
    'pneumonia': 'pne',
    'infectious diseases': 'infd',
}

CAUSE_GROUP_SUFFIX_MAP = {
    'total population males': '_male',
    'total population females': '_female',
    'jewish and others males': '_jew_male',
    'jewish and others females': '_jew_female',
    'arab males': '_arab_male',
    'arab females': '_arab_female',
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

MIFKAD_2008_AGE_ROWS_1_14 = {
    'Total': '',
    'TOTAL': '',
    'סך הכל': '',
    '14-0': '_0To14Years',
    '0-14': '_0To14Years',
    '24-15': '_15To24Years',
    '15-24': '_15To24Years',
    '34-25': '_25To34Years',
    '25-34': '_25To34Years',
    '39-35': '_35To39Years',
    '35-39': '_35To39Years',
    '44-40': '_40To44Years',
    '40-44': '_40To44Years',
    '49-45': '_45To49Years',
    '45-49': '_45To49Years',
    '54-50': '_50To54Years',
    '50-54': '_50To54Years',
    '59-55': '_55To59Years',
    '55-59': '_55To59Years',
    '64-60': '_60To64Years',
    '60-64': '_60To64Years',
    '69-65': '_65To69Years',
    '65-69': '_65To69Years',
    '74-70': '_70To74Years',
    '70-74': '_70To74Years',
    '79-75': '_75To79Years',
    '75-79': '_75To79Years',
    '84-80': '_80To84Years',
    '80-84': '_80To84Years',
    '+85': '_85OrMoreYears',
    '85+': '_85OrMoreYears',
}

MIFKAD_2008_MARITAL_COLS_1_14 = (
    (1, ''),
    (2, '_NeverMarried'),
    (3, '_MarriedAndNotSeparated'),
    (4, '_Divorced'),
    (5, '_Widowed'),
    (6, '_Separated'),
)

MIFKAD_2008_DIST_MAP = {
    'TOTAL': 'ISR',
    'Jerusalem District': 'DIST_1',
    'Northern District': 'DIST_2',
    'Haifa District': 'DIST_3',
    'Central District': 'DIST_4',
    'Tel Aviv District': 'DIST_5',
    'Southern District': 'DIST_6',
    'Judea and Samaria Area': 'DIST_7',
}

MIFKAD_2008_URBAN_RURAL_COLS = (
    (1, 'Grand totalTotal'),
    (2, 'Grand totalMales'),
    (3, 'Grand totalFemales'),
    (4, 'Urban localitiesTotal'),
    (5, 'Urban localitiesMales'),
    (6, 'Urban localitiesFemales'),
    (7, 'Rural localitiesTotal'),
    (8, 'Rural localitiesMales'),
    (9, 'Rural localitiesFemales'),
)

MIFKAD_2008_EMP_MARITAL_ROWS = {
    'TOTAL': '',
    'Never married': '_NeverMarried',
    'Married': '_MarriedAndNotSeparated',
    'Divorced': '_Divorced',
    'Widowed': '_Widowed',
}

MIFKAD_2008_EMP_AGE_COLS = (
    (1, ''),
    (2, '_15To24Years'),
    (3, '_25To29Years'),
    (4, '_30To34Years'),
    (5, '_35To39Years'),
    (6, '_40To44Years'),
    (7, '_45To49Years'),
    (8, '_50To54Years'),
    (9, '_55To59Years'),
    (10, '_60To64Years'),
    (11, '_65OrMoreYears'),
)

EXPECTED_INPUT_TABLE_FILENAMES = (
    'isr_age_maritalstatus_2008.csv',
    'isr_agebracket_gender_aa1_2008.csv',
    'isr_causeofdeath_religion_1950_2020.csv',
    'isr_livebirth_infantdeath_deaths_religion_1996_2021.csv',
    'isr_menemployed_age_maritalstatus_2008.csv',
    'isr_population_religion_1949_2021.csv',
    'isr_subdistrict_age_gender_2008.csv',
    'isr_subdistrict_population_gender_2008.csv',
    'isr_totalemployed_age_maritalstatus_2008.csv',
    'isr_urban_rural_gender_aa1_2008.csv',
    'isr_womenemployed_age_maritalstatus_2008.csv',
)

_ANNUAL_TIME_PERIOD_RE = re.compile(r'^[0-9]{4}(?:-01)?$')
_POPULATION_CORE_SIDS = frozenset({'3700', '3701', '3702', '3703', '3704'})


def _parse_annual_year(time_period: str) -> str | None:
    """Returns 4-digit ASCII year if time_period matches YYYY or YYYY-01, else None."""
    if _ANNUAL_TIME_PERIOD_RE.fullmatch(time_period):
        return time_period[:4]
    return None


def _is_subannual_period(time_period: str) -> bool:
    """Returns True if time_period is YYYY-<suffix> with suffix != '01'."""
    return (len(time_period) >= 6 and time_period[:4].isascii() and
            time_period[:4].isdigit() and time_period[4] == '-' and
            time_period[5:] != '01')


def _find_blank_unit_subannual_sids(
    series_rows: list[dict[str, str]],) -> set[str]:
    """Finds series_ids that have sub-annual periods while time_unit is blank."""
    flagged: set[str] = set()
    for row in series_rows:
        if row.get('time_unit', '').strip() != '':
            continue
        sid = row.get('series_id', '').strip()
        tp = row.get('time_period', '').strip()
        if sid and _is_subannual_period(tp):
            flagged.add(sid)
    return flagged


def _normalize_cbs_label(text: str) -> str:
    """Normalizes CBS labels by stripping pipe/comma punctuation and collapsing whitespace."""
    return re.sub(r'\s+', ' ', re.sub(r'[|,]', ' ', text)).strip().lower()


def _parse_number(val: str | None) -> float | None:
    """Parses a numeric string (handling commas and whitespace) into finite float."""
    if val is None:
        return None
    cleaned = str(val).replace(',', '').strip()
    if not cleaned or cleaned in ('-', '..', '...', '*'):
        return None
    try:
        parsed = float(cleaned)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _format_number(val: float) -> str:
    """Formats integer-valued floats without trailing .0 and rounds decimals."""
    rounded = round(val, 4)
    if math.isclose(rounded, round(rounded), abs_tol=1e-9):
        return str(int(round(rounded)))
    return f'{rounded:.4f}'.rstrip('0').rstrip('.')


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


def _write_table_atomically(
    dest_path: str,
    headers: list[str] | tuple[str, ...],
    rows: list[list[str]],
) -> None:
    """Atomically writes a header row and list of row lists to a CSV file."""
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=os.path.dirname(os.path.abspath(dest_path)),
        prefix='.tmp_cbs_',
        suffix='.csv',
    )
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as fp:
            writer = csv.writer(fp, lineterminator='\n')
            writer.writerow(headers)
            for row in rows:
                writer.writerow(row)
        os.replace(tmp_path, dest_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def read_raw_cbs_series_csv(csv_path: str) -> list[dict[str, str]]:
    """Reads a raw CBS Series API CSV file into normalized row dictionaries."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f'Missing raw CBS Series CSV file: {csv_path}')
    rows: list[dict[str, str]] = []
    with open(csv_path, 'r', encoding='utf-8-sig', errors='replace') as fp:
        for raw_row in csv.DictReader(fp):
            row = {
                k.strip(): (v or '') for k, v in raw_row.items() if k is not None
            }
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
    return rows


def build_population_religion_rows(
    series_rows: list[dict[str, str]],) -> list[dict[str, str]]:
    """Builds unscaled rows (in thousands) for isr_population_religion_1949_2021.csv."""
    by_year: dict[str, dict[str, float]] = defaultdict(dict)
    by_year_prio: dict[str, dict[str, tuple[bool, bool]]] = defaultdict(dict)
    tainted_negative_years: set[str] = set()
    blank_subannual_sids = _find_blank_unit_subannual_sids(series_rows)
    warned_subannual_sids: set[str] = set()
    for row in series_rows:
        time_unit = row.get('time_unit', '').strip()
        if time_unit not in ('', 'Year'):
            continue
        sid = row.get('series_id', '').strip()
        if sid not in _POPULATION_CORE_SIDS:
            continue
        if time_unit == '' and sid in blank_subannual_sids:
            if sid not in warned_subannual_sids:
                logging.warning(
                    'Skipping blank-time_unit sub-annual series sid=%s in population builder',
                    sid,
                )
                warned_subannual_sids.add(sid)
            continue
        tp = row.get('time_period', '').strip()
        year = _parse_annual_year(tp)
        val = _parse_number(row.get('value'))
        if year is None or val is None:
            continue
        if val < 0:
            logging.warning(
                'Skipping negative CBS population value for sid=%s year=%s: %s',
                sid,
                year,
                val,
            )
            tainted_negative_years.add(year)
            by_year.pop(year, None)
            by_year_prio.pop(year, None)
            continue
        if year in tainted_negative_years:
            continue
        prio = (time_unit == 'Year', tp.endswith('-01'))
        if sid in by_year[year]:
            prev_val = by_year[year][sid]
            prev_prio = by_year_prio[year][sid]
            if not math.isclose(prev_val, val, abs_tol=1e-9):
                logging.warning(
                    'Duplicate CBS population row for sid=%s year=%s: '
                    'existing=%s (prio=%s) vs incoming=%s (prio=%s)',
                    sid,
                    year,
                    prev_val,
                    prev_prio,
                    val,
                    prio,
                )
            if prio < prev_prio:
                continue
        by_year[year][sid] = val
        by_year_prio[year][sid] = prio

    out_rows: list[dict[str, str]] = []
    for year, s_map in sorted(by_year.items()):
        if year in tainted_negative_years:
            continue
        val_total = s_map.get('3700')
        val_jews = s_map.get('3701')
        val_nonjews = s_map.get('3702')
        val_jews_others = s_map.get('3703')
        val_arab = s_map.get('3704')

        core_vals = (
            val_total,
            val_jews,
            val_nonjews,
            val_jews_others,
            val_arab,
        )
        if not any(v is not None for v in core_vals):
            continue
        if val_total is None:
            logging.warning(
                'Skipping incomplete CBS population row missing Total (3700) for year %s: '
                'Jews (%s), Non-Jews (%s), Jews and Others (%s), Arab (%s)',
                year,
                val_jews,
                val_nonjews,
                val_jews_others,
                val_arab,
            )
            continue
        if (val_jews is None and val_nonjews is None and
                val_jews_others is None and val_arab is None):
            logging.warning(
                'Skipping total-only CBS population row lacking religion breakdown '
                'for year %s: Total (%s)',
                year,
                val_total,
            )
            continue

        if val_jews_others is not None:
            min_expected_total = val_jews_others + (val_arab or 0.0) - 1.0
            missing_post1994 = val_jews is None or val_arab is None
            invalid_post1994 = (not missing_post1994 and
                                (val_total < min_expected_total or
                                 val_jews > val_jews_others or
                                 (val_jews_others - val_jews) > val_jews or
                                 val_arab > val_total))
            if missing_post1994 or invalid_post1994:
                logging.warning(
                    'Skipping anomalous CBS population row for year %s: '
                    'Total (%s), Jews (%s), Jews and Others (%s), Arab (%s)',
                    year,
                    val_total,
                    val_jews,
                    val_jews_others,
                    val_arab,
                )
                continue
        elif val_arab is not None:
            logging.warning(
                'Skipping anomalous CBS population row missing Jews and Others (3703) '
                'for year %s: Total (%s), Jews (%s), Arab (%s)',
                year,
                val_total,
                val_jews,
                val_arab,
            )
            continue

        # Validate pre-1995 Non-Jews (3702) independently even if 3703 is also present.
        if val_nonjews is not None:
            if (val_jews is None or val_total < val_jews + val_nonjews - 1.0 or
                    val_jews > val_total or val_nonjews > val_total):
                logging.warning(
                    'Skipping anomalous pre-1995 CBS population row for year %s: '
                    'Total (%s), Jews (%s), Non-Jews (%s)',
                    year,
                    val_total,
                    val_jews,
                    val_nonjews,
                )
                continue
        if val_jews is not None and val_jews > val_total:
            logging.warning(
                'Skipping anomalous CBS population row for year %s: '
                'Total (%s), Jews (%s)',
                year,
                val_total,
                val_jews,
            )
            continue

        rec: dict[str, str] = {'Region': 'ISR', 'Year': year}
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
        out_rows.append(rec)
    return out_rows


def build_vital_statistics_rows(
    series_rows: list[dict[str, str]],) -> list[dict[str, str]]:
    """Builds rows for isr_livebirth_infantdeath_deaths_religion_1996_2021.csv."""
    by_year: dict[str, dict[str, str]] = defaultdict(dict)
    by_year_prio: dict[str, dict[str, tuple[bool, bool]]] = defaultdict(dict)
    tainted_negative_cells: set[tuple[str, str]] = set()
    blank_subannual_sids = _find_blank_unit_subannual_sids(series_rows)
    warned_subannual_sids: set[str] = set()
    for row in series_rows:
        time_unit = row.get('time_unit', '').strip()
        if time_unit not in ('', 'Year'):
            continue
        sid = row.get('series_id', '').strip()
        col = VITAL_STATS_SERIES_COL_MAP.get(sid)
        if not col:
            continue
        if time_unit == '' and sid in blank_subannual_sids:
            if sid not in warned_subannual_sids:
                logging.warning(
                    'Skipping blank-time_unit sub-annual series sid=%s in vital stats builder',
                    sid,
                )
                warned_subannual_sids.add(sid)
            continue
        tp = row.get('time_period', '').strip()
        year = _parse_annual_year(tp)
        val = _parse_number(row.get('value'))
        if year is None or val is None:
            continue
        if val < 0:
            logging.warning(
                'Skipping negative CBS vital statistics value for sid=%s year=%s: %s',
                sid,
                year,
                val,
            )
            tainted_negative_cells.add((year, col))
            by_year[year].pop(col, None)
            by_year_prio[year].pop(col, None)
            continue
        if (year, col) in tainted_negative_cells:
            continue
        formatted = _format_number(val)
        prio = (time_unit == 'Year', tp.endswith('-01'))
        if col in by_year[year]:
            prev_val = by_year[year][col]
            prev_prio = by_year_prio[year][col]
            if prev_val != formatted:
                logging.warning(
                    'Duplicate CBS vital statistics row for sid=%s year=%s: '
                    'existing=%s (prio=%s) vs incoming=%s (prio=%s)',
                    sid,
                    year,
                    prev_val,
                    prev_prio,
                    formatted,
                    prio,
                )
            if prio < prev_prio:
                continue
        by_year[year][col] = formatted
        by_year_prio[year][col] = prio

    ac_col = 'live_births_arab_christian'
    applied_ac_years: list[str] = []
    if ac_col in by_year.get('2009', {}):
        for yr, val_str in _CBS_ARAB_CHRISTIAN_LIVE_BIRTHS_FALLBACK.items():
            if (yr, ac_col) in tainted_negative_cells:
                logging.warning(
                    'Not applying Arab Christian live-births fallback for %s '
                    'due to rejected negative upstream value',
                    yr,
                )
                continue
            if ac_col not in by_year[yr]:
                by_year[yr][ac_col] = val_str
                applied_ac_years.append(yr)
    if applied_ac_years:
        logging.info(
            'Applied historical CBS Arab Christian live-births fallback for '
            '%d years (%s..%s)',
            len(applied_ac_years),
            applied_ac_years[0],
            applied_ac_years[-1],
        )

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
    by_year_prio: dict[str, dict[str, tuple[bool, bool,
                                            bool]]] = defaultdict(dict)
    canonical_cells: set[tuple[str, str]] = set()
    tainted_canonical_cells: set[tuple[str, str]] = set()
    tainted_fallback_cells: set[tuple[str, str]] = set()
    blank_subannual_sids = _find_blank_unit_subannual_sids(series_rows)
    warned_subannual_sids: set[str] = set()
    for row in series_rows:
        time_unit = row.get('time_unit', '').strip()
        if time_unit not in ('', 'Year'):
            continue
        sid = row.get('series_id', '').strip()
        col = CAUSE_OF_DEATH_SERIES_COL_MAP.get(sid)
        is_canonical = col is not None
        if not col:
            if sid in _CAUSE_OF_DEATH_IGNORED_SERIES_IDS:
                continue
            cause_norm = _normalize_cbs_label(row.get('level4', ''))
            group_norm = _normalize_cbs_label(row.get('name_id', ''))
            prefix = CAUSE_OF_DEATH_PREFIX_MAP.get(cause_norm)
            suffix = CAUSE_GROUP_SUFFIX_MAP.get(group_norm)
            if not (prefix and suffix):
                continue
            col = f'{prefix}{suffix}'
        if time_unit == '' and sid in blank_subannual_sids:
            if sid not in warned_subannual_sids:
                logging.warning(
                    'Skipping blank-time_unit sub-annual series sid=%s in cause-of-death builder',
                    sid,
                )
                warned_subannual_sids.add(sid)
            continue
        tp = row.get('time_period', '').strip()
        year = _parse_annual_year(tp)
        val = _parse_number(row.get('value'))
        if year is None or val is None:
            continue
        if val < 0:
            logging.warning(
                'Skipping negative CBS cause-of-death value for sid=%s col=%s year=%s: %s',
                sid,
                col,
                year,
                val,
            )
            if is_canonical:
                tainted_canonical_cells.add((year, col))
                canonical_cells.discard((year, col))
                by_year[year].pop(col, None)
                by_year_prio[year].pop(col, None)
            else:
                tainted_fallback_cells.add((year, col))
                if (year, col) not in canonical_cells:
                    by_year[year].pop(col, None)
                    by_year_prio[year].pop(col, None)
            continue
        if is_canonical and (year, col) in tainted_canonical_cells:
            continue
        if not is_canonical:
            if ((year, col) in canonical_cells or
                (year, col) in tainted_canonical_cells or
                (year, col) in tainted_fallback_cells):
                logging.warning(
                    'Ignoring fallback cause-of-death series sid=%s for %s (%s): '
                    'canonical or rejected series already seen',
                    sid,
                    col,
                    year,
                )
                continue
            logging.warning(
                'Matched cause-of-death column %s (%s) via label fallback for '
                'unmapped series_id=%r',
                col,
                year,
                sid,
            )
        formatted = _format_number(val)
        prio = (is_canonical, time_unit == 'Year', tp.endswith('-01'))
        if col in by_year[year]:
            prev_val = by_year[year][col]
            prev_prio = by_year_prio[year][col]
            if prev_val != formatted and not (is_canonical and
                                              not prev_prio[0]):
                logging.warning(
                    'Duplicate CBS cause-of-death row for col=%s year=%s: '
                    'existing=%s (prio=%s) vs incoming=%s (prio=%s)',
                    col,
                    year,
                    prev_val,
                    prev_prio,
                    formatted,
                    prio,
                )
            if prio < prev_prio:
                continue
        by_year[year][col] = formatted
        by_year_prio[year][col] = prio
        if is_canonical:
            canonical_cells.add((year, col))

    applied_2019_cols: list[str] = []
    for col, val_2019 in _CBS_2019_CAUSE_OF_DEATH_FALLBACK.items():
        if (('2019', col) in tainted_canonical_cells or
            ('2019', col) in tainted_fallback_cells):
            logging.warning(
                'Not applying 2019 cause-of-death fallback for %s '
                'due to rejected negative upstream value',
                col,
            )
            continue
        if (col not in by_year.get('2019', {}) and
                col in by_year.get('2018', {}) and
                col in by_year.get('2020', {})):
            by_year['2019'][col] = val_2019
            applied_2019_cols.append(col)
    if applied_2019_cols:
        logging.info(
            'Applied CBS Statistical Abstract 2019 cause-of-death fallback '
            'for %d series',
            len(applied_2019_cols),
        )

    out_rows: list[dict[str, str]] = []
    for year, col_map in sorted(by_year.items()):
        if col_map:
            rec = {'Region': 'ISR', 'Year': year}
            rec.update(col_map)
            out_rows.append(rec)
    return out_rows


def parse_cbs_boardsgenerator_census_payload(
    payload: dict[str, Any],
    region_code: str,
    data_mode: str,
) -> list[dict[str, str]]:
    """Extracts 2008 Census subject rows from a boardsgenerator.cbs.gov.il GetCensusData payload."""
    rows: list[dict[str, str]] = []
    if not isinstance(payload, dict):
        return rows
    groups = payload.get('Groups')
    if not isinstance(groups, list):
        return rows
    for group in groups:
        if not isinstance(group, dict):
            continue
        raw_group_id = group.get('Id')
        raw_group_name = group.get('Name')
        group_id = '' if raw_group_id is None else str(raw_group_id).strip()
        group_name = ('' if raw_group_name is None else
                      str(raw_group_name).strip())
        subjects = group.get('Subjects')
        if not isinstance(subjects, list):
            continue
        for subj in subjects:
            if not isinstance(subj, dict):
                continue
            raw_subject_id = subj.get('Id')
            raw_subject_name = subj.get('Name')
            raw_val = subj.get('Value')
            subject_id = ('' if raw_subject_id is None else
                          str(raw_subject_id).strip())
            subject_name = ('' if raw_subject_name is None else
                            str(raw_subject_name).strip())
            val = '' if raw_val is None else str(raw_val).strip()
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


def _convert_yishuv_json_to_csvs(json_path: str, output_dir: str) -> None:
    """Converts cbs_yishuv_census_2008.json into the 3 regional 2008 Census CSVs."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f'Missing raw 2008 Census JSON file: {json_path}')
    with open(json_path, 'r', encoding='utf-8') as fp:
        records = json.load(fp)
    if not isinstance(records, list):
        raise RuntimeError(
            f'Expected list of records in 2008 Census JSON file: {json_path}')

    all_rows: list[dict[str, str]] = []
    for item in records:
        if not isinstance(item, dict):
            continue
        raw_region_code = item.get('region_code')
        raw_data_mode = item.get('data_mode')
        all_rows.extend(
            parse_cbs_boardsgenerator_census_payload(
                item.get('payload') or {},
                '' if raw_region_code is None else str(raw_region_code),
                '' if raw_data_mode is None else str(raw_data_mode),
            ))

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
        if raw_val < 0:
            logging.warning(
                'Skipping negative 2008 Census value for region_code=%s '
                'data_mode=%s subject_id=%s: %s',
                region_code,
                data_mode,
                subject_id,
                raw_val,
            )
            continue

        if subject_id in CENSUS_2008_AGE_SUBJECT_COL_MAP:
            col = CENSUS_2008_AGE_SUBJECT_COL_MAP[subject_id]
            if data_mode == 'Machoz':
                machoz_age[reg_key][col] = _format_number(raw_val)
            elif data_mode == 'Nafa':
                nafa_age[reg_key][col] = _format_number(raw_val)
            else:
                logging.warning(
                    'Skipping unexpected 2008 Census data_mode=%r for '
                    'region_code=%s subject_id=%s',
                    data_mode,
                    region_code,
                    subject_id,
                )

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

    _write_rows_atomically(
        os.path.join(output_dir, 'isr_agebracket_gender_aa1_2008.csv'),
        age_fields,
        [{
            'Region': reg,
            'Year': '2008',
            **cols
        } for reg, cols in sorted(machoz_age.items())],
    )
    _write_rows_atomically(
        os.path.join(output_dir, 'isr_subdistrict_age_gender_2008.csv'),
        age_fields,
        [{
            'Region': reg,
            'Year': '2008',
            **cols
        } for reg, cols in sorted(nafa_age.items())],
    )
    _write_rows_atomically(
        os.path.join(output_dir, 'isr_subdistrict_population_gender_2008.csv'),
        pop_fields,
        [{
            'Region': reg,
            'Year': '2008',
            **cols
        } for reg, cols in sorted(nafa_pop.items())],
    )


def _read_mifkad_table_rows(fpath: str) -> list[list[str]]:
    """Reads rows from a raw CBS Mifkad table (.xls/.xlsx binary or .csv text)."""
    if not os.path.exists(fpath):
        raise FileNotFoundError(f'Missing Mifkad table file: {fpath}')
    with open(fpath, 'rb') as fp:
        head = fp.read(8)
    if head.startswith(b'\xd0\xcf\x11\xe0') or head.startswith(b'PK\x03\x04'):
        import pandas as pd  # pylint: disable=import-outside-toplevel

        engine = 'openpyxl' if head.startswith(b'PK\x03\x04') else 'calamine'
        df = pd.read_excel(fpath, header=None, dtype=str,
                           engine=engine).fillna('')
        return [[str(c) for c in row] for row in df.values.tolist()]
    with open(fpath, 'r', encoding='utf-8-sig', errors='replace') as fp:
        return list(csv.reader(fp))


def _match_mifkad_row_label(
    row: list[str],
    mapping: dict[str, str],
    preferred_indices: tuple[int, ...],
) -> str | None:
    """Resolves a Mifkad row label against mapping using preferred indices, last non-empty cell, and row[0]."""
    candidates: list[str] = []
    for idx in preferred_indices:
        if 0 <= idx < len(row):
            cand = row[idx].strip()
            if cand:
                candidates.append(cand)
    for cell in reversed(row):
        cand = cell.strip()
        if cand:
            candidates.append(cand)
            break
    if row:
        cand = row[0].strip()
        if cand:
            candidates.append(cand)
    for cand in candidates:
        if cand in mapping:
            return mapping[cand]
    return None


def _convert_dem1_2_xls_to_csv(xls_path: str, dest_path: str) -> None:
    """Converts dem1_2.xls (in hundreds) into isr_urban_rural_gender_aa1_2008.csv."""
    headers = ['Region', 'Year'
              ] + [col_name for _, col_name in MIFKAD_2008_URBAN_RURAL_COLS]
    rows_by_reg: dict[str, list[str]] = {}
    for row in _read_mifkad_table_rows(xls_path):
        if len(row) < 10:
            continue
        reg = _match_mifkad_row_label(row, MIFKAD_2008_DIST_MAP, (10,))
        if not reg:
            continue
        vals: list[str] = []
        for col_idx, col_name in MIFKAD_2008_URBAN_RURAL_COLS:
            if reg == 'ISR' and col_name == 'Grand totalTotal':
                vals.append('')
                continue
            val = _parse_number(row[col_idx])
            if val is not None and val < 0:
                logging.warning(
                    'Skipping negative value in %s for %s col=%s: %s',
                    xls_path,
                    reg,
                    col_name,
                    val,
                )
                vals.append('')
                continue
            vals.append('' if val is None else _format_number(val))
        if any(vals):
            rows_by_reg[reg] = vals

    if not rows_by_reg:
        raise RuntimeError(f'No data rows extracted from {xls_path}')

    table_rows = [
        [reg, '2008'] + rows_by_reg[reg] for reg in sorted(rows_by_reg)
    ]
    _write_table_atomically(dest_path, headers, table_rows)


def _convert_dem1_14_xls_to_csv(xls_path: str, dest_path: str) -> None:
    """Converts dem1_14.xls (in hundreds) into isr_age_maritalstatus_2008.csv."""
    # Canonical Data Commons StatVars (Count_Person_NeverMarried,
    # Count_Person_MarriedAndNotSeparated, Count_Person_Divorced,
    # Count_Person_Widowed, Count_Person_Separated) all specify
    # age: Years15Onwards. Subtracting the 0-14 row from the all-ages TOTAL row
    # yields the exact 15+ population (notably removing 2,052,460 children from
    # Never married: 36,684.4 - 20,524.6 = 16,159.8 hundreds = 1,615,980).
    age_order = (
        ('', '15+'),
        ('_0To14Years', '0-14'),
        ('_15To24Years', '15-24'),
        ('_25To34Years', '25-34'),
        ('_35To39Years', '35-39'),
        ('_40To44Years', '40-44'),
        ('_45To49Years', '45-49'),
        ('_50To54Years', '50-54'),
        ('_55To59Years', '55-59'),
        ('_60To64Years', '60-64'),
        ('_65To69Years', '65-69'),
        ('_70To74Years', '70-74'),
        ('_75To79Years', '75-79'),
        ('_80To84Years', '80-84'),
        ('_85OrMoreYears', '85+'),
    )
    marital_cols = (
        ('', 'Total'),
        ('_NeverMarried', 'Never married'),
        ('_MarriedAndNotSeparated', 'Married'),
        ('_Divorced', 'Divorced'),
        ('_Widowed', 'Widowed'),
        ('_Separated', 'Married but separated'),
    )

    raw_cells: dict[tuple[str, str], float] = {}
    invalid_child_cols: set[str] = set()
    for row in _read_mifkad_table_rows(xls_path):
        if len(row) < 7:
            continue
        age_suf = _match_mifkad_row_label(row, MIFKAD_2008_AGE_ROWS_1_14,
                                          (7, 0))
        if age_suf is None:
            continue
        for col_idx, marital_suf in MIFKAD_2008_MARITAL_COLS_1_14:
            if age_suf == '' and marital_suf == '':
                continue
            val = _parse_number(row[col_idx])
            if val is None:
                continue
            if val < 0:
                logging.warning(
                    'Skipping negative cell (%s, %s) in %s: %s',
                    age_suf or 'TOTAL',
                    marital_suf or 'Total',
                    xls_path,
                    val,
                )
                if age_suf == '_0To14Years':
                    invalid_child_cols.add(marital_suf)
                continue
            raw_cells[(age_suf, marital_suf)] = val

    cell_map: dict[tuple[str, str], str] = {}
    for (age_suf, marital_suf), val in raw_cells.items():
        if age_suf != '':
            cell_map[(age_suf, marital_suf)] = _format_number(val)
            continue
        if marital_suf in invalid_child_cols:
            logging.warning(
                'Skipping 15+ total for %s in %s due to negative 0-14 cell',
                marital_suf,
                xls_path,
            )
            continue
        child_val = raw_cells.get(('_0To14Years', marital_suf))
        if marital_suf == '_NeverMarried' and child_val is None:
            logging.warning(
                'Skipping 15+ Never married total in %s: missing 0-14 row '
                'needed to subtract children from all-ages total (%s)',
                xls_path,
                val,
            )
            continue
        if child_val is not None:
            if val < child_val:
                logging.warning(
                    'Skipping anomalous 15+ total for %s in %s: all-ages (%s) < 0-14 (%s)',
                    marital_suf,
                    xls_path,
                    val,
                    child_val,
                )
                continue
            cell_map[('', marital_suf)] = _format_number(val - child_val)
        else:
            cell_map[('', marital_suf)] = _format_number(val)

    if not cell_map:
        raise RuntimeError(f'No data rows extracted from {xls_path}')

    headers = ['Year', 'Region', 'Age group'] + [m[1] for m in marital_cols]
    table_rows: list[list[str]] = []
    for age_suf, age_label in age_order:
        vals = [cell_map.get((age_suf, m_suf), '') for m_suf, _ in marital_cols]
        if any(vals):
            table_rows.append(['2008', 'ISR', age_label] + vals)
    _write_table_atomically(dest_path, headers, table_rows)


def _convert_emp_xls_to_csv(
    xls_path: str,
    dest_path: str,
    gender_suf: str,
    is_female: bool,
) -> None:
    """Converts a Mifkad employment .xls table (in hundreds) into its 2D CSV."""
    marital_rows = (
        ('', 'סך הכל'),
        ('_NeverMarried', 'רווקה' if is_female else 'רווק'),
        ('_MarriedAndNotSeparated', 'נשואה' if is_female else 'נשוי'),
        ('_Divorced', 'גרושה' if is_female else 'גרוש'),
        ('_Widowed', 'אלמנה' if is_female else 'אלמן'),
    )
    age_cols = (
        ('', 'סך הכל'),
        ('_15To24Years', '24-15'),
        ('_25To29Years', '29-25'),
        ('_30To34Years', '34-30'),
        ('_35To39Years', '39-35'),
        ('_40To44Years', '44-40'),
        ('_45To49Years', '49-45'),
        ('_50To54Years', '54-50'),
        ('_55To59Years', '59-55'),
        ('_60To64Years', '64-60'),
        ('_65OrMoreYears', '+65'),
    )

    cell_map: dict[tuple[str, str], str] = {}
    widowed_15_39: str = ''
    for row in _read_mifkad_table_rows(xls_path):
        if len(row) < 12:
            continue
        marital_suf = _match_mifkad_row_label(row, MIFKAD_2008_EMP_MARITAL_ROWS,
                                              (12, 0))
        if marital_suf is None:
            continue
        for col_idx, age_suf in MIFKAD_2008_EMP_AGE_COLS:
            val = _parse_number(row[col_idx])
            if val is None:
                continue
            if val < 0:
                logging.warning(
                    'Skipping negative employment cell (%s, %s) in %s: %s',
                    marital_suf or 'TOTAL',
                    age_suf or 'TOTAL',
                    xls_path,
                    val,
                )
                continue
            # CBS footnote R26 in lab4_14_1.xls (employed men) merges ages
            # 15-39 for widowed men into the 35-39 cell (2.1 hundreds = 210).
            if (gender_suf == '_Male' and marital_suf == '_Widowed' and
                    age_suf == '_35To39Years'):
                widowed_15_39 = _format_number(val)
            else:
                cell_map[(marital_suf, age_suf)] = _format_number(val)

    if gender_suf == '_Male' and widowed_15_39:
        overlapping = [
            age_suf for age_suf in ('_15To24Years', '_25To29Years',
                                    '_30To34Years')
            if ('_Widowed', age_suf) in cell_map
        ]
        if overlapping:
            raise RuntimeError(
                f'Unexpected widowed male 15-34 cells {overlapping} present '
                f'alongside CBS footnote R26 merged 15-39 cell in {xls_path}; '
                f'emitting both would double-count ages 15-34')

    if not cell_map and not widowed_15_39:
        raise RuntimeError(f'No data rows extracted from {xls_path}')

    headers = ['Year', 'Region', 'code'] + [a[1] for a in age_cols]
    table_rows: list[list[str]] = []
    for m_suf, m_label in marital_rows:
        vals = [cell_map.get((m_suf, a_suf), '') for a_suf, _ in age_cols]
        if gender_suf and m_suf == '' and vals and vals[0]:
            base_val = vals[0]
            vals[0] = ''
            row_vals = [''] * len(age_cols)
            row_vals[0] = base_val
            table_rows.append(['2008', 'ISR', 'מועסקים'] + row_vals)
        if any(vals):
            table_rows.append(['2008', 'ISR', m_label] + vals)
    if gender_suf == '_Male' and widowed_15_39:
        vals = [''] * len(age_cols)
        vals[0] = widowed_15_39
        table_rows.append(['2008', 'ISR', 'אלמן_15_39'] + vals)
    _write_table_atomically(dest_path, headers, table_rows)


EXPECTED_MIN_DATA_ROWS_BY_TABLE: dict[str, int] = {
    'isr_age_maritalstatus_2008.csv': 15,
    'isr_agebracket_gender_aa1_2008.csv': 8,
    'isr_causeofdeath_religion_1950_2020.csv': 70,
    'isr_livebirth_infantdeath_deaths_religion_1996_2021.csv': 25,
    'isr_menemployed_age_maritalstatus_2008.csv': 7,
    'isr_population_religion_1949_2021.csv': 70,
    'isr_subdistrict_age_gender_2008.csv': 11,
    'isr_subdistrict_population_gender_2008.csv': 11,
    'isr_totalemployed_age_maritalstatus_2008.csv': 5,
    'isr_urban_rural_gender_aa1_2008.csv': 8,
    'isr_womenemployed_age_maritalstatus_2008.csv': 6,
}


def build_input_tables(
    raw_dir: str,
    output_dir: str,
    strict_completeness: bool = True,
) -> list[str]:
    """Transforms all raw CBS files in raw_dir into the 11 staged CSV tables in output_dir."""
    if not os.path.isdir(raw_dir):
        raise FileNotFoundError(f'Input directory does not exist: {raw_dir}')
    os.makedirs(output_dir, exist_ok=True)

    # 1. Transform raw CBS Series API CSVs into the 3 time-series CSV tables
    pop_raw_path = os.path.join(raw_dir, 'cbs_series_2_1_1_1.csv')
    pop_cols = ('total', 'jews', 'nonjews', 'Others', 'arab')
    pop_rows = build_population_religion_rows(
        read_raw_cbs_series_csv(pop_raw_path))
    _write_rows_atomically(
        os.path.join(output_dir, 'isr_population_religion_1949_2021.csv'),
        ('Region', 'Year') + pop_cols,
        pop_rows,
    )

    vital_raw_path = os.path.join(raw_dir, 'cbs_series_2_3_1.csv')
    vital_cols = tuple(VITAL_STATS_SERIES_COL_MAP.values())
    vital_rows = build_vital_statistics_rows(
        read_raw_cbs_series_csv(vital_raw_path))
    _write_rows_atomically(
        os.path.join(output_dir,
                     'isr_livebirth_infantdeath_deaths_religion_1996_2021.csv'),
        ('Region', 'Year') + vital_cols,
        vital_rows,
    )

    cod_raw_path = os.path.join(raw_dir, 'cbs_series_4_2_1.csv')
    cod_rows = build_cause_of_death_rows(read_raw_cbs_series_csv(cod_raw_path))
    _write_rows_atomically(
        os.path.join(output_dir, 'isr_causeofdeath_religion_1950_2020.csv'),
        ('Region', 'Year') + CAUSE_OF_DEATH_COLS,
        cod_rows,
    )

    # 2. Transform raw 2008 Census regional JSON into the 3 regional CSV tables
    _convert_yishuv_json_to_csvs(
        os.path.join(raw_dir, 'cbs_yishuv_census_2008.json'),
        output_dir,
    )

    # 3. Convert the 5 Mifkad .xls tables into .csv tables in output_dir
    _convert_dem1_2_xls_to_csv(
        os.path.join(raw_dir, 'dem1_2.xls'),
        os.path.join(output_dir, 'isr_urban_rural_gender_aa1_2008.csv'),
    )
    _convert_dem1_14_xls_to_csv(
        os.path.join(raw_dir, 'dem1_14.xls'),
        os.path.join(output_dir, 'isr_age_maritalstatus_2008.csv'),
    )
    emp_tables = (
        ('lab4_14.xls', 'isr_totalemployed_age_maritalstatus_2008.csv', '',
         False),
        ('lab4_14_1.xls', 'isr_menemployed_age_maritalstatus_2008.csv', '_Male',
         False),
        ('lab4_14_2.xls', 'isr_womenemployed_age_maritalstatus_2008.csv',
         '_Female', True),
    )
    for xls_name, csv_name, gender_suf, is_female in emp_tables:
        _convert_emp_xls_to_csv(
            os.path.join(raw_dir, xls_name),
            os.path.join(output_dir, csv_name),
            gender_suf=gender_suf,
            is_female=is_female,
        )

    expected_set = set(EXPECTED_INPUT_TABLE_FILENAMES)
    if os.path.realpath(output_dir) == os.path.realpath(_SCRIPT_DIR):
        logging.warning(
            'Refusing to run stale-file cleanup in script directory: %s',
            output_dir,
        )
    else:
        for existing_name in os.listdir(output_dir):
            existing_path = os.path.join(output_dir, existing_name)
            if (existing_name not in expected_set and
                    existing_name.startswith('isr_') and
                    existing_name.endswith('.csv') and
                    os.path.isfile(existing_path)):
                logging.info('Removing stale staged file: %s', existing_path)
                os.remove(existing_path)

    staged_paths = [
        os.path.join(output_dir, fname)
        for fname in EXPECTED_INPUT_TABLE_FILENAMES
        if os.path.exists(os.path.join(output_dir, fname))
    ]
    missing_tables = expected_set - {os.path.basename(p) for p in staged_paths}
    if missing_tables:
        raise RuntimeError(
            f'Missing expected staged CSV files in {output_dir}: {sorted(missing_tables)}'
        )
    for staged_path in staged_paths:
        fname = os.path.basename(staged_path)
        with open(staged_path, 'r', encoding='utf-8') as fp:
            data_rows = max(0, sum(1 for _ in csv.reader(fp)) - 1)
        min_rows = (EXPECTED_MIN_DATA_ROWS_BY_TABLE.get(fname, 1)
                    if strict_completeness else 1)
        if data_rows < min_rows:
            raise RuntimeError(
                f'Staged CSV file has too few data rows ({data_rows} < {min_rows}): '
                f'{staged_path}')
    return staged_paths


def main(argv: list[str] | None = None) -> None:
    logging.set_verbosity(logging.INFO)
    parser = argparse.ArgumentParser(
        description=
        'Transforms raw CBS files in input_files/ into the 11 staged CSVs in staged_inputs/.'
    )
    parser.add_argument(
        '--input_dir',
        default=os.path.join(_SCRIPT_DIR, 'input_files'),
        help=
        'Directory containing raw downloaded CBS .csv, .json, and .xls files.',
    )
    parser.add_argument(
        '--output_dir',
        default=os.path.join(_SCRIPT_DIR, 'staged_inputs'),
        help='Directory where the 11 CSV tables will be staged.',
    )
    args = parser.parse_args(argv)
    build_input_tables(args.input_dir, args.output_dir)


if __name__ == '__main__':
    main()
