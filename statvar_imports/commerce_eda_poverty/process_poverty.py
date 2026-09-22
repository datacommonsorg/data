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

"""Preprocessing script for Commerce EDA Persistent Poverty Counties dataset.

This script ingests the raw Persistent Poverty Counties dataset downloaded
from the authoritative upstream source (U.S. Treasury CDFI Fund), standardizes
geographic identifiers (FIPS codes for US counties and island territories),
validates and sanitizes poverty percentage rates, and generates the normalized
cleaned CSV for stat_var_processor.py.
"""

import io
import os
import re
import tempfile
from absl import app, flags, logging
import pandas as pd

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_SOURCE_XLSX = os.path.join(MODULE_DIR, "input_files", "poverty_source.xlsx")
DEFAULT_SOURCE_CSV = os.path.join(MODULE_DIR, "output", "Poverty_original.csv")
CLEANED_CSV = os.path.join(MODULE_DIR, "output", "Poverty_cleaned.csv")

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "source_path",
    None,
    "Path to downloaded source file (.xlsx or .csv). If not specified, automatically "
    "resolves from input_files/poverty_source.xlsx or output/Poverty_original.csv.",
)
flags.DEFINE_string("cleaned_csv_path", CLEANED_CSV, "Path to save cleaned output CSV.")
flags.DEFINE_integer("min_county_count", 400, "Minimum number of valid places expected.")

# Valid 2-digit US State and Territory FIPS codes
VALID_STATE_FIPS = {
    # 50 States + DC
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15",
    "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27",
    "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    "40", "41", "42", "44", "45", "46", "47", "48", "49", "50", "51", "53",
    "54", "55", "56",
    # Territories: American Samoa, Guam, Northern Mariana Islands, Puerto Rico, Virgin Islands
    "60", "66", "69", "72", "78"
}

# Territory-wide FIPS codes reported as 2-digit codes in CDFI PPC datasets
ISLAND_TERRITORY_FIPS = {"60", "66", "69", "78"}

COLUMN_RENAME_MAP = {
    "County FIPS": "GEOID",
    "County FIPS Code": "GEOID",
    "GEOID": "GEOID",
    "1990 Poverty %": "poverty_rate_1990",
    "1990 Decennial Census, % in Poverty": "poverty_rate_1990",
    "2000 Poverty %": "poverty_rate_2000",
    "2000 Decennial Census, % in Poverty": "poverty_rate_2000",
    "2016-2020 Poverty %": "poverty_rate_2020",
    "Most Recent Estimate, % in Poverty*": "poverty_rate_2020",
}


def clean_geoid(val):
    """Standardizes GEOIDs to 5-digit county FIPS or 2-digit island territory FIPS.

    Rejects state summaries (ending in '000'), invalid prefixes, and non-numeric codes.
    """
    if pd.isna(val):
        return None
    s = str(val).strip()
    match = re.match(r"^(\d+)(?:\.0+)?$", s)
    if not match:
        return None
    digits = match.group(1)
    if len(digits) <= 2:
        padded_terr = digits.zfill(2)
        if padded_terr in ISLAND_TERRITORY_FIPS:
            return padded_terr
        return None
    if len(digits) == 4:
        digits = digits.zfill(5)
    if len(digits) == 5 and digits[:2] in VALID_STATE_FIPS and digits[2:] != "000":
        return digits
    return None


def _extract_dataframe_from_excel(excel_bytes_or_path):
    """Extracts the Persistent Poverty Counties data table from an Excel workbook."""
    xl = pd.ExcelFile(excel_bytes_or_path)
    sheet_name = "Sheet1" if "Sheet1" in xl.sheet_names else xl.sheet_names[0]
    raw_df = xl.parse(sheet_name, header=None, dtype=str)

    header_row_idx = 0
    for idx in range(min(10, len(raw_df))):
        row_values = {str(v).strip() for v in raw_df.iloc[idx].values if pd.notna(v)}
        if row_values & {"County FIPS", "County FIPS Code", "GEOID"}:
            header_row_idx = idx
            break

    df = xl.parse(sheet_name, skiprows=header_row_idx, dtype=str)
    return df


