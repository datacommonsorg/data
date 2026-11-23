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
import re
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
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

PORTAL_HOST = "data.dartmouthatlas.org"
PORTAL_URL = f"https://{PORTAL_HOST}"
BASE_URL = f"{PORTAL_URL}/downloads"
DEFAULT_HSA_PLACES_CSV = Path(_CODEDIR) / "dartmouth_hsa_places.csv"
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

# Official Dartmouth Atlas topic pages scraped dynamically on each run so newly
# published annual tables or longitudinal research archives are picked up
# automatically without code changes.
TOPIC_DISCOVERY_PAGES: tuple[str, ...] = (
    f"{PORTAL_URL}/medicare-reimbursements/",
    f"{PORTAL_URL}/primary-care/",
    f"{PORTAL_URL}/mortality/",
)

# Note on mortality scope:
# - HSA mortality workbooks (hsa_mortality_dead6599ffs_2016..2017.xlsx and any
#   future hsa_mortality* releases) advance the 2,964 7-digit HSA City/Town/
#   Village/Neighborhood Count_MedicareEnrollee series from dartmouth_mortality_count.
# - State mortality files are excluded because they report all-Medicare (HMO +
#   FFS) enrollees whereas state_stdprices_ffs.csv.zip supplies consistent FFS
#   counts through 2019+.
# - HRR mortality files are excluded because HRRs are multi-county referral
#   regions ~2x-10x larger than the HSA city series stored on 7-digit place
#   DCIDs in 1999-2015 (e.g., Birmingham AL 2015 prod = 120,523 matches 2016 HSA
#   = 124,299 vs 2016 HRR = 359,057).
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
        "filename": "hsa_mortality_dead6599ffs_2016.xlsx",
        "url": f"{BASE_URL}/tables/hsa_mortality_dead6599ffs_2016.xlsx",
        "kind": "hsa_mortality",
        "is_state": False,
    },
    {
        "filename": "hsa_mortality_dead6599ffs_2017.xlsx",
        "url": f"{BASE_URL}/tables/hsa_mortality_dead6599ffs_2017.xlsx",
        "kind": "hsa_mortality",
        "is_state": False,
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
    except (ValueError, OverflowError):
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
    state_fips = county_fips[:2]
    if state_fips not in VALID_COUNTY_STATE_FIPS:
        return None
    county_subcode = int(county_fips[2:])
    max_subcode = 840 if state_fips == "51" else 510
    if county_subcode <= 0 or county_subcode > max_subcode:
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


_DOWNLOAD_LINK_RE = re.compile(
    r"https?://data\.dartmouthatlas\.org/downloads/[^\s\"'<>]+",
    re.IGNORECASE,
)
_STDPRICES_RESEARCH_RE = re.compile(
    r"^/downloads/research_files/(county|state)_stdprices[a-z0-9_]*\.csv\.zip$",
    re.IGNORECASE,
)
_HEDIS_RESEARCH_RE = re.compile(
    r"^/downloads/research_files/(county|state)_hedis[a-z0-9_]*\.csv\.zip$",
    re.IGNORECASE,
)
_HSA_MORTALITY_TABLE_RE = re.compile(
    r"^/downloads/(?:tables/(?:hsa_mortality[a-z0-9_]*_(201[6-9]|20[2-9]\d)"
    r"|(201[6-9]|20[2-9]\d)_mortality_hsa)\.(?:xlsx|csv\.zip)"
    r"|research_files/hsa_mortality[a-z0-9_]*\.csv\.zip)$",
    re.IGNORECASE,
)
_STDPRICES_ANNUAL_TABLE_RE = re.compile(
    r"^/downloads/tables/(county|state)_stdprices[a-z0-9_]*_(20[2-9]\d)\.(?:csv\.zip|xlsx)$",
    re.IGNORECASE,
)
_XLSX_NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_CELL_COL_RE = re.compile(r"^([A-Z]+)")


def classify_download_url(url: str) -> dict[str, object] | None:
    """Classifies a Dartmouth Atlas download URL into an archive spec."""
    try:
        parsed = urllib.parse.urlsplit(url.strip())
    except ValueError:
        return None
    if parsed.scheme.lower() not in ("http", "https"):
        return None
    if not parsed.hostname or parsed.hostname.lower() != PORTAL_HOST:
        return None
    if (parsed.username is not None or parsed.password is not None or
            parsed.port is not None or parsed.query or parsed.fragment):
        return None

    rel_path = parsed.path
    if ".." in rel_path.split("/"):
        return None
    canonical_url = f"{PORTAL_URL}{rel_path}"
    filename = os.path.basename(rel_path)

    m_std = _STDPRICES_RESEARCH_RE.match(rel_path)
    if m_std:
        return {
            "filename": filename,
            "url": canonical_url,
            "kind": "stdprices",
            "is_state": m_std.group(1).lower() == "state",
        }
    m_hedis = _HEDIS_RESEARCH_RE.match(rel_path)
    if m_hedis:
        return {
            "filename": filename,
            "url": canonical_url,
            "kind": "hedis",
            "is_state": m_hedis.group(1).lower() == "state",
        }
    if _HSA_MORTALITY_TABLE_RE.match(rel_path):
        return {
            "filename": filename,
            "url": canonical_url,
            "kind": "hsa_mortality",
            "is_state": False,
        }
    m_annual = _STDPRICES_ANNUAL_TABLE_RE.match(rel_path)
    if m_annual:
        return {
            "filename": filename,
            "url": canonical_url,
            "kind": "stdprices_table",
            "is_state": m_annual.group(1).lower() == "state",
        }
    return None


def discover_source_archives(
        session: requests.Session) -> list[dict[str, object]]:
    """Discovers upstream archives dynamically with fallback to SOURCE_ARCHIVES."""
    archives: list[dict[str, object]] = [dict(spec) for spec in SOURCE_ARCHIVES]
    seen_urls: set[str] = {str(spec["url"]).lower() for spec in archives}
    discovered_new = 0

    for page_url in TOPIC_DISCOVERY_PAGES:
        try:
            resp = session.get(page_url, timeout=REQUEST_TIMEOUT_SECONDS)
            resp.raise_for_status()
            html = getattr(resp, "text", "")
            if not isinstance(html, str) or not html:
                logging.warning(
                    "Empty or non-text HTML from %s; keeping baseline archives",
                    page_url,
                )
                continue
        except Exception as err:  # pylint: disable=broad-except
            logging.warning(
                "Dynamic discovery failed for %s (%s); keeping baseline archives",
                page_url,
                err,
            )
            continue

        for raw_link in sorted(set(_DOWNLOAD_LINK_RE.findall(html))):
            spec = classify_download_url(raw_link)
            if spec and str(spec["url"]).lower() not in seen_urls:
                seen_urls.add(str(spec["url"]).lower())
                archives.append(spec)
                discovered_new += 1
                logging.info("Discovered new upstream Dartmouth archive: %s",
                             spec["url"])

    if discovered_new:
        logging.info("Added %d newly discovered upstream archive(s)",
                     discovered_new)
    return archives


def _excel_col_index(cell_ref: str) -> int | None:
    """Converts an Excel cell reference such as 'C12' to a 0-based col index."""
    match = _CELL_COL_RE.match(cell_ref.upper())
    if not match:
        return None
    idx = 0
    for ch in match.group(1):
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def iter_xlsx_rows(xlsx_path: Path):
    """Yields normalized dict rows from data sheets in an .xlsx workbook."""
    with zipfile.ZipFile(xlsx_path, "r") as zf:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            sst_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in sst_root.findall("main:si", _XLSX_NS):
                shared_strings.append("".join(
                    t.text or "" for t in si.findall(".//main:t", _XLSX_NS)))

        sheet_files = sorted(name for name in zf.namelist()
                             if re.match(r"xl/worksheets/sheet\d+\.xml$", name))
        if not sheet_files:
            raise RuntimeError(f"No worksheets found in workbook {xlsx_path}")

        found_data_sheet = False
        for sheet_file in sheet_files:
            ws_root = ET.fromstring(zf.read(sheet_file))
            raw_rows: list[list[str]] = []
            for row_el in ws_root.findall(".//main:sheetData/main:row",
                                          _XLSX_NS):
                cells: list[str] = []
                for cell_el in row_el.findall("main:c", _XLSX_NS):
                    col_idx = _excel_col_index(cell_el.attrib.get("r", ""))
                    if col_idx is not None and col_idx >= len(cells):
                        cells.extend([""] * (col_idx - len(cells) + 1))
                    cell_type = cell_el.attrib.get("t", "")
                    val_el = cell_el.find("main:v", _XLSX_NS)
                    if val_el is not None and val_el.text is not None:
                        text_val = (shared_strings[int(val_el.text)]
                                    if cell_type == "s" else val_el.text)
                    else:
                        inline_el = cell_el.find("main:is", _XLSX_NS)
                        text_val = ("".join(
                            t.text or ""
                            for t in inline_el.findall(".//main:t", _XLSX_NS))
                                    if inline_el is not None else "")
                    if col_idx is not None:
                        cells[col_idx] = text_val
                    else:
                        cells.append(text_val)
                if any(c.strip() for c in cells):
                    raw_rows.append(cells)

            header_idx: int | None = None
            header: list[str] = []
            for idx, candidate in enumerate(raw_rows[:10]):
                normalized_hdr = [
                    h.lstrip("\ufeff").strip().lower() for h in candidate
                ]
                if "year" in normalized_hdr:
                    header_idx = idx
                    header = normalized_hdr
                    break
            if header_idx is None or header_idx + 1 >= len(raw_rows):
                continue
            found_data_sheet = True
            for values in raw_rows[header_idx + 1:]:
                row_dict = {
                    header[i]: (values[i] if i < len(values) else "").strip()
                    for i in range(len(header))
                    if header[i]
                }
                yield row_dict

        if not found_data_sheet:
            raise RuntimeError(
                f"No tabular Year header sheet found in {xlsx_path}")


def iter_rows_from_archive(archive_path: Path):
    """Yields normalized dict rows from a .csv.zip archive or .xlsx workbook."""
    lower_name = archive_path.name.lower()
    if lower_name.endswith(".zip"):
        yield from iter_csv_rows_from_zip(archive_path)
    elif lower_name.endswith(".xlsx"):
        yield from iter_xlsx_rows(archive_path)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")


def _normalize_year(raw_year: str) -> str | None:
    """Normalizes 4-digit year strings including Excel float years ('2016.0')."""
    cleaned = (raw_year or "").strip()
    if cleaned.isdigit() and len(cleaned) == 4:
        return cleaned
    try:
        as_float = float(cleaned)
    except ValueError:
        return None
    if math.isfinite(as_float) and as_float.is_integer():
        year_str = str(int(as_float))
        if len(year_str) == 4 and year_str.isdigit():
            return year_str
    return None


def _normalize_hsa_name(raw_name: str) -> str:
    return re.sub(r"\s+", " ", (raw_name or "").strip().upper())


def load_hsa_place_map(
    hsa_places_csv: Path = DEFAULT_HSA_PLACES_CSV,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Loads reviewed Dartmouth HSA code and name mappings to 7-digit DCIDs."""
    by_code: dict[str, list[str]] = {}
    by_name: dict[str, list[str]] = {}
    if not hsa_places_csv.exists():
        logging.warning("HSA place map %s not found; skipping HSA resolution",
                        hsa_places_csv)
        return by_code, by_name
    with hsa_places_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            code = (row.get("hsa_code") or "").strip()
            name = _normalize_hsa_name(row.get("hsa_name") or "")
            dcid = _strip_namespace_prefix(row.get("dcid") or "")
            if not dcid:
                continue
            if code:
                by_code.setdefault(code, []).append(dcid)
            if name:
                by_name.setdefault(name, []).append(dcid)
    return by_code, by_name


def extract_stdprices_observations(
        rows, is_state: bool, observations: dict[tuple[str, str, str],
                                                 str]) -> None:
    """Extracts Count_MedicareEnrollee and Mean Price observations."""
    for row in rows:
        if row.get("eventname", "").lower() != "stdprice_total":
            continue
        year = _normalize_year(row.get("year", ""))
        if not year:
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


def extract_stdprices_table_observations(
        rows, is_state: bool, observations: dict[tuple[str, str, str],
                                                 str]) -> None:
    """Extracts enrollees and price-adjusted Total reimbursements from wide tables."""
    price_col = (
        "price-adjusted total medicare reimbursements per enrollee (parts a and b)"
    )
    code_col = "state #" if is_state else "county #"
    for row in rows:
        year = _normalize_year(row.get("year", ""))
        if not year:
            continue
        place = format_place_dcid(row.get(code_col, ""), is_state=is_state)
        if not place:
            continue
        pop_val = clean_numeric_value(row.get("medicare enrollees", ""))
        if pop_val is not None:
            observations[(year, place, "MedicareEnrollee_Count")] = pop_val
        price_val = clean_numeric_value(row.get(price_col, ""))
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
        year = _normalize_year(row.get("year", ""))
        if not year:
            continue
        place = format_place_dcid(row.get("geo_code", ""), is_state=is_state)
        if not place:
            continue
        pop_val = clean_numeric_value(row.get("population", ""))
        if pop_val is not None:
            observations[(year, place, sv_key)] = pop_val


def extract_hsa_mortality_observations(
    rows,
    observations: dict[tuple[str, str, str], str],
    hsa_place_map: tuple[dict[str, list[str]], dict[str, list[str]]] |
    None = None,
) -> None:
    """Extracts 7-digit HSA City/Town/Village Medicare enrollee denominators."""
    by_code, by_name = (hsa_place_map
                        if hsa_place_map is not None else load_hsa_place_map())
    for row in rows:
        year = _normalize_year(row.get("year", ""))
        if not year:
            continue
        raw_code = (row.get("hsa #") or row.get("geo_code") or "").strip()
        code_str = ""
        if raw_code:
            try:
                code_int = int(float(raw_code))
                if code_int in (999, 99999) or code_int <= 0:
                    continue
                code_str = str(code_int)
            except (ValueError, OverflowError):
                code_str = ""
        hsa_name = _normalize_hsa_name(
            row.get("hsa name") or row.get("geo_name") or "")
        if hsa_name in ("UNITED STATES", "US- UNITED STATES"):
            continue
        dcids = by_code.get(code_str) or by_name.get(hsa_name)
        if not dcids:
            continue
        pop_val = clean_numeric_value(
            row.get("medicare enrollees") or row.get("population") or "")
        if pop_val is not None:
            for dcid in dcids:
                observations[(year, dcid, "MedicareEnrollee_Count")] = pop_val


def process_archive(
    archive_path: Path,
    kind: str,
    is_state: bool,
    observations: dict[tuple[str, str, str], str],
    hsa_place_map: tuple[dict[str, list[str]], dict[str, list[str]]] |
    None = None,
) -> None:
    """Dispatches a downloaded archive or workbook to the appropriate extractor."""
    rows = iter_rows_from_archive(archive_path)
    if kind == "stdprices":
        extract_stdprices_observations(rows,
                                       is_state=is_state,
                                       observations=observations)
    elif kind == "stdprices_table":
        extract_stdprices_table_observations(rows,
                                             is_state=is_state,
                                             observations=observations)
    elif kind == "hedis":
        extract_hedis_observations(rows,
                                   is_state=is_state,
                                   observations=observations)
    elif kind == "hsa_mortality":
        extract_hsa_mortality_observations(rows,
                                           observations=observations,
                                           hsa_place_map=hsa_place_map)
    else:
        raise ValueError(f"Unknown archive kind: {kind}")


def write_cleaned_csv(
    observations: dict[tuple[str, str, str], str],
    output_path: Path,
    allow_empty: bool = False,
) -> None:
    """Writes normalized observations to output_path atomically."""
    if not observations and not allow_empty:
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


def should_supersede_historical_row(
    year: str,
    place: str,
    sv: str,
    raw_value: str,
    live_observations: dict[tuple[str, str, str], str] | None = None,
) -> bool:
    """Returns True when a historical row is corrupted or superseded by live data.

    Specifically:
    1. Drops legacy CNS TFRecord sub-service slices on dc/rn90czcrqcv06 where
       value < $1,000 (comma-quoted >= $1,000 Total values were dropped during
       cl/954587569 StatPop conversion).
    2. Supersedes 2003-2009 5-digit county Count_MedicareEnrollee rows (which
       used a 20% sample in legacy tables) whenever the unified 100% count is
       present in live_observations, while preserving retired counties absent
       from live archives.
    """
    if sv == "dc/rn90czcrqcv06":
        cleaned_val = clean_numeric_value(raw_value)
        if cleaned_val is None or float(cleaned_val) < 1000.0:
            return True
    if (live_observations is not None and sv == "Count_MedicareEnrollee" and
            "2003" <= year <= "2009" and place.startswith("geoId/") and
            len(place) == 11 and
        (year, place, "MedicareEnrollee_Count") in live_observations):
        return True
    return False


def load_historical_observation_keys(
    historical_csv_paths: list[Path],
    live_observations: dict[tuple[str, str, str], str] | None = None,
    rewrite_staged: bool = False,
) -> set[tuple[str, str, str]]:
    """Loads retained (year, place_bare, sv_bare) keys and optionally prunes CSVs."""
    keys: set[tuple[str, str, str]] = set()
    for csv_path in historical_csv_paths:
        retained_rows: list[list[str]] = []
        superseded = 0
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [
                "observationDate",
                "observationAbout",
                "variableMeasured",
                "value",
                "observationPeriod",
            ])
            for row in reader:
                year = _strip_namespace_prefix(row.get("observationDate", ""))
                place = _strip_namespace_prefix(row.get("observationAbout", ""))
                sv = _strip_namespace_prefix(row.get("variableMeasured", ""))
                raw_val = row.get("value", "")
                if should_supersede_historical_row(
                        year=year,
                        place=place,
                        sv=sv,
                        raw_value=raw_val,
                        live_observations=live_observations,
                ):
                    superseded += 1
                    continue
                if year and place and sv:
                    keys.add((year, place, sv))
                if rewrite_staged:
                    retained_rows.append(
                        [row.get(col, "") for col in fieldnames])
        if rewrite_staged and superseded > 0:
            buf = io.StringIO()
            writer = csv.writer(buf, lineterminator="\n")
            writer.writerow(fieldnames)
            writer.writerows(retained_rows)
            atomic_write_bytes(csv_path, buf.getvalue().encode("utf-8"))
            logging.info(
                "Pruned %d superseded/corrupted row(s) from staged %s "
                "(retained %d rows)",
                superseded,
                csv_path,
                len(retained_rows),
            )
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
    hsa_places_csv: Path = DEFAULT_HSA_PLACES_CSV,
) -> Path:
    """Downloads live archives, stages/prunes historical CSV, writes net-new CSV."""
    raw_dir = output_dir / "raw"
    cleaned_path = output_dir / "cleaned" / "dartmouth_atlas_medicare.csv"
    observations: dict[tuple[str, str, str], str] = {}
    hsa_place_map = load_hsa_place_map(hsa_places_csv)

    with create_session() as session:
        archives = discover_source_archives(session)
        for spec in archives:
            dest_path = raw_dir / str(spec["filename"])
            download_file(session, str(spec["url"]), dest_path)
            process_archive(
                dest_path,
                kind=str(spec["kind"]),
                is_state=bool(spec["is_state"]),
                observations=observations,
                hsa_place_map=hsa_place_map,
            )

    if not observations:
        raise RuntimeError(
            "No observations extracted from Dartmouth Atlas sources")

    historical_keys: set[tuple[str, str, str]] = set()
    if historical_gcs_dir and historical_output_dir is not None:
        copied_csvs = copy_historical_files_from_gcs(
            historical_gcs_dir=historical_gcs_dir,
            historical_output_dir=historical_output_dir,
        )
        historical_keys = load_historical_observation_keys(
            copied_csvs,
            live_observations=observations,
            rewrite_staged=True,
        )

    net_new_observations = filter_out_historical_observations(
        observations, historical_keys)
    write_cleaned_csv(net_new_observations, cleaned_path, allow_empty=True)
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
