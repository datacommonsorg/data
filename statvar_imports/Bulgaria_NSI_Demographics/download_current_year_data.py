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
"""Monthly Monitoring & Downloader for Bulgaria NSI Demographics.

This script checks the official NSI website
(https://www.nsi.bg/en/statistical-data/206/649)
for newly published annual population data. If a new release is detected (e.g.
2026 or newer):
1. Downloads and parses the table with full Urban & Rural residence breakdowns.
2. Formats it into the exact NSI single-year structure:
       BulgariaNSI_Demographics_Year_input_{YEAR}.csv
   strictly verified against the reference template schema:
       https://docs.google.com/spreadsheets/d/18jZ06lzXQi_bqOKDoGZOpOMmD6RuTBuSxdOxLuMFOLo
3. Validates the generated file against structural, ordering, and arithmetic
constraints:
   - 3 Header rows, exactly 10 columns per row
   - Total Bulgaria + 28 Oblasts in identical sequence
   - All 22 age cohorts (0, 1 - 4, 5 - 9, ..., 100 +)
   - Internal consistency on both district and age rows:
     Total = Urban + Rural, Total = Male + Female,
     Urban = Urban_Male + Urban_Female, Rural = Rural_Male + Rural_Female,
     and District Header = sum of 22 age cohorts across all 9 numeric columns.
4. Automatically uploads the verified file to the shared GCS folder:
       gs://unresolved_mcf/country/Bulgaria/input_files/
"""

import argparse
import csv
import io
import os
import re
import subprocess
import sys
import tempfile

try:
    from absl import logging
except ImportError:
    import logging
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

EXPECTED_DISTRICTS = [
    "Total",
    "Blagoevgrad",
    "Burgas",
    "Varna",
    "Veliko Tarnovo",
    "Vidin",
    "Vratsa",
    "Gabrovo",
    "Dobrich",
    "Kardzhali",
    "Kyustendil",
    "Lovech",
    "Montana",
    "Pazardzhik",
    "Pernik",
    "Pleven",
    "Plovdiv",
    "Razgrad",
    "Ruse",
    "Silistra",
    "Sliven",
    "Smolyan",
    "Sofia",
    "Sofia (stolitsa)",
    "Stara Zagora",
    "Targovishte",
    "Haskovo",
    "Shumen",
    "Yambol",
]

EXPECTED_AGES = [
    "0",
    "1 - 4",
    "5 - 9",
    "10 - 14",
    "15 - 19",
    "20 - 24",
    "25 - 29",
    "30 - 34",
    "35 - 39",
    "40 - 44",
    "45 - 49",
    "50 - 54",
    "55 - 59",
    "60 - 64",
    "65 - 69",
    "70 - 74",
    "75 - 79",
    "80 - 84",
    "85 - 89",
    "90 - 94",
    "95 - 99",
    "100 +",
]


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
            os.path.basename(line.strip())
            for line in res.stdout.splitlines()
            if line.strip()
        ]
    except Exception as e:
        logging.warning("gcloud storage list failed (%s), trying gsutil...", e)
        try:
            cmd = ["gsutil", "ls", target]
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
            )
            return [
                os.path.basename(line.strip())
                for line in res.stdout.splitlines()
                if line.strip()
            ]
        except Exception as e2:
            logging.error("Failed to list GCS directory %s: %s", target, e2)
            raise RuntimeError(
                f"Failed to list GCS directory {target}: {e2}") from e2


def normalize_cell(val: str, is_numeric_col: bool = False) -> str:
    """Normalizes NSI cell text (whitespace, hyphens, footnote asterisks, .0)."""
    s = str(val).replace('"""', '"').replace("\xa0", " ")
    s = re.sub(r"(AS OF 31\.12\.)\*+", r"\1", s)
    if is_numeric_col:
        s = re.sub(r"\s+", "", s)
        if s.endswith(".0"):
            s = s[:-2]
        return s
    s = re.sub(r"(\b\d+)\s*-\s*(\d+\b)", r"\1 - \2", s)
    s = re.sub(r"(\b100)\s*\+", r"\1 +", s)
    return re.sub(r"\s+", " ", s).strip()


def sanitize_csv_content(content: str) -> list[list[str]]:
    """Parses raw CSV text and normalizes all cells for PVMap and validation."""
    reader = list(csv.reader(io.StringIO(content)))
    return [[
        normalize_cell(c, is_numeric_col=(r_idx >= 3 and c_idx > 0))
        for c_idx, c in enumerate(row)
    ]
            for r_idx, row in enumerate(reader)]


def to_num(val_str: str) -> int:
    """Converts value string to int, treating '-' as 0."""
    v = val_str.replace(" ", "").replace("\xa0", "").strip()
    if v.endswith(".0"):
        v = v[:-2]
    if v.isdigit():
        return int(v)
    return 0


