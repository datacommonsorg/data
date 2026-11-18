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
"""Download and preprocess CDC NNDSS Weekly Socrata CSV for stat_var_processor."""

import datetime
import importlib.util
import os
from pathlib import Path
import time
from typing import Dict, Optional, Tuple

from absl import app
from absl import flags
from absl import logging
import pandas as pd

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    "input_csv",
    "",
    "Optional local path to NNDSS Socrata CSV (skips CDC download).",
)
flags.DEFINE_string(
    "output_csv",
    "",
    "Optional output CSV path (defaults to input_files/NNDSS_Weekly_Data.csv).",
)
flags.DEFINE_bool(
    "skip_gcs_history",
    False,
    "If true, skips downloading 2006-2021 historical files from GCS.",
)
flags.DEFINE_bool(
    "normalize_output",
    False,
    "If true, ensures output/nndss_weekly_output.{csv,tmcf} exposes "
    "observationPeriod as a column so genmcf matches the historical TMCF.",
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
HISTORY_DIR = os.path.join(SCRIPT_DIR, "history")
HISTORY_GCS_BUCKET = "unresolved_mcf"
HISTORY_GCS_PREFIX = "cdc/nndss_infectious_diseasesweekly/history"
HISTORY_FILES = (
    "cdc_nndss_weekly_tables_historical.csv",
    "cdc_nndss_weekly_tables_historical.tmcf",
)
RAW_FILE = os.path.join(INPUT_DIR, "rows.csv")
OUTPUT_FILE = os.path.join(INPUT_DIR, "NNDSS_Weekly_Data.csv")
SOURCE_URL = ("https://data.cdc.gov/api/views/x9gk-5huc/rows.csv"
              "?accessType=DOWNLOAD&api_foundry=true")
SKIP_FLAGS = {"N", "NN", "NP", "NC", "U"}

OUTPUT_COLUMNS = [
    "Reporting Area",
    "Current MMWR Year",
    "MMWR WEEK",
    "observationDate",
    "Label",
    "Current week",
]


def _start_date_of_year(year: int) -> datetime.date:
    """Return the first day of the first MMWR week for a given year."""
    jan_one = datetime.date(year, 1, 1)
    diff = 7 * (jan_one.isoweekday() > 3) - jan_one.isoweekday()
    return jan_one + datetime.timedelta(days=diff)


def get_mmwr_week_start_date(year, week) -> Optional[str]:
    """Compute ISO YYYY-MM-DD start date for a given MMWR year and week."""
    try:
        y = int(year)
        w = int(week)
    except (ValueError, TypeError):
        return None
    if not (1 <= w <= 53):
        logging.warning(f"Invalid MMWR WEEK found: {w}. Skipping.")
        return None
    day_one = _start_date_of_year(y)
    return (day_one + datetime.timedelta(days=7 * (w - 1))).isoformat()


def _format_number(val: float) -> str:
    """Format integer-valued floats without trailing .0."""
    return str(int(val)) if val.is_integer() else str(val)


def download_source_csv() -> str:
    """Download x9gk-5huc CSV from CDC with exponential backoff retry."""
    util_script_path = os.path.abspath(
        os.path.join(SCRIPT_DIR, "../../../util/download_util_script.py"))
    spec = importlib.util.spec_from_file_location("download_util_script",
                                                  util_script_path)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load download_util_script from {util_script_path}")
    download_util_script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(download_util_script)
    download_file = download_util_script.download_file

    max_attempts = 3
    retry_delay = 5
    download_ok = False
    for attempt in range(1, max_attempts + 1):
        try:
            logging.info(f"Download attempt {attempt}/{max_attempts}...")
            if os.path.exists(RAW_FILE):
                os.remove(RAW_FILE)
            download_ok = download_file(
                url=SOURCE_URL,
                output_folder=INPUT_DIR,
                unzip=False,
                headers=None,
                tries=3,
                delay=5,
                backoff=2,
            )
            if download_ok and os.path.exists(RAW_FILE):
                logging.info("Download completed successfully.")
                break
            logging.warning(
                f"Download attempt {attempt}/{max_attempts} returned {download_ok}."
            )
        except Exception as exc:
            logging.warning(
                f"Download attempt {attempt}/{max_attempts} raised {exc}.")
        if attempt < max_attempts:
            time.sleep(retry_delay)
            retry_delay *= 2

    if not download_ok or not os.path.exists(RAW_FILE):
        raise IOError("Failed to download rows.csv after all retry attempts.")

    size_mb = os.path.getsize(RAW_FILE) / (1024 * 1024)
    logging.info(f"Downloaded file size: {size_mb:.2f} MB.")
    if size_mb < 0.1:
        raise ValueError("Downloaded file is suspiciously small (<0.1 MB).")
    return RAW_FILE


def preprocess_csv(
    filepath: str,
    out_filepath: str,
    min_year: int = 2022,
) -> pd.DataFrame:
    """Filter x9gk-5huc to valid Current week rows (>= min_year), add observationDate, and sum NY+NYC."""
    chunks = []
    ny_sums: Dict[Tuple[str, str, str, str], float] = {}
    required_cols = [
        "Current week",
        "Current MMWR Year",
        "MMWR WEEK",
        "Reporting Area",
        "Label",
    ]

    header_cols = pd.read_csv(filepath, nrows=0).columns
    missing_cols = [col for col in required_cols if col not in header_cols]
    if missing_cols:
        raise KeyError(f"Missing required columns in input CSV: {missing_cols}")

    bad_lines_count = 0

    def _handle_bad_line(bad_line):
        nonlocal bad_lines_count
        bad_lines_count += 1
        return None

    reader = pd.read_csv(
        filepath,
        chunksize=100000,
        dtype=str,
        engine="python",
        on_bad_lines=_handle_bad_line,
    )
    for chunk_idx, chunk in enumerate(reader, start=1):
        logging.info(f"Processing chunk {chunk_idx}...")

        if "Current week, flag" in chunk.columns:
            flag_series = chunk["Current week, flag"].fillna("").str.strip()
            chunk = chunk[~flag_series.isin(SKIP_FLAGS)]

        chunk = chunk[chunk["Current week"].notna()].copy()
        mmwr_year = pd.to_numeric(chunk["Current MMWR Year"], errors="coerce")
        chunk = chunk[mmwr_year.notna() & (mmwr_year >= min_year)]
        chunk["val_num"] = pd.to_numeric(chunk["Current week"], errors="coerce")
        chunk = chunk[chunk["val_num"].notna() & (chunk["val_num"] >= 0)]
        if chunk.empty:
            continue

        yw_pairs = chunk[["Current MMWR Year", "MMWR WEEK"]].drop_duplicates()
        date_lookup = {
            (r["Current MMWR Year"], r["MMWR WEEK"]):
                get_mmwr_week_start_date(r["Current MMWR Year"], r["MMWR WEEK"])
            for _, r in yw_pairs.iterrows()
        }
        chunk["observationDate"] = [
            date_lookup.get((y, w))
            for y, w in zip(chunk["Current MMWR Year"], chunk["MMWR WEEK"])
        ]
        chunk = chunk[chunk["observationDate"].notna()]
        if chunk.empty:
            continue

        area_upper = chunk["Reporting Area"].astype(str).str.strip().str.upper()
        is_ny_ex_nyc = area_upper == "NEW YORK"
        is_nyc = area_upper == "NEW YORK CITY"

        for rec in chunk[is_ny_ex_nyc | is_nyc][[
                "Current MMWR Year", "MMWR WEEK", "observationDate", "Label",
                "val_num"
        ]].to_dict("records"):
            key = (
                rec["Current MMWR Year"],
                rec["MMWR WEEK"],
                rec["observationDate"],
                rec["Label"],
            )
            ny_sums[key] = ny_sums.get(key, 0.0) + float(rec["val_num"])

        kept = chunk[~is_ny_ex_nyc].copy()
        kept["Current week"] = kept["val_num"].map(_format_number)
        chunks.append(kept[OUTPUT_COLUMNS])

    if ny_sums:
        ny_rows = [{
            "Reporting Area": "NEW YORK",
            "Current MMWR Year": k[0],
            "MMWR WEEK": k[1],
            "observationDate": k[2],
            "Label": k[3],
            "Current week": _format_number(v),
        } for k, v in ny_sums.items()]
        chunks.append(pd.DataFrame(ny_rows, columns=OUTPUT_COLUMNS))

    out_df = (pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(
        columns=OUTPUT_COLUMNS))
    if bad_lines_count:
        logging.warning(f"Skipped {bad_lines_count} malformed CSV rows.")
    tmp_out = f"{out_filepath}.tmp"
    out_df.to_csv(tmp_out, index=False)
    os.replace(tmp_out, out_filepath)
    logging.info(f"Wrote {len(out_df)} preprocessed rows to {out_filepath}.")
    return out_df


def download_historical_files(
    history_dir: str = HISTORY_DIR,
    bucket_name: str = HISTORY_GCS_BUCKET,
    prefix: str = HISTORY_GCS_PREFIX,
) -> None:
    """Download frozen 2006-2021 historical CSV and TMCF from GCS."""
    from google.cloud import storage

    Path(history_dir).mkdir(parents=True, exist_ok=True)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    for filename in HISTORY_FILES:
        blob_path = f"{prefix}/{filename}"
        dest_path = os.path.join(history_dir, filename)
        logging.info(
            f"Downloading gs://{bucket_name}/{blob_path} to {dest_path}...")
        bucket.blob(blob_path).download_to_filename(dest_path)


def normalize_output_files(
    output_dir: str = os.path.join(SCRIPT_DIR, "output"),
    prefix: str = "nndss_weekly_output",
) -> None:
    """Ensure output CSV/TMCF exposes observationPeriod as a column."""
    import csv

    csv_path = os.path.join(output_dir, f"{prefix}.csv")
    tmcf_path = os.path.join(output_dir, f"{prefix}.tmcf")

    tmp_csv = f"{csv_path}.tmp"
    with open(csv_path, "r", encoding="utf-8", newline="") as src:
        reader = csv.reader(src)
        header = next(reader)
        if "observationPeriod" not in header:
            with open(tmp_csv, "w", encoding="utf-8", newline="") as dst:
                writer = csv.writer(dst)
                writer.writerow(header + ["observationPeriod"])
                for row in reader:
                    writer.writerow(row + ["P1W"])
            os.replace(tmp_csv, csv_path)

    with open(tmcf_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    found_period = False
    for line in lines:
        if line.startswith("observationPeriod:"):
            new_lines.append(
                f"observationPeriod: C:{prefix}->observationPeriod\n")
            found_period = True
        else:
            new_lines.append(line)
    if not found_period:
        new_lines.append(f"observationPeriod: C:{prefix}->observationPeriod\n")
    tmp_tmcf = f"{tmcf_path}.tmp"
    with open(tmp_tmcf, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    os.replace(tmp_tmcf, tmcf_path)


def main(argv):
    del argv
    if _FLAGS.normalize_output:
        normalize_output_files()
        return
    Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)
    if not _FLAGS.skip_gcs_history:
        download_historical_files()
    source_csv = _FLAGS.input_csv or download_source_csv()
    out_csv = _FLAGS.output_csv or OUTPUT_FILE
    preprocess_csv(source_csv, out_csv)


if __name__ == "__main__":
    app.run(main)
