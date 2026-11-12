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
"""CRDC School Retention Data Downloader & Preprocessor.

1. Downloads CRDC data archives across published survey years.
2. Cleans and zero-pads LEAID (7 chars) and SCHID (5 chars) or COMBOKEY
   (12 chars) while preserving valid alphanumeric NCES IDs and rejecting
   null/zero IDs.
3. Normalizes JJ / SCH_JUST to column 3 ('JJ') and retains only columns mapped
   in retention_pvmap.csv.
4. Masks negative CRDC reserve codes (-9, -5, -2) to NaN, formats integers as
   nullable Int64 (avoiding float '.0' suffixes), and writes all transformed
   files directly as CSV in input_files/.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import glob
import os
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

from absl import app
from absl import logging
import numpy as np
import pandas as pd
import requests
from retry import retry

# ==========================================
# Configuration
# ==========================================
MAX_WORKERS = 5
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

RAW_SAVE_FOLDER = os.path.join(SCRIPT_DIR, "raw_input_files")
TRANSFORMED_SAVE_FOLDER = os.path.join(SCRIPT_DIR, "input_files")
PVMAP_PATH = os.path.join(SCRIPT_DIR, "retention_pvmap.csv")

RETENTION_KEYWORDS = [
    r".*09-2 Retention.*",
    r"Retention of Students.*grade (0[1-9]|1[0-2])\.xlsx$",
    r"Retention of Students.*kindergarten\.xlsx$",
    r"Retention\.csv$",
    r"Retention\.xlsx$",
]

FALLBACK_KEYWORDS = [
    r"School Data\.csv$",
]

KEYWORDS = RETENTION_KEYWORDS + FALLBACK_KEYWORDS

EXCLUDE_COLS = [
    "JJ",
    "SCH_JUST",
    "LEA_STATE",
    "LEA_STATE_NAME",
    "LEA_NAME",
    "SCH_NAME",
    "NCESID",
    "LEAID",
    "SCHID",
    "COMBOKEY",
    "OBSERVATIONDATE",
]

REPLACEMENT_MAP = {
    "Yes": "1",
    "No": "0",
    "yes": "1",
    "no": "0",
    "YES": "1",
    "NO": "0",
}

_INVALID_ID_STRINGS = {"", "nan", "none", "null", "na", "<na>"}
_YES_VALUES = {"yes", "y", "1", "1.0", "true"}
_NO_VALUES = {"no", "n", "0", "0.0", "false"}
_KNOWN_SURVEY_YEARS = {2009, 2011, 2013, 2015, 2017, 2020, 2021, 2023}

# ==========================================
# Helper Functions
# ==========================================


def load_pv_mapped_columns(pvmap_path: str = PVMAP_PATH) -> set:
    """Loads the set of uppercase column names mapped in retention_pvmap.csv."""
    if not os.path.exists(pvmap_path):
        raise FileNotFoundError(f"PV map file not found: {pvmap_path}")

    mapped_cols = set()
    with open(pvmap_path, mode="r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            first_token = stripped.split(",", 1)[0].strip().strip('"')
            if not first_token or first_token.startswith("#"):
                continue
            col_name = first_token.split(":", 1)[0].strip().upper()
            if col_name:
                mapped_cols.add(col_name)
    return mapped_cols


def _is_excluded_archive_member(filename: str) -> bool:
    """Returns True if archive member is a dir, temp, layout, or LEA file."""
    if not filename or filename.endswith("/"):
        return True
    if "__MACOSX" in filename:
        return True
    basename = os.path.basename(filename)
    if not basename or basename.startswith("~$") or basename.startswith("."):
        return True
    if "layout" in basename.lower():
        return True
    if re.search(r"(^|[_\W])lea([_\W]|$)", basename, re.IGNORECASE):
        return True
    return False


def matches_keywords(filename: str) -> bool:
    """Returns True if filename matches CRDC school retention file patterns."""
    if _is_excluded_archive_member(filename):
        return False
    return any(
        re.search(pattern, filename, re.IGNORECASE) for pattern in KEYWORDS)


def select_matched_files(namelist: list) -> list:
    """Selects retention files from a ZIP archive namelist.

    Prefers dedicated retention files (Retention.csv, Retention.xlsx, etc.) and
    only falls back to School Data.csv when no dedicated retention file exists
    in the archive (e.g., 2015-16).
    """
    valid_members = [f for f in namelist if not _is_excluded_archive_member(f)]
    primary_matches = [
        f for f in valid_members if any(
            re.search(pattern, f, re.IGNORECASE)
            for pattern in RETENTION_KEYWORDS)
    ]
    if primary_matches:
        return primary_matches
    return [
        f for f in valid_members if any(
            re.search(pattern, f, re.IGNORECASE)
            for pattern in FALLBACK_KEYWORDS)
    ]


def get_survey_years(current_year: int = None) -> list:
    """Returns CRDC survey start years (odd 2009-2017, then 2020 onward)."""
    if current_year is None:
        current_year = datetime.now().year
    odd_years = list(range(2009, 2018, 2))
    recent_years = list(range(2020, current_year, 1))
    return odd_years + recent_years


def get_urls_for_year(start_year: int, end_year: int) -> list:
    """Returns candidate CRDC archive URLs for a given survey year pair."""
    short_end = str(end_year)[-2:]
    base = "https://civilrightsdata.ed.gov/assets/ocr/docs"
    return [
        f"{base}/{start_year}-{short_end}-crdc-data.zip",
        f"{base}/CRDC{start_year}_{short_end}_CSV.zip",
        f"{base}/CRDC{start_year}_{short_end}_data.zip",
        f"{base}/{start_year}-{short_end}-crdc-csv.zip",
    ]


def _is_valid_ascii_alnum_id(val: str, max_width: int = None) -> bool:
    """Returns True if val is a non-zero ASCII alphanumeric ID."""
    if not val or val.lower() in _INVALID_ID_STRINGS:
        return False
    if not (val.isascii() and val.isalnum()):
        return False
    if max_width is not None and len(val) > max_width:
        return False
    return int(val, 36) > 0


def _pad_id_series(series: pd.Series, width: int) -> pd.Series:
    """Strips trailing '.0+' float suffixes and zero-pads ASCII alnum IDs."""
    cleaned = (series.fillna("").astype(str).str.strip().str.replace(
        r"\.0+$", "", regex=True))
    return cleaned.map(lambda x: x.upper().zfill(width)
                       if _is_valid_ascii_alnum_id(x, max_width=width) else "")


def clean_id_column(series: pd.Series, width: int = None) -> pd.Series:
    """Cleans an ID series, optionally zero-padding to the specified width."""
    if width is not None:
        return _pad_id_series(series, width)
    cleaned = (series.fillna("").astype(str).str.strip().str.replace(
        r"\.0+$", "", regex=True))
    return cleaned.map(lambda x: x.upper()
                       if _is_valid_ascii_alnum_id(x) else "")


def _normalize_jj_value(val) -> str:
    """Normalizes JJ / SCH_JUST values to 'Yes', 'No', or ''."""
    if pd.isna(val):
        return ""
    s = str(val).strip().lower()
    if s in _YES_VALUES:
        return "Yes"
    if s in _NO_VALUES:
        return "No"
    return ""


def _normalize_metric_cell(val):
    """Normalizes indicator strings ('Yes'/'No') before numeric conversion."""
    if pd.isna(val):
        return val
    if isinstance(val, str):
        stripped = val.strip()
        return REPLACEMENT_MAP.get(stripped, stripped)
    return val


def transform_crdc_data(
    df: pd.DataFrame,
    year: int,
    filename: str = "",
    mapped_cols: set = None,
) -> pd.DataFrame:
    """Transforms a raw CRDC DataFrame into a clean retention table."""
    if mapped_cols is None:
        mapped_cols = load_pv_mapped_columns(PVMAP_PATH)

    df = df.copy()
    df.columns = [str(x).strip().upper() for x in df.columns]
    df = df.loc[:, ~df.columns.duplicated(keep="first")].copy()
    df["observationDate"] = year

    # 1. Construct validated 12-character NCESID
    if "LEAID" in df.columns and "SCHID" in df.columns:
        leaid = _pad_id_series(df["LEAID"], 7)
        schid = _pad_id_series(df["SCHID"], 5)
        valid_pair = (leaid != "") & (schid != "")
        df["NCESID"] = leaid.where(valid_pair, "") + schid.where(valid_pair, "")
    elif "COMBOKEY" in df.columns:
        df["NCESID"] = _pad_id_series(df["COMBOKEY"], 12)
    elif "NCESID" in df.columns:
        df["NCESID"] = _pad_id_series(df["NCESID"], 12)
    else:
        df["NCESID"] = ""

    # Filter out invalid or all-zero NCESIDs and deduplicate per school-year
    df = df[(df["NCESID"].str.len() == 12) &
            (df["NCESID"] != "000000000000")].copy()
    df = df.drop_duplicates(subset=["observationDate", "NCESID"],
                            keep="first").copy()

    # 2. Normalize SCH_JUST / JJ and place ['observationDate', 'NCESID', 'JJ']
    if "JJ" in df.columns and "SCH_JUST" in df.columns:
        jj_norm = df["JJ"].map(_normalize_jj_value)
        sch_just_norm = df["SCH_JUST"].map(_normalize_jj_value)
        df["JJ"] = jj_norm.where(jj_norm != "", sch_just_norm)
    elif "SCH_JUST" in df.columns:
        df = df.rename(columns={"SCH_JUST": "JJ"})
        df["JJ"] = df["JJ"].map(_normalize_jj_value)
    elif "JJ" in df.columns:
        df["JJ"] = df["JJ"].map(_normalize_jj_value)
    else:
        df["JJ"] = ""

    priority_cols = ["observationDate", "NCESID", "JJ"]
    exclude_upper = {c.upper() for c in EXCLUDE_COLS}
    target_cols = [
        col for col in df.columns
        if col.upper() not in exclude_upper and col.upper() in mapped_cols
    ]

    if not target_cols:
        return df[priority_cols].iloc[0:0].copy()
    if df.empty:
        return df[priority_cols + target_cols].iloc[0:0].copy()

    # 3. Convert indicator strings, coerce to numeric, and mask negative codes
    numeric_cols = {}
    for col in target_cols:
        mapped_series = df[col].map(_normalize_metric_cell)
        num_series = pd.to_numeric(mapped_series, errors="coerce")
        num_series = num_series.where((num_series >= 0) &
                                      np.isfinite(num_series))
        numeric_cols[col] = num_series

    numeric_df = pd.DataFrame(numeric_cols, index=df.index)

    # Drop rows where every retention metric column is NaN
    has_valid_metric = numeric_df.notna().any(axis=1)
    df = df.loc[has_valid_metric, priority_cols].copy()
    numeric_df = numeric_df.loc[has_valid_metric].copy()

    # Cast integral columns to nullable Int64 so CSV output has no '.0' suffix
    for col in target_cols:
        col_series = numeric_df[col]
        non_na = col_series.dropna()
        if non_na.empty or np.all(np.floor(non_na) == non_na):
            df[col] = col_series.round().astype("Int64")
        else:
            df[col] = col_series

    return df[priority_cols + target_cols]


# ==========================================
# Core Processing Logic
# ==========================================


def process_dataframe(
    raw_file_path: str,
    year: int,
    mapped_cols: set = None,
    output_folder: str = None,
) -> str:
    """Loads a raw CSV/XLSX CRDC file, transforms it, and writes a clean CSV."""
    if output_folder is None:
        output_folder = TRANSFORMED_SAVE_FOLDER
    os.makedirs(output_folder, exist_ok=True)

    filename = os.path.basename(raw_file_path)
    stem, ext = os.path.splitext(filename)
    ext = ext.lower()

    transformed_filename = f"transformed_{stem}.csv"
    transformed_path = os.path.join(output_folder, transformed_filename)

    if ext == ".csv":
        try:
            df = pd.read_csv(raw_file_path,
                             dtype=str,
                             low_memory=False,
                             encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(raw_file_path,
                             dtype=str,
                             low_memory=False,
                             encoding="latin1")
    elif ext == ".xlsx":
        df = pd.read_excel(raw_file_path, dtype=str, sheet_name=0)
    else:
        logging.warning(f"Skipping unsupported file extension: {raw_file_path}")
        return ""

    df_transformed = transform_crdc_data(df,
                                         year=year,
                                         filename=filename,
                                         mapped_cols=mapped_cols)
    if df_transformed.empty:
        logging.warning(
            f"No valid retention observations in {raw_file_path} ({year}).")
        return ""

    temp_path = f"{transformed_path}.tmp.{os.getpid()}"
    try:
        df_transformed.to_csv(temp_path, index=False)
        os.replace(temp_path, transformed_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    logging.info(
        f"Processed {raw_file_path} -> {transformed_path} "
        f"({len(df_transformed)} rows, {len(df_transformed.columns)} cols)")
    return transformed_path


def _is_zip_archive_available(url: str,
                              session: requests.Session = None) -> bool:
    """Checks via HTTP HEAD whether a CRDC zip archive exists."""
    logging.info(f"Checking availability of CRDC archive at {url}")
    requester = session or requests
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requester.head(url,
                              headers=headers,
                              allow_redirects=True,
                              timeout=30)
        if resp.status_code != 200:
            return False
        content_type = resp.headers.get("Content-Type", "").lower()
        return "html" not in content_type
    except requests.RequestException:
        return False


@retry(exceptions=(requests.RequestException,), tries=3, delay=2, backoff=2)
def try_download_url(url: str,
                     temp_file,
                     session: requests.Session = None) -> bool:
    """Downloads a ZIP archive from url into temp_file if available."""
    logging.info(f"Attempting to download CRDC archive from {url}")
    temp_file.seek(0)
    temp_file.truncate()
    requester = session or requests
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        with requester.get(url, headers=headers, stream=True,
                           timeout=180) as resp:
            if resp.status_code == 429 or resp.status_code >= 500:
                raise requests.HTTPError(
                    f"Transient HTTP {resp.status_code} for {url}",
                    response=resp,
                )
            if (resp.status_code == 200 and
                    "html" not in resp.headers.get("Content-Type", "").lower()):
                shutil.copyfileobj(resp.raw, temp_file)
                return True
    except requests.RequestException as exc:
        logging.warning(f"Download attempt failed for {url}: {exc}")
        raise
    return False


def process_year_data(start_year: int,
                      end_year: int,
                      mapped_cols: set = None) -> list:
    """Downloads, extracts, and transforms CRDC files for a survey year."""
    possible_urls = get_urls_for_year(start_year, end_year)
    zip_label = f"{start_year}-{str(end_year)[-2:]}"

    with requests.Session() as session:
        if start_year not in _KNOWN_SURVEY_YEARS:
            if not any(
                    _is_zip_archive_available(u, session=session)
                    for u in possible_urls):
                logging.info(
                    f"No published CRDC archive found for {zip_label}. Skipping."
                )
                return []

        produced_files = []
        with tempfile.NamedTemporaryFile(delete=True) as tmp_zip:
            downloaded = False
            for url in possible_urls:
                tmp_zip.seek(0)
                tmp_zip.truncate()
                try:
                    if try_download_url(url, tmp_zip, session=session):
                        downloaded = True
                        logging.info(
                            f"Downloaded CRDC archive for {zip_label} from {url}"
                        )
                        break
                except Exception as exc:
                    logging.warning(
                        f"Could not download {zip_label} from {url}: {exc}")

            if not downloaded:
                if start_year in _KNOWN_SURVEY_YEARS:
                    raise RuntimeError(
                        "Failed to download required historical CRDC archive "
                        f"for {zip_label}")
                return []

            tmp_zip.flush()
            with zipfile.ZipFile(tmp_zip.name) as z:
                matched_files = select_matched_files(z.namelist())
                if not matched_files and start_year in _KNOWN_SURVEY_YEARS:
                    raise RuntimeError(
                        "No matching retention files found in CRDC archive "
                        f"for {zip_label}")
                for file_name in matched_files:
                    output_filename = (
                        f"{end_year}_{os.path.basename(file_name)}")
                    raw_output_path = os.path.join(RAW_SAVE_FOLDER,
                                                   output_filename)
                    with z.open(file_name) as source, open(
                            raw_output_path, "wb") as target:
                        shutil.copyfileobj(source, target)

                    out_csv = process_dataframe(raw_output_path,
                                                end_year,
                                                mapped_cols=mapped_cols)
                    if out_csv:
                        produced_files.append(out_csv)

        return produced_files


def main(argv):
    """Main entry point for downloading and preprocessing CRDC retention data."""
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")

    os.makedirs(RAW_SAVE_FOLDER, exist_ok=True)
    os.makedirs(TRANSFORMED_SAVE_FOLDER, exist_ok=True)

    # Remove stale transformed files (including legacy .xlsx files)
    stale_pattern = os.path.join(TRANSFORMED_SAVE_FOLDER, "transformed_*")
    for stale_file in glob.glob(stale_pattern):
        if os.path.isfile(stale_file):
            os.remove(stale_file)

    mapped_cols = load_pv_mapped_columns(PVMAP_PATH)
    survey_start_years = get_survey_years()
    year_pairs = [(sy, sy + 1) for sy in survey_start_years]

    all_transformed_files = []
    errors = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_year_data, sy, ey, mapped_cols): (sy, ey)
            for sy, ey in year_pairs
        }
        for future in as_completed(futures):
            sy, ey = futures[future]
            try:
                res = future.result()
                all_transformed_files.extend(res)
            except Exception as exc:
                logging.error(f"Worker failed for {sy}-{ey}: {exc}")
                errors.append(f"{sy}-{ey}: {exc}")

    if errors:
        raise RuntimeError(
            f"CRDC retention processing failed: {'; '.join(errors)}")

    if not all_transformed_files:
        raise RuntimeError("No transformed CSV files were generated in "
                           f"{TRANSFORMED_SAVE_FOLDER}")

    logging.info(
        f"Successfully generated {len(all_transformed_files)} transformed CSV "
        f"files in {TRANSFORMED_SAVE_FOLDER}.")


if __name__ == "__main__":
    app.run(main)