def _validate_annual_row_values(row: list[str], row_idx: int, label: str):
    """Validates integer formatting and residence/sex arithmetic on a 10-col row."""
    for col_i in range(1, 10):
        val_str = row[col_i].strip()
        if not (val_str.isdigit() or val_str == "-"):
            raise ValueError(f"Row {row_idx} ({label}), col {col_i}: "
                             f"Expected integer or '-', got '{val_str}'.")

    tot = to_num(row[1])
    m = to_num(row[2])
    fem = to_num(row[3])
    urb = to_num(row[4])
    urb_m = to_num(row[5])
    urb_f = to_num(row[6])
    rur = to_num(row[7])
    rur_m = to_num(row[8])
    rur_f = to_num(row[9])

    if tot != urb + rur:
        raise ValueError(f"Row {row_idx} ({label}): "
                         f"Total ({tot}) != Urban ({urb}) + Rural ({rur}).")
    if tot != m + fem:
        raise ValueError(f"Row {row_idx} ({label}): "
                         f"Total ({tot}) != Male ({m}) + Female ({fem}).")
    if urb != urb_m + urb_f:
        raise ValueError(
            f"Row {row_idx} ({label}): "
            f"Urban ({urb}) != Urban Male ({urb_m}) + Urban Female ({urb_f}).")
    if rur != rur_m + rur_f:
        raise ValueError(
            f"Row {row_idx} ({label}): "
            f"Rural ({rur}) != Rural Male ({rur_m}) + Rural Female ({rur_f}).")
    if m != urb_m + rur_m:
        raise ValueError(
            f"Row {row_idx} ({label}): "
            f"Male ({m}) != Urban Male ({urb_m}) + Rural Male ({rur_m}).")
    if fem != urb_f + rur_f:
        raise ValueError(
            f"Row {row_idx} ({label}): "
            f"Female ({fem}) != Urban Female ({urb_f}) + Rural Female ({rur_f})."
        )


