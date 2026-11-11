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
"""Preprocesses raw Israel CBS files in input_files/ into the 11 wide/2D tables in staged_inputs/."""

import argparse
from collections import defaultdict
import csv
import math
import os

from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

VITAL_STATS_SERIES_MAP = {
    '3751': (
        'IND_Count_BirthEvent_LiveBirth_CBSIsraelJudaismOrNonArabChristianOrNoReligion'
    ),
    '3752': 'IND_Count_BirthEvent_LiveBirth_Arab',
    '3755': 'IND_Count_BirthEvent_LiveBirth_CBSIsraelArabChristian',
    '3759': (
        'IND_Count_MortalityEvent_CBSIsraelJudaismOrNonArabChristianOrNoReligion'
    ),
    '3762': 'IND_Count_MortalityEvent_Arab',
    '3729': (
        'IND_Count_MortalityEvent_Infant_CBSIsraelJudaismOrNonArabChristianOrNoReligion'
    ),
    '3747': 'IND_Count_MortalityEvent_Infant_Arab',
}

CAUSE_OF_DEATH_MAP = {
    'Ischaemic Heart Diseases': 'CoronaryHeartDisease',
    'Malignant Neoplasm': 'MalignantNeoplasms',
    'Cerebrovascular Diseases': 'CerebrovascularDiseases',
    'External Causes': 'ExternalCausesOfDeath',
    'Pneumonia': 'Pneumonia',
    'Infectious Diseases': 'InfectiousDiseases',
}

