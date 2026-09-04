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
"""Preprocesses Zurich WIR255OD2552 dataset to filter total roll-up rows.

Filters total rows (Alle Rechtsformen and Alle Betriebsgrössen) where
RechtsformSort == 0 and BetriebsgrSort == 0, and coerces numeric metric
columns to numbers (converting markers such as 'K' to NaN).
"""

import os
import sys
from absl import app
from absl import flags
from absl import logging
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT_RAW = os.path.join(CURRENT_DIR, 'input_files', 'WIR255OD2552.csv')
DEFAULT_OUTPUT_ROLLUPS = os.path.join(CURRENT_DIR, 'input_files',
                                      'WIR255OD2552_rollups.csv')

FLAGS = flags.FLAGS
flags.DEFINE_string('input_csv', DEFAULT_INPUT_RAW,
                    'Path to raw input CSV file.')
flags.DEFINE_string('output_csv', DEFAULT_OUTPUT_ROLLUPS,
                    'Path to output rollups CSV file.')

REQUIRED_FILTER_COLS = ['RechtsformSort', 'BetriebsgrSort']
NUMERIC_VAL_COLS = [
    'Arbeitsstaetten', 'AnzBesch', 'AnzBeschW', 'AnzBeschM', 'AnzVZA',
    'AnzVZAW', 'AnzVZAM'
]


def process_rollups(df: pd.DataFrame) -> pd.DataFrame:
    """Filters total roll-up rows and coerces metric columns to numeric.

  Args:
    df: Input pandas DataFrame containing raw Zurich workplace data.

  Returns:
    Filtered pandas DataFrame containing only total rollup rows.

  Raises:
    ValueError: If input DataFrame is empty or no rows match filter.
    KeyError: If required filter columns are missing.
  """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    missing_cols = [
        col for col in REQUIRED_FILTER_COLS if col not in df.columns
    ]
    if missing_cols:
        raise KeyError(
            f"Input DataFrame is missing required filter columns: {missing_cols}. "
            f"Available columns: {list(df.columns)}")

    # Keep only the total rows (Alle Rechtsformen and Alle Betriebsgrössen).
    # Coerce sort columns to numeric so string or numeric '0' matches reliably.
    rechtsform_sort = pd.to_numeric(df['RechtsformSort'], errors='coerce')
    betriebsgr_sort = pd.to_numeric(df['BetriebsgrSort'], errors='coerce')
    df_rollups = df[(rechtsform_sort == 0) & (betriebsgr_sort == 0)].copy()

    if df_rollups.empty:
        raise ValueError(
            "No rows matched filter (RechtsformSort == 0 & BetriebsgrSort == 0)."
        )

    # Convert numeric columns, converting non-numeric markers (e.g. 'K') to NaN/numeric
    for col in NUMERIC_VAL_COLS:
        if col in df_rollups.columns:
            df_rollups[col] = pd.to_numeric(df_rollups[col], errors='coerce')

    return df_rollups


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
        raise FileNotFoundError(f"Input file not found: {input_csv}")
    if os.path.getsize(input_csv) == 0:
        raise ValueError(f"Input file is empty: {input_csv}")

    try:
        df = pd.read_csv(input_csv, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(input_csv, encoding='iso-8859-1')

    df_rollups = process_rollups(df)

    output_dir = os.path.dirname(output_csv)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    df_rollups.to_csv(output_csv, index=False, encoding='utf-8')
    logging.info("Successfully generated %s with %d rows.", output_csv,
                 len(df_rollups))
    return df_rollups


def main(argv):
    del argv  # Unused.
    try:
        generate_rollups(FLAGS.input_csv, FLAGS.output_csv)
    except Exception as e:
        logging.fatal("Failed to generate rollups: %s", e, exc_info=True)


if __name__ == '__main__':
    app.run(main)
