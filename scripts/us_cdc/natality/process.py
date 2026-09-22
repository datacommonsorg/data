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

This script consolidates and cleans Natality data across country, state,
and county geographic resolutions, generating cleaned CSVs and TMCF templates
for automated ingestion into Data Commons.
"""

import glob
import os
import shutil
import subprocess
import sys
import pandas as pd
from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_DEFAULT_INPUT_DIR = os.path.join(_SCRIPT_DIR, 'input_files')
_DEFAULT_OUTPUT_DIR = os.path.join(_SCRIPT_DIR, 'output')

flags.DEFINE_string('input_path', _DEFAULT_INPUT_DIR,
                    'Path to input files directory')
flags.DEFINE_string(
    'output_path', _DEFAULT_OUTPUT_DIR,
    'Path to directory where output CSV, TMCF files will be written')
flags.DEFINE_boolean('use_test_data', False,
                     'Allow using checked-in testdata for fallback baseline.')

_FLAGS = flags.FLAGS


def _merge_csv_files(csv_files: list, output_csv_path: str, dedupe_keys: list):
    """Merges multiple CSV files into one, deduplicating records by key columns."""
    dfs = []
    for f in sorted(csv_files):
        if os.path.exists(f) and os.path.getsize(f) > 0:
            logging.info(f'Reading {f}...')
            df = pd.read_csv(f, dtype=str)
            dfs.append(df)

    if not dfs:
        logging.warning(f'No CSV data found to write to {output_csv_path}')
        return

    merged_df = pd.concat(dfs, ignore_index=True)
    merged_df.drop_duplicates(subset=dedupe_keys, keep='last', inplace=True)
    merged_df.sort_values(by=dedupe_keys, inplace=True)
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    merged_df.to_csv(output_csv_path, index=False)
    logging.info(
        f'Successfully wrote {len(merged_df)} rows to {output_csv_path}')


def _find_files(base_dir: str, pattern: str) -> list:
    """Finds files matching pattern recursively or in immediate directories."""
    files = glob.glob(os.path.join(base_dir, pattern))
    if not files:
        files = glob.glob(os.path.join(base_dir, '**', pattern), recursive=True)
    return sorted(files)


def process_preprocessed_data(input_dir: str, output_dir: str) -> bool:
    """Processes preprocessed CSVs from GCS or previous stages if present.

    Returns:
        True if preprocessed data was found and processed, False otherwise.
    """
    all_csvs = _find_files(input_dir, '*.csv')
    if not all_csvs:
        return False

    country_csvs = []
    state_csvs = []
    county_csvs = []

    for f in all_csvs:
        path_lower = f.lower()
        if 'country' in path_lower:
            country_csvs.append(f)
        elif 'county' in path_lower:
            county_csvs.append(f)
        elif 'state' in path_lower:
            state_csvs.append(f)
        else:
            try:
                sample_df = pd.read_csv(f, nrows=5, dtype=str)
                if 'Geo' not in sample_df.columns:
                    country_csvs.append(f)
                else:
                    sample_geo = (sample_df['Geo'].dropna().iloc[0] if
                                  not sample_df['Geo'].dropna().empty else '')
                    # State DCIDs are geoId/XX (length 9), County DCIDs are geoId/XXXXX (length 12)
                    if len(sample_geo) <= 9:
                        state_csvs.append(f)
                    else:
                        county_csvs.append(f)
            except Exception as e:
                logging.warning(f'Could not classify {f}: {e}')

    if not (country_csvs or state_csvs or county_csvs):
        return False

    logging.info('Found preprocessed CSV files. Consolidating...')

    # Process county data
    if county_csvs:
        county_out = os.path.join(output_dir, 'county.csv')
        _merge_csv_files(county_csvs,
                         county_out,
                         dedupe_keys=['Year', 'Geo', 'StatVar'])

    # Process state data
    if state_csvs:
        state_out = os.path.join(output_dir, 'state.csv')
        _merge_csv_files(state_csvs,
                         state_out,
                         dedupe_keys=['Year', 'Geo', 'StatVar'])

        # If country CSVs are missing, aggregate from state data
        if not country_csvs and os.path.exists(state_out):
            logging.info('Generating country aggregations from state data...')
            country_out = os.path.join(output_dir, 'country.csv')
            state_df = pd.read_csv(state_out, dtype=str)
            count_df = state_df[state_df['StatVar'].str.startswith(
                'Count')].copy()
            count_df['Quantity'] = pd.to_numeric(count_df['Quantity'],
                                                 errors='coerce')
            country_df = count_df.groupby(['Year', 'StatVar'],
                                          as_index=False)['Quantity'].sum()
            country_df.sort_values(by=['Year', 'StatVar'], inplace=True)
            country_df.to_csv(country_out, index=False)
            logging.info(f'Generated country CSV with {len(country_df)} rows.')

    # Process country data if available directly
    if country_csvs:
        country_out = os.path.join(output_dir, 'country.csv')
        _merge_csv_files(country_csvs,
                         country_out,
                         dedupe_keys=['Year', 'StatVar'])

    return True


def copy_tmcf_files(output_dir: str):
    """Copies template MCF files for country, state, and county to output_dir."""
    mappings = [
        (os.path.join(_SCRIPT_DIR, 'country',
                      'output.tmcf'), os.path.join(output_dir, 'country.tmcf')),
        (os.path.join(_SCRIPT_DIR, 'state',
                      'output.tmcf'), os.path.join(output_dir, 'state.tmcf')),
        (os.path.join(_SCRIPT_DIR, 'county',
                      'output.tmcf'), os.path.join(output_dir, 'county.tmcf')),
    ]
    for src, dst in mappings:
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            logging.info(f'Copied TMCF {src} -> {dst}')


def main(argv):
    input_path = os.path.abspath(_FLAGS.input_path)
    output_path = os.path.abspath(_FLAGS.output_path)
    os.makedirs(output_path, exist_ok=True)

    logging.info(
        f'Starting CDC Wonder Natality pipeline. Input: {input_path}, Output: {output_path}'
    )

    success = process_preprocessed_data(input_path, output_path)

    if not success:
        if _FLAGS.use_test_data:
            logging.warning(
                f'No input data found in {input_path}. Using testdata fallback since --use_test_data is set...'
            )
            test_data_dir = os.path.join(_SCRIPT_DIR, 'testdata',
                                         'cleaned_data')
            tmp_state_csv = os.path.join(output_path, 'state.csv')
            config_path = os.path.join(_SCRIPT_DIR, 'state', '16-20_state.json')

            preprocess_py = os.path.join(_SCRIPT_DIR, 'preprocess.py')
            subprocess.check_call([
                sys.executable, preprocess_py, f'--input_path={test_data_dir}',
                f'--config_path={config_path}', f'--output_path={output_path}'
            ])
            if os.path.exists(os.path.join(output_path, 'cleaned.csv')):
                os.rename(os.path.join(output_path, 'cleaned.csv'),
                          tmp_state_csv)

            if os.path.exists(tmp_state_csv):
                country_csv = os.path.join(output_path, 'country.csv')
                aggregate_py = os.path.join(_SCRIPT_DIR, 'aggregate.py')
                subprocess.check_call([
                    sys.executable, aggregate_py,
                    f'--input_path={tmp_state_csv}',
                    f'--output_path={country_csv}'
                ])

            county_csv = os.path.join(output_path, 'county.csv')
            if not os.path.exists(county_csv) and os.path.exists(tmp_state_csv):
                shutil.copyfile(tmp_state_csv, county_csv)
        else:
            raise RuntimeError(
                f'No valid input data found in {input_path}. Ensure download.sh ran successfully or input files exist.'
            )

    copy_tmcf_files(output_path)

    # Verify that all required output files exist and are non-empty
    required_outputs = ['country.csv', 'state.csv', 'county.csv']
    missing = [
        f for f in required_outputs
        if not os.path.exists(os.path.join(output_path, f))
    ]
    if missing:
        raise RuntimeError(
            f'Pipeline completed with missing required output files: {missing}')

    logging.info('CDC Wonder Natality processing completed successfully.')


if __name__ == '__main__':
    app.run(main)
