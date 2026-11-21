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
"""Downloads and normalizes Dartmouth Atlas Medicare data for stat_var_processor."""

import argparse
import csv
import io
import math
import os
from pathlib import Path
import sys
import tempfile
import zipfile

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
_UTIL_DIR = os.path.abspath(os.path.join(_CODEDIR, "../../util"))
if _UTIL_DIR not in sys.path:
    sys.path.insert(1, _UTIL_DIR)

from absl import logging
import file_util
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_OUTPUT_DIR = os.path.join(_CODEDIR, "input_files")
DEFAULT_HISTORICAL_GCS_DIR = (
    "gs://unresolved_mcf/dartmouth_atlas_medicare/historical")
DEFAULT_HISTORICAL_OUTPUT_DIR = os.path.join(_CODEDIR, "output_files")

BASE_URL = "https://data.dartmouthatlas.org/downloads"
HISTORICAL_CSVS: tuple[str, ...] = (
    "dartmouth_atlas_medicare_historical_1999_2016.csv",)

COMMON_TMCF_CONTENT = (
    "Node: E:dartmouth_atlas_medicare->E0\n"
    "observationDate: C:dartmouth_atlas_medicare->observationDate\n"
    "observationAbout: C:dartmouth_atlas_medicare->observationAbout\n"
    "variableMeasured: C:dartmouth_atlas_medicare->variableMeasured\n"
    "value: C:dartmouth_atlas_medicare->value\n"
    "observationPeriod: C:dartmouth_atlas_medicare->observationPeriod\n"
    "typeOf: dcs:StatVarObservation\n")

SOURCE_ARCHIVES = (
    {
        "filename": "county_stdprices_2003_2010.csv.zip",
        "url": f"{BASE_URL}/research_files/county_stdprices_2003_2010.csv.zip",
        "kind": "stdprices",
        "is_state": False,
    },
    {
        "filename": "county_stdprices_ffs.csv.zip",
        "url": f"{BASE_URL}/research_files/county_stdprices_ffs.csv.zip",
        "kind": "stdprices",
        "is_state": False,
    },
    {
        "filename": "state_stdprices_2003_2010.csv.zip",
        "url": f"{BASE_URL}/research_files/state_stdprices_2003_2010.csv.zip",
        "kind": "stdprices",
        "is_state": True,
    },
    {
        "filename": "state_stdprices_ffs.csv.zip",
        "url": f"{BASE_URL}/research_files/state_stdprices_ffs.csv.zip",
        "kind": "stdprices",
        "is_state": True,
    },
    {
        "filename": "county_hedis_6575ffs.csv.zip",
        "url": f"{BASE_URL}/research_files/county_hedis_6575ffs.csv.zip",
        "kind": "hedis",
        "is_state": False,
    },
    {
        "filename": "state_hedis_6575ffs.csv.zip",
        "url": f"{BASE_URL}/research_files/state_hedis_6575ffs.csv.zip",
        "kind": "hedis",
        "is_state": True,
    },
)

# Dartmouth Atlas state-level files use CMS/SSA state codes (01-53, skipping 40
# and 48) rather than US Census FIPS codes (01-56).
SSA_STATE_TO_FIPS = {
    1: "01",  # Alabama
    2: "02",  # Alaska
    3: "04",  # Arizona
    4: "05",  # Arkansas
    5: "06",  # California
    6: "08",  # Colorado
    7: "09",  # Connecticut
    8: "10",  # Delaware
    9: "11",  # District of Columbia
    10: "12",  # Florida
    11: "13",  # Georgia
    12: "15",  # Hawaii
    13: "16",  # Idaho
    14: "17",  # Illinois
    15: "18",  # Indiana
    16: "19",  # Iowa
    17: "20",  # Kansas
    18: "21",  # Kentucky
    19: "22",  # Louisiana
    20: "23",  # Maine
    21: "24",  # Maryland
    22: "25",  # Massachusetts
    23: "26",  # Michigan
    24: "27",  # Minnesota
    25: "28",  # Mississippi
    26: "29",  # Missouri
    27: "30",  # Montana
    28: "31",  # Nebraska
    29: "32",  # Nevada
    30: "33",  # New Hampshire
    31: "34",  # New Jersey
    32: "35",  # New Mexico
    33: "36",  # New York
    34: "37",  # North Carolina
    35: "38",  # North Dakota
    36: "39",  # Ohio
    37: "40",  # Oklahoma
    38: "41",  # Oregon
    39: "42",  # Pennsylvania
    41: "44",  # Rhode Island
    42: "45",  # South Carolina
    43: "46",  # South Dakota
    44: "47",  # Tennessee
    45: "48",  # Texas
    46: "49",  # Utah
    47: "50",  # Vermont
    49: "51",  # Virginia
    50: "53",  # Washington
    51: "54",  # West Virginia
    52: "55",  # Wisconsin
    53: "56",  # Wyoming
}

