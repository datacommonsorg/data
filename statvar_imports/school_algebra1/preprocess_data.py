# Copyright 2025 Google LLC
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
"""Preprocesses raw CRDC Algebra 1 input files into standardized CSVs.

Reads raw downloaded files from input_files/ (keeping them intact), standardizes
identifiers (ncesid, YEAR), dynamically filters out unmapped non-algebra
columns, and writes clean CSVs into processed_files/ for stat_var_processor.
"""

import glob
import os
import re
from absl import app
from absl import logging
import pandas as pd

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
_INPUT_DIR = os.path.join(_SCRIPT_PATH, "input_files")
_PROCESSED_DIR = os.path.join(_SCRIPT_PATH, "processed_files")
_PVMAP_PATH = os.path.join(_SCRIPT_PATH, "Algebra1_pvmap.csv")

logging.set_verbosity(logging.INFO)

# Essential identifier columns always preserved
_IDENTIFIER_COLS = {
    'NCESID', 'YEAR', 'LEAID', 'SCHID', 'COMBOKEY', 'LEA_STATE',
    'LEA_STATE_NAME', 'LEA_NAME', 'SCH_NAME'
}


def load_pv_mapped_columns(pvmap_path: str) -> set:
    """Reads column names mapped in the PV map file."""
    mapped_cols = set()
    if not os.path.exists(pvmap_path):
        raise FileNotFoundError(f"PV map file not found at: {pvmap_path}")

    with open(pvmap_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            col_name = line.split(',')[0].strip()
            if col_name:
                mapped_cols.add(col_name)

    logging.info(f"Loaded {len(mapped_cols)} mapped columns from {pvmap_path}")
    return mapped_cols


def extract_survey_end_year(filename: str) -> int:
    """Extracts the 4-digit survey completion year from CRDC file names."""
    # Matches patterns like crdc_2015-16_... -> 2016
    match = re.search(r'crdc_(\d{4})-(\d{2})', filename, re.IGNORECASE)
    if match:
        start_year = match.group(1)
        end_yy = match.group(2)
        century = start_year[:2]
        return int(f"{century}{end_yy}")
    return 0


def _pad_id_series(series: pd.Series, width: int) -> pd.Series:
    """Safely zero-pads non-empty, non-NaN string identifiers."""
    cleaned = series.fillna('').astype(str).str.strip()
    return cleaned.apply(
        lambda x: x.zfill(width) if x and x.lower() != 'nan' else '')


def preprocess_dataframe(df: pd.DataFrame, filename: str,
                         mapped_cols: set) -> pd.DataFrame:
    """Adds standardized ncesid, YEAR, and filters to mapped columns."""
    # Ensure ncesid exists and is properly zero-padded
    if 'ncesid' not in df.columns:
        if 'LEAID' in df.columns and 'SCHID' in df.columns:
            leaid = _pad_id_series(df['LEAID'], 7)
            schid = _pad_id_series(df['SCHID'], 5)
            df.insert(0, 'ncesid', leaid + schid)
        elif 'COMBOKEY' in df.columns:
            combokey = _pad_id_series(df['COMBOKEY'], 12)
            df.insert(0, 'ncesid', combokey)
        else:
            raise ValueError(f"Cannot resolve 'ncesid' in {filename}")
    else:
        df['ncesid'] = _pad_id_series(df['ncesid'], 12)

    # Ensure YEAR exists
    if 'YEAR' not in df.columns:
        survey_year = extract_survey_end_year(filename)
        if survey_year <= 0:
            raise ValueError(
                f"Cannot resolve survey completion year for {filename}")
        df.insert(1, 'YEAR', survey_year)

    # Filter columns dynamically: keep identifier columns + any column in pv_map
    keep_cols = [
        col for col in df.columns
        if col in mapped_cols or col.upper() in _IDENTIFIER_COLS
    ]
    dropped_count = len(df.columns) - len(keep_cols)
    if dropped_count > 0:
        logging.info(f"Filtered {filename}: retained {len(keep_cols)} cols, "
                     f"dropped {dropped_count} unmapped cols.")

    return df[keep_cols]


def process_file(filepath: str, mapped_cols: set):
    """Processes a single raw file and writes the clean CSV to processed_files/."""
    filename = os.path.basename(filepath)
    base, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in ['.csv', '.xlsx']:
        return

    output_csv_filename = f"{base}.csv"
    os.makedirs(_PROCESSED_DIR, exist_ok=True)
    output_csv_path = os.path.join(_PROCESSED_DIR, output_csv_filename)
    temp_csv_path = f"{output_csv_path}.tmp"

    logging.info(f"Processing raw file: {filename}")

    try:
        if ext == '.csv':
            df = pd.read_csv(filepath,
                             encoding='latin-1',
                             low_memory=False,
                             dtype=str)
            df = preprocess_dataframe(df, filename, mapped_cols)
            df.to_csv(temp_csv_path, index=False)
        elif ext == '.xlsx':
            # Excel files have 'Sheet1'
            df = pd.read_excel(filepath, sheet_name=0, dtype=str)
            df = preprocess_dataframe(df, filename, mapped_cols)
            df.to_csv(temp_csv_path, index=False)

        os.replace(temp_csv_path, output_csv_path)
        logging.info(f"Wrote processed file: {output_csv_path}")

    except Exception as e:
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)
        logging.error(f"Error processing {filepath}: {e}")
        raise


def preprocess_all_files():
    """Preprocesses all raw CSV and XLSX files in input_files/."""
    os.makedirs(_PROCESSED_DIR, exist_ok=True)
    mapped_cols = load_pv_mapped_columns(_PVMAP_PATH)

    raw_files = sorted(
        glob.glob(os.path.join(_INPUT_DIR, '*.csv')) +
        glob.glob(os.path.join(_INPUT_DIR, '*.xlsx')))

    if not raw_files:
        raise FileNotFoundError(f"No raw files found in {_INPUT_DIR}")

    logging.info(f"Found {len(raw_files)} files in {_INPUT_DIR} to preprocess.")

    for filepath in raw_files:
        process_file(filepath, mapped_cols)

    logging.info(f"All files successfully preprocessed into {_PROCESSED_DIR}")


def main(argv):
    """Main entry point for preprocessing CRDC Algebra 1 files."""
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")
    try:
        preprocess_all_files()
    except Exception as e:
        logging.fatal(f"Preprocessing failed: {e}", exc_info=True)


if __name__ == '__main__':
    app.run(main)
