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
     Urban = Urban_Male + Urban_Female, Rural = Rural_Male + Rural_Female
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
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOCAL_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_GCS_DIR = "gs://unresolved_mcf/country/Bulgaria/input_files"

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

EXPECTED_HISTORICAL_AGES = [
    "0 - 4",
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
    "100+",
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
    try:
        cmd = ["gcloud", "storage", "ls", gcs_dir.rstrip("/") + "/"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        files = [
            os.path.basename(line.strip()) for line in res.stdout.splitlines()
            if line.strip()
        ]
        return files
    except Exception as e:
        print(f"  Notice: gcloud storage list failed ({e}), trying gsutil...")
        try:
            cmd = ["gsutil", "ls", gcs_dir.rstrip("/") + "/"]
            res = subprocess.run(cmd,
                                 capture_output=True,
                                 text=True,
                                 check=True)
            files = [
                os.path.basename(line.strip())
                for line in res.stdout.splitlines() if line.strip()
            ]
            return files
        except Exception:
            return []


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
    print(
        f"\n[Validation] Verifying format against reference schema ({file_path})..."
    )

    with open(file_path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    # 1. Row count: 3 Header rows + (29 districts * 23 rows) = 670 rows
    expected_total_rows = 3 + len(EXPECTED_DISTRICTS) * (1 +
                                                         len(EXPECTED_AGES))
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
            row_idx += 1

    print("  ✓ Format validation PASSED: Exactly matches reference template "
          "structure and internal arithmetic!")
    return True


def validate_historical_file_format(file_path: str) -> bool:
    """Validates historical multi-year CSV structure and Total == Male + Female."""
    with open(file_path, "r", encoding="utf-8") as f:
        rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]

    # Locate the 'Age (years)' subheader row
    subheader_idx = None
    for idx, r in enumerate(rows[:10]):
        if r and r[0].strip() == "Age (years)":
            subheader_idx = idx
            break
    if subheader_idx is None:
        raise ValueError(f"{file_path}: Missing 'Age (years)' header row.")

    num_cols = len(rows[subheader_idx])
    if (num_cols - 1) % 3 != 0 or num_cols < 4:
        raise ValueError(
            f"{file_path}: Expected 1 + 3*N columns, got {num_cols}.")
    num_years = (num_cols - 1) // 3

    data_rows = rows[subheader_idx + 1:]
    expected_data_rows = len(EXPECTED_DISTRICTS) * (
        1 + len(EXPECTED_HISTORICAL_AGES))
    if len(data_rows) < expected_data_rows:
        raise ValueError(
            f"{file_path}: Expected at least {expected_data_rows} data rows, "
            f"got {len(data_rows)}.")

    seen_districts = []
    for b_idx in range(len(EXPECTED_DISTRICTS)):
        base = b_idx * (1 + len(EXPECTED_HISTORICAL_AGES))
        d_row = data_rows[base]
        d_name = d_row[0].replace("\xa0", " ").strip()
        if d_name not in EXPECTED_DISTRICTS:
            raise ValueError(
                f"{file_path}: Block {b_idx} unexpected district '{d_name}'.")
        seen_districts.append(d_name)
        district = d_name
        a_rows = data_rows[base + 1:base + 1 + len(EXPECTED_HISTORICAL_AGES)]
        for a_idx, expected_age in enumerate(EXPECTED_HISTORICAL_AGES):
            a_name = a_rows[a_idx][0].replace("\xa0", " ").strip()
            if a_name != expected_age:
                raise ValueError(
                    f"{file_path}: District '{district}' expected age "
                    f"'{expected_age}', got '{a_name}'.")

        # Check Total == Male + Female on district header and all age rows
        for r in [d_row] + a_rows:
            label = f"{district} - {r[0].strip()}"
            for y_i in range(num_years):
                c = 1 + y_i * 3
                tot = to_num(r[c])
                m = to_num(r[c + 1])
                fem = to_num(r[c + 2])
                if tot != m + fem:
                    raise ValueError(
                        f"{file_path} ({label}, year_idx={y_i}): "
                        f"Total ({tot}) != Male ({m}) + Female ({fem}).")

        # Check vertical sum: district header == sum of 21 age cohorts
        for c in range(1, num_cols):
            d_val = to_num(d_row[c])
            a_sum = sum(to_num(r[c]) for r in a_rows)
            if d_val != a_sum:
                raise ValueError(
                    f"{file_path} ({district}, col={c}): "
                    f"District header ({d_val}) != sum of age rows ({a_sum}).")

    if set(seen_districts) != set(EXPECTED_DISTRICTS):
        raise ValueError(
            f"{file_path}: District set mismatch: "
            f"missing {set(EXPECTED_DISTRICTS) - set(seen_districts)}.")
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
    print("=" * 70)
    print("Bulgaria NSI Demographics: Monthly Monitor & Auto-Downloader")
    print(f"Source Portal:   {NSI_URL}")
    print(f"Destination GCS: {gcs_dir}")
    print("=" * 70)

    html_content = None
    session = _create_retry_session()
    try:
        resp = session.get(NSI_URL, headers=HEADERS, timeout=25)
        if resp.status_code == 200:
            html_content = resp.text
            print("✓ Successfully connected to live NSI portal.")
        else:
            print(f"Warning: NSI portal returned HTTP {resp.status_code} "
                  f"for {NSI_URL}.")
    except Exception as e:
        print(f"Notice: Direct request to nsi.bg failed: {e}")

    # Fallback to cached copy if environment restricts direct outbound HTTP to nsi.bg
    if not html_content:
        cache_path = os.path.join(SCRIPT_DIR, "cached_nsi_page.html")
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()
            print("Using cached HTML snapshot for NSI table.")

    if not html_content:
        print("Warning: Direct connection to NSI portal blocked "
              "(e.g. Cloudflare challenge/firewall).")
        if allow_staged_fallback:
            print("Checking if input files are already present in GCS "
                  f"({gcs_dir}) (--allow-staged-fallback enabled)...")
            existing_gcs_files = list_gcs_files(gcs_dir)
            if existing_gcs_files:
                print(f"✓ Existing files in GCS folder: {existing_gcs_files}. "
                      "Proceeding with staged data.")
                return
        print("❌ Error: Unable to fetch live NSI portal content "
              "(pass --allow-staged-fallback to use existing GCS files).")
        sys.exit(1)

    # 1. Detect Year from caption (<div id="ttitle">...31.12.YYYY...</div>)
    ttitle_match = re.search(
        r'id=["\']ttitle["\'][^>]*>(.*?)</div>',
        html_content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    caption_text = ttitle_match.group(1) if ttitle_match else html_content
    year_match = re.search(r"31\.12\.(\d{4})", caption_text)
    if not year_match:
        print("❌ Error: Could not parse reference year from caption: "
              f"'{caption_text[:200]}'")
        sys.exit(1)

    detected_year = int(year_match.group(1))
    print(f"✓ Detected published year on NSI portal: {detected_year}")

    target_filename = (
        f"BulgariaNSI_Demographics_Year_input_{detected_year}.csv")
    local_output_path = os.path.join(local_dir, target_filename)
    gcs_target_path = f"{gcs_dir.rstrip('/')}/{target_filename}"

    # 2. Check if file already exists in GCS
    existing_gcs_files = list_gcs_files(gcs_dir)
    print(f"Current files in GCS folder: {existing_gcs_files}")

    if target_filename in existing_gcs_files and not force:
        print(f"\n✓ Up-to-date: '{target_filename}' is already present in "
              f"{gcs_dir}.")
        print("No new annual release detected. Exiting.")
        return

    print(f"\n⚡ Processing release for {detected_year}! Formatting dataset...")

    # 3. Parse HTML table
    try:
        tables = pd.read_html(io.StringIO(html_content),
                              attrs={"class": "nsit3"})
    except ValueError:
        tables = []
    if not tables:
        print(
            "❌ Error: Could not locate table with class 'nsit3' in page HTML.")
        sys.exit(1)
    df = tables[0]

    # Clean strings and non-breaking spaces
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = (df[col].astype(str).str.replace("\xa0",
                                                       " ").str.strip())

    # 4. Write CSV in exact structure matching Google Sheet
    with open(local_output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Header rows
        writer.writerow([
            "\nPOPULATION BY DISTRICTS, AGE, PLACE OF RESIDENCE AND SEX"
            f" AS OF 31.12.{detected_year}\n(Number)\n"
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
            clean_vals = []
            for i, v in enumerate(row.values):
                if i > 0:
                    val_str = (str(v).replace(" ", "").replace("\xa0",
                                                               "").strip())
                    if val_str.endswith(".0"):
                        val_str = val_str[:-2]
                    clean_vals.append(val_str)
                else:
                    # Clean age label or district label
                    clean_vals.append(str(v).replace("\xa0", " ").strip())
            writer.writerow(clean_vals)

    print(f"✓ Saved local file: {local_output_path} "
          f"({os.path.getsize(local_output_path):,} bytes)")

    # 5. Format validation against reference template
    validate_file_format(local_output_path, detected_year)

    # 6. Upload to shared GCS destination
    if dry_run:
        print("\n[Dry Run] Validation succeeded! Skipping upload to "
              f"{gcs_target_path}.")
        return

    print(f"\nUploading '{target_filename}' to {gcs_target_path}...")
    upload_success = False
    try:
        cmd = ["gcloud", "storage", "cp", local_output_path, gcs_target_path]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        upload_success = True
    except Exception as e:
        print(f"  Notice: gcloud storage failed ({e}), trying gsutil...")
        try:
            cmd = ["gsutil", "cp", local_output_path, gcs_target_path]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            upload_success = True
        except Exception as e2:
            print(f"❌ Upload failed: {e2}")

    if not upload_success:
        print(f"❌ Upload to {gcs_target_path} failed.")
        sys.exit(1)

    print(f"✓ Successfully uploaded to {gcs_target_path}!")
    print("=" * 70)


def main():
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