CAUSE_GROUP_MAP = {
    'Total Population, Males': ('Male', ''),
    'Total Population| Males': ('Male', ''),
    'Total Population, Females': ('Female', ''),
    'Total Population| Females': ('Female', ''),
    'Jewish  and Others, Males': ('Male', '_Judaism'),
    'Jewish  and Others| Males': ('Male', '_Judaism'),
    'Jewish and Others, Males': ('Male', '_Judaism'),
    'Jewish and Others| Males': ('Male', '_Judaism'),
    'Jewish  and Others, Females': ('Female', '_Judaism'),
    'Jewish  and Others| Females': ('Female', '_Judaism'),
    'Jewish and Others, Females': ('Female', '_Judaism'),
    'Jewish and Others| Females': ('Female', '_Judaism'),
    'Arab Males': ('Male', '_Arab'),
    'Arab Females': ('Female', '_Arab'),
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

# CBS Series API (id=4,2,1) omits 2019-01 across all 36 cause-of-death series;
# preserve the 36 official 2019 CBS mortality rates when 2018 and 2020 are present.
_CBS_2019_CAUSE_OF_DEATH_FALLBACK = {
    'IND_Count_MortalityEvent_CoronaryHeartDisease_Male_Judaism_AsAFractionOf_Count_Person_Male_Judaism':
        '25.2',
    'IND_Count_MortalityEvent_MalignantNeoplasms_Male_Judaism_AsAFractionOf_Count_Person_Male_Judaism':
        '83.8',
    'IND_Count_MortalityEvent_CerebrovascularDiseases_Male_Judaism_AsAFractionOf_Count_Person_Male_Judaism':
        '12.7',
    'IND_Count_MortalityEvent_ExternalCausesOfDeath_Male_Judaism_AsAFractionOf_Count_Person_Male_Judaism':
        '21',
    'IND_Count_MortalityEvent_Pneumonia_Male_Judaism_AsAFractionOf_Count_Person_Male_Judaism':
        '8.8',
    'IND_Count_MortalityEvent_InfectiousDiseases_Male_Judaism_AsAFractionOf_Count_Person_Male_Judaism':
        '15.7',
    'IND_Count_MortalityEvent_CoronaryHeartDisease_Female_Judaism_AsAFractionOf_Count_Person_Female_Judaism':
        '11.8',
    'IND_Count_MortalityEvent_MalignantNeoplasms_Female_Judaism_AsAFractionOf_Count_Person_Female_Judaism':
        '72.1',
    'IND_Count_MortalityEvent_CerebrovascularDiseases_Female_Judaism_AsAFractionOf_Count_Person_Female_Judaism':
        '9.2',
    'IND_Count_MortalityEvent_ExternalCausesOfDeath_Female_Judaism_AsAFractionOf_Count_Person_Female_Judaism':
        '7.1',
    'IND_Count_MortalityEvent_Pneumonia_Female_Judaism_AsAFractionOf_Count_Person_Female_Judaism':
        '5.7',
    'IND_Count_MortalityEvent_InfectiousDiseases_Female_Judaism_AsAFractionOf_Count_Person_Female_Judaism':
        '10.8',
    'IND_Count_MortalityEvent_CoronaryHeartDisease_Male_AsAFractionOf_Count_Person_Male':
        '27.4',
    'IND_Count_MortalityEvent_MalignantNeoplasms_Male_AsAFractionOf_Count_Person_Male':
        '88.4',
    'IND_Count_MortalityEvent_CerebrovascularDiseases_Male_AsAFractionOf_Count_Person_Male':
        '13.7',
    'IND_Count_MortalityEvent_ExternalCausesOfDeath_Male_AsAFractionOf_Count_Person_Male':
        '24.1',
    'IND_Count_MortalityEvent_Pneumonia_Male_AsAFractionOf_Count_Person_Male':
        '9.1',
    'IND_Count_MortalityEvent_InfectiousDiseases_Male_AsAFractionOf_Count_Person_Male':
        '16',
    'IND_Count_MortalityEvent_CoronaryHeartDisease_Female_AsAFractionOf_Count_Person_Female':
        '12.2',
    'IND_Count_MortalityEvent_MalignantNeoplasms_Female_AsAFractionOf_Count_Person_Female':
        '71.8',
    'IND_Count_MortalityEvent_CerebrovascularDiseases_Female_AsAFractionOf_Count_Person_Female':
        '10',
    'IND_Count_MortalityEvent_ExternalCausesOfDeath_Female_AsAFractionOf_Count_Person_Female':
        '7.6',
    'IND_Count_MortalityEvent_Pneumonia_Female_AsAFractionOf_Count_Person_Female':
        '6',
    'IND_Count_MortalityEvent_InfectiousDiseases_Female_AsAFractionOf_Count_Person_Female':
        '11.1',
    'IND_Count_MortalityEvent_CoronaryHeartDisease_Male_Arab_AsAFractionOf_Count_Person_Male_Arab':
        '41',
    'IND_Count_MortalityEvent_MalignantNeoplasms_Male_Arab_AsAFractionOf_Count_Person_Male_Arab':
        '102.5',
    'IND_Count_MortalityEvent_CerebrovascularDiseases_Male_Arab_AsAFractionOf_Count_Person_Male_Arab':
        '22.7',
    'IND_Count_MortalityEvent_ExternalCausesOfDeath_Male_Arab_AsAFractionOf_Count_Person_Male_Arab':
        '32.7',
    'IND_Count_MortalityEvent_Pneumonia_Male_Arab_AsAFractionOf_Count_Person_Male_Arab':
        '11.2',
    'IND_Count_MortalityEvent_InfectiousDiseases_Male_Arab_AsAFractionOf_Count_Person_Male_Arab':
        '15.5',
    'IND_Count_MortalityEvent_CoronaryHeartDisease_Female_Arab_AsAFractionOf_Count_Person_Female_Arab':
        '17.4',
    'IND_Count_MortalityEvent_MalignantNeoplasms_Female_Arab_AsAFractionOf_Count_Person_Female_Arab':
        '61.2',
    'IND_Count_MortalityEvent_CerebrovascularDiseases_Female_Arab_AsAFractionOf_Count_Person_Female_Arab':
        '16.3',
    'IND_Count_MortalityEvent_ExternalCausesOfDeath_Female_Arab_AsAFractionOf_Count_Person_Female_Arab':
        '8.5',
    'IND_Count_MortalityEvent_Pneumonia_Female_Arab_AsAFractionOf_Count_Person_Female_Arab':
        '9.5',
    'IND_Count_MortalityEvent_InfectiousDiseases_Female_Arab_AsAFractionOf_Count_Person_Female_Arab':
        '15.5',
}

CENSUS_2008_REGION_DCID_MAP = {
    '999': 'country/ISR',
    '1': 'wikidataId/Q192232',
    '2': 'wikidataId/Q189942',
    '3': 'wikidataId/Q185845',
    '4': 'wikidataId/Q188785',
    '5': 'wikidataId/Q192811',
    '6': 'wikidataId/Q188781',
    '7': 'wikidataId/Q513200',
    '21': 'wikidataId/Q5423089',
    '24': 'wikidataId/Q5423103',
    '29': 'wikidataId/Q5423040',
    '31': 'wikidataId/Q5423411',
    '32': 'wikidataId/Q5423414',
    '41': 'wikidataId/Q152379',
    '42': 'wikidataId/Q46993019',
    '43': 'wikidataId/Q5419070',
    '44': 'wikidataId/Q46992983',
    '61': 'wikidataId/Q5423623',
    '62': 'wikidataId/Q5423629',
}

CENSUS_2008_AGE_SUBJECT_MAP = {
    '218': ('IND_Count_Person_15OrMoreYears', 1000.0),
    '219': ('IND_Count_Person_15OrMoreYears_Male', 1000.0),
    '220': ('IND_Count_Person_15OrMoreYears_Female', 1000.0),
    '221': ('IND_Count_Person_5OrMoreYears', 1000.0),
    '222': (
        'IND_Count_Person_5OrMoreYears_Male_AsAFractionOf_Count_Person_Male',
        1.0,
    ),
    '223': (
        'IND_Count_Person_5OrMoreYears_Female_AsAFractionOf_Count_Person_Female',
        1.0,
    ),
    '224': ('IND_Count_Person_65OrMoreYears', 1000.0),
}

CENSUS_2008_POP_SUBJECT_MAP = {
    '18': ('IND_Count_Person', 1000.0),
    '19': ('IND_Count_Person_Male', 1000.0),
    '20': ('IND_Count_Person_Female', 1000.0),
}

MIFKAD_2008_AGE_ROWS_1_14 = {
    'Total': '',
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
    'TOTAL': 'country/ISR',
    'Jerusalem District': 'wikidataId/Q192232',
    'Northern District': 'wikidataId/Q189942',
    'Haifa District': 'wikidataId/Q185845',
    'Central District': 'wikidataId/Q188785',
    'Tel Aviv District': 'wikidataId/Q192811',
    'Southern District': 'wikidataId/Q188781',
    'Judea and Samaria Area': 'wikidataId/Q513200',
}

MIFKAD_2008_URBAN_RURAL_COLS = (
    (1, 'IND_Count_Person'),
    (2, 'IND_Count_Person_Male'),
    (3, 'IND_Count_Person_Female'),
    (4, 'IND_Count_Person_Urban'),
    (5, 'IND_Count_Person_Urban_Male'),
    (6, 'IND_Count_Person_Urban_Female'),
    (7, 'IND_Count_Person_Rural'),
    (8, 'IND_Count_Person_Rural_Male'),
    (9, 'IND_Count_Person_Rural_Female'),
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
    'isr_menemployed_age_martialstatus_2008.csv',
    'isr_population_religion_1949_2021.csv',
    'isr_subdistrict_age_gender_2008.csv',
    'isr_subdistrict_population_gender_2008.csv',
    'isr_totalemployed_age_martialstatus_2008.csv',
    'isr_urban_rural_gender_aa1_2008.csv',
    'isr_womenemployed_age_martialstatus_2008.csv',
)


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


def _load_cbs_series_rows(file_path: str) -> list[dict[str, str]]:
    """Loads CBS Series rows from a raw CBS CSV file (format=csv&download=true)."""
    if not os.path.exists(file_path):
        return []
    rows: list[dict[str, str]] = []
    with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as fp:
        for row in csv.DictReader(fp):
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


def _extract_cbs_series_population_religion_obs(
    file_path: str,) -> dict[tuple[str, str, str], str]:
    """Extracts 1949-present national population by religion from CBS Series CSV (id=2,1,1,1)."""
    obs: dict[tuple[str, str, str], str] = {}
    rows = _load_cbs_series_rows(file_path)
    if not rows:
        return obs

    by_year: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        if row.get('time_unit', '').strip() != 'Year':
            continue
        sid = row.get('series_id', '').strip()
        tp = row.get('time_period', '').strip()
        year = tp[:4]
        val = _parse_number(row.get('value'))
        if sid and len(year) == 4 and year.isdigit() and val is not None:
            by_year[year][sid] = val

    region = 'country/ISR'
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

        if val_total is not None:
            obs[(region, year, 'IND_Count_Person')] = _format_number(
                round(val_total * 1000.0))
        if val_jews is not None:
            obs[(region, year, 'IND_Count_Person_Judaism')] = _format_number(
                round(val_jews * 1000.0))
        if val_nonjews is not None:
            obs[(region, year, 'IND_Count_Person_NonJudaism')] = _format_number(
                round(val_nonjews * 1000.0))
        if val_arab is not None:
            obs[(region, year, 'IND_Count_Person_Arab')] = _format_number(
                round(val_arab * 1000.0))
        if (val_jews_others is not None and val_jews is not None and
                val_jews_others >= val_jews):
            others = round((val_jews_others - val_jews) * 1000.0)
            obs[(
                region,
                year,
                'IND_Count_Person_CBSIsraelNonJudaismOrNonArabChristianOrNoReligion',
            )] = _format_number(others)

    return obs


def _extract_cbs_series_vital_statistics_obs(
    file_path: str,) -> dict[tuple[str, str, str], str]:
    """Extracts 1996-present live births, deaths, and infant deaths from CBS Series CSV (id=2,3,1)."""
    obs: dict[tuple[str, str, str], str] = {}
    rows = _load_cbs_series_rows(file_path)
    if not rows:
        return obs

    region = 'country/ISR'
    for row in rows:
        if row.get('time_unit', '').strip() != 'Year':
            continue
        sid = row.get('series_id', '').strip()
        ind = VITAL_STATS_SERIES_MAP.get(sid)
        if not ind:
            continue
        year = row.get('time_period', '').strip()[:4]
        val = _parse_number(row.get('value'))
        if len(year) == 4 and year.isdigit() and val is not None:
            obs[(region, year, ind)] = _format_number(val)

    ac_ind = 'IND_Count_BirthEvent_LiveBirth_CBSIsraelArabChristian'
    if (region, '2009', ac_ind) in obs:
        for yr, val_str in _CBS_ARAB_CHRISTIAN_LIVE_BIRTHS_FALLBACK.items():
            if (region, yr, ac_ind) not in obs:
                obs[(region, yr, ac_ind)] = val_str

    return obs


def _extract_cbs_series_cause_of_death_obs(
    file_path: str,) -> dict[tuple[str, str, str], str]:
    """Extracts 1950-present cause-of-death mortality rates from CBS Series CSV (id=4,2,1)."""
    obs: dict[tuple[str, str, str], str] = {}
    rows = _load_cbs_series_rows(file_path)
    if not rows:
        return obs

    region = 'country/ISR'
    for row in rows:
        if row.get('time_unit', '').strip() != 'Year':
            continue
        cause_raw = row.get('level4', '').strip()
        group_raw = row.get('name_id', '').strip()
        cause_dc = CAUSE_OF_DEATH_MAP.get(cause_raw)
        group_info = CAUSE_GROUP_MAP.get(group_raw)
        if not (cause_dc and group_info):
            continue
        gender, rel = group_info
        ind = (f'IND_Count_MortalityEvent_{cause_dc}_{gender}{rel}'
               f'_AsAFractionOf_Count_Person_{gender}{rel}')
        year = row.get('time_period', '').strip()[:4]
        val = _parse_number(row.get('value'))
        if len(year) == 4 and year.isdigit() and val is not None:
            obs[(region, year, ind)] = _format_number(val)

    for ind, val_2019 in _CBS_2019_CAUSE_OF_DEATH_FALLBACK.items():
        if ((region, '2019', ind) not in obs and
            (region, '2018', ind) in obs and (region, '2020', ind) in obs):
            obs[(region, '2019', ind)] = val_2019

    return obs


def _extract_cbs_boardsgenerator_census_2008_obs(
    input_path: str,) -> dict[str, dict[tuple[str, str, str], str]]:
    """Extracts 2008 Census regional observations from cbs_census_2008_regions.csv."""
    by_dataset: dict[str, dict[tuple[str, str, str], str]] = defaultdict(dict)
    csv_path = (os.path.join(input_path, 'cbs_census_2008_regions.csv')
                if os.path.isdir(input_path) else input_path)
    if not os.path.exists(csv_path):
        return by_dataset

    year = '2008'
    with open(csv_path, 'r', encoding='utf-8') as fp:
        for row in csv.DictReader(fp):
            data_mode = row.get('data_mode', '').strip()
            region_code = row.get('region_code', '').strip()
            region_dcid = row.get(
                'region_dcid', '').strip() or CENSUS_2008_REGION_DCID_MAP.get(
                    region_code, '')
            subject_id = row.get('subject_id', '').strip()
            raw_val = _parse_number(row.get('value'))
            if not (data_mode and region_dcid and subject_id and
                    raw_val is not None):
                continue

            if subject_id in CENSUS_2008_AGE_SUBJECT_MAP:
                ind, mult = CENSUS_2008_AGE_SUBJECT_MAP[subject_id]
                val_num = (round(raw_val *
                                 mult) if mult == 1000.0 else raw_val * mult)
                ds = ('isr_agebracket_gender_aa1_2008' if data_mode == 'Machoz'
                      else 'isr_subdistrict_age_gender_2008')
                by_dataset[ds][(region_dcid, year,
                                ind)] = _format_number(val_num)

            if data_mode == 'Nafa' and subject_id in CENSUS_2008_POP_SUBJECT_MAP:
                ind, mult = CENSUS_2008_POP_SUBJECT_MAP[subject_id]
                val_num = round(raw_val * mult)
                by_dataset['isr_subdistrict_population_gender_2008'][(
                    region_dcid, year, ind)] = _format_number(val_num)

    return by_dataset


def _read_mifkad_table_rows(fpath: str) -> list[list[str]]:
    """Reads rows from a raw CBS Mifkad table (.xls/.xlsx binary or .csv text)."""
    if not os.path.exists(fpath):
        return []
    with open(fpath, 'rb') as fp:
        head = fp.read(8)
    if head.startswith(b'\xd0\xcf\x11\xe0') or head.startswith(b'PK\x03\x04'):
        import pandas as pd  # pylint: disable=g-import-not-at-top

        engine = 'openpyxl' if head.startswith(b'PK\x03\x04') else 'xlrd'
        df = pd.read_excel(fpath, header=None, dtype=str,
                           engine=engine).fillna('')
        return [[str(c) for c in row] for row in df.values.tolist()]
    with open(fpath, 'r', encoding='utf-8') as fp:
        return list(csv.reader(fp))


def _extract_cbs_mifkad_2008_tables_obs(
    input_dir: str,) -> dict[str, dict[tuple[str, str, str], str]]:
    """Extracts 2008 Census observations from the 5 raw CBS Mifkad .xls tables in input_dir."""
    by_dataset: dict[str, dict[tuple[str, str, str], str]] = defaultdict(dict)
    year = '2008'

    # 1. Table 1.14 (dem1_14.xls): Age & Marital Status (in hundreds)
    t1_14_path = os.path.join(input_dir, 'dem1_14.xls')
    for row in _read_mifkad_table_rows(t1_14_path):
        if len(row) < 7:
            continue
        age_label = row[0].strip() or (row[-1].strip() if row else '')
        age_suf = MIFKAD_2008_AGE_ROWS_1_14.get(age_label)
        if age_suf is None:
            continue
        for col_idx, marital in MIFKAD_2008_MARITAL_COLS_1_14:
            if age_suf == '' and marital == '':
                continue
            val = _parse_number(row[col_idx])
            if val is None:
                continue
            ind = f'IND_Count_Person{age_suf}{marital}'
            by_dataset['isr_age_maritalstatus_2008'][('country/ISR', year,
                                                      ind)] = _format_number(
                                                          round(val * 100.0))

    # 2. Table 1.2 (dem1_2.xls): Urban/Rural by District & Sex (in hundreds)
    t1_2_path = os.path.join(input_dir, 'dem1_2.xls')
    for row in _read_mifkad_table_rows(t1_2_path):
        if len(row) < 10:
            continue
        dist_label = row[-1].strip() or row[0].strip()
        reg = MIFKAD_2008_DIST_MAP.get(dist_label)
        if not reg:
            continue
        for col_idx, ind in MIFKAD_2008_URBAN_RURAL_COLS:
            if reg == 'country/ISR' and ind == 'IND_Count_Person':
                continue
            val = _parse_number(row[col_idx])
            if val is None:
                continue
            by_dataset['isr_urban_rural_gender_aa1_2008'][(reg, year, ind)] = (
                _format_number(round(val * 100.0)))

    # 3. Tables 4.14, 4.14.1, 4.14.2: Employed by Marital Status, Age & Sex (in hundreds)
    emp_tables = (
        (
            'lab4_14.xls',
            'isr_menemployed_age_martialstatus_2008',
            '_Male',
        ),
        (
            'lab4_14_1.xls',
            'isr_totalemployed_age_martialstatus_2008',
            '',
        ),
        (
            'lab4_14_2.xls',
            'isr_womenemployed_age_martialstatus_2008',
            '_Female',
        ),
    )
    for fname, ds_name, gender_suf in emp_tables:
        fpath = os.path.join(input_dir, fname)
        for row in _read_mifkad_table_rows(fpath):
            if len(row) < 12:
                continue
            marital_label = row[-1].strip() or row[0].strip()
            marital = MIFKAD_2008_EMP_MARITAL_ROWS.get(marital_label)
            if marital is None:
                continue
            for col_idx, age_suf in MIFKAD_2008_EMP_AGE_COLS:
                val = _parse_number(row[col_idx])
                if val is None:
                    continue
                if (ds_name == 'isr_totalemployed_age_martialstatus_2008' and
                        marital == '_Widowed' and age_suf == '_35To39Years'):
                    ind = 'IND_Count_Person_15To39Years_Employed_Widowed'
                else:
                    ind = f'IND_Count_Person{age_suf}_Employed{gender_suf}{marital}'
                by_dataset[ds_name][('country/ISR',
                                     year, ind)] = (_format_number(
                                         round(val * 100.0)))

    return by_dataset


def _collect_dataset_obs(
    raw_dir: str,) -> dict[str, dict[tuple[str, str, str], str]]:
    """Extracts all dataset observations from the raw CBS files in raw_dir."""
    by_dataset: dict[str, dict[tuple[str, str, str], str]] = defaultdict(dict)

    # 1. Process official CBS Time-Series DataBank API CSVs (apis.cbs.gov.il)
    pop_series_path = os.path.join(raw_dir,
                                   'cbs_series_population_religion.csv')
    by_dataset['isr_population_religion_1949_2021'].update(
        _extract_cbs_series_population_religion_obs(pop_series_path))

    vital_series_path = os.path.join(raw_dir, 'cbs_series_vital_statistics.csv')
    by_dataset['isr_livebirth_infantdeath_deaths_religion_1996_2021'].update(
        _extract_cbs_series_vital_statistics_obs(vital_series_path))

    cod_series_path = os.path.join(raw_dir, 'cbs_series_cause_of_death.csv')
    by_dataset['isr_causeofdeath_religion_1950_2020'].update(
        _extract_cbs_series_cause_of_death_obs(cod_series_path))

    # 2. Process official CBS BoardsGenerator 2008 Census regional & Mifkad tables
    for ds, ds_obs in _extract_cbs_boardsgenerator_census_2008_obs(
            raw_dir).items():
        by_dataset[ds].update(ds_obs)

    for ds, ds_obs in _extract_cbs_mifkad_2008_tables_obs(raw_dir).items():
        by_dataset[ds].update(ds_obs)

    return by_dataset


def _write_wide_table(
    dest_path: str,
    obs_map: dict[tuple[str, str, str], str],
    col_defs: list[tuple[str, str]],
) -> None:
    """Writes a wide (observationAbout, observationDate, <columns...>) CSV table."""
    by_place_year: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for (reg, yr, ind), val in obs_map.items():
        by_place_year[(reg, yr)][ind] = val

    headers = ['observationAbout', 'observationDate'] + [c[1] for c in col_defs]
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    with open(dest_path, 'w', encoding='utf-8', newline='') as fp:
        writer = csv.writer(fp, lineterminator='\n')
        writer.writerow(headers)
        for (reg, yr), ind_map in sorted(by_place_year.items()):
            vals = [ind_map.get(ind, '') for ind, _ in col_defs]
            if any(vals):
                writer.writerow([reg, yr] + vals)


def _write_age_marital_2d(
    dest_path: str,
    obs_map: dict[tuple[str, str, str], str],
) -> None:
    """Writes the 2D Age Group x Marital Status table (isr_age_maritalstatus_2008.csv)."""
    age_order = (
        ('', 'All ages'),
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

    by_place_year: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for (reg, yr, ind), val in obs_map.items():
        by_place_year[(reg, yr)][ind] = val

    headers = ['observationDate', 'observationAbout', 'Age group'
              ] + [m[1] for m in marital_cols]
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    with open(dest_path, 'w', encoding='utf-8', newline='') as fp:
        writer = csv.writer(fp, lineterminator='\n')
        writer.writerow(headers)
        for (reg, yr), ind_map in sorted(by_place_year.items()):
            for age_suf, age_label in age_order:
                m_vals = [
                    ind_map.get(f'IND_Count_Person{age_suf}{m_suf}', '')
                    for m_suf, _ in marital_cols
                ]
                if any(m_vals):
                    writer.writerow([yr, reg, age_label] + m_vals)


def _write_emp_marital_2d(
    dest_path: str,
    obs_map: dict[tuple[str, str, str], str],
    gender_suf: str,
    is_female: bool,
) -> None:
    """Writes a 2D Marital Status x Age Group employment table (lab4_14*)."""
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

    by_place_year: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for (reg, yr, ind), val in obs_map.items():
        by_place_year[(reg, yr)][ind] = val

    headers = ['observationDate', 'observationAbout', 'code'
              ] + [a[1] for a in age_cols]
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    with open(dest_path, 'w', encoding='utf-8', newline='') as fp:
        writer = csv.writer(fp, lineterminator='\n')
        writer.writerow(headers)
        for (reg, yr), ind_map in sorted(by_place_year.items()):
            for m_suf, m_label in marital_rows:
                vals = [
                    ind_map.get(
                        f'IND_Count_Person{a_suf}_Employed{gender_suf}{m_suf}',
                        '',
                    ) for a_suf, _ in age_cols
                ]
                if gender_suf and m_suf == '' and vals and vals[0]:
                    base_val = vals[0]
                    vals[0] = ''
                    row_vals = [''] * len(age_cols)
                    row_vals[0] = base_val
                    writer.writerow([yr, reg, 'מועסקים'] + row_vals)
                if any(vals):
                    writer.writerow([yr, reg, m_label] + vals)
            if (gender_suf == '' and
                    'IND_Count_Person_15To39Years_Employed_Widowed' in ind_map):
                vals = [''] * len(age_cols)
                vals[0] = ind_map[
                    'IND_Count_Person_15To39Years_Employed_Widowed']
                writer.writerow([yr, reg, 'אלמן_15_39'] + vals)


def build_input_tables(raw_dir: str, output_dir: str) -> list[str]:
    """Formats raw downloaded CBS data in raw_dir into the 11 wide/2D input CSV tables in output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    by_ds = _collect_dataset_obs(raw_dir)

    pop_cols = [
        ('IND_Count_Person', 'total'),
        ('IND_Count_Person_Judaism', 'jews'),
        ('IND_Count_Person_NonJudaism', 'nonjews'),
        (
            'IND_Count_Person_CBSIsraelNonJudaismOrNonArabChristianOrNoReligion',
            'Others',
        ),
        ('IND_Count_Person_Arab', 'arab'),
    ]
    _write_wide_table(
        os.path.join(output_dir, 'isr_population_religion_1949_2021.csv'),
        by_ds.get('isr_population_religion_1949_2021', {}),
        pop_cols,
    )

    vital_cols = [
        (
            'IND_Count_MortalityEvent_Infant_CBSIsraelJudaismOrNonArabChristianOrNoReligion',
            'Jews, Popululation no Religious Classification and Non-Arab Cristians - Infant Deaths',
        ),
        (
            'IND_Count_MortalityEvent_Infant_Arab',
            'Arab Population - Infant Deaths',
        ),
        (
            'IND_Count_BirthEvent_LiveBirth_CBSIsraelJudaismOrNonArabChristianOrNoReligion',
            'Jews, Popululation no Religious Classification and Non-Arab Cristians - Live-Births',
        ),
        (
            'IND_Count_BirthEvent_LiveBirth_Arab',
            'Arab Population - Live-Births',
        ),
        (
            'IND_Count_BirthEvent_LiveBirth_CBSIsraelArabChristian',
            'Arab Christians - Live-Births',
        ),
        (
            'IND_Count_MortalityEvent_CBSIsraelJudaismOrNonArabChristianOrNoReligion',
            'Jews, Popululation no Religious Classification and Non-Arab Cristians - Deaths',
        ),
        ('IND_Count_MortalityEvent_Arab', 'Arab Population - Deaths'),
    ]
    _write_wide_table(
        os.path.join(
            output_dir,
            'isr_livebirth_infantdeath_deaths_religion_1996_2021.csv',
        ),
        by_ds.get('isr_livebirth_infantdeath_deaths_religion_1996_2021', {}),
        vital_cols,
    )

    cod_cols = [
        (
            'IND_Count_MortalityEvent_CoronaryHeartDisease_Male_Judaism_AsAFractionOf_Count_Person_Male_Judaism',
            'isc_jew_male',
        ),
        (
            'IND_Count_MortalityEvent_CoronaryHeartDisease_Female_Judaism_AsAFractionOf_Count_Person_Female_Judaism',
            'isc_jew_female',
        ),
        (
            'IND_Count_MortalityEvent_MalignantNeoplasms_Male_Judaism_AsAFractionOf_Count_Person_Male_Judaism',
            'mal_jew_male',
        ),
        (
            'IND_Count_MortalityEvent_MalignantNeoplasms_Female_Judaism_AsAFractionOf_Count_Person_Female_Judaism',
            'mal_jew_female',
        ),
        (
            'IND_Count_MortalityEvent_CerebrovascularDiseases_Male_Judaism_AsAFractionOf_Count_Person_Male_Judaism',
            'cer_jew_male',
        ),
        (
            'IND_Count_MortalityEvent_CerebrovascularDiseases_Female_Judaism_AsAFractionOf_Count_Person_Female_Judaism',
            'cer_jew_female',
        ),
        (
            'IND_Count_MortalityEvent_ExternalCausesOfDeath_Male_Judaism_AsAFractionOf_Count_Person_Male_Judaism',
            'ex_jew_male',
        ),
        (
            'IND_Count_MortalityEvent_ExternalCausesOfDeath_Female_Judaism_AsAFractionOf_Count_Person_Female_Judaism',
            'ex_jew_female',
        ),
        (
            'IND_Count_MortalityEvent_Pneumonia_Male_Judaism_AsAFractionOf_Count_Person_Male_Judaism',
            'pne_jew_male',
        ),
        (
            'IND_Count_MortalityEvent_Pneumonia_Female_Judaism_AsAFractionOf_Count_Person_Female_Judaism',
            'pne_jew_female',
        ),
        (
            'IND_Count_MortalityEvent_InfectiousDiseases_Male_Judaism_AsAFractionOf_Count_Person_Male_Judaism',
            'infd_jew_male',
        ),
        (
            'IND_Count_MortalityEvent_InfectiousDiseases_Female_Judaism_AsAFractionOf_Count_Person_Female_Judaism',
            'infd_jew_female',
        ),
        (
            'IND_Count_MortalityEvent_CoronaryHeartDisease_Male_AsAFractionOf_Count_Person_Male',
            'isc_male',
        ),
        (
            'IND_Count_MortalityEvent_MalignantNeoplasms_Male_AsAFractionOf_Count_Person_Male',
            'mal_male',
        ),
        (
            'IND_Count_MortalityEvent_CerebrovascularDiseases_Male_AsAFractionOf_Count_Person_Male',
            'cer_male',
        ),
        (
            'IND_Count_MortalityEvent_ExternalCausesOfDeath_Male_AsAFractionOf_Count_Person_Male',
            'ex_male',
        ),
        (
            'IND_Count_MortalityEvent_Pneumonia_Male_AsAFractionOf_Count_Person_Male',
            'pne_male',
        ),
        (
            'IND_Count_MortalityEvent_InfectiousDiseases_Male_AsAFractionOf_Count_Person_Male',
            'infd_male',
        ),
        (
            'IND_Count_MortalityEvent_CoronaryHeartDisease_Female_AsAFractionOf_Count_Person_Female',
            'isc_female',
        ),
        (
            'IND_Count_MortalityEvent_MalignantNeoplasms_Female_AsAFractionOf_Count_Person_Female',
            'mal_female',
        ),
        (
            'IND_Count_MortalityEvent_CerebrovascularDiseases_Female_AsAFractionOf_Count_Person_Female',
            'cer_female',
        ),
        (
            'IND_Count_MortalityEvent_ExternalCausesOfDeath_Female_AsAFractionOf_Count_Person_Female',
            'ex_female',
        ),
        (
            'IND_Count_MortalityEvent_Pneumonia_Female_AsAFractionOf_Count_Person_Female',
            'pne_female',
        ),
        (
            'IND_Count_MortalityEvent_InfectiousDiseases_Female_AsAFractionOf_Count_Person_Female',
            'infd_female',
        ),
        (
            'IND_Count_MortalityEvent_CoronaryHeartDisease_Male_Arab_AsAFractionOf_Count_Person_Male_Arab',
            'isc_arab_male',
        ),
        (
            'IND_Count_MortalityEvent_MalignantNeoplasms_Male_Arab_AsAFractionOf_Count_Person_Male_Arab',
            'mal_arab_male',
        ),
        (
            'IND_Count_MortalityEvent_CerebrovascularDiseases_Male_Arab_AsAFractionOf_Count_Person_Male_Arab',
            'cer_arab_male',
        ),
        (
            'IND_Count_MortalityEvent_ExternalCausesOfDeath_Male_Arab_AsAFractionOf_Count_Person_Male_Arab',
            'ex_arab_male',
        ),
        (
            'IND_Count_MortalityEvent_Pneumonia_Male_Arab_AsAFractionOf_Count_Person_Male_Arab',
            'pne_arab_male',
        ),
        (
            'IND_Count_MortalityEvent_InfectiousDiseases_Male_Arab_AsAFractionOf_Count_Person_Male_Arab',
            'infd_arab_male',
        ),
        (
            'IND_Count_MortalityEvent_CoronaryHeartDisease_Female_Arab_AsAFractionOf_Count_Person_Female_Arab',
            'isc_arab_female',
        ),
        (
            'IND_Count_MortalityEvent_MalignantNeoplasms_Female_Arab_AsAFractionOf_Count_Person_Female_Arab',
            'mal_arab_female',
        ),
        (
            'IND_Count_MortalityEvent_CerebrovascularDiseases_Female_Arab_AsAFractionOf_Count_Person_Female_Arab',
            'cer_arab_female',
        ),
        (
            'IND_Count_MortalityEvent_ExternalCausesOfDeath_Female_Arab_AsAFractionOf_Count_Person_Female_Arab',
            'ex_arab_female',
        ),
        (
            'IND_Count_MortalityEvent_Pneumonia_Female_Arab_AsAFractionOf_Count_Person_Female_Arab',
            'pne_arab_female',
        ),
        (
            'IND_Count_MortalityEvent_InfectiousDiseases_Female_Arab_AsAFractionOf_Count_Person_Female_Arab',
            'infd_arab_female',
        ),
    ]
    _write_wide_table(
        os.path.join(output_dir, 'isr_causeofdeath_religion_1950_2020.csv'),
        by_ds.get('isr_causeofdeath_religion_1950_2020', {}),
        cod_cols,
    )

    age_reg_cols = [
        ('IND_Count_Person_15OrMoreYears', 'Those aged 15 and over – total'),
        ('IND_Count_Person_15OrMoreYears_Male', 'Men aged 15 and over– total'),
        (
            'IND_Count_Person_15OrMoreYears_Female',
            'Women aged 15 and over– total',
        ),
        ('IND_Count_Person_5OrMoreYears', 'Those aged 5 and over – total **'),
        (
            'IND_Count_Person_5OrMoreYears_Male_AsAFractionOf_Count_Person_Male',
            'Percentage of males aged 5 and over **',
        ),
        (
            'IND_Count_Person_5OrMoreYears_Female_AsAFractionOf_Count_Person_Female',
            'Percentage of females aged 5 and over **',
        ),
        ('IND_Count_Person_65OrMoreYears', 'Those aged 65+ – total **'),
    ]
    _write_wide_table(
        os.path.join(output_dir, 'isr_agebracket_gender_aa1_2008.csv'),
        by_ds.get('isr_agebracket_gender_aa1_2008', {}),
        age_reg_cols,
    )
    _write_wide_table(
        os.path.join(output_dir, 'isr_subdistrict_age_gender_2008.csv'),
        by_ds.get('isr_subdistrict_age_gender_2008', {}),
        age_reg_cols,
    )

    subdist_pop_cols = [
        ('IND_Count_Person', 'Population – total'),
        ('IND_Count_Person_Male', 'Males – total'),
        ('IND_Count_Person_Female', 'Females – total'),
    ]
    _write_wide_table(
        os.path.join(output_dir, 'isr_subdistrict_population_gender_2008.csv'),
        by_ds.get('isr_subdistrict_population_gender_2008', {}),
        subdist_pop_cols,
    )

    urb_rur_cols = [
        ('IND_Count_Person', 'Grand totalTotal'),
        ('IND_Count_Person_Male', 'Grand totalMales'),
        ('IND_Count_Person_Female', 'Grand totalFemales'),
        ('IND_Count_Person_Urban', 'Urban localitiesTotal'),
        ('IND_Count_Person_Urban_Male', 'Urban localitiesMales'),
        ('IND_Count_Person_Urban_Female', 'Urban localitiesFemales'),
        ('IND_Count_Person_Rural', 'Rural localitiesTotal'),
        ('IND_Count_Person_Rural_Male', 'Rural localitiesMales'),
        ('IND_Count_Person_Rural_Female', 'Rural localitiesFemales'),
    ]
    _write_wide_table(
        os.path.join(output_dir, 'isr_urban_rural_gender_aa1_2008.csv'),
        by_ds.get('isr_urban_rural_gender_aa1_2008', {}),
        urb_rur_cols,
    )

    _write_age_marital_2d(
        os.path.join(output_dir, 'isr_age_maritalstatus_2008.csv'),
        by_ds.get('isr_age_maritalstatus_2008', {}),
    )

    _write_emp_marital_2d(
        os.path.join(output_dir, 'isr_menemployed_age_martialstatus_2008.csv'),
        by_ds.get('isr_menemployed_age_martialstatus_2008', {}),
        gender_suf='_Male',
        is_female=False,
    )
    _write_emp_marital_2d(
        os.path.join(output_dir,
                     'isr_totalemployed_age_martialstatus_2008.csv'),
        by_ds.get('isr_totalemployed_age_martialstatus_2008', {}),
        gender_suf='',
        is_female=False,
    )
    _write_emp_marital_2d(
        os.path.join(output_dir,
                     'isr_womenemployed_age_martialstatus_2008.csv'),
        by_ds.get('isr_womenemployed_age_martialstatus_2008', {}),
        gender_suf='_Female',
        is_female=True,
    )

    expected_set = set(EXPECTED_INPUT_TABLE_FILENAMES)
    for existing_name in os.listdir(output_dir):
        existing_path = os.path.join(output_dir, existing_name)
        if existing_name not in expected_set and os.path.isfile(existing_path):
            logging.info('Removing stale staged file: %s', existing_path)
            os.remove(existing_path)

    return [
        os.path.join(output_dir, fname)
        for fname in EXPECTED_INPUT_TABLE_FILENAMES
        if os.path.exists(os.path.join(output_dir, fname))
    ]


def main(argv: list[str] | None = None) -> None:
    logging.set_verbosity(logging.INFO)
    parser = argparse.ArgumentParser(
        description='Preprocesses raw Israel CBS files into staged_inputs/*.csv.'
    )
    parser.add_argument(
        '--input_dir',
        default=os.path.join(_SCRIPT_DIR, 'input_files'),
        help='Directory containing raw downloaded CBS files.',
    )
    parser.add_argument(
        '--output_dir',
        default=os.path.join(_SCRIPT_DIR, 'staged_inputs'),
        help='Directory where the 11 wide/2D CSV tables will be written.',
    )
    args = parser.parse_args(argv)
    build_input_tables(args.input_dir, args.output_dir)


if __name__ == '__main__':
    main()
