import csv
import datetime
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------
# Path resolution and Environment Setup
# ---------------------------------------------------------
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

_OUTPUT_DIRECTORY = "input_files"
OUTPUT_DIR = os.path.join(_SCRIPT_PATH, _OUTPUT_DIRECTORY)
_COUNTY_SUBFOLDER = "county_input_file"
COUNTY_OUTPUT_DIR = os.path.join(OUTPUT_DIR, _COUNTY_SUBFOLDER)

_BASE_URL = "https://gaftp.epa.gov/air/nei"
_START_YEAR = 2008
_CYCLE_YEARS = 3
_CURRENT_YEAR = datetime.datetime.now().year


def check_and_create_dir(dir_path: str):
    """Ensures input folder exists; creates it if missing."""
    if not os.path.exists(dir_path):
        logging.info(f"Directory not found. Creating: {dir_path}")
        os.makedirs(dir_path, exist_ok=True)
    else:
        logging.info(f"Directory exists: {dir_path}")


def get_target_years():
    """Generates 3-year NEI cycles from _START_YEAR up to current year."""
    return list(range(_START_YEAR, _CURRENT_YEAR + 1, _CYCLE_YEARS))


def resolve_file_url(year: int):
    """Scrapes the EPA directory listing for NEI tier summary files."""
    dir_url = f"{_BASE_URL}/{year}/tier_summaries/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        resp = requests.get(dir_url, headers=headers, timeout=20)
        if resp.status_code != 200:
            logging.warning(f"Could not open directory {dir_url} (HTTP status: {resp.status_code})")
            return None, None
    except requests.RequestException as e:
        logging.warning(f"Network error accessing {dir_url}: {e}")
        return None, None

    soup = BeautifulSoup(resp.text, "html.parser")
    all_files = []
    candidates = []

    # Matches tier1 summaries (including prefixed names like 2011neiv2_tier1_summary.zip)
    pattern = re.compile(r".*tier1_summary.*?\.(zip|accdb|mdb)$", re.IGNORECASE)

    for link in soup.find_all("a", href=True):
        raw_href = link["href"].split("?")[0].strip("/")
        fname = os.path.basename(raw_href)
        if fname:
            all_files.append(fname)
        if pattern.match(fname):
            candidates.append(fname)

    if not candidates:
        logging.warning(f"No matching tier summary found in {dir_url}")
        # Log available archive files to debug naming conventions
        sample_files = [
            f for f in all_files 
            if any(ext in f.lower() for ext in [".zip", ".accdb", ".mdb", ".csv"])
        ]
        if sample_files:
            logging.info(f"Available database/archive files in {year}: {sample_files[:10]}")
        return None, None

    # Ranking logic:
    # 1. Prioritize 'final' releases
    # 2. Prioritize higher version numbers (v3 > v2 > v1)
    def rank_candidate(name: str):
        val = 0
        name_lower = name.lower()
        if "final" in name_lower:
            val += 10
        version_match = re.search(r"v(\d+)", name_lower)
        if version_match:
            val += int(version_match.group(1))
        return val

    candidates.sort(key=rank_candidate, reverse=True)
    selected_file = candidates[0]
    logging.info(f"Selected file for {year}: {selected_file}")
    return f"{dir_url}{selected_file}", selected_file


def download_file(url: str, dest_path: str):
    """Streams the download to destination path."""
    logging.info(f"Downloading: {url} -> {os.path.basename(dest_path)}")
    headers = {"User-Agent": "Mozilla/5.0"}
    temp_path = dest_path + ".tmp"
    try:
        with requests.get(url, headers=headers, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        os.replace(temp_path, dest_path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def extract_databases_from_zip(zip_path: str):
    """Extracts .mdb or .accdb files from zip into OUTPUT_DIR."""
    extracted_db_paths = []
    with zipfile.ZipFile(zip_path, "r") as archive:
        for file_info in archive.infolist():
            if file_info.filename.lower().endswith((".accdb", ".mdb")):
                target_filename = os.path.basename(file_info.filename)
                target_path = os.path.join(OUTPUT_DIR, target_filename)

                if not os.path.exists(target_path):
                    logging.info(f"Extracting {target_filename}...")
                    with archive.open(file_info) as source, open(target_path, "wb") as dest:
                        dest.write(source.read())
                extracted_db_paths.append(target_path)

    return extracted_db_paths


def export_db_to_csv(db_path: str, year: int):
    """Exports all tables inside .mdb or .accdb to CSV with 'year' column prepended."""
    stem = os.path.splitext(os.path.basename(db_path))[0]
    parent_dir = os.path.dirname(db_path)

    try:
        res = subprocess.run(
            ["mdb-tables", "-1", db_path],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Error reading tables from {db_path}: {e.stderr.strip()}")
        raise

    tables = [t.strip() for t in res.stdout.splitlines() if t.strip()]

    for table in tables:
        out_file = os.path.join(parent_dir, f"{stem}_{table}.csv")
        if os.path.exists(out_file):
            logging.info(f"CSV already exists: {out_file}. Skipping.")
            continue

        logging.info(f"Exporting '{table}' -> {out_file} (year={year})")

        proc = subprocess.Popen(
            ["mdb-export", db_path, table],
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        with open(out_file, "w", newline="", encoding="utf-8") as f_out:
            reader = csv.reader(proc.stdout)
            writer = csv.writer(f_out)

            header = next(reader, None)
            if header is not None:
                writer.writerow(["year"] + header)
                stfips_idx = header.index("stfips") if "stfips" in header else None
                state_idx = header.index("state") if "state" in header else None
                for row in reader:
                    if row:
                        if (
                            year == 2014
                            and stfips_idx is not None
                            and state_idx is not None
                            and len(row) > max(stfips_idx, state_idx)
                            and row[state_idx].strip() == "Tribal"
                        ):
                            row[stfips_idx] = "88"
                        writer.writerow([year] + row)

        if proc.wait() != 0:
            raise RuntimeError(f"mdb-export failed with exit code {proc.returncode}")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    check_and_create_dir(OUTPUT_DIR)

    target_years = get_target_years()
    logging.info(f"Target NEI cycle years to check: {target_years}")

    for year in target_years:
        url, filename = resolve_file_url(year)
        if not url:
            logging.warning(f"No matching summary found for year {year}. Skipping.")
            continue

        local_file = os.path.join(OUTPUT_DIR, filename)

        # 1. Download
        if not os.path.exists(local_file):
            try:
                download_file(url, local_file)
            except Exception as e:
                logging.error(f"Failed to download {url}: {e}")
                if os.path.exists(local_file):
                    os.remove(local_file)
                raise

        # 2. Extract or Identify DB files
        db_files_to_process = []
        if local_file.lower().endswith(".zip"):
            db_files_to_process = extract_databases_from_zip(local_file)
        elif local_file.lower().endswith((".accdb", ".mdb")):
            db_files_to_process = [local_file]

        # 3. Export to CSV
        for db_file in db_files_to_process:
            export_db_to_csv(db_file, year)

    # 4. Move all county CSV files to county_input_file subfolder
    check_and_create_dir(COUNTY_OUTPUT_DIR)
    for fname in os.listdir(OUTPUT_DIR):
        src_path = os.path.join(OUTPUT_DIR, fname)
        if (
            os.path.isfile(src_path)
            and fname.lower().endswith(".csv")
            and "county" in fname.lower()
        ):
            dest_path = os.path.join(COUNTY_OUTPUT_DIR, fname)
            logging.info(f"Moving county CSV: {fname} -> {dest_path}")
            shutil.move(src_path, dest_path)


if __name__ == "__main__":
    main()