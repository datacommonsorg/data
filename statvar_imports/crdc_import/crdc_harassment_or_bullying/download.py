# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Downloads and extracts school-level CRDC Harassment or Bullying tables."""

import csv
import datetime
import os
import re
import shutil
import sys
import time

from absl import app
from absl import logging
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
_UTIL_PATH = os.path.abspath(os.path.join(_SCRIPT_PATH, "../../../util"))
if _UTIL_PATH not in sys.path:
    sys.path.append(_UTIL_PATH)

from download_util_script import download_file  # noqa: E402

_BASE_URL = "https://civilrightsdata.ed.gov/assets/ocr/docs/{year_range}-crdc-data.zip"
_DEFAULT_DOWNLOAD_DIR = os.path.join(_SCRIPT_PATH, "source_files")
_DEFAULT_OUTPUT_DIR = os.path.join(_SCRIPT_PATH, "input_files")
_DEFAULT_PV_MAP_PATH = os.path.join(_SCRIPT_PATH,
                                    "harassment_or_bullying_pvmap.csv")

# Published CRDC survey start years containing school-level Harassment/Bullying
# tables (2011-12 -> 2012, 2013-14 -> 2014, 2017-18 -> 2018, 2020-21 -> 2021,
# 2021-22 -> 2022, 2023-24 -> 2024).
_REQUIRED_SURVEY_START_YEARS = (2011, 2013, 2017, 2020, 2021, 2023)
_SINGLE_FILE_TARGET_YEARS = frozenset({2014, 2018, 2021, 2022})
_EXPECTED_2012_PARTS = 6
_MAX_DOWNLOAD_ATTEMPTS = 3
_RETRY_INITIAL_DELAY_SECS = 5

_METADATA_KEYS = frozenset({
    "",
    "KEY",
    "LEAID",
    "LEA_NAME",
    "SCHID",
    "SCH_NAME",
    "COMBOKEY",
    "YEAR",
})
_LEA_TOKEN_RE = re.compile(r"(^|[^a-z0-9])leas?([^a-z0-9]|$)")
_CLEAN_HEADER_RE = re.compile(r"[`'\"]")


def create_http_session() -> requests.Session:
    """Creates a shared HTTP session with bounded retries for status checks."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"HEAD", "GET"}),
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_survey_start_years(current_year: int | None = None) -> list[int]:
    """Returns sorted CRDC survey start years (required baseline + 2024+)."""
    if current_year is None:
        current_year = datetime.datetime.now(datetime.timezone.utc).year
    future_years = range(2024, max(2024, current_year + 1))
    return sorted(set(_REQUIRED_SURVEY_START_YEARS).union(future_years))


def load_mapped_metric_columns(
        pv_map_path: str = _DEFAULT_PV_MAP_PATH) -> set[str]:
    """Loads mapped uppercase metric column names from the PV map CSV."""
    mapped_cols: set[str] = set()
    if not os.path.isfile(pv_map_path):
        raise FileNotFoundError(f"PV map file not found: {pv_map_path}")

    with open(pv_map_path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            key = _CLEAN_HEADER_RE.sub("", row[0]).strip().upper()
            if key in _METADATA_KEYS or key.startswith("#"):
                continue
            prop = row[1].strip().lower() if len(row) > 1 else ""
            if prop.startswith("not needed") or prop.startswith("#not needed"):
                continue
            mapped_cols.add(key)
    return mapped_cols


def _normalize_header(col_name: object) -> str:
    return _CLEAN_HEADER_RE.sub("", str(col_name)).strip().upper()


def _read_columns(filepath: str) -> set[str]:
    """Reads only the header row of a CSV or Excel file as uppercase names."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                df = pd.read_csv(filepath,
                                 nrows=0,
                                 dtype=str,
                                 encoding=encoding)
                return {_normalize_header(c) for c in df.columns}
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Unable to decode CSV header: {filepath}")
    if ext in (".xlsx", ".xls"):
        engine = "openpyxl" if ext == ".xlsx" else None
        df = pd.read_excel(filepath,
                           sheet_name=0,
                           nrows=0,
                           dtype=str,
                           engine=engine)
        return {_normalize_header(c) for c in df.columns}
    return set()


