#!/usr/bin/env python3
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
"""Preprocesses Zurich BEV403OD4031 dataset to generate all marginal and total roll-up slices."""

import os
from absl import app
from absl import flags
from absl import logging
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT_RAW = os.path.join(CURRENT_DIR, 'input_files', 'BEV403OD4031.csv')
DEFAULT_OUTPUT_ROLLUPS = os.path.join(CURRENT_DIR, 'input_files',
                                      'BEV403OD4031_rollups.csv')

FLAGS = flags.FLAGS
flags.DEFINE_string('input_csv',
                    DEFAULT_INPUT_RAW,
                    'Path to raw input CSV file.',
                    allow_override=True)
flags.DEFINE_string('output_csv',
                    DEFAULT_OUTPUT_ROLLUPS,
                    'Path to output rollups CSV file.',
                    allow_override=True)

REQUIRED_COLS = [
    'GueltigAbDatJahr', 'QuarLang', 'KreisLang', 'SexLang', 'HerkunftLang',
    'AnzGebuWir'
]
OUTPUT_COLS = [
    'GueltigAbDatJahr', 'QuarLang', 'SexLang', 'HerkunftLang', 'AnzGebuWir'
]


def process_rollups(df: pd.DataFrame) -> pd.DataFrame:
    """Generates 2-way, 1-way, and total birth rollups across geographic levels.

  Args:
    df: Input pandas DataFrame containing raw Zurich BEV4031 birth data.

  Returns:
    Pandas DataFrame containing all demographic rollups across Quarters, Kreise, and Ganze Stadt.

  Raises:
    ValueError: If input DataFrame is empty.
    KeyError: If required columns are missing.
  """
    if df.empty:
        logging.error("Input DataFrame is empty.")
        raise ValueError("Input DataFrame is empty.")

    missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing_cols:
        err_msg = (
            f"Input DataFrame is missing required columns: {missing_cols}. "
            f"Available columns: {list(df.columns)}")
        logging.error("%s", err_msg)
        raise KeyError(err_msg)

    df = df.copy()

    # Filter out unknown regions (e.g., code 990/999 or Unbekannt)
    for code_col in ['QuarSort', 'QuarCd', 'KreisCd']:
        if code_col in df.columns:
            df = df[~pd.to_numeric(df[code_col], errors='coerce').
                    isin([990, 999])].copy()
    unknown_labels = {'Unbekannt', 'Kreis Unbekannt', 'Quartier Unbekannt'}
    df = df[
        ~df['QuarLang'].astype(str).str.strip().isin(unknown_labels) &
        ~df['KreisLang'].astype(str).str.strip().isin(unknown_labels)].copy()

    if df.empty:
        logging.error(
            "No valid rows remaining after filtering unknown regions.")
        raise ValueError(
            "No valid rows remaining after filtering unknown regions.")

    val_col = 'AnzGebuWir'
    df[val_col] = pd.to_numeric(df[val_col], errors='coerce')

    all_dfs = []
    spatial_levels = [('QuarLang', 'QuarLang'), ('KreisLang', 'KreisLang'),
                      ('Ganze Stadt', None)]

    for _, col in spatial_levels:
        sub_df = df.copy()
        if col is not None:
            sub_df['QuarLang'] = sub_df[col]
        else:
            sub_df['QuarLang'] = 'Ganze Stadt'

        group_keys = ['GueltigAbDatJahr', 'QuarLang']

        # 1. Full 2-way breakdown (Gender + Nativity)
        df_full = sub_df.groupby(group_keys + ['SexLang', 'HerkunftLang'],
                                 as_index=False)[val_col].sum(min_count=1)

        # 2. Gender only (marginal over nativity)
        df_sex = sub_df.groupby(group_keys + ['SexLang'],
                                as_index=False)[val_col].sum(min_count=1)
        df_sex['HerkunftLang'] = ''

        # 3. Nativity only (marginal over gender)
        df_hel = sub_df.groupby(group_keys + ['HerkunftLang'],
                                as_index=False)[val_col].sum(min_count=1)
        df_hel['SexLang'] = ''

        # 4. Total (all demographics aggregated)
        df_tot = sub_df.groupby(group_keys,
                                as_index=False)[val_col].sum(min_count=1)
        df_tot['SexLang'] = ''
        df_tot['HerkunftLang'] = ''

        for slice_df in [df_full, df_sex, df_hel, df_tot]:
            all_dfs.append(slice_df[OUTPUT_COLS])

    df_all = pd.concat(all_dfs, ignore_index=True)
    df_all = df_all.dropna(subset=[val_col]).reset_index(drop=True)
    if df_all.empty:
        logging.error(
            "No valid numeric rows remaining after rollup aggregation.")
        raise ValueError(
            "No valid numeric rows remaining after rollup aggregation.")
    if (df_all[val_col] % 1 == 0).all():
        df_all[val_col] = df_all[val_col].astype(int)
    return df_all[OUTPUT_COLS]


def generate_rollups(input_csv: str, output_csv: str) -> pd.DataFrame:
    """Reads raw CSV, processes rollups, and writes the output CSV file.

  Args:
    input_csv: Path to input CSV file.
    output_csv: Path to output CSV file.

  Returns:
    Processed pandas DataFrame written to output_csv.

  Raises:
    FileNotFoundError: If input_csv does not exist.
    ValueError: If input_csv is empty.
  """
    if not os.path.exists(input_csv):
        logging.error("Input file not found: %s", input_csv)
        raise FileNotFoundError(f"Input file not found: {input_csv}")
    if os.path.getsize(input_csv) == 0:
        logging.error("Input file is empty: %s", input_csv)
        raise ValueError(f"Input file is empty: {input_csv}")

    try:
        df = pd.read_csv(input_csv, encoding='utf-8-sig')
    except UnicodeDecodeError:
        df = pd.read_csv(input_csv, encoding='iso-8859-1')

    df_rollups = process_rollups(df)

    output_dir = os.path.dirname(output_csv)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    tmp_output_csv = f'{output_csv}.tmp'
    df_rollups.to_csv(tmp_output_csv, index=False, encoding='utf-8')
    if not os.path.exists(tmp_output_csv) or os.path.getsize(
            tmp_output_csv) == 0:
        logging.error("Temporary output file is missing or empty: %s",
                      tmp_output_csv)
        raise ValueError(
            f"Temporary output file is missing or empty: {tmp_output_csv}")
    os.replace(tmp_output_csv, output_csv)
    logging.info("Successfully generated %s with %d rows across %d places.",
                 output_csv, len(df_rollups), df_rollups['QuarLang'].nunique())
    return df_rollups


def main(argv):
    del argv  # Unused.
    try:
        generate_rollups(FLAGS.input_csv, FLAGS.output_csv)
    except Exception as e:
        logging.fatal("Failed to generate rollups: %s", e, exc_info=True)


if __name__ == '__main__':
    app.run(main)