VALID_COUNTY_STATE_FIPS = frozenset(SSA_STATE_TO_FIPS.values()) | frozenset({
    "60",  # American Samoa
    "66",  # Guam
    "69",  # Northern Mariana Islands
    "72",  # Puerto Rico
    "78",  # U.S. Virgin Islands
})

NON_NUMERIC_TOKENS = frozenset({
    "",
    ".",
    "-",
    "--",
    "*",
    "na",
    "n/a",
    "nan",
    "none",
    "null",
    "suppressed",
})

HEDIS_PART_B_RACE_MAP = {
    "overall": "MedicareEnrollee_MedicareB",
    "black": "MedicareEnrollee_MedicareB_Black",
    "non-black": "MedicareEnrollee_MedicareB_NonBlack",
}

HEDIS_DIABETIC_RACE_MAP = {
    "black": "MedicareEnrollee_Diabetic_Black",
    "non-black": "MedicareEnrollee_Diabetic_NonBlack",
}

SV_KEY_TO_DCID: dict[str, str] = {
    "MedicareEnrollee_Count":
        "Count_MedicareEnrollee",
    "MedicareEnrollee_MeanPrice":
        "dc/rn90czcrqcv06",
    "MedicareEnrollee_MedicareA":
        "Count_MedicareEnrollee_MedicareA",
    "MedicareEnrollee_MedicareA_Black":
        "Count_MedicareEnrollee_MedicareA_Black",
    "MedicareEnrollee_MedicareA_NonBlack":
        "Count_MedicareEnrollee_MedicareA_NonBlack",
    "MedicareEnrollee_MedicareB":
        "Count_MedicareEnrollee_MedicareB",
    "MedicareEnrollee_MedicareB_Black":
        "Count_MedicareEnrollee_MedicareB_Black",
    "MedicareEnrollee_MedicareB_NonBlack":
        "Count_MedicareEnrollee_MedicareB_NonBlack",
    "MedicareEnrollee_Diabetic_Black":
        "Count_MedicareEnrollee_ConditionDiabetic_Black",
    "MedicareEnrollee_Diabetic_NonBlack":
        "Count_MedicareEnrollee_ConditionDiabetic_NonBlack",
}

REQUEST_TIMEOUT_SECONDS = 120


def create_session() -> requests.Session:
    """Creates an HTTP session with bounded retries and backoff."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "DataCommons-Import/1.0"})
    return session


def atomic_write_bytes(target_path: Path, content: bytes) -> None:
    """Writes bytes to target_path atomically via a sibling temporary file."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=target_path.parent, prefix=".tmp_")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        os.replace(tmp_name, target_path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def download_file(session: requests.Session, url: str, dest_path: Path) -> None:
    """Downloads url to dest_path atomically, raising on HTTP or empty errors."""
    logging.info("GET %s", url)
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as err:
        raise RuntimeError(f"Failed to download {url}: {err}") from err
    if not response.content:
        raise RuntimeError(f"Downloaded empty response from {url}")
    atomic_write_bytes(dest_path, response.content)
    logging.info("Saved %s (%d bytes)", dest_path, len(response.content))


def format_place_dcid(raw_code: str, is_state: bool) -> str | None:
    """Converts a Dartmouth Atlas state (SSA) or county (FIPS) code to a DCID."""
    cleaned = (raw_code or "").strip()
    if not cleaned:
        return None
    try:
        code_int = int(float(cleaned))
    except ValueError:
        return None
    if code_int == 99 or (not is_state and code_int == 99999):
        return "country/USA"
    if code_int <= 0:
        return None
    if is_state:
        state_fips = SSA_STATE_TO_FIPS.get(code_int)
        if not state_fips:
            return None
        return f"geoId/{state_fips}"
    if code_int < 1000 or code_int > 99999:
        return None
    county_fips = f"{code_int:05d}"
    if county_fips[:2] not in VALID_COUNTY_STATE_FIPS:
        return None
    county_subcode = int(county_fips[2:])
    if county_subcode == 0 or county_subcode >= 900:
        return None
    return f"geoId/{county_fips}"


def clean_numeric_value(raw_val: str) -> str | None:
    """Normalizes numeric strings and filters NaN/suppressed placeholders."""
    if raw_val is None:
        return None
    cleaned = raw_val.strip().replace(",", "").replace("$", "").strip()
    if cleaned.lower() in NON_NUMERIC_TOKENS:
        return None
    try:
        parsed = float(cleaned)
    except ValueError:
        return None
    if not math.isfinite(parsed) or parsed < 0:
        return None
    if parsed.is_integer():
        return str(int(parsed))
    return f"{parsed:.6f}".rstrip("0").rstrip(".")


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    """Lowercases and strips CSV column keys for BOM/casing resilience."""
    return {
        (k.lstrip("\ufeff").strip().lower() if k else ""): (v or "").strip()
        for k, v in row.items()
    }


