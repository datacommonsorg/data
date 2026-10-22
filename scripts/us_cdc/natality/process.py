# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""End-to-end data processing pipeline for CDC Wonder Natality.

Consolidates, cleans, and formats Natality data across country, state, and county
geographic resolutions, generating cleaned CSVs and TMCF templates for
automated ingestion into Data Commons.
"""

import csv
import glob
import os
import re
import pandas as pd
from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_INPUT_DIR = os.path.join(_SCRIPT_DIR, 'input_files')
_DEFAULT_OUTPUT_DIR = os.path.join(_SCRIPT_DIR, 'output')

flags.DEFINE_string(
    'input_path', _DEFAULT_INPUT_DIR,
    'Path to input directory containing downloaded TSV/CSV files.')
flags.DEFINE_string(
    'output_path', _DEFAULT_OUTPUT_DIR,
    'Path to directory where output CSV and TMCF files will be written.')
flags.DEFINE_boolean(
    'use_test_data', False,
    'Generate mock baseline data if input directory has no files.')

_FLAGS = flags.FLAGS

_MEASURE_MAP = {
    'Births': ('Count_BirthEvent_LiveBirth', ''),
    'Average Age of Mother (years)':
        ('Mean_MothersAge_BirthEvent_LiveBirth', 'Year'),
    'Average OE Gestational Age (weeks)':
        ('Mean_OeGestationalAge_BirthEvent_LiveBirth', 'Week'),
    'Average LMP Gestational Age (weeks)':
        ('Mean_LmpGestationalAge_BirthEvent_LiveBirth', 'Week'),
    'Average Birth Weight (grams)':
        ('Mean_BirthWeight_BirthEvent_LiveBirth', 'Gram'),
    'Average Pre-pregnancy BMI':
        ('Mean_PrePregnancyBMI_BirthEvent_LiveBirth', ''),
    'Average Number of Prenatal Visits':
        ('Mean_PrenatalVisitCount_BirthEvent_LiveBirth', ''),
    'Average Interval Since Last Live Birth (months)':
        ('Mean_IntervalSinceLastBirth_BirthEvent_LiveBirth', 'Month'),
    'Average Interval Since Last Other Pregnancy Outcome (months)': (
        'Mean_IntervalSinceLastPregnancyOutcomeNotLiveBirth_BirthEvent_LiveBirth',
        'Month'),
}

_DEMOGRAPHIC_CODE_MAP = {
    'Age of Mother 13 Code': {
        '15-': '_Mother15OrMoreYears',
        '15': '_Mother15Years',
        '16': '_Mother16Years',
        '17': '_Mother17Years',
        '18': '_Mother18Years',
        '19': '_Mother19Years',
        '20-24': '_Mother20To24Years',
        '25-29': '_Mother25To29Years',
        '30-34': '_Mother30To34Years',
        '35-39': '_Mother35To39Years',
        '40-44': '_Mother40To44Years',
        '45-49': '_Mother45To49Years',
        '50+': '_Mother50OrMoreYears',
    },
    "Mother's Single Race 15 Code": {
        '1': '_MotherWhiteAlone',
        '2': '_MotherBlackOrAfricanAmericanAlone',
        '3': '_MotherAmericanIndianOrAlaskaNativeAlone',
        '4': '_MotherAsianIndian',
        '5': '_MotherChinese',
        '6': '_MotherFilipino',
        '7': '_MotherJapanese',
        '8': '_MotherKorean',
        '9': '_MotherVietnamese',
        '10': '_MotherOtherAsian',
        '11': '_MotherNativeHawaiian',
        '12': '_MotherGuamanianOrChamorro',
        '13': '_MotherSamoan',
        '14': '_MotherOtherPacificIslander',
        '15': '_MotherTwoOrMoreRaces',
        '99': '_MotherRaceUnknownOrNotStated',
    },
    "Mother's Education Code": {
        '1': '_MotherLessThan9ThGrade',
        '2': '_Mother9ThTo12ThGradeNoDiploma',
        '3': '_MotherHighSchoolGraduateGedOrAlternative',
        '4': '_MotherSomeCollegeNoDegree',
        '5': '_MotherAssociatesDegree',
        '6': '_MotherBachelorsDegree',
        '7': '_MotherMastersDegree',
        '8': '_MotherDoctorateDegreeOrProfessionalSchoolDegree',
        'Unk': '_MotherEducationalAttainmentUnknownOrNotStated',
    },
    "Mother's Hispanic Origin Code": {
        '2135-2': '_MotherHispanicOrLatino',
        '2186-5': '_MotherNotHispanicOrLatino',
        '9': '_MotherEthnicityUnknownOrNotStated',
    },
    'Marital Status Code': {
        '1': '_MotherNowMarried',
        '2': '_MotherUnmarried',
        '9': '_MotherMaritalStatusUnknownOrNotStated',
    },
    "Mother's Nativity Code": {
        '1': '_MotherNative',
        '2': '_MotherForeignBorn',
        '3': '_MotherNativityUnknownOrNotStated',
    },
}

_ZERO_PLACEHOLDER_SUFFIXES = (
    '_MotherMaritalStatusUnknownOrNotStated',
    '_MotherRaceUnknownOrNotStated',
)

_UNIT_NORMALIZATION = {
    'Weeks': 'Week',
    'Grams': 'Gram',
    'Months': 'Month',
    'Years': 'Year',
}


def _filter_zero_unknown_placeholders(df: pd.DataFrame) -> pd.DataFrame:
    """Removes 0.0 placeholder rows on Not Available unknown/unstated slices."""
    if df.empty or 'StatVar' not in df.columns or 'Quantity' not in df.columns:
        return df
    nums = pd.to_numeric(df['Quantity'], errors='coerce')
    unk_mask = df['StatVar'].str.endswith(_ZERO_PLACEHOLDER_SUFFIXES, na=False)
    if 'Year' in df.columns:
        yr_nums = pd.to_numeric(df['Year'], errors='coerce')
        unk_mask = unk_mask & (yr_nums >= 2016)
    drop_mask = unk_mask & (nums == 0)
    return df.loc[~drop_mask].copy()


def _normalize_quantities(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes Count_* StatVar quantities to integer strings without decimals."""
    if df.empty or 'StatVar' not in df.columns or 'Quantity' not in df.columns:
        return df
    count_mask = df['StatVar'].str.startswith('Count')
    nums = pd.to_numeric(df['Quantity'], errors='coerce')
    valid_mask = count_mask & nums.notna()
    df.loc[valid_mask, 'Quantity'] = (
        nums.loc[valid_mask].round().astype('int64').astype(str))
    return df


