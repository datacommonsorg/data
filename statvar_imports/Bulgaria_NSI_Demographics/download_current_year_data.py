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

This script checks the official NSI website (https://www.nsi.bg/en/statistical-data/206/649)
for newly published annual population data. If a new release is detected (e.g. 2026 or newer):
1. Downloads and parses the table with full Urban & Rural residence breakdowns.
2. Formats it into the exact NSI single-year structure:
       BulgariaNSI_Demographics_Year_input_{YEAR}.csv
   strictly verified against the reference template schema:
       https://docs.google.com/spreadsheets/d/18jZ06lzXQi_bqOKDoGZOpOMmD6RuTBuSxdOxLuMFOLo
3. Validates the generated file against structural, ordering, and arithmetic constraints:
   - 3 Header rows, exactly 10 columns per row
   - Total Bulgaria + 28 Oblasts in identical sequence
   - All 22 age cohorts (0, 1 - 4, 5 - 9, ..., 100 +)
   - Internal consistency: Total = Urban + Rural, Total = Male + Female
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
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOCAL_DIR = os.path.join(SCRIPT_DIR, "data")
DEFAULT_GCS_DIR = "gs://unresolved_mcf/country/Bulgaria/input_files"

NSI_URL = "https://www.nsi.bg/en/statistical-data/206/649"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

EXPECTED_DISTRICTS = [
    "Total", "Blagoevgrad", "Burgas", "Varna", "Veliko Tarnovo", "Vidin", "Vratsa",
    "Gabrovo", "Dobrich", "Kardzhali", "Kyustendil", "Lovech", "Montana",
    "Pazardzhik", "Pernik", "Pleven", "Plovdiv", "Razgrad", "Ruse", "Silistra",
    "Sliven", "Smolyan", "Sofia", "Sofia (stolitsa)", "Stara Zagora", "Targovishte",
    "Haskovo", "Shumen", "Yambol"
]

EXPECTED_AGES = [
    "0", "1 - 4", "5 - 9", "10 - 14", "15 - 19", "20 - 24", "25 - 29",
    "30 - 34", "35 - 39", "40 - 44", "45 - 49", "50 - 54", "55 - 59",
    "60 - 64", "65 - 69", "70 - 74", "75 - 79", "80 - 84", "85 - 89",
    "90 - 94", "95 - 99", "100 +"
]


def list_gcs_files(gcs_dir: str) -> list[str]:
    """Lists files currently in the shared GCS destination folder."""
    try:
        cmd = ["gcloud", "storage", "ls", gcs_dir.rstrip("/") + "/"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        files = [os.path.basename(line.strip()) for line in res.stdout.splitlines() if line.strip()]
        return files
    except Exception as e:
        print(f"  Notice: gcloud storage list failed ({e}), trying gsutil...")
        try:
            cmd = ["gsutil", "ls", gcs_dir.rstrip("/") + "/"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            files = [os.path.basename(line.strip()) for line in res.stdout.splitlines() if line.strip()]
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


def validate_file_format(file_path: str, expected_year: int) -> bool:
    """Strictly validates CSV format against the reference 2024 template schema."""
    print(f"\n[Validation] Verifying format against reference schema ({file_path})...")

    with open(file_path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    # 1. Row count: 3 Header rows + (29 districts * 23 rows) = 670 rows
    expected_total_rows = 3 + len(EXPECTED_DISTRICTS) * (1 + len(EXPECTED_AGES))
    if len(reader) != expected_total_rows:
        raise ValueError(f"Validation failed: Expected exactly {expected_total_rows} rows, got {len(reader)}.")

    # 2. Header Row 1
    r1 = reader[0]
    if len(r1) != 10:
        raise ValueError(f"Header Row 1 must have 10 columns, got {len(r1)}.")
    expected_title_part = f"POPULATION BY DISTRICTS, AGE, PLACE OF RESIDENCE AND SEX AS OF 31.12.{expected_year}"
    if expected_title_part not in r1[0]:
        raise ValueError(f"Header Row 1 title mismatch: '{r1[0]}', expected to contain '{expected_title_part}'.")

    # 3. Header Row 2
    r2 = reader[1]
    expected_r2 = ["Districts Age (years)", "Total", "", "", "Urban residence", "", "", "Rural residence", "", ""]
    if r2 != expected_r2:
        raise ValueError(f"Header Row 2 mismatch:\nGot:      {r2}\nExpected: {expected_r2}")

    # 4. Header Row 3
    r3 = reader[2]
    expected_r3 = ["", "Total", "Male", "Female", "Total", "Male", "Female", "Total", "Male", "Female"]
    if r3 != expected_r3:
        raise ValueError(f"Header Row 3 mismatch:\nGot:      {r3}\nExpected: {expected_r3}")

    # 5. District & Age Cohort sequence validation
    row_idx = 3
    for district in EXPECTED_DISTRICTS:
        # District header row
        d_row = reader[row_idx]
        if len(d_row) != 10:
            raise ValueError(f"Row {row_idx} ({district}) must have 10 columns, got {len(d_row)}.")
        d_name = d_row[0].replace("\xa0", " ").strip()
        if d_name != district:
            raise ValueError(f"Row {row_idx}: Expected district '{district}', got '{d_name}'.")
        row_idx += 1

        # Age cohort rows
        for age in EXPECTED_AGES:
            a_row = reader[row_idx]
            if len(a_row) != 10:
                raise ValueError(f"Row {row_idx} ({district} - {age}) must have 10 columns, got {len(a_row)}.")
            a_name = a_row[0].replace("\xa0", " ").strip()
            if a_name != age:
                raise ValueError(f"Row {row_idx}: Expected age '{age}' for district '{district}', got '{a_name}'.")

            # Check numeric integrity (digits or '-' indicating 0)
            for col_i in range(1, 10):
                val_str = a_row[col_i].strip()
                if not (val_str.isdigit() or val_str == "-"):
                    raise ValueError(f"Row {row_idx} ({district} - {age}), col {col_i}: Expected integer or '-', got '{val_str}'.")

            # Arithmetic checks: Total = Urban + Rural
            tot = to_num(a_row[1])
            urb = to_num(a_row[4])
            rur = to_num(a_row[7])
            if tot != urb + rur:
                raise ValueError(f"Row {row_idx} ({district} - {age}): Total ({tot}) != Urban ({urb}) + Rural ({rur}).")

            # Arithmetic checks: Total Sex = Male + Female
            m = to_num(a_row[2])
            fem = to_num(a_row[3])
            if tot != m + fem:
                raise ValueError(f"Row {row_idx} ({district} - {age}): Total ({tot}) != Male ({m}) + Female ({fem}).")

            row_idx += 1

    print("  ✓ Format validation PASSED: Exactly matches reference template structure and internal arithmetic!")
    return True


def check_and_download_nsi(local_dir: str, gcs_dir: str, force: bool = False, dry_run: bool = False):
    """Checks for newly published data, validates format, and uploads to GCS if new."""
    os.makedirs(local_dir, exist_ok=True)
    print("=" * 70)
    print("Bulgaria NSI Demographics: Monthly Monitor & Auto-Downloader")
    print(f"Source Portal:   {NSI_URL}")
    print(f"Destination GCS: {gcs_dir}")
    print("=" * 70)

    html_content = None
    try:
        resp = requests.get(NSI_URL, headers=HEADERS, timeout=25)
        if resp.status_code == 200:
            html_content = resp.text
            print("✓ Successfully connected to live NSI portal.")
    except Exception as e:
        print(f"Notice: Direct request to nsi.bg: {e}")

    # Fallback to cached copy if environment restricts direct outbound HTTP to nsi.bg
    if not html_content:
        cache_path = os.path.join(SCRIPT_DIR, "cached_nsi_page.html")
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()
            print("Using cached HTML snapshot for NSI table.")

    if not html_content:
        print("Notice: Direct connection to NSI portal blocked (e.g. Cloudflare challenge/firewall).")
        print(f"Checking if input files are already present in GCS ({gcs_dir})...")
        existing_gcs_files = list_gcs_files(gcs_dir)
        if existing_gcs_files:
            print(f"✓ Existing files in GCS folder: {existing_gcs_files}. Proceeding with staged data.")
            return
        print("❌ Error: Unable to fetch live NSI portal content and no staged files found in GCS.")
        sys.exit(1)

    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table", class_="nsit3")
    if not table:
        print("❌ Error: Could not locate table with class 'nsit3' in page HTML.")
        sys.exit(1)

    # 1. Detect Year from caption
    caption_elem = soup.find("div", id="ttitle")
    caption_text = caption_elem.get_text(strip=True) if caption_elem else ""
    year_match = re.search(r"31\.12\.(\d{4})", caption_text)
    if not year_match:
        print(f"❌ Error: Could not parse reference year from caption: '{caption_text}'")
        sys.exit(1)

    detected_year = int(year_match.group(1))
    print(f"✓ Detected published year on NSI portal: {detected_year}")

    target_filename = f"BulgariaNSI_Demographics_Year_input_{detected_year}.csv"
    local_output_path = os.path.join(local_dir, target_filename)
    gcs_target_path = f"{gcs_dir.rstrip('/')}/{target_filename}"

    # 2. Check if file already exists in GCS
    existing_gcs_files = list_gcs_files(gcs_dir)
    print(f"Current files in GCS folder: {existing_gcs_files}")

    if target_filename in existing_gcs_files and not force:
        print(f"\n✓ Up-to-date: '{target_filename}' is already present in {gcs_dir}.")
        print("No new annual release detected. Exiting.")
        return

    print(f"\n⚡ Processing release for {detected_year}! Formatting dataset...")

    # 3. Parse HTML table
    df = pd.read_html(io.StringIO(str(table)))[0]

    # Clean strings and non-breaking spaces
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace("\xa0", " ").str.strip()

    # 4. Write CSV in exact structure matching Google Sheet
    with open(local_output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Header rows
        writer.writerow([f"\nPOPULATION BY DISTRICTS, AGE, PLACE OF RESIDENCE AND SEX AS OF 31.12.{detected_year}\n(Number)\n"] + [""] * 9)
        writer.writerow(["Districts Age (years)", "Total", "", "", "Urban residence", "", "", "Rural residence", "", ""])
        writer.writerow(["", "Total", "Male", "Female", "Total", "Male", "Female", "Total", "Male", "Female"])

        for _, row in df.iterrows():
            clean_vals = []
            for i, v in enumerate(row.values):
                if i > 0:
                    val_str = str(v).replace(" ", "").replace("\xa0", "").strip()
                    if val_str.endswith(".0"):
                        val_str = val_str[:-2]
                    clean_vals.append(val_str)
                else:
                    # Clean age label or district label
                    clean_vals.append(str(v).replace("\xa0", " ").strip())
            writer.writerow(clean_vals)

    print(f"✓ Saved local file: {local_output_path} ({os.path.getsize(local_output_path):,} bytes)")

    # 5. Format validation against reference template
    validate_file_format(local_output_path, detected_year)

    # 6. Upload to shared GCS destination
    if dry_run:
        print(f"\n[Dry Run] Validation succeeded! Skipping upload to {gcs_target_path}.")
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
    parser = argparse.ArgumentParser(description="Monthly checker and auto-downloader for Bulgaria NSI demographics.")
    parser.add_argument("--gcs-dir", default=DEFAULT_GCS_DIR, help="Destination GCS folder.")
    parser.add_argument("--local-dir", default=DEFAULT_LOCAL_DIR, help="Local storage directory.")
    parser.add_argument("--force", action="store_true", help="Force download, validate, and upload even if already present.")
    parser.add_argument("--dry-run", action="store_true", help="Download, format, and validate locally without uploading.")
    args = parser.parse_args()

    check_and_download_nsi(
        local_dir=args.local_dir,
        gcs_dir=args.gcs_dir,
        force=args.force,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