def iter_csv_rows_from_zip(zip_path: Path):
    """Yields normalized dict rows from CSV members of a ZIP archive."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        csv_members = [
            name for name in zf.namelist()
            if name.lower().endswith(".csv") and not name.startswith(
                "__MACOSX/") and not os.path.basename(name).startswith("._")
        ]
        if not csv_members:
            raise RuntimeError(f"No CSV files found in archive {zip_path}")
        for member in csv_members:
            with zf.open(member, "r") as raw_file:
                with io.TextIOWrapper(raw_file,
                                      encoding="utf-8-sig",
                                      errors="replace") as text_stream:
                    reader = csv.DictReader(text_stream)
                    for row in reader:
                        yield normalize_row(row)


def extract_stdprices_observations(
        rows, is_state: bool, observations: dict[tuple[str, str, str],
                                                 str]) -> None:
    """Extracts Count_MedicareEnrollee and Mean Price observations."""
    for row in rows:
        if row.get("eventname", "").lower() != "stdprice_total":
            continue
        year = row.get("year", "")
        if not year.isdigit() or len(year) != 4:
            continue
        place = format_place_dcid(row.get("geo_code", ""), is_state=is_state)
        if not place:
            continue
        pop_val = clean_numeric_value(row.get("population", ""))
        if pop_val is not None:
            observations[(year, place, "MedicareEnrollee_Count")] = pop_val
        price_val = clean_numeric_value(row.get("adjusted_rate", ""))
        if price_val is not None:
            observations[(year, place,
                          "MedicareEnrollee_MeanPrice")] = price_val


def extract_hedis_observations(
        rows, is_state: bool, observations: dict[tuple[str, str, str],
                                                 str]) -> None:
    """Extracts Part B and Diabetic race-stratified enrollee counts."""
    for row in rows:
        event = row.get("eventname", "").lower()
        race = row.get("race", "").lower()
        if event == "ptbjune_amcare2":
            sv_key = HEDIS_PART_B_RACE_MAP.get(race)
        elif event == "diab_hgb":
            sv_key = HEDIS_DIABETIC_RACE_MAP.get(race)
        else:
            continue
        if not sv_key:
            continue
        year = row.get("year", "")
        if not year.isdigit() or len(year) != 4:
            continue
        place = format_place_dcid(row.get("geo_code", ""), is_state=is_state)
        if not place:
            continue
        pop_val = clean_numeric_value(row.get("population", ""))
        if pop_val is not None:
            observations[(year, place, sv_key)] = pop_val


def process_archive(
    archive_path: Path,
    kind: str,
    is_state: bool,
    observations: dict[tuple[str, str, str], str],
) -> None:
    """Dispatches a downloaded archive to the appropriate row extractor."""
    rows = iter_csv_rows_from_zip(archive_path)
    if kind == "stdprices":
        extract_stdprices_observations(rows,
                                       is_state=is_state,
                                       observations=observations)
    elif kind == "hedis":
        extract_hedis_observations(rows,
                                   is_state=is_state,
                                   observations=observations)
    else:
        raise ValueError(f"Unknown archive kind: {kind}")


def write_cleaned_csv(observations: dict[tuple[str, str, str], str],
                      output_path: Path) -> None:
    """Writes normalized observations to output_path atomically."""
    if not observations:
        raise RuntimeError(
            "No observations extracted from Dartmouth Atlas sources")
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["year", "place", "stat_var_key", "value"])
    for (year, place, sv_key), val in sorted(observations.items()):
        writer.writerow([year, place, sv_key, val])
    atomic_write_bytes(output_path, buf.getvalue().encode("utf-8"))
    logging.info("Wrote %d cleaned observations to %s", len(observations),
                 output_path)


def _strip_namespace_prefix(value: str) -> str:
    """Strips whitespace, quotes, and leading dcid:/dcs: prefixes."""
    cleaned = (value or "").strip().strip('"').strip("'").strip()
    for prefix in ("dcid:", "dcs:"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    return cleaned


def copy_historical_files_from_gcs(
    historical_gcs_dir: str,
    historical_output_dir: str | Path,
) -> list[Path]:
    """Copies consolidated historical CSVs and writes common_tmcf.tmcf."""
    if not historical_gcs_dir:
        return []
    out_dir = Path(historical_output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dst_tmcf = out_dir / "common_tmcf.tmcf"
    atomic_write_bytes(dst_tmcf, COMMON_TMCF_CONTENT.encode("utf-8"))
    logging.info("Wrote shared historical TMCF to %s", dst_tmcf)

    gcs_base = historical_gcs_dir.rstrip("/")
    copied_paths: list[Path] = []
    for fname in HISTORICAL_CSVS:
        src_path = f"{gcs_base}/{fname}"
        dst_path = out_dir / fname
        if (not src_path.startswith("gs://") and
                os.path.abspath(src_path) == os.path.abspath(str(dst_path))):
            logging.info(
                "Historical CSV already present at %s; skipping self-copy",
                dst_path)
            copied_paths.append(dst_path)
            continue
        logging.info("Copying historical CSV from %s to %s", src_path, dst_path)
        file_util.file_copy(src_path, str(dst_path))
        copied_paths.append(dst_path)
    return copied_paths


def load_historical_observation_keys(
    historical_csv_paths: list[Path],) -> set[tuple[str, str, str]]:
    """Loads (year, place_bare, sv_bare) keys from consolidated historical CSVs."""
    keys: set[tuple[str, str, str]] = set()
    for csv_path in historical_csv_paths:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                year = _strip_namespace_prefix(row.get("observationDate", ""))
                place = _strip_namespace_prefix(row.get("observationAbout", ""))
                sv = _strip_namespace_prefix(row.get("variableMeasured", ""))
                if year and place and sv:
                    keys.add((year, place, sv))
    logging.info("Loaded %d historical observation keys from %d file(s)",
                 len(keys), len(historical_csv_paths))
    return keys


def filter_out_historical_observations(
    observations: dict[tuple[str, str, str], str],
    historical_keys: set[tuple[str, str, str]],
) -> dict[tuple[str, str, str], str]:
    """Removes live observations already present in the historical baseline."""
    if not historical_keys:
        return observations
    filtered: dict[tuple[str, str, str], str] = {}
    skipped = 0
    for (year, place, sv_key), val in observations.items():
        sv_dcid = SV_KEY_TO_DCID.get(sv_key, sv_key)
        if (year, place, sv_dcid) in historical_keys:
            skipped += 1
            continue
        filtered[(year, place, sv_key)] = val
    logging.info(
        "Filtered live observations against historical baseline: "
        "total=%d, skipped_historical=%d, net_new=%d",
        len(observations),
        skipped,
        len(filtered),
    )
    return filtered


def run_download_and_transform(
    output_dir: Path,
    historical_gcs_dir: str = "",
    historical_output_dir: Path | None = None,
) -> Path:
    """Stages historical CSV, downloads live archives, and writes net-new CSV."""
    historical_keys: set[tuple[str, str, str]] = set()
    if historical_gcs_dir and historical_output_dir is not None:
        copied_csvs = copy_historical_files_from_gcs(
            historical_gcs_dir=historical_gcs_dir,
            historical_output_dir=historical_output_dir,
        )
        historical_keys = load_historical_observation_keys(copied_csvs)

    raw_dir = output_dir / "raw"
    cleaned_path = output_dir / "cleaned" / "dartmouth_atlas_medicare.csv"
    observations: dict[tuple[str, str, str], str] = {}
    with create_session() as session:
        for spec in SOURCE_ARCHIVES:
            dest_path = raw_dir / spec["filename"]
            download_file(session, spec["url"], dest_path)
            process_archive(
                dest_path,
                kind=spec["kind"],
                is_state=spec["is_state"],
                observations=observations,
            )
    net_new_observations = filter_out_historical_observations(
        observations, historical_keys)
    write_cleaned_csv(net_new_observations, cleaned_path)
    return cleaned_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parses CLI arguments for Dartmouth Atlas download and preprocessing."""
    parser = argparse.ArgumentParser(
        description="Downloads and normalizes Dartmouth Atlas Medicare data.")
    parser.add_argument(
        "--output_dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory path to save raw downloaded ZIPs and cleaned CSVs.",
    )
    parser.add_argument(
        "--historical_gcs_dir",
        default=DEFAULT_HISTORICAL_GCS_DIR,
        help=("GCS or local directory containing the consolidated 1999-2016 "
              "historical CSV file. Pass empty string to skip historical "
              "baseline copy/dedup."),
    )
    parser.add_argument(
        "--historical_output_dir",
        default=DEFAULT_HISTORICAL_OUTPUT_DIR,
        help="Directory path to copy historical CSV and common_tmcf.tmcf into.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    logging.set_verbosity(logging.INFO)
    args = parse_args(argv)
    run_download_and_transform(
        output_dir=Path(args.output_dir),
        historical_gcs_dir=args.historical_gcs_dir,
        historical_output_dir=Path(args.historical_output_dir),
    )


if __name__ == "__main__":
    main()