_COUNTRY_TMCF_TEMPLATE = """Node: E:CDCWonderNatality->E0
typeOf: dcs:StatVarObservation
measurementMethod: dcs:DataCommonsAggregate
observationAbout: country/USA
observationDate: C:CDCWonderNatality->Year
variableMeasured: C:CDCWonderNatality->StatVar
observationPeriod: "P1Y"
value: C:CDCWonderNatality->Quantity
"""

_GEO_TMCF_TEMPLATE = """Node: E:CDCWonderNatality->E0
typeOf: dcs:StatVarObservation
observationAbout: C:CDCWonderNatality->Geo
observationDate: C:CDCWonderNatality->Year
variableMeasured: C:CDCWonderNatality->StatVar
observationPeriod: "P1Y"
value: C:CDCWonderNatality->Quantity
unit: C:CDCWonderNatality->Unit
"""


def parse_wonder_tsv(tsv_path: str, geo_type: str) -> pd.DataFrame:
    """Parses raw tab-delimited export file downloaded from CDC WONDER."""
    if not os.path.exists(tsv_path) or os.path.getsize(tsv_path) == 0:
        return pd.DataFrame(
            columns=['Year', 'Geo', 'StatVar', 'Quantity', 'Unit'])

    valid_lines = []
    with open(tsv_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            if (stripped.startswith('"---"') or stripped.startswith('---') or
                    stripped.startswith('Caveats:') or
                    stripped.startswith('"Query Date:')):
                break
            if stripped.startswith('"Total"') or stripped.startswith('Total'):
                continue
            valid_lines.append(line.rstrip('\r\n'))

    if not valid_lines:
        return pd.DataFrame(
            columns=['Year', 'Geo', 'StatVar', 'Quantity', 'Unit'])

    reader = csv.reader(valid_lines, delimiter='\t')
    try:
        header = [col.strip().strip('"') for col in next(reader)]
    except StopIteration:
        return pd.DataFrame(
            columns=['Year', 'Geo', 'StatVar', 'Quantity', 'Unit'])

    missing_measures = [col for col in _MEASURE_MAP if col not in header]
    if missing_measures:
        raise ValueError(
            f'Missing expected measure columns in {tsv_path}: {missing_measures}'
        )

    code_col_idx = None
    year_col_idx = None
    demo_col_name = None
    demo_col_idx = None
    for idx, col in enumerate(header):
        if 'Code' in col and ('State' in col or 'County' in col):
            code_col_idx = idx
        elif col in ('Year', 'Year Code') and year_col_idx is None:
            year_col_idx = idx
        elif col in _DEMOGRAPHIC_CODE_MAP and demo_col_idx is None:
            demo_col_name = col
            demo_col_idx = idx

    measure_col_indices = {
        col_name: header.index(col_name) for col_name in _MEASURE_MAP
    }

    rows = []
    for line_parts in reader:
        parts = [p.strip().strip('"') for p in line_parts]
        if len(parts) != len(header):
            continue

        fips = parts[code_col_idx] if code_col_idx is not None else ''
        year = parts[year_col_idx] if year_col_idx is not None else ''
        if not re.match(r'^\d{4}$', year):
            continue

        if geo_type == 'state':
            if not re.match(r'^\d{2}$', fips) or fips in ('99', '00'):
                continue
            geo_dcid = f'geoId/{fips}'
        else:
            if not re.match(r'^\d{5}$', fips) or fips in (
                    '99999', '00000') or fips.endswith('999'):
                continue
            geo_dcid = f'geoId/{fips}'

        statvar_suffix = ''
        if demo_col_idx is not None:
            demo_code = parts[demo_col_idx]
            code_map = _DEMOGRAPHIC_CODE_MAP[demo_col_name]
            if demo_code not in code_map:
                continue
            statvar_suffix = code_map[demo_code]

        for col_name, (base_statvar, unit) in _MEASURE_MAP.items():
            if (demo_col_name == 'Age of Mother 13 Code' and
                    col_name == 'Average Age of Mother (years)'):
                continue
            val = parts[measure_col_indices[col_name]].strip()
            if not val or val.lower() in ('unreliable', 'suppressed', 'missing',
                                          'not available', 'not applicable'):
                continue
            try:
                num = float(val)
                statvar = f'{base_statvar}{statvar_suffix}'
                qty_str = str(int(round(num))) if statvar.startswith(
                    'Count') else f'{num:.2f}'
                rows.append({
                    'Year': year,
                    'Geo': geo_dcid,
                    'StatVar': statvar,
                    'Quantity': qty_str,
                    'Unit': unit
                })
            except ValueError:
                continue

    return pd.DataFrame(rows)


def aggregate_state_to_country(state_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates state-level Count_* StatVars to national country totals."""
    df_count = state_df.loc[state_df['StatVar'].str.startswith('Count')].copy()
    df_count = _filter_zero_unknown_placeholders(df_count)
    if 'Unit' in df_count.columns:
        df_count.drop('Unit', axis=1, inplace=True)
    df_count.drop_duplicates(subset=['Year', 'Geo', 'StatVar'],
                             keep='last',
                             inplace=True)
    df_count['Quantity'] = pd.to_numeric(df_count['Quantity'], errors='coerce')
    df_count.dropna(subset=['Quantity'], inplace=True)
    if df_count.empty:
        return pd.DataFrame(columns=['Year', 'StatVar', 'Quantity'])

    country_df = df_count.groupby(by=['Year', 'StatVar'],
                                  as_index=False).agg({'Quantity': 'sum'})
    if pd.api.types.is_numeric_dtype(country_df['Quantity']):
        country_df['Quantity'] = (
            country_df['Quantity'].round().astype('int64').astype(str))
    country_df.sort_values(by=['Year', 'StatVar'], inplace=True)
    return country_df


def _extract_year_bracket(filepath: str) -> tuple:
    """Extracts (start_year, end_year) tuple from bracket filename."""
    basename = os.path.basename(filepath)
    m4 = re.search(r'(\d{4})-(\d{4})', basename)
    if m4:
        return (int(m4.group(1)), int(m4.group(2)))
    m2 = re.search(r'(\d{2})-(\d{2})', basename)
    if m2:
        s_yr = int(m2.group(1))
        e_yr = int(m2.group(2))
        start_year = 1900 + s_yr if s_yr >= 50 else 2000 + s_yr
        end_year = 1900 + e_yr if e_yr >= 50 else 2000 + e_yr
        return (start_year, end_year)
    m_single = re.search(r'(\d{4})', basename)
    if m_single:
        yr = int(m_single.group(1))
        return (yr, yr)
    return (9999, 9999)


def write_tmcf_files(output_dir: str):
    """Writes template MCF files for country, state, and county to output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, 'country.tmcf'), 'w',
              encoding='utf-8') as f:
        f.write(_COUNTRY_TMCF_TEMPLATE)
    with open(os.path.join(output_dir, 'state.tmcf'), 'w',
              encoding='utf-8') as f:
        f.write(_GEO_TMCF_TEMPLATE)
    with open(os.path.join(output_dir, 'county.tmcf'), 'w',
              encoding='utf-8') as f:
        f.write(_GEO_TMCF_TEMPLATE)
    logging.info('Written TMCF templates to output directory.')