def resolve_source_file_path(requested_path=None):
    """Finds the raw downloaded source file, raising FileNotFoundError if missing."""
    if requested_path:
        if os.path.exists(requested_path) and os.path.getsize(requested_path) > 0:
            return requested_path
        raise FileNotFoundError(f"Specified source file not found or empty: {requested_path}")

    # Check default paths in order of preference
    candidates = [
        DEFAULT_SOURCE_XLSX,
        DEFAULT_SOURCE_CSV,
        os.path.join(MODULE_DIR, "test_data", "Poverty_input.csv"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
            return candidate

    raise FileNotFoundError(
        "No downloaded source file found. Please run download_poverty.py first to "
        f"fetch the dataset, or specify --source_path. Checked: {candidates}"
    )


def preprocess_poverty(src_path, dst_path=CLEANED_CSV, min_county_count=400):
    """Preprocesses the downloaded source dataset into cleaned format with normalized columns."""
    logging.info("Preprocessing source Poverty dataset from %s...", src_path)
    if not os.path.exists(src_path) or os.path.getsize(src_path) == 0:
        logging.error("Source file does not exist or is empty: %s", src_path)
        raise ValueError(f"Source file does not exist or is empty: {src_path}")

    if src_path.lower().endswith((".xlsx", ".xls")):
        df = _extract_dataframe_from_excel(src_path)
    else:
        df = pd.read_csv(src_path, dtype=str)
        # Handle legacy CSV files that have 2 leading title rows before the header row
        stripped_cols = {str(c).strip() for c in df.columns}
        if not (stripped_cols & {"County FIPS", "County FIPS Code", "GEOID"}):
            df = pd.read_csv(src_path, skiprows=2, dtype=str)

    if df.empty:
        logging.error("Source dataset is empty: %s", src_path)
        raise ValueError(f"Source dataset is empty: {src_path}")

    # Strip column headers to avoid whitespace issues
    df.columns = df.columns.str.strip()

    # Rename columns to standardized schema
    rename_dict = {}
    for col in df.columns:
        if col in COLUMN_RENAME_MAP:
            rename_dict[col] = COLUMN_RENAME_MAP[col]
        elif re.match(r"^20\d{2}-2020\s+Poverty\s*%$", col, flags=re.IGNORECASE):
            rename_dict[col] = "poverty_rate_2020"

    df = df.rename(columns=rename_dict)

    required_cols = ["GEOID", "poverty_rate_1990", "poverty_rate_2000", "poverty_rate_2020"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logging.error("Missing required columns in source dataset: %s", missing_cols)
        raise ValueError(f"Missing required columns in source dataset: {missing_cols}")

    # Standardize and validate GEOIDs
    df["GEOID"] = df["GEOID"].apply(clean_geoid)
    df = df.dropna(subset=["GEOID"])

    # Coerce and validate poverty values within [0.0, 100.0]
    poverty_cols = ["poverty_rate_1990", "poverty_rate_2000", "poverty_rate_2020"]
    for col in poverty_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.strip(), errors="coerce")
        invalid_mask = df[col].notna() & ((df[col] < 0.0) | (df[col] > 100.0))
        if invalid_mask.any():
            logging.warning(
                "Found %d out-of-bounds values in %s; setting to NaN",
                invalid_mask.sum(),
                col,
            )
            df.loc[invalid_mask, col] = None

    # Keep rows that have at least one valid poverty rate observation
    df = df.dropna(subset=poverty_cols, how="all")

    # Keep target columns only
    df = df[required_cols]

    # Verify sanity threshold
    if len(df) < min_county_count:
        logging.error(
            "Sanity check failed: Expected at least %d places, but found %d.",
            min_county_count,
            len(df),
        )
        raise ValueError(
            f"Sanity check failed: Expected at least {min_county_count} places, but found {len(df)}."
        )

    # Atomic write to destination file
    dst_dir = os.path.dirname(os.path.abspath(dst_path))
    os.makedirs(dst_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", dir=dst_dir, delete=False, suffix=".tmp", encoding="utf-8"
    ) as tmp_file:
        df.to_csv(tmp_file.name, index=False)
        temp_path = tmp_file.name

    os.replace(temp_path, dst_path)
    logging.info("Poverty dataset cleaned and saved successfully to %s!", dst_path)
    logging.info("Shape: %s", df.shape)
    return dst_path


def main(argv):
    del argv  # Unused
    source_path = resolve_source_file_path(FLAGS.source_path)
    preprocess_poverty(
        src_path=source_path,
        dst_path=FLAGS.cleaned_csv_path,
        min_county_count=FLAGS.min_county_count,
    )


if __name__ == "__main__":
    app.run(main)
