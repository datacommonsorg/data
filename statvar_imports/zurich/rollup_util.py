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
"""Shared demographic and spatial rollup helper for Zurich StatVar imports."""

import itertools
import os
from typing import Sequence
from absl import logging
import pandas as pd

UNKNOWN_CODES = (990, 999)
UNKNOWN_LABELS = frozenset(
    {'Unbekannt', 'Kreis Unbekannt', 'Quartier Unbekannt'})
SPATIAL_LEVELS = (
    ('QuarLang', 'QuarLang'),
    ('KreisLang', 'KreisLang'),
    ('Ganze Stadt', None),
)


def process_demographic_rollups(
    df: pd.DataFrame,
    year_col: str,
    demographic_cols: Sequence[str],
    val_col: str,
) -> pd.DataFrame:
    """Generates multi-way, marginal, and total rollups across Zurich places.

  Aggregates input observations across 3 geographic levels (Quarter `QuarLang`,
  District `KreisLang` mapped into `QuarLang`, and City total `'Ganze Stadt'`)
  and all 2^d demographic combinations of `demographic_cols`, using
  `sum(min_count=1)` so slices containing only suppressed `'K'` markers remain
  `NaN` and are dropped rather than emitted as false `0` counts.

  Args:
    df: Input pandas DataFrame containing raw Zurich dataset rows.
    year_col: Name of the year column (e.g. `'StichtagDatJahr'` or
      `'GueltigAbDatJahr'`).
    demographic_cols: Ordered sequence of demographic dimension columns (e.g.
      `['AlterV10Kurz', 'SexKurz', 'HerkunftLang']`).
    val_col: Name of the numeric metric column (e.g. `'AnzBestWir'` or
      `'AnzGebuWir'`).

  Returns:
    Pandas DataFrame with columns `[year_col, 'QuarLang', *demographic_cols,
    val_col]`.

  Raises:
    ValueError: If input DataFrame is empty or no valid rows remain after
      filtering.
    KeyError: If required columns are missing.
  """
    if df.empty:
        logging.error('Input DataFrame is empty.')
        raise ValueError('Input DataFrame is empty.')

    required_cols = [
        year_col, 'QuarLang', 'KreisLang', *demographic_cols, val_col
    ]
    # val_col (AnzBestWir) must remain the final column so demographic columns are bound in locals() before #Eval executes.
    output_cols = [year_col, 'QuarLang', *demographic_cols, val_col]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        err_msg = (
            f'Input DataFrame is missing required columns: {missing_cols}. '
            f'Available columns: {list(df.columns)}')
        logging.error('%s', err_msg)
        raise KeyError(err_msg)

    df = df.copy()

    # Filter out rows with null or whitespace-only geographic/demographic labels
    # and normalize whitespace before aggregation.
    label_cols = ['QuarLang', 'KreisLang', *demographic_cols]
    df = df.dropna(subset=label_cols).copy()
    for label_col in label_cols:
        df[label_col] = df[label_col].astype(str).str.strip()
        df = df[df[label_col] != ''].copy()

    # Filter out unknown regions (e.g., code 990/999 or Unbekannt)
    for code_col in ('QuarSort', 'QuarCd', 'KreisCd'):
        if code_col in df.columns:
            df = df[~pd.to_numeric(df[code_col], errors='coerce').
                    isin(UNKNOWN_CODES)].copy()
    df = df[~df['QuarLang'].isin(UNKNOWN_LABELS) &
            ~df['KreisLang'].isin(UNKNOWN_LABELS)].copy()

    if df.empty:
        logging.error(
            'No valid rows remaining after filtering unknown regions.')
        raise ValueError(
            'No valid rows remaining after filtering unknown regions.')

    df[val_col] = pd.to_numeric(df[val_col], errors='coerce')

    all_dfs = []
    for _, col in SPATIAL_LEVELS:
        sub_df = df.copy()
        if col is not None:
            sub_df['QuarLang'] = sub_df[col]
        else:
            sub_df['QuarLang'] = 'Ganze Stadt'

        group_keys = [year_col, 'QuarLang']

        for r in range(len(demographic_cols), -1, -1):
            for active_cols in itertools.combinations(demographic_cols, r):
                active_list = list(active_cols)
                slice_df = sub_df.groupby(
                    group_keys + active_list,
                    as_index=False)[val_col].sum(min_count=1)
                for dem_col in demographic_cols:
                    if dem_col not in active_cols:
                        slice_df[dem_col] = ''
                all_dfs.append(slice_df[output_cols])

    df_all = pd.concat(all_dfs, ignore_index=True)
    df_all = df_all.dropna(subset=[val_col]).reset_index(drop=True)
    if df_all.empty:
        logging.error(
            'No valid numeric rows remaining after rollup aggregation.')
        raise ValueError(
            'No valid numeric rows remaining after rollup aggregation.')
    if (df_all[val_col] % 1 == 0).all():
        df_all[val_col] = df_all[val_col].astype(int)
    return df_all[output_cols]


def generate_rollups_from_csv(
    input_csv: str,
    output_csv: str,
    year_col: str,
    demographic_cols: Sequence[str],
    val_col: str,
) -> pd.DataFrame:
    """Reads raw CSV, computes demographic/spatial rollups, and writes output CSV.

  Args:
    input_csv: Path to raw input CSV file.
    output_csv: Path to output rollups CSV file.
    year_col: Name of the year column.
    demographic_cols: Ordered sequence of demographic dimension columns.
    val_col: Name of the numeric metric column.

  Returns:
    Processed pandas DataFrame written to `output_csv`.

  Raises:
    FileNotFoundError: If `input_csv` does not exist.
    ValueError: If `input_csv` is empty or produces an empty output.
  """
    if not os.path.exists(input_csv):
        logging.error('Input file not found: %s', input_csv)
        raise FileNotFoundError(f'Input file not found: {input_csv}')
    if os.path.getsize(input_csv) == 0:
        logging.error('Input file is empty: %s', input_csv)
        raise ValueError(f'Input file is empty: {input_csv}')

    try:
        df = pd.read_csv(input_csv, encoding='utf-8-sig')
    except UnicodeDecodeError:
        logging.warning(
            'UTF-8 decoding failed for %s; falling back to iso-8859-1.',
            input_csv)
        df = pd.read_csv(input_csv, encoding='iso-8859-1')

    df_rollups = process_demographic_rollups(
        df=df,
        year_col=year_col,
        demographic_cols=demographic_cols,
        val_col=val_col,
    )

    output_dir = os.path.dirname(output_csv)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    tmp_output_csv = f'{output_csv}.tmp'
    df_rollups.to_csv(tmp_output_csv, index=False, encoding='utf-8')
    if not os.path.exists(tmp_output_csv) or os.path.getsize(
            tmp_output_csv) == 0:
        logging.error('Temporary output file is missing or empty: %s',
                      tmp_output_csv)
        raise ValueError(
            f'Temporary output file is missing or empty: {tmp_output_csv}')
    os.replace(tmp_output_csv, output_csv)
    logging.info('Successfully generated %s with %d rows across %d places.',
                 output_csv, len(df_rollups), df_rollups['QuarLang'].nunique())
    return df_rollups