def _find_csvs(input_dir: str, keyword: str) -> list:
    """Finds CSV files containing keyword in filename within input_dir or subdirs."""
    found = []
    for root, _, files in os.walk(input_dir):
        for f in files:
            f_lower = f.lower()
            if f_lower.endswith('.csv') and keyword in f_lower:
                found.append(os.path.join(root, f))
    return sorted(list(set(found)))


def process_data(input_dir: str, output_dir: str) -> bool:
    """Processes downloaded TSVs or existing CSVs into final output files."""
    os.makedirs(output_dir, exist_ok=True)

    state_raw_files = [os.path.join(input_dir, 'state_raw.tsv')] + sorted(
        glob.glob(os.path.join(input_dir, 'state_*_raw.tsv')))
    county_raw_files = [os.path.join(input_dir, 'county_raw.tsv')] + sorted(
        glob.glob(os.path.join(input_dir, 'county_*_raw.tsv')))

    live_state_dfs = []
    for raw_path in state_raw_files:
        if os.path.exists(raw_path) and os.path.getsize(raw_path) > 0:
            logging.info(f'Parsing raw State TSV: {raw_path}')
            df = parse_wonder_tsv(raw_path, 'state')
            if not df.empty:
                live_state_dfs.append(df)

    live_county_dfs = []
    for raw_path in county_raw_files:
        if os.path.exists(raw_path) and os.path.getsize(raw_path) > 0:
            logging.info(f'Parsing raw County TSV: {raw_path}')
            df = parse_wonder_tsv(raw_path, 'county')
            if not df.empty:
                live_county_dfs.append(df)

    # Incorporate pre-existing CSV brackets / historical baseline in input_dir
    pre_state_csvs = [
        f for f in _find_csvs(input_dir, 'state')
        if not f.startswith(output_dir) and not f.endswith('raw.tsv')
    ]
    pre_county_csvs = [
        f for f in _find_csvs(input_dir, 'county')
        if not f.startswith(output_dir) and not f.endswith('raw.tsv')
    ]
    pre_state_csvs.sort(key=_extract_year_bracket)
    pre_county_csvs.sort(key=_extract_year_bracket)

    state_dfs = []
    for f in pre_state_csvs:
        try:
            df = pd.read_csv(f, dtype=str)
            if not df.empty and 'Year' in df.columns and 'StatVar' in df.columns:
                state_dfs.append(df)
        except Exception as e:
            logging.warning(f'Could not read historical state file {f}: {e}')
    state_dfs.extend(live_state_dfs)

    county_dfs = []
    for f in pre_county_csvs:
        try:
            df = pd.read_csv(f, dtype=str)
            if not df.empty and 'Year' in df.columns and 'StatVar' in df.columns:
                county_dfs.append(df)
        except Exception as e:
            logging.warning(f'Could not read historical county file {f}: {e}')
    county_dfs.extend(live_county_dfs)

    if not state_dfs and not county_dfs:
        return False

    # 1. State data consolidation and direct Country aggregation
    if state_dfs:
        final_state_df = pd.concat(state_dfs, ignore_index=True)
        final_state_df = _filter_zero_unknown_placeholders(final_state_df)
        if 'Unit' in final_state_df.columns:
            final_state_df['Unit'] = final_state_df['Unit'].fillna('').replace(
                _UNIT_NORMALIZATION)
        final_state_df = final_state_df[~final_state_df['Geo'].
                                        isin(['geoId/99', 'geoId/00'])]
        final_state_df.drop_duplicates(subset=['Year', 'Geo', 'StatVar'],
                                       keep='last',
                                       inplace=True)
        final_state_df = _normalize_quantities(final_state_df)
        final_state_df.sort_values(by=['Year', 'Geo', 'StatVar'], inplace=True)
        state_out = os.path.join(output_dir, 'state.csv')
        final_state_df.to_csv(state_out, index=False)
        logging.info(f'Generated state.csv with {len(final_state_df)} rows.')

        # Compute country totals directly from consolidated state data
        final_country_df = aggregate_state_to_country(final_state_df)
        final_country_df = _normalize_quantities(final_country_df)
        final_country_df.sort_values(by=['Year', 'StatVar'], inplace=True)
        country_out = os.path.join(output_dir, 'country.csv')
        final_country_df.to_csv(country_out, index=False)
        logging.info(
            f'Generated country.csv with {len(final_country_df)} rows.')

    # 2. County data consolidation
    if county_dfs:
        final_county_df = pd.concat(county_dfs, ignore_index=True)
        final_county_df = _filter_zero_unknown_placeholders(final_county_df)
        if 'Unit' in final_county_df.columns:
            final_county_df['Unit'] = final_county_df['Unit'].fillna(
                '').replace(_UNIT_NORMALIZATION)
        final_county_df = final_county_df[
            final_county_df['Geo'].notna() &
            ~final_county_df['Geo'].isin(['geoId/99999', 'geoId/00000']) &
            ~final_county_df['Geo'].str.endswith('999', na=False)]
        final_county_df.drop_duplicates(subset=['Year', 'Geo', 'StatVar'],
                                        keep='last',
                                        inplace=True)
        final_county_df = _normalize_quantities(final_county_df)
        final_county_df.sort_values(by=['Year', 'Geo', 'StatVar'], inplace=True)
        county_out = os.path.join(output_dir, 'county.csv')
        final_county_df.to_csv(county_out, index=False)
        logging.info(f'Generated county.csv with {len(final_county_df)} rows.')

    write_tmcf_files(output_dir)
    return True


