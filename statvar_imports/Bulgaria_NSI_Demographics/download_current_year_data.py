#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Downloader and Preprocessor for Bulgaria NSI Demographics.

This script checks the official NSI website
(https://www.nsi.bg/en/statistical-data/206/649)
for published annual population data:
1. Downloads the live NSI HTML page and saves the raw `.html` into `input_files/`
   (copied to `source_files` and GCS for archival and debugging reference).
2. Parses the HTML table (`<table class="nsit3">`) with Urban & Rural residence
   and sex breakdowns and formats it into the NSI single-year CSV schema:
       BulgariaNSI_Demographics_Year_input_{YEAR}.csv
   Always prefers freshly downloaded source data over cached GCS files.
3. Uploads the raw HTML and CSV to the shared GCS folder:
       gs://unresolved_mcf/country/Bulgaria/input_files/
4. When `--sanitized_dir` is provided, sanitizes all annual CSVs in
   `--local_dir` (retaining original downloaded files in `input_files/` for
   `source_files` while writing normalized copies to `sanitized_input_files/`
   for `stat_var_processor.py`). Data, place, and StatVar coverage validations
   are enforced downstream via `validation_config.json` (`SQL_VALIDATOR` and
   `MAX_DATE_CONSISTENT`).
"""

import csv
import glob
import io
import os
import re
import subprocess
import sys
import tempfile

from absl import app
from absl import flags
from absl import logging
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOCAL_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_GCS_DIR = "gs://unresolved_mcf/country/Bulgaria/input_files"
SUBPROCESS_TIMEOUT_SECONDS = 120

NSI_URL = "https://www.nsi.bg/en/statistical-data/206/649"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36")
}

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "gcs_dir",
    DEFAULT_GCS_DIR,
    "Destination GCS folder for raw source and annual input files.",
)
flags.DEFINE_string(
    "local_dir",
    DEFAULT_LOCAL_DIR,
    "Local storage directory for raw downloaded source files.",
)
flags.DEFINE_string(
    "sanitized_dir",
    "",
    "Optional output directory for sanitized CSVs ready for stat_var_processor.",
)
flags.DEFINE_boolean(
    "dry_run",
    False,
    "Download and format locally without uploading to GCS.",
)
flags.DEFINE_boolean(
    "allow_staged_fallback",
    False,
    "Allow falling back to existing staged GCS files if live NSI portal is "
    "blocked by Cloudflare.",
)


def _create_retry_session() -> requests.Session:
    """Creates a requests.Session configured with retry/backoff."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def list_gcs_files(gcs_dir: str) -> list[str]:
    """Lists files currently in the shared GCS destination folder."""
    target = gcs_dir.rstrip("/") + "/"
    try:
        cmd = ["gcloud", "storage", "ls", target]
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
        return [
            os.path.basename(line.strip()) for line in res.stdout.splitlines()
            if line.strip()
        ]
    except Exception as e:
        logging.error("Failed to list GCS directory %s: %s", target, e)
        raise RuntimeError(
            f"Failed to list GCS directory {target}: {e}") from e


def _upload_to_gcs(local_path: str, gcs_target_path: str):
    """Uploads a local file to GCS using gcloud storage cp."""
    logging.info("Uploading '%s' to %s...", os.path.basename(local_path),
                 gcs_target_path)
    try:
        cmd = ["gcloud", "storage", "cp", local_path, gcs_target_path]
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except Exception as e:
        logging.error("Upload to %s failed: %s", gcs_target_path, e)
        sys.exit(1)
    logging.info("Successfully uploaded to %s!", gcs_target_path)


def normalize_cell(val: str, is_numeric_col: bool = False) -> str:
    """Normalizes NSI cell text (whitespace, hyphens, footnote asterisks, .0)."""
    s = str(val).replace('"""', '"').replace("\xa0", " ")
    s = re.sub(r"(AS OF 31\.12\.)\*+", r"\1", s, flags=re.IGNORECASE)
    if is_numeric_col:
        s = re.sub(r"\s+", "", s)
        if s.endswith(".0"):
            s = s[:-2]
        return s
    s = re.sub(r"(\b\d+)\s*-\s*(\d+\b)", r"\1 - \2", s)
    s = re.sub(r"(\b100)\s*\+", r"\1 +", s)
    return re.sub(r"\s+", " ", s).strip()


def sanitize_csv_content(content: str) -> list[list[str]]:
    """Parses raw CSV text and normalizes all cells for PVMap processing."""
    reader = list(csv.reader(io.StringIO(content)))
    return [[
        normalize_cell(c, is_numeric_col=(r_idx >= 3 and c_idx > 0))
        for c_idx, c in enumerate(row)
    ] for r_idx, row in enumerate(reader)]


def sanitize_directory_files(input_dir: str, sanitized_dir: str):
    """Writes sanitized copies of annual CSVs without modifying raw source files."""
    os.makedirs(sanitized_dir, exist_ok=True)
    pattern = os.path.join(input_dir,
                           "BulgariaNSI_Demographics_Year_input_*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        logging.error("No annual input CSV files matched in %s", input_dir)
        sys.exit(1)

    for fpath in files:
        bname = os.path.basename(fpath)
        if not re.search(r"Year_input_(\d{4})\.csv$", bname):
            logging.error(
                "Input file '%s' does not match expected pattern "
                "'Year_input_YYYY.csv'", bname)
            sys.exit(1)

        with open(fpath, "r", encoding="utf-8") as f:
            cleaned_rows = sanitize_csv_content(f.read())

        out_path = os.path.join(sanitized_dir, bname)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(cleaned_rows)
        logging.info("Sanitized %s -> %s (%d rows)", fpath, out_path,
                     len(cleaned_rows))


def check_and_download_nsi(
    local_dir: str,
    gcs_dir: str,
    dry_run: bool = False,
    allow_staged_fallback: bool = False,
):
    """Downloads latest NSI data, saves raw HTML and CSV, and uploads to GCS."""
    os.makedirs(local_dir, exist_ok=True)
    logging.info(
        "Bulgaria NSI Demographics: Live Portal Downloader "
        "(Source: %s, Destination GCS: %s)", NSI_URL, gcs_dir)

    html_content = None
    is_cloudflare_blocked = False
    session = _create_retry_session()
    try:
        resp = session.get(NSI_URL, headers=HEADERS, timeout=25)
        if resp.status_code == 200:
            html_content = resp.text
            logging.info("Successfully connected to live NSI portal.")
        elif resp.status_code == 403:
            is_cloudflare_blocked = True
            logging.warning(
                "NSI portal returned HTTP 403 (Cloudflare challenge/block) "
                "for %s.", NSI_URL)
        else:
            logging.error("NSI portal returned unexpected HTTP %d for %s.",
                          resp.status_code, NSI_URL)
            sys.exit(1)
    except Exception as e:
        logging.error("Direct request to nsi.bg failed: %s", e)
        sys.exit(1)

    if not html_content:
        if is_cloudflare_blocked and allow_staged_fallback:
            logging.info(
                "Checking if input files are already present in GCS "
                "(%s) (--allow_staged_fallback enabled)...", gcs_dir)
            existing_gcs_files = list_gcs_files(gcs_dir)
            annual_files = [
                f for f in existing_gcs_files if re.match(
                    r"BulgariaNSI_Demographics_Year_input_\d{4}\.csv$", f)
            ]
            if annual_files:
                logging.info(
                    "Existing annual files in GCS folder: %s. "
                    "Proceeding with staged data.", annual_files)
                return
        logging.error(
            "Unable to fetch live NSI portal content "
            "(pass --allow_staged_fallback to use existing GCS files).")
        sys.exit(1)

    # 1. Detect Year from caption (<div id="ttitle">...31.12.YYYY...</div>)
    ttitle_match = re.search(
        r'id=["\']ttitle["\'][^>]*>(.*?)</div>',
        html_content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not ttitle_match:
        logging.error("Could not find <div id='ttitle'> caption in NSI HTML.")
        sys.exit(1)
    caption_text = ttitle_match.group(1)
    year_match = re.search(r"31\.12\.(\d{4})", caption_text)
    if not year_match:
        logging.error("Could not parse reference year from caption: '%s'",
                      caption_text[:200])
        sys.exit(1)

    detected_year = int(year_match.group(1))
    logging.info("Detected published year on NSI portal: %d", detected_year)

    # 2. Save raw HTML to local_dir (for source_files and debugging/archival)
    html_filename = f"BulgariaNSI_Demographics_Year_input_{detected_year}.html"
    local_html_path = os.path.join(local_dir, html_filename)
    with open(local_html_path, "w", encoding="utf-8") as html_f:
        html_f.write(html_content)
    logging.info("Saved raw NSI HTML to %s (%d bytes)", local_html_path,
                 os.path.getsize(local_html_path))

    target_filename = (
        f"BulgariaNSI_Demographics_Year_input_{detected_year}.csv")
    local_output_path = os.path.join(local_dir, target_filename)
    gcs_target_path = f"{gcs_dir.rstrip('/')}/{target_filename}"
    gcs_html_path = f"{gcs_dir.rstrip('/')}/{html_filename}"

    # 3. Always prefer newly downloaded data from source over cached GCS files
    logging.info("Processing live source data for %d...", detected_year)

    try:
        tables = pd.read_html(io.StringIO(html_content),
                              attrs={"class": "nsit3"})
    except ValueError:
        tables = []
    if not tables:
        logging.error(
            "Could not locate table with class 'nsit3' in page HTML.")
        sys.exit(1)
    df = tables[0]

    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = (df[col].astype(str).str.replace("\xa0",
                                                       " ").str.strip())

    # 4. Write CSV to temporary file first, then atomically replace
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=f".{target_filename}.",
                                        suffix=".tmp",
                                        dir=local_dir)
    try:
        with os.fdopen(tmp_fd, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Header rows required by BulgariaNSI_Demographics_pvmap.csv
            writer.writerow([
                "POPULATION BY DISTRICTS, AGE, PLACE OF RESIDENCE AND SEX"
                f" AS OF 31.12.{detected_year} (Number)"
            ] + [""] * 9)
            writer.writerow([
                "Districts Age (years)",
                "Total",
                "",
                "",
                "Urban residence",
                "",
                "",
                "Rural residence",
                "",
                "",
            ])
            writer.writerow([
                "",
                "Total",
                "Male",
                "Female",
                "Total",
                "Male",
                "Female",
                "Total",
                "Male",
                "Female",
            ])

            for _, row in df.iterrows():
                clean_vals = [
                    normalize_cell(v, is_numeric_col=(i > 0))
                    for i, v in enumerate(row.values)
                ]
                writer.writerow(clean_vals)

        os.replace(tmp_path, local_output_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    logging.info("Saved local CSV file: %s (%d bytes)", local_output_path,
                 os.path.getsize(local_output_path))

    # 5. Upload raw HTML and CSV to shared GCS destination
    if dry_run:
        logging.info("[Dry Run] Skipping upload to %s.", gcs_target_path)
        return

    _upload_to_gcs(local_html_path, gcs_html_path)
    _upload_to_gcs(local_output_path, gcs_target_path)


def main(argv):
    del argv
    logging.set_verbosity(logging.INFO)
    check_and_download_nsi(
        local_dir=FLAGS.local_dir,
        gcs_dir=FLAGS.gcs_dir,
        dry_run=FLAGS.dry_run,
        allow_staged_fallback=FLAGS.allow_staged_fallback,
    )
    if FLAGS.sanitized_dir:
        sanitize_directory_files(FLAGS.local_dir, FLAGS.sanitized_dir)


if __name__ == "__main__":
    app.run(main)
