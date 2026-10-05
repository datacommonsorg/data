# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

from absl import app, logging
import pandas as pd

import config

script_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(script_dir, '../../../util'))

from download_util_script import download_file
from file_util import FileIO

COMMERCE_NTIA_URL = config.COMMERCE_NTIA_URL

INPUT_DIR = os.path.join(script_dir, "input_files")

COMMON_COLUMNS = ["dataset", "variable", "description", "universe"]
AGE_COLUMNS = [
    "age314Count", "age1524Count", "age2544Count", "age4564Count", "age65pCount"
]
_AGE_RESOL_MAP = {'isPerson': 'CivilPerson', 'isAdult': 'Adult'}
INPUT_FILE = os.path.join(INPUT_DIR, "ntia-analyze-table.csv")
INPUT_FILE_1 = os.path.join(INPUT_DIR, "ntia-data-age-only.csv")
INPUT_FILE_2 = os.path.join(INPUT_DIR, "ntia-data.csv")

HEADERS = {
    'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def move_column_left(df, column_to_move, target_column):
    """Moves the universe column to the left of variable column."""
    if column_to_move == target_column:
        return df
    cols = df.columns.tolist()
    if column_to_move in cols and target_column in cols:
        cols.remove(column_to_move)
        target_index = cols.index(target_column)
        new_cols = cols[:target_index] + [column_to_move] + cols[target_index:]
        return df[new_cols]
    return df


def preprocess_data():
    """Preprocesses and splits the raw NTIA Internet Use Survey dataset.

    The raw source dataset (ntia-analyze-table.csv) combines both general survey
    demographic metrics and age-bracket distributions in a single tabular file.
    These require two different PV-mapping strategies and cannot be processed in
    a single pass by stat_var_processor.py because:
      1. stat_var_processor.py expects a uniform column schema per run mapped to
         a single PV-map and metadata config.
      2. Age-bracket counts (age314Count to age65pCount) map column names
         directly to DC Age properties via ntia_age_pvmap.csv, whereas general
         survey rows map variable codes to statistical properties via
         ntia_pvmap.csv.
      3. The processor cannot dynamically split columns, reorder columns to place
         'universe' ahead of 'variable' for hierarchical resolution, or inject
         helper resolution columns (universeAgeResol / variableAgeResol) needed
         to distinguish Civilian Person vs. Adult populations.

    This function performs the necessary bifurcation and generates:
      - input_files/ntia-data-age-only.csv: Age-bracket counts with age PV mappings.
      - input_files/ntia-data.csv: General survey metrics with standard PV mappings.
    """
    try:
        os.makedirs(INPUT_DIR, exist_ok=True)
        org_df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')

        # 1. Process Age-only data
        df1 = org_df[COMMON_COLUMNS + AGE_COLUMNS].copy()
        df1['universeAgeResol'] = df1['universe'].map(_AGE_RESOL_MAP)
        df1['variableAgeResol'] = df1['variable'].map(_AGE_RESOL_MAP)
        df1_moved = move_column_left(df1, 'universe', 'variable')
        with FileIO(INPUT_FILE_1, mode='w') as f:
            df1_moved.to_csv(f, index=False)

        # 2. Process General survey data
        df2_cols_to_keep = [
            col for col in org_df.columns
            if not col.startswith(('age314', 'age1524', 'age2544', 'age4564',
                                   'age65p'))
        ]
        df2 = org_df[df2_cols_to_keep].copy()
        df2['universeAgeResol'] = df2['universe'].map(_AGE_RESOL_MAP)
        df2['variableAgeResol'] = df2['variable'].map(_AGE_RESOL_MAP)
        df2_moved = move_column_left(df2, 'universe', 'variable')
        with FileIO(INPUT_FILE_2, mode='w') as f:
            df2_moved.to_csv(f, index=False)
        logging.info(
            f"Successfully preprocessed {len(df1_moved)} age-only rows "
            f"and {len(df2_moved)} general survey rows.")

    except Exception as e:
        logging.error(
            f"An error occurred while preprocessing the input data: {e}",
            exc_info=True)
        raise RuntimeError(
            f"An error occurred while preprocessing the input data: {e}") from e


def main(argv):
    del argv
    try:
        logging.info(f"Downloading source data from {COMMERCE_NTIA_URL}")
        success = download_file(
            url=COMMERCE_NTIA_URL,
            output_folder=INPUT_DIR,
            unzip=False,
            headers=HEADERS,
            tries=3,
            delay=5,
            backoff=2,
        )
        if not success or not os.path.exists(INPUT_FILE) or os.path.getsize(
                INPUT_FILE) == 0:
            logging.fatal(
                f"Failed to download Commerce_NTIA file from {COMMERCE_NTIA_URL} or file is empty.",
                exc_info=True)
        logging.info(
            f"Successfully downloaded {INPUT_FILE} ({os.path.getsize(INPUT_FILE)} bytes)."
        )
    except Exception as e:
        logging.fatal(
            f"Failed to download Commerce_NTIA file from {COMMERCE_NTIA_URL}: {e}",
            exc_info=True)

    try:
        preprocess_data()
    except Exception as e:
        logging.fatal(f"Failed to preprocess Commerce_NTIA data: {e}",
                      exc_info=True)


if __name__ == "__main__":
    app.run(main)
