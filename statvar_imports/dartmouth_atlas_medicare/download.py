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

import csv
import io
import math
import os
from pathlib import Path
import tempfile
import zipfile

from absl import app
from absl import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://data.dartmouthatlas.org/downloads"

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
    {
        "filename": "state_mortality_2019.csv.zip",
        "url": f"{BASE_URL}/tables/state_mortality_2019.csv.zip",
        "kind": "mortality_state",
        "is_state": True,
    },
)

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
    """Converts a numeric Dartmouth Atlas FIPS/summary code to a DCID."""
    cleaned = (raw_code or "").strip()
    if not cleaned:
        return None
    try:
        code_int = int(float(cleaned))
    except ValueError:
        return None
    if code_int == 99:
        return "country/USA"
    if code_int <= 0:
        return None
    if is_state:
        if code_int > 99:
            return None
        return f"geoId/{code_int:02d}"
    if code_int < 1000 or code_int > 99999:
        return None
    return f"geoId/{code_int:05d}"


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


def extract_mortality_state_observations(
        rows, observations: dict[tuple[str, str, str], str]) -> None:
    """Extracts state and national Medicare enrollee counts from mortality CSV."""
    for row in rows:
        year = row.get("year", "")
        if not year.isdigit() or len(year) != 4:
            continue
        place = format_place_dcid(row.get("state #", ""), is_state=True)
        if not place:
            continue
        pop_val = clean_numeric_value(row.get("medicare enrollees", ""))
        if pop_val is not None:
            observations[(year, place, "MedicareEnrollee_Count")] = pop_val


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
    elif kind == "mortality_state":
        extract_mortality_state_observations(rows, observations=observations)
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


def run_download_and_transform(base_dir: Path) -> Path:
    """Downloads all configured archives and writes the cleaned input CSV."""
    raw_dir = base_dir / "input_files" / "raw"
    cleaned_path = (base_dir / "input_files" / "cleaned" /
                    "dartmouth_atlas_medicare.csv")
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
    write_cleaned_csv(observations, cleaned_path)
    return cleaned_path


def main(_argv) -> None:
    base_dir = Path(__file__).resolve().parent
    run_download_and_transform(base_dir)


if __name__ == "__main__":
    app.run(main)
