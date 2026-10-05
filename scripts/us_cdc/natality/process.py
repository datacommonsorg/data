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
        ('Mean_MothersAge_BirthEvent_LiveBirth', 'Years'),
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
            if (line.startswith('"---"') or line.startswith('Caveats:') or
                    line.startswith('"Query Date:')):
                break
            if line.startswith('"Total"'):
                continue
            cleaned = line.lstrip('\t').strip()
            if cleaned:
                valid_lines.append(cleaned)

    if not valid_lines:
        return pd.DataFrame(
            columns=['Year', 'Geo', 'StatVar', 'Quantity', 'Unit'])

    reader = csv.reader(valid_lines, delimiter='\t')
    try:
        header = [col.strip().strip('"') for col in next(reader)]
    except StopIteration:
        return pd.DataFrame(
            columns=['Year', 'Geo', 'StatVar', 'Quantity', 'Unit'])

    if header and header[0] == 'Notes':
        header = header[1:]

    code_col_idx = None
    year_col_idx = None
    for idx, col in enumerate(header):
        if 'Code' in col and ('State' in col or 'County' in col):
            code_col_idx = idx
        elif col in ('Year', 'Year Code') and year_col_idx is None:
            year_col_idx = idx

    rows = []
    for line_parts in reader:
        parts = [p.strip().strip('"') for p in line_parts]
        if parts and parts[0] == 'Notes':
            parts = parts[1:]
        if len(parts) != len(header):
            continue

        fips = parts[code_col_idx] if code_col_idx is not None else ''
        year = parts[year_col_idx] if year_col_idx is not None else ''
        if not re.match(r'^\d{4}$', year):
            continue

        if geo_type == 'state':
            if not re.match(r'^\d{2}$', fips):
                continue
            geo_dcid = f'geoId/{fips}'
        else:
            if not re.match(r'^\d{5}$', fips):
                continue
            geo_dcid = f'geoId/{fips}'

        for col_name, (statvar, unit) in _MEASURE_MAP.items():
            if col_name in header:
                val = parts[header.index(col_name)].strip()
                if not val or val.lower() in ('unreliable', 'suppressed',
                                              'missing', 'not available'):
                    continue
                try:
                    num = float(val)
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
    m = re.search(r'(\d{2})-(\d{2})', os.path.basename(filepath))
    if m:
        s_yr = int(m.group(1))
        e_yr = int(m.group(2))
        start_year = 1900 + s_yr if s_yr >= 50 else 2000 + s_yr
        end_year = 1900 + e_yr if e_yr >= 50 else 2000 + e_yr
        return (start_year, end_year)
    return (9999, 9999)