def _read_tabular_file(filepath: str) -> pd.DataFrame:
    """Reads a CSV or Excel table with all columns preserved as strings."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                return pd.read_csv(
                    filepath,
                    dtype=str,
                    low_memory=False,
                    keep_default_na=False,
                    encoding=encoding,
                )
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Unable to decode CSV file: {filepath}")
    if ext in (".xlsx", ".xls"):
        engine = "openpyxl" if ext == ".xlsx" else None
        return pd.read_excel(
            filepath,
            sheet_name=0,
            dtype=str,
            keep_default_na=False,
            engine=engine,
        )
    raise ValueError(f"Unsupported file extension '{ext}' for {filepath}")


def _is_ignored_directory(dir_name: str, year_range: str) -> bool:
    """Returns True if a directory should be pruned during discovery."""
    if dir_name == "__MACOSX" or dir_name.startswith("."):
        return True
    lower = dir_name.lower()
    if _LEA_TOKEN_RE.search(lower):
        return True
    # In 2009-10 and 2011-12, "Pt 2-Reported Allegations of Harassment or
    # Bullying" is a separate unmapped sibling directory of "Pt 2-Harassment or
    # Bullying" that previously caused non-deterministic glob.glob()[0] failures.
    if year_range in ("2009-10", "2011-12") and "alleg" in lower:
        return True
    return False


def _is_candidate_data_file(filename: str, rel_path: str,
                            year_range: str) -> bool:
    """Checks filename conventions for school-level Harassment/Bullying files."""
    if filename.startswith(".") or filename.startswith("~$"):
        return False
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        return False
    lower_name = filename.lower()
    if any(tok in lower_name
           for tok in ("layout", "readme", "codebook", "dictionary")):
        return False
    if _LEA_TOKEN_RE.search(lower_name):
        return False
    if year_range in ("2009-10", "2011-12") and "alleg" in lower_name:
        return False
    lower_rel = rel_path.lower()
    return "harass" in lower_rel or "bully" in lower_rel


def discover_harassment_files(
    year_download_dir: str,
    year_range: str,
    mapped_columns: set[str],
) -> list[str]:
    """Deterministically discovers school-level Harassment/Bullying tables."""
    matched_files: list[str] = []
    for root, dirs, files in os.walk(year_download_dir, topdown=True):
        dirs[:] = sorted(
            d for d in dirs if not _is_ignored_directory(d, year_range))
        for filename in sorted(files):
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, year_download_dir)
            if not _is_candidate_data_file(filename, rel_path, year_range):
                continue
            try:
                cols = _read_columns(full_path)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed reading header from candidate file '{full_path}' "
                    f"for {year_range}: {exc}") from exc

            if "COMBOKEY" not in cols:
                logging.info(
                    "Skipping '%s' for %s: missing school COMBOKEY column.",
                    rel_path,
                    year_range,
                )
                continue
            if mapped_columns and not (cols & mapped_columns):
                logging.info(
                    "Skipping '%s' for %s: no columns mapped in PV map.",
                    rel_path,
                    year_range,
                )
                continue
            matched_files.append(full_path)

    matched_files.sort(
        key=lambda p: os.path.relpath(p, year_download_dir).replace("\\", "/"))
    return matched_files


def collect_and_convert_year_files(
    year_range: str,
    base_download_dir: str = _DEFAULT_DOWNLOAD_DIR,
    output_dir: str = _DEFAULT_OUTPUT_DIR,
    mapped_columns: set[str] | None = None,
    is_required: bool = True,
) -> list[str]:
    """Converts discovered Harassment/Bullying files for one survey year to CSV."""
    logging.info("Starting file collection and CSV conversion for %s...",
                 year_range)
    year_download_dir = os.path.join(base_download_dir,
                                     f"crdc_data_{year_range}")
    if mapped_columns is None:
        mapped_columns = load_mapped_metric_columns()

    try:
        first_year = int(year_range.split("-")[0])
    except (ValueError, IndexError) as exc:
        raise ValueError(
            f"Invalid CRDC year_range '{year_range}'; expected 'YYYY-YY'."
        ) from exc
    target_year = first_year + 1

    file_paths = discover_harassment_files(
        year_download_dir=year_download_dir,
        year_range=year_range,
        mapped_columns=mapped_columns,
    )

    if not file_paths:
        if is_required:
            raise RuntimeError(
                f"Zero mapped school-level Harassment/Bullying files found for "
                f"required release {year_range} in '{year_download_dir}'.")
        logging.info("No Harassment/Bullying data files found for %s.",
                     year_range)
        return []

    if year_range == "2011-12" and len(file_paths) != _EXPECTED_2012_PARTS:
        raise RuntimeError(
            f"Expected exactly {_EXPECTED_2012_PARTS} Harassment/Bullying "
            f"tables for 2011-12, but found {len(file_paths)}: {file_paths}")

    if target_year in _SINGLE_FILE_TARGET_YEARS and len(file_paths) != 1:
        raise RuntimeError(
            f"Expected exactly 1 Harassment/Bullying table for {year_range} "
            f"(target year {target_year}), but found {len(file_paths)}: "
            f"{file_paths}")

    os.makedirs(output_dir, exist_ok=True)
    base_name = f"crdc_harassment_or_bullying_{target_year}"
    written_paths: list[str] = []
    use_parts = (year_range == "2011-12") or (len(file_paths) > 1)

    for idx, old_filepath in enumerate(file_paths, start=1):
        if use_parts:
            new_filename = f"{base_name}_part_{idx:02d}.csv"
        else:
            new_filename = f"{base_name}.csv"
        new_filepath = os.path.join(output_dir, new_filename)
        tmp_filepath = f"{new_filepath}.tmp"

        orig_ext = os.path.splitext(old_filepath)[1].lower()
        logging.info(
            "Collecting '%s' (%s) to '%s'",
            os.path.relpath(old_filepath, year_download_dir),
            orig_ext,
            new_filepath,
        )
        if orig_ext == ".csv":
            # Preserve raw source CSV byte-for-byte for GCS source_files attribution;
            # verify at least 1 data row exists before accepting.
            df_check = pd.read_csv(
                old_filepath,
                nrows=1,
                dtype=str,
                encoding="latin-1",
            )
            if df_check.empty:
                raise RuntimeError(
                    f"Extracted CSV '{old_filepath}' for {year_range} is empty."
                )
            shutil.copyfile(old_filepath, tmp_filepath)
        else:
            df = _read_tabular_file(old_filepath)
            if df.empty:
                raise RuntimeError(
                    f"Extracted table '{old_filepath}' for {year_range} is empty."
                )
            df.to_csv(tmp_filepath, index=False)

        os.replace(tmp_filepath, new_filepath)
        written_paths.append(new_filepath)

    logging.info(
        "Collection and conversion complete for %s. Saved %d CSV file(s).",
        year_range,
        len(written_paths),
    )
    return written_paths


def _probe_optional_archive_available(url: str,
                                      session: requests.Session) -> bool | None:
    """Probes whether an optional future CRDC archive exists as a non-HTML file.

    Returns:
        True if the server confirms a non-HTML archive is available,
        False if 404 or HTML soft-404 (not yet published),
        None if HEAD was inconclusive (e.g. 405 or transient error).
    """
    logging.info("Probing availability via HEAD request: %s", url)
    try:
        resp = session.head(url, allow_redirects=True, timeout=15)
    except requests.exceptions.RequestException as exc:
        logging.warning("HEAD probe inconclusive for '%s': %s", url, exc)
        return None

    if resp.status_code == 404:
        logging.info("Archive not yet available (HTTP 404): %s", url)
        return False

    content_type = resp.headers.get("Content-Type", "").lower()
    if 200 <= resp.status_code < 300 and ("text/html" in content_type or
                                          "application/xml" in content_type):
        logging.info(
            "Archive not yet published (soft-404, Content-Type='%s'): %s",
            content_type,
            url,
        )
        return False

    if 200 <= resp.status_code < 300:
        try:
            content_len = int(resp.headers.get("Content-Length", "0"))
        except ValueError:
            content_len = 0
        if "zip" in content_type or content_len >= 1_000_000:
            return True

    return None


def download_year_archive(
    year_range: str,
    url: str,
    output_dir_for_year: str,
    is_required: bool,
    session: requests.Session,
    sleep_fn=time.sleep,
) -> bool:
    """Downloads and unzips one CRDC year archive with full-stream retries."""
    confirmed_available = is_required
    if not is_required:
        probe = _probe_optional_archive_available(url, session)
        if probe is False:
            return False
        if probe is True:
            confirmed_available = True

    max_attempts = _MAX_DOWNLOAD_ATTEMPTS if confirmed_available else 1
    for attempt in range(1, max_attempts + 1):
        if os.path.exists(output_dir_for_year):
            shutil.rmtree(output_dir_for_year)
        os.makedirs(output_dir_for_year, exist_ok=True)

        logging.info(
            "Downloading CRDC archive for %s (attempt %d/%d): GET %s",
            year_range,
            attempt,
            max_attempts,
            url,
        )
        success = download_file(
            url=url,
            output_folder=output_dir_for_year,
            unzip=True,
            tries=3,
            delay=5,
            backoff=2,
            session=session,
        )
        if success:
            return True

        shutil.rmtree(output_dir_for_year, ignore_errors=True)
        if attempt < max_attempts:
            delay_secs = _RETRY_INITIAL_DELAY_SECS * (2**(attempt - 1))
            logging.warning(
                "Download/unzip failed for %s on attempt %d/%d; retrying in %ds...",
                year_range,
                attempt,
                max_attempts,
                delay_secs,
            )
            sleep_fn(delay_secs)

    if confirmed_available:
        raise RuntimeError(
            f"Failed to download and extract CRDC archive for {year_range} "
            f"from '{url}' after {max_attempts} attempt(s).")

    logging.info(
        "Optional future CRDC archive %s is not available yet (%s).",
        year_range,
        url,
    )
    return False


def run_download(
    base_download_dir: str = _DEFAULT_DOWNLOAD_DIR,
    output_dir: str = _DEFAULT_OUTPUT_DIR,
    pv_map_path: str = _DEFAULT_PV_MAP_PATH,
    current_year: int | None = None,
) -> list[str]:
    """Downloads, extracts, and converts all available CRDC Harassment tables."""
    os.makedirs(base_download_dir, exist_ok=True)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    mapped_columns = load_mapped_metric_columns(pv_map_path)
    years_to_try = get_survey_start_years(current_year=current_year)
    required_set = set(_REQUIRED_SURVEY_START_YEARS)
    all_written_files: list[str] = []

    with create_http_session() as session:
        for year in years_to_try:
            year_range = f"{year}-{str(year + 1)[-2:]}"
            is_required = year in required_set
            url = _BASE_URL.format(year_range=year_range)
            output_dir_for_year = os.path.join(base_download_dir,
                                               f"crdc_data_{year_range}")

            downloaded = download_year_archive(
                year_range=year_range,
                url=url,
                output_dir_for_year=output_dir_for_year,
                is_required=is_required,
                session=session,
            )
            if not downloaded:
                continue

            try:
                written = collect_and_convert_year_files(
                    year_range=year_range,
                    base_download_dir=base_download_dir,
                    output_dir=output_dir,
                    mapped_columns=mapped_columns,
                    is_required=is_required,
                )
                all_written_files.extend(written)
            finally:
                # Reclaim multi-GB extracted archive space after each year.
                shutil.rmtree(output_dir_for_year, ignore_errors=True)

    logging.info(
        "Download and collection complete. Wrote %d CSV file(s) to '%s'.",
        len(all_written_files),
        output_dir,
    )
    return all_written_files


def main(_):
    logging.set_verbosity(logging.INFO)
    run_download()


if __name__ == "__main__":
    app.run(main)
