"""Preprocessing script for Commerce EDA Persistent Poverty import."""

import os
import re
import sys
import tempfile
import time
import pandas as pd
from absl import app, flags, logging

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "util"))

from util import file_util

ORIGINAL_CSV = os.path.join(MODULE_DIR, "output", "Poverty_original.csv")
CLEANED_CSV = os.path.join(MODULE_DIR, "output", "Poverty_cleaned.csv")
GCS_SOURCE_URI = "gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv"

FLAGS = flags.FLAGS
flags.DEFINE_string("gcs_source_uri", GCS_SOURCE_URI, "GCS URI for raw Poverty CSV.")
flags.DEFINE_string("raw_csv_path", ORIGINAL_CSV, "Path to save downloaded raw CSV.")
flags.DEFINE_string("cleaned_csv_path", CLEANED_CSV, "Path to save cleaned output CSV.")
flags.DEFINE_integer("min_county_count", 3000, "Minimum number of valid counties expected.")

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

# Island territories where most recent estimate is from 2020 Decennial Census
ISLAND_TERRITORY_FIPS = {"60", "66", "69", "78"}

COLUMN_RENAME_MAP = {
    "GEOID": "GEOID",
    "1990 Decennial Census, % in Poverty": "poverty_rate_1990",
    "2000 Decennial Census, % in Poverty": "poverty_rate_2000",
    "Most Recent Estimate, % in Poverty*": "poverty_rate_recent",
}


def download_from_gcs(src_uri=GCS_SOURCE_URI, dst_path=ORIGINAL_CSV, max_retries=3, backoff_factor=1.5):
    """Downloads the original Poverty dataset from GCS with retry and validates it."""
    logging.info("Downloading original Poverty dataset from GCS: %s", src_uri)
    os.makedirs(os.path.dirname(os.path.abspath(dst_path)), exist_ok=True)
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            file_util.file_copy(src_uri, dst_path)
            if os.path.exists(dst_path) and os.path.getsize(dst_path) > 0:
                logging.info("GCS Download completed successfully. File size: %d bytes.", os.path.getsize(dst_path))
                return
            last_err = RuntimeError(f"Destination {dst_path} does not exist or is empty.")
        except Exception as e:
            last_err = e
            logging.warning("Attempt %d/%d failed to download %s: %s", attempt, max_retries, src_uri, e)
        if attempt < max_retries:
            time.sleep(backoff_factor ** (attempt - 1))

    logging.error("GCS download failed after %d attempts for %s: %s", max_retries, src_uri, last_err)
    raise RuntimeError(f"GCS download failed after {max_retries} attempts for {src_uri}: {last_err}") from last_err


def clean_geoid(val):
    """Standardizes GEOIDs to 5 digits and validates against US state FIPS (rejecting state summary XX000)."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    match = re.match(r"^(\d+)(?:\.0+)?$", s)
    if not match:
        return None
    digits = match.group(1)
    if len(digits) == 4:
        digits = digits.zfill(5)
    if len(digits) == 5 and digits[:2] in VALID_STATE_FIPS and digits[2:] != "000":
        return digits
    return None


def preprocess_poverty(src_path=ORIGINAL_CSV, dst_path=CLEANED_CSV, min_county_count=3000):
    """Preprocesses the raw Poverty dataset into cleaned format with normalized columns."""
    logging.info("Preprocessing original Poverty dataset from %s...", src_path)
    if not os.path.exists(src_path) or os.path.getsize(src_path) == 0:
        logging.error("Source file does not exist or is empty: %s", src_path)
        raise ValueError(f"Source file does not exist or is empty: {src_path}")

    # Load original Poverty.csv, skipping first 2 rows of headers/explanations
    df = pd.read_csv(src_path, skiprows=2, dtype=str)
    if df.empty:
        logging.error("Source CSV is empty: %s", src_path)
        raise ValueError(f"Source CSV is empty: {src_path}")

    # Strip column headers to avoid fragile whitespace issues
    df.columns = df.columns.str.strip()

    # Verify expected columns exist
    missing_cols = [col for col in COLUMN_RENAME_MAP if col not in df.columns]
    if missing_cols:
        logging.error("Missing required columns in source CSV: %s", missing_cols)
        raise ValueError(f"Missing required columns in source CSV: {missing_cols}")

    # Guard against silent year corruption if Data Source column is present
    data_source_cols = [c for c in df.columns if "Data Source" in c]
    df = df.rename(columns=COLUMN_RENAME_MAP)

    # Standardize and validate GEOIDs
    df["GEOID"] = df["GEOID"].apply(clean_geoid)
    df = df.dropna(subset=["GEOID"])

    if data_source_cols:
        ds_col = data_source_cols[0]
        is_terr = df["GEOID"].str[:2].isin(ISLAND_TERRITORY_FIPS)
        for idx, row in df.iterrows():
            val = str(row.get(ds_col, "")).strip()
            if val and val != "nan":
                m = re.search(r"(\d{4})\s*$", val)
                if m:
                    yr = m.group(1)
                    expected_yr = "2020" if is_terr.loc[idx] else "2021"
                    if yr != expected_yr:
                        logging.error("Unexpected survey year %s in %s for GEOID %s (expected %s)", yr, ds_col, row["GEOID"], expected_yr)
                        raise ValueError(f"Unexpected survey year {yr} in {ds_col} for GEOID {row['GEOID']} (expected {expected_yr})")

    # Coerce and validate poverty values within [0.0, 100.0]
    raw_poverty_cols = ["poverty_rate_1990", "poverty_rate_2000", "poverty_rate_recent"]
    for col in raw_poverty_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.strip(), errors="coerce")
        invalid_mask = df[col].notna() & ((df[col] < 0.0) | (df[col] > 100.0))
        if invalid_mask.any():
            logging.warning("Found %d out-of-bounds values in %s; setting to NaN", invalid_mask.sum(), col)
            df.loc[invalid_mask, col] = None

    # Split recent poverty rate:
    is_territory = df["GEOID"].str[:2].isin(ISLAND_TERRITORY_FIPS)
    df["poverty_rate_2020"] = df["poverty_rate_recent"].where(is_territory, None)
    df["poverty_rate_2021"] = df["poverty_rate_recent"].where(~is_territory, None)

    # Keep rows that have at least one valid poverty rate observation
    poverty_cols = ["poverty_rate_1990", "poverty_rate_2000", "poverty_rate_2020", "poverty_rate_2021"]
    df = df.dropna(subset=poverty_cols, how="all")

    # Keep target columns only
    target_cols = ["GEOID"] + poverty_cols
    df = df[target_cols]

    # Verify sanity threshold
    if len(df) < min_county_count:
        logging.error(
            "Sanity check failed: Expected at least %d counties, but found %d.",
            min_county_count,
            len(df),
        )
        raise ValueError(
            f"Sanity check failed: Expected at least {min_county_count} counties, but found {len(df)}."
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
    download_from_gcs(src_uri=FLAGS.gcs_source_uri, dst_path=FLAGS.raw_csv_path)
    preprocess_poverty(src_path=FLAGS.raw_csv_path, dst_path=FLAGS.cleaned_csv_path, min_county_count=FLAGS.min_county_count)


if __name__ == "__main__":
    app.run(main)