def validate_file_format(file_path: str, expected_year: int) -> bool:
    """Strictly validates CSV format against the reference 2024 template schema."""
    logging.info("Verifying format against reference schema (%s)...", file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    # 1. Row count: 3 Header rows + (29 districts * 23 rows) = 670 rows
    expected_total_rows = 3 + len(EXPECTED_DISTRICTS) * (1 + len(EXPECTED_AGES))
    if len(reader) != expected_total_rows:
        raise ValueError(
            f"Validation failed: Expected exactly {expected_total_rows} rows, "
            f"got {len(reader)}.")

    # 2. Header Row 1
    r1 = reader[0]
    if len(r1) != 10:
        raise ValueError(f"Header Row 1 must have 10 columns, got {len(r1)}.")
    expected_title_part = (
        "POPULATION BY DISTRICTS, AGE, PLACE OF RESIDENCE AND SEX AS OF"
        f" 31.12.{expected_year}")
    if expected_title_part not in r1[0]:
        raise ValueError(f"Header Row 1 title mismatch: '{r1[0]}', "
                         f"expected to contain '{expected_title_part}'.")

    # 3. Header Row 2
    r2 = reader[1]
    expected_r2 = [
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
    ]
    if r2 != expected_r2:
        raise ValueError(
            f"Header Row 2 mismatch:\nGot:      {r2}\nExpected: {expected_r2}")

    # 4. Header Row 3
    r3 = reader[2]
    expected_r3 = [
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
    ]
    if r3 != expected_r3:
        raise ValueError(
            f"Header Row 3 mismatch:\nGot:      {r3}\nExpected: {expected_r3}")

    # 5. District & Age Cohort sequence validation
    row_idx = 3
    for district in EXPECTED_DISTRICTS:
        # District header row
        d_row = reader[row_idx]
        if len(d_row) != 10:
            raise ValueError(
                f"Row {row_idx} ({district}) must have 10 columns, "
                f"got {len(d_row)}.")
        d_name = d_row[0].replace("\xa0", " ").strip()
        if d_name != district:
            raise ValueError(f"Row {row_idx}: Expected district '{district}', "
                             f"got '{d_name}'.")
        _validate_annual_row_values(d_row, row_idx, district)
        row_idx += 1

        # Age cohort rows
        a_rows = []
        for age in EXPECTED_AGES:
            a_row = reader[row_idx]
            if len(a_row) != 10:
                raise ValueError(
                    f"Row {row_idx} ({district} - {age}) must have 10 columns, "
                    f"got {len(a_row)}.")
            a_name = a_row[0].replace("\xa0", " ").strip()
            if a_name != age:
                raise ValueError(
                    f"Row {row_idx}: Expected age '{age}' for district "
                    f"'{district}', got '{a_name}'.")
            _validate_annual_row_values(a_row, row_idx, f"{district} - {age}")
            a_rows.append(a_row)
            row_idx += 1

        # Vertical sum validation: District header == sum of 22 age cohorts
        for col_i in range(1, 10):
            d_val = to_num(d_row[col_i])
            a_sum = sum(to_num(r[col_i]) for r in a_rows)
            if d_val != a_sum:
                raise ValueError(
                    f"District '{district}', col {col_i}: "
                    f"District header ({d_val}) != sum of age rows ({a_sum}).")

    logging.info("Format validation PASSED: Exactly matches reference template "
                 "structure and internal arithmetic!")
    return True


def check_and_download_nsi(
    local_dir: str,
    gcs_dir: str,
    force: bool = False,
    dry_run: bool = False,
    allow_staged_fallback: bool = False,
):
    """Checks for newly published data, validates format, and uploads to GCS if new."""
    os.makedirs(local_dir, exist_ok=True)
    logging.info(
        "Bulgaria NSI Demographics: Monthly Monitor & Auto-Downloader "
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

    # Fallback to cached copy if environment restricts direct outbound HTTP to nsi.bg
    if not html_content:
        cache_path = os.path.join(SCRIPT_DIR, "cached_nsi_page.html")
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()
            logging.info("Using cached HTML snapshot for NSI table.")

    if not html_content:
        if is_cloudflare_blocked and allow_staged_fallback:
            logging.info(
                "Checking if input files are already present in GCS "
                "(%s) (--allow-staged-fallback enabled)...", gcs_dir)
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
            "(pass --allow-staged-fallback to use existing GCS files).")
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

    target_filename = (
        f"BulgariaNSI_Demographics_Year_input_{detected_year}.csv")
    local_output_path = os.path.join(local_dir, target_filename)
    gcs_target_path = f"{gcs_dir.rstrip('/')}/{target_filename}"

    # 2. Check if file already exists in GCS
    existing_gcs_files = list_gcs_files(gcs_dir)
    logging.info("Current files in GCS folder: %s", existing_gcs_files)

    if target_filename in existing_gcs_files and not force:
        logging.info(
            "Up-to-date: '%s' is already present in %s. "
            "No new annual release detected. Exiting.", target_filename,
            gcs_dir)
        return

    logging.info("Processing release for %d! Formatting dataset...",
                 detected_year)

    # 3. Parse HTML table
    try:
        tables = pd.read_html(io.StringIO(html_content),
                              attrs={"class": "nsit3"})
    except ValueError:
        tables = []
    if not tables:
        logging.error("Could not locate table with class 'nsit3' in page HTML.")
        sys.exit(1)
    df = tables[0]

    # Clean strings and non-breaking spaces
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = (df[col].astype(str).str.replace("\xa0", " ").str.strip())

    # 4. Write CSV to temporary file first, validate, then atomically replace
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=f".{target_filename}.",
                                        suffix=".tmp",
                                        dir=local_dir)
    try:
        with os.fdopen(tmp_fd, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Header rows
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

        # 5. Format validation against reference template before moving into place
        validate_file_format(tmp_path, detected_year)
        os.replace(tmp_path, local_output_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    logging.info("Saved validated local file: %s (%d bytes)", local_output_path,
                 os.path.getsize(local_output_path))

    # 6. Upload to shared GCS destination
    if dry_run:
        logging.info("[Dry Run] Validation succeeded! Skipping upload to %s.",
                     gcs_target_path)
        return

    logging.info("Uploading '%s' to %s...", target_filename, gcs_target_path)
    upload_success = False
    try:
        cmd = ["gcloud", "storage", "cp", local_output_path, gcs_target_path]
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
        upload_success = True
    except Exception as e:
        logging.warning("gcloud storage failed (%s), trying gsutil...", e)
        try:
            cmd = ["gsutil", "cp", local_output_path, gcs_target_path]
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
            )
            upload_success = True
        except Exception as e2:
            logging.error("Upload failed: %s", e2)

    if not upload_success:
        if os.path.exists(local_output_path):
            os.remove(local_output_path)
        logging.error("Upload to %s failed.", gcs_target_path)
        sys.exit(1)

    logging.info("Successfully uploaded to %s!", gcs_target_path)


def main():
    if hasattr(logging, "set_verbosity"):
        logging.set_verbosity(logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=(
        "Monthly checker and auto-downloader for Bulgaria NSI demographics."))
    parser.add_argument(
        "--gcs-dir",
        default=DEFAULT_GCS_DIR,
        help="Destination GCS folder.",
    )
    parser.add_argument(
        "--local-dir",
        default=DEFAULT_LOCAL_DIR,
        help="Local storage directory.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force download, validate, and upload even if already present.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Download, format, and validate locally without uploading.",
    )
    parser.add_argument(
        "--allow-staged-fallback",
        action="store_true",
        help=("Allow falling back to existing staged GCS files if live NSI "
              "portal is blocked by Cloudflare."),
    )
    args = parser.parse_args()

    check_and_download_nsi(
        local_dir=args.local_dir,
        gcs_dir=args.gcs_dir,
        force=args.force,
        dry_run=args.dry_run,
        allow_staged_fallback=args.allow_staged_fallback,
    )


if __name__ == "__main__":
    main()