def main(argv):
    input_path = os.path.abspath(_FLAGS.input_path)
    output_path = os.path.abspath(_FLAGS.output_path)
    os.makedirs(output_path, exist_ok=True)

    logging.info(
        f'Starting CDC Wonder Natality process. Input: {input_path}, Output: {output_path}'
    )

    success = process_data(input_path, output_path)

    if not success:
        if _FLAGS.use_test_data:
            logging.warning('Using test data fallback...')
            mock_state = pd.DataFrame([{
                'Year': '2020',
                'Geo': 'geoId/01',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '57647',
                'Unit': ''
            }, {
                'Year': '2020',
                'Geo': 'geoId/02',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '9469',
                'Unit': ''
            }])
            mock_county = pd.DataFrame([{
                'Year': '2020',
                'Geo': 'geoId/01003',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '2245',
                'Unit': ''
            }])
            mock_country = aggregate_state_to_country(mock_state)
            mock_state.to_csv(os.path.join(output_path, 'state.csv'),
                              index=False)
            mock_county.to_csv(os.path.join(output_path, 'county.csv'),
                               index=False)
            mock_country.to_csv(os.path.join(output_path, 'country.csv'),
                                index=False)
            write_tmcf_files(output_path)
        else:
            logging.fatal(
                f'No valid input data found in {input_path}. Ensure download.py ran successfully.'
            )

    required_outputs = [
        'country.csv',
        'state.csv',
        'county.csv',
        'country.tmcf',
        'state.tmcf',
        'county.tmcf',
    ]
    missing = [
        f for f in required_outputs
        if not (os.path.exists(os.path.join(output_path, f)) and
                os.path.getsize(os.path.join(output_path, f)) > 0)
    ]
    if missing:
        logging.fatal(f'Missing or empty required output files: {missing}')

    logging.info('CDC Wonder Natality processing completed successfully.')


if __name__ == '__main__':
    app.run(main)