def _merge_csv_files(csv_files: list, output_csv_path: str, dedupe_keys: list):
    """Merges multiple CSV files, sorting brackets and deduplicating records."""
    dfs = []
    for f in sorted(csv_files, key=_extract_year_bracket):
        if os.path.exists(f) and os.path.getsize(f) > 0:
            logging.info(f'Reading {f}...')
            df = pd.read_csv(f, dtype=str)
            dfs.append(df)

    if not dfs:
        return

    merged_df = pd.concat(dfs, ignore_index=True)
    merged_df.drop_duplicates(subset=dedupe_keys, keep='last', inplace=True)
    merged_df.sort_values(by=dedupe_keys, inplace=True)
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    merged_df.to_csv(output_csv_path, index=False)
    logging.info(f'Wrote {len(merged_df)} rows to {output_csv_path}')


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

    state_raw = os.path.join(input_dir, 'state_raw.tsv')
    county_raw = os.path.join(input_dir, 'county_raw.tsv')

    state_df = pd.DataFrame()
    county_df = pd.DataFrame()

    if os.path.exists(state_raw) and os.path.getsize(state_raw) > 0:
        logging.info(f'Parsing raw State TSV: {state_raw}')
        state_df = parse_wonder_tsv(state_raw, 'state')

    if os.path.exists(county_raw) and os.path.getsize(county_raw) > 0:
        logging.info(f'Parsing raw County TSV: {county_raw}')
        county_df = parse_wonder_tsv(county_raw, 'county')

    # Also incorporate any pre-existing CSV brackets / historical baseline in input_dir
    pre_state_csvs = [
        f for f in _find_csvs(input_dir, 'state')
        if not f.startswith(output_dir) and not f.endswith('raw.tsv')
    ]
    pre_county_csvs = [
        f for f in _find_csvs(input_dir, 'county')
        if not f.startswith(output_dir) and not f.endswith('raw.tsv')
    ]
    pre_country_csvs = [
        f for f in _find_csvs(input_dir, 'country')
        if not f.startswith(output_dir) and not f.endswith('raw.tsv')
    ]

    state_dfs = []
    for f in pre_state_csvs:
        try:
            df = pd.read_csv(f, dtype=str)
            if not df.empty and 'Year' in df.columns and 'StatVar' in df.columns:
                state_dfs.append(df)
        except Exception as e:
            logging.warning(f'Could not read historical state file {f}: {e}')
    if not state_df.empty:
        state_dfs.append(state_df)

    county_dfs = []
    for f in pre_county_csvs:
        try:
            df = pd.read_csv(f, dtype=str)
            if not df.empty and 'Year' in df.columns and 'StatVar' in df.columns:
                county_dfs.append(df)
        except Exception as e:
            logging.warning(f'Could not read historical county file {f}: {e}')
    if not county_df.empty:
        county_dfs.append(county_df)

    country_dfs = []
    for f in pre_country_csvs:
        try:
            df = pd.read_csv(f, dtype=str)
            if not df.empty and 'Year' in df.columns and 'StatVar' in df.columns:
                country_dfs.append(df)
        except Exception as e:
            logging.warning(f'Could not read historical country file {f}: {e}')

    if not state_dfs and not county_dfs and not country_dfs:
        return False

    # 1. State data consolidation
    if state_dfs:
        final_state_df = pd.concat(state_dfs, ignore_index=True)
        if 'Unit' in final_state_df.columns:
            final_state_df['Unit'] = final_state_df['Unit'].fillna('').replace({
                'Weeks': 'Week',
                'Grams': 'Gram',
                'Months': 'Month'
            })
        final_state_df.drop_duplicates(subset=['Year', 'Geo', 'StatVar'],
                                       keep='last',
                                       inplace=True)
        final_state_df.sort_values(by=['Year', 'Geo', 'StatVar'], inplace=True)
        state_out = os.path.join(output_dir, 'state.csv')
        final_state_df.to_csv(state_out, index=False)
        logging.info(f'Generated state.csv with {len(final_state_df)} rows.')

        # Aggregate country totals from state data (using new state_df or final_state_df)
        agg_source = state_df if not state_df.empty else final_state_df
        country_agg = aggregate_state_to_country(agg_source)
        if not country_agg.empty:
            country_dfs.append(country_agg)

    # 2. County data consolidation
    if county_dfs:
        final_county_df = pd.concat(county_dfs, ignore_index=True)
        if 'Unit' in final_county_df.columns:
            final_county_df['Unit'] = final_county_df['Unit'].fillna(
                '').replace({
                    'Weeks': 'Week',
                    'Grams': 'Gram',
                    'Months': 'Month'
                })
        final_county_df.drop_duplicates(subset=['Year', 'Geo', 'StatVar'],
                                        keep='last',
                                        inplace=True)
        final_county_df.sort_values(by=['Year', 'Geo', 'StatVar'], inplace=True)
        county_out = os.path.join(output_dir, 'county.csv')
        final_county_df.to_csv(county_out, index=False)
        logging.info(f'Generated county.csv with {len(final_county_df)} rows.')

    # 3. Country data consolidation
    if country_dfs:
        final_country_df = pd.concat(country_dfs, ignore_index=True)
        final_country_df.drop_duplicates(subset=['Year', 'StatVar'],
                                         keep='last',
                                         inplace=True)
        final_country_df.sort_values(by=['Year', 'StatVar'], inplace=True)
        country_out = os.path.join(output_dir, 'country.csv')
        final_country_df.to_csv(country_out, index=False)
        logging.info(
            f'Generated country.csv with {len(final_country_df)} rows.')

    # Clean Count_* integer format in country.csv
    country_out = os.path.join(output_dir, 'country.csv')
    if os.path.exists(country_out):
        cdf = pd.read_csv(country_out, dtype=str)
        if 'Quantity' in cdf.columns and 'StatVar' in cdf.columns:
            count_mask = cdf['StatVar'].str.startswith('Count')
            nums = pd.to_numeric(cdf['Quantity'], errors='coerce')
            valid_mask = count_mask & nums.notna()
            cdf.loc[valid_mask, 'Quantity'] = (
                nums.loc[valid_mask].round().astype('int64').astype(str))
            cdf.to_csv(country_out, index=False)

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
        else:
            logging.fatal(
                f'No valid input data found in {input_path}. Ensure download.py ran successfully.'
            )
            raise RuntimeError(f'No input data found in {input_path}')

    write_tmcf_files(output_path)

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
        raise RuntimeError(f'Missing required outputs: {missing}')

    logging.info('CDC Wonder Natality processing completed successfully.')


if __name__ == '__main__':
    app.run(main)
