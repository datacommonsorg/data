"""Preprocessing script for Commerce EDA Persistent Poverty import."""

import os
import sys
import tempfile
import pandas as pd
from absl import app, logging

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "util"))

from util import file_util

ORIGINAL_CSV = os.path.join(MODULE_DIR, "output", "Poverty_original.csv")
CLEANED_CSV = os.path.join(MODULE_DIR, "output", "Poverty_cleaned.csv")
GCS_SOURCE_URI = "gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv"

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

COLUMN_RENAME_MAP = {
    "GEOID": "GEOID",
    "1990 Decennial Census, % in Poverty": "poverty_rate_1990",
    "2000 Decennial Census, % in Poverty": "poverty_rate_2000",
    "Most Recent Estimate, % in Poverty*": "poverty_rate_recent",
}


def download_from_gcs(dst_path=ORIGINAL_CSV):
    """Downloads the original Poverty dataset from GCS and validates it."""
    logging.info("Downloading original Poverty dataset from GCS: %s", GCS_SOURCE_URI)
    os.makedirs(os.path.dirname(os.path.abspath(dst_path)), exist_ok=True)
    file_util.file_copy(GCS_SOURCE_URI, dst_path)
    if not os.path.exists(dst_path) or os.path.getsize(dst_path) == 0:
        logging.fatal("GCS download failed: destination %s does not exist or is empty.", dst_path)
    logging.info("GCS Download completed successfully. File size: %d bytes.", os.path.getsize(dst_path))


def clean_geoid(val):
    """Standardizes GEOIDs to 5 digits and validates against US state FIPS."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if len(s) == 4 and s.isdigit():
        s = s.zfill(5)
    if len(s) == 5 and s.isdigit() and s[:2] in VALID_STATE_FIPS:
        return s
    return None


def preprocess_poverty(src_path=ORIGINAL_CSV, dst_path=CLEANED_CSV, min_county_count=3000):
    """Preprocesses the raw Poverty dataset into cleaned format with normalized columns."""
    logging.info("Preprocessing original Poverty dataset from %s...", src_path)
    if not os.path.exists(src_path) or os.path.getsize(src_path) == 0:
        logging.fatal("Source file does not exist or is empty: %s", src_path)

    # Load original Poverty.csv, skipping first 2 rows of headers/explanations
    df = pd.read_csv(src_path, skiprows=2, dtype=str)
    if df.empty:
        logging.fatal("Source CSV is empty: %s", src_path)

    # Strip column headers to avoid fragile whitespace issues
    df.columns = df.columns.str.strip()

    # Verify expected columns exist
    missing_cols = [col for col in COLUMN_RENAME_MAP if col not in df.columns]
    if missing_cols:
        logging.fatal("Missing required columns in source CSV: %s", missing_cols)

    df = df.rename(columns=COLUMN_RENAME_MAP)

    # Standardize and validate GEOIDs
    df["GEOID"] = df["GEOID"].apply(clean_geoid)
    df = df.dropna(subset=["GEOID"])

    # Coerce and validate poverty values within [0.0, 100.0]
    poverty_cols = ["poverty_rate_1990", "poverty_rate_2000", "poverty_rate_recent"]
    for col in poverty_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.strip(), errors="coerce")
        invalid_mask = df[col].notna() & ((df[col] < 0.0) | (df[col] > 100.0))
        if invalid_mask.any():
            logging.warning("Found %d out-of-bounds values in %s; setting to NaN", invalid_mask.sum(), col)
            df.loc[invalid_mask, col] = None

    # Keep rows that have at least one valid poverty rate observation
    df = df.dropna(subset=poverty_cols, how="all")

    # Keep target columns only
    target_cols = ["GEOID"] + poverty_cols
    df = df[target_cols]

    # Verify sanity threshold
    if len(df) < min_county_count:
        logging.fatal(
            "Sanity check failed: Expected at least %d counties, but found %d.",
            min_county_count,
            len(df),
        )

    # Atomic write to destination file
    dst_dir = os.path.dirname(os.path.abspath(dst_path))
    os.makedirs(dst_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=dst_dir, delete=False, suffix=".tmp") as tmp_file:
        df.to_csv(tmp_file.name, index=False)
        temp_path = tmp_file.name

    os.replace(temp_path, dst_path)
    logging.info("Poverty dataset cleaned and saved successfully to %s!", dst_path)
    logging.info("Shape: %s", df.shape)


def main(argv):
    del argv  # Unused
    download_from_gcs()
    preprocess_poverty()


if __name__ == "__main__":
    app.run(main)
