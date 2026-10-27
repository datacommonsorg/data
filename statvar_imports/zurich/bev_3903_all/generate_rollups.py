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
"""Preprocesses Zurich BEV390OD3903 dataset to generate all marginal and total roll-up slices."""

import os
import sys
from absl import app
from absl import flags
from absl import logging
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.zurich import rollup_util  # pylint: disable=g-import-not-at-top

DEFAULT_INPUT_RAW = os.path.join(CURRENT_DIR, 'input_files', 'BEV390OD3903.csv')
DEFAULT_OUTPUT_ROLLUPS = os.path.join(CURRENT_DIR, 'input_files',
                                      'BEV390OD3903_rollups.csv')

FLAGS = flags.FLAGS
flags.DEFINE_string('input_csv',
                    DEFAULT_INPUT_RAW,
                    'Path to raw input CSV file.',
                    allow_override=True)
flags.DEFINE_string('output_csv',
                    DEFAULT_OUTPUT_ROLLUPS,
                    'Path to output rollups CSV file.',
                    allow_override=True)

YEAR_COL = 'StichtagDatJahr'
DEMOGRAPHIC_COLS = ['AlterV10Kurz', 'SexKurz', 'HerkunftLang']
VAL_COL = 'AnzBestWir'
REQUIRED_COLS = [YEAR_COL, 'QuarLang', 'KreisLang', *DEMOGRAPHIC_COLS, VAL_COL]
# VAL_COL (AnzBestWir) must remain the final column so demographic columns are bound in locals() before #Eval executes.
OUTPUT_COLS = [YEAR_COL, 'QuarLang', *DEMOGRAPHIC_COLS, VAL_COL]


def process_rollups(df: pd.DataFrame) -> pd.DataFrame:
    """Generates 3-way, 2-way, 1-way, and total population rollups across geographic levels.

  Args:
    df: Input pandas DataFrame containing raw Zurich BEV3903 population data.

  Returns:
    Pandas DataFrame containing all demographic rollups across Quarters, Kreise, and Ganze Stadt.

  Raises:
    ValueError: If input DataFrame is empty.
    KeyError: If required columns are missing.
  """
    return rollup_util.process_demographic_rollups(
        df=df,
        year_col=YEAR_COL,
        demographic_cols=DEMOGRAPHIC_COLS,
        val_col=VAL_COL,
    )


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
    return rollup_util.generate_rollups_from_csv(
        input_csv=input_csv,
        output_csv=output_csv,
        year_col=YEAR_COL,
        demographic_cols=DEMOGRAPHIC_COLS,
        val_col=VAL_COL,
    )


def main(argv):
    del argv  # Unused.
    try:
        generate_rollups(FLAGS.input_csv, FLAGS.output_csv)
    except Exception as e:
        logging.fatal('Failed to generate rollups: %s', e, exc_info=True)


if __name__ == '__main__':
    app.run(main)
