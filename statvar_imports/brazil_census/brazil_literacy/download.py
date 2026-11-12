# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Automated download script for Brazil Census Literacy data.

Downloads literacy and illiteracy counts and rates from official IBGE SIDRA REST API
(Tables 9952, 9543, and 9542 across national, regional, state, and municipal levels)
and merges historical 1940, 2000, and 2010 raw input files from GCS
(gs://unresolved_mcf/country/brazil/input_files/), integrating them into clean
tabular CSV input files.
"""

import io
import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from absl import app, flags, logging
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

SIDRA_BASE_URL = "https://apisidra.ibge.gov.br"
# Table 9952: População de 15 anos ou mais de idade por alfabetização e sexo (2022+ Census)
# Split by sex (c2/6794 Total, c2/4 Homens, c2/5 Mulheres) to stay under SIDRA's 50,000-row API cap across n6/all.
TABLE_9952_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/9952/n1/all/n2/all/n3/all"
    f"/v/950/p/all/c59/all/c2/all/c58/0/c2661/0/c1/0?formato=json")
TABLE_9952_API_URLS = [
    (
        "sidra_9952_total_n6.json",
        f"{SIDRA_BASE_URL}/values/t/9952/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c59/all/c2/6794/c58/0/c2661/0/c1/0?formato=json",
    ),
    (
        "sidra_9952_male_n6.json",
        f"{SIDRA_BASE_URL}/values/t/9952/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c59/all/c2/4/c58/0/c2661/0/c1/0?formato=json",
    ),
    (
        "sidra_9952_female_n6.json",
        f"{SIDRA_BASE_URL}/values/t/9952/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c59/all/c2/5/c58/0/c2661/0/c1/0?formato=json",
    ),
]

# Table 9543 & Table 9542 for 2022 literacy & illiteracy rates across all territorial levels (n1/n2/n3/n6)
TABLE_9543_RATES_URL = (
    f"{SIDRA_BASE_URL}/values/t/9543/n1/all/n2/all/n3/all/n6/all"
    f"/v/2513/p/all/c2/6794/c86/95251/c287/100362,93086?formato=json")
TABLE_9542_RATES_URLS = [
    (
        "sidra_9542_rates_p1a.json",
        f"{SIDRA_BASE_URL}/values/t/9542/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c2/6794/c86/95251/c59/93024/c287/100362,93086,93087?formato=json",
    ),
    (
        "sidra_9542_rates_p1b.json",
        f"{SIDRA_BASE_URL}/values/t/9542/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c2/6794/c86/95251/c59/1023,1024/c287/100362,93086,93087?formato=json",
    ),
    (
        "sidra_9542_rates_p2a.json",
        f"{SIDRA_BASE_URL}/values/t/9542/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c2/6794/c86/95251/c59/93024/c287/2999,9482,9483,9484,3000?formato=json",
    ),
    (
        "sidra_9542_rates_p2b.json",
        f"{SIDRA_BASE_URL}/values/t/9542/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c2/6794/c86/95251/c59/1024/c287/2999,9482,9483,9484,3000?formato=json",
    ),
    (
        "sidra_9542_rates_p3a.json",
        f"{SIDRA_BASE_URL}/values/t/9542/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c2/6794/c86/95251/c59/93024/c287/6613,6614,6615,6616,6617?formato=json",
    ),
    (
        "sidra_9542_rates_p3b.json",
        f"{SIDRA_BASE_URL}/values/t/9542/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c2/6794/c86/95251/c59/1024/c287/6613,6614,6615,6616,6617?formato=json",
    ),
]

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_INPUT_FILE = "country/brazil/input_files/Brazil_1940_Literate.xls"

FLAGS = flags.FLAGS
if "output_file" not in FLAGS:
    flags.DEFINE_string(
        "output_file",
        "",
        "Output CSV file path. Defaults to input_files/brazil_literacy.csv.",
    )
if "fallback_to_cached" not in FLAGS:
    flags.DEFINE_boolean(
        "fallback_to_cached",
        False,
        "Whether to fallback to locally cached CSV if live download fails.",
    )

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, "brazil_literacy.csv")


def get_robust_session() -> requests.Session:
    """Configures a requests Session with retries and connection pooling."""
    session = requests.Session()
    retries = Retry(
        total=10,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def _get_raw_dir(target_path: str) -> str:
    """Returns the directory for archiving raw downloaded payloads."""
    if os.path.abspath(target_path) == os.path.abspath(DEFAULT_OUTPUT_FILE):
        raw_dir = os.path.join(SCRIPT_DIR, "raw_files")
    else:
        raw_dir = os.path.join(os.path.dirname(os.path.abspath(target_path)),
                               "raw_files")
    os.makedirs(raw_dir, exist_ok=True)
    return raw_dir


def fetch_sidra_data(
    session: requests.Session,
    url: str,
    raw_file_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetches raw JSON payload from IBGE SIDRA REST API."""
    logging.info(f"Dispatching outbound HTTP request: url={url}")
    res = session.get(url, timeout=90)
    res.raise_for_status()
    raw_json = res.json()
    if not isinstance(raw_json, list) or len(raw_json) < 2:
        raise RuntimeError(
            f"Invalid or empty response payload from SIDRA API: {url}")
    if raw_file_path:
        with open(raw_file_path, "w", encoding="utf-8") as f:
            json.dump(raw_json, f, ensure_ascii=False)
    return raw_json


def parse_raw_literacy_xls(content_bytes: bytes) -> List[Dict[str, Any]]:
    """Parses raw IBGE Table 10 literacy XLS workbook across Total, Homens, Mulheres sheets."""
    rows: List[Dict[str, Any]] = []
    xl = pd.ExcelFile(io.BytesIO(content_bytes))
    sheet_sex_map = {
        "T10_1940A": "Total",
        "T10_1940B": "Homens",
        "T10_1940C": "Mulheres",
    }
    for sheet_name, sex in sheet_sex_map.items():
        if sheet_name not in xl.sheet_names:
            continue
        df = pd.read_excel(xl, sheet_name=sheet_name, header=None)
        if len(df) <= 6:
            continue
        for r_idx in range(8, len(df)):
            r = df.iloc[r_idx]
            place = str(r.iloc[0]).strip()
            place_lower = place.lower()
            if (not place or pd.isna(r.iloc[0]) or
                ("fonte" in place_lower and "fonte boa" not in place_lower) or
                    "nota" in place_lower or "placename" in place_lower):
                continue
            if place == "Brasil":
                place = "Brazil"

            try:
                tot_val = int(round(float(r.iloc[1])))
                rows.append({
                    "Ano": 1940,
                    "Localidade": place,
                    "FaixaEtaria": "10 anos ou mais",
                    "Raca": "Total",
                    "StatusAlfabetizacao": "Total",
                    "Sexo": sex,
                    "Populacao": tot_val,
                })
            except (ValueError, TypeError):
                pass

            try:
                lit_val = int(round(float(r.iloc[2])))
                rows.append({
                    "Ano": 1940,
                    "Localidade": place,
                    "FaixaEtaria": "10 anos ou mais",
                    "Raca": "Total",
                    "StatusAlfabetizacao": "Alfabetizada",
                    "Sexo": sex,
                    "Populacao": lit_val,
                })
            except (ValueError, TypeError):
                pass

            try:
                illit_val = int(round(float(r.iloc[3])))
                rows.append({
                    "Ano": 1940,
                    "Localidade": place,
                    "FaixaEtaria": "10 anos ou mais",
                    "Raca": "Total",
                    "StatusAlfabetizacao": "Analfabeta",
                    "Sexo": sex,
                    "Populacao": illit_val,
                })
            except (ValueError, TypeError):
                pass
    if not rows:
        raise ValueError("Parsed 0 rows from 1940 literacy XLS workbook.")
    return rows


def fetch_raw_input_files(
        raw_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Reads raw 1940 literacy input file from GCS input_files."""
    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(GCS_INPUT_FILE)
    content = blob.download_as_bytes()
    if raw_dir:
        with open(os.path.join(raw_dir, "Brazil_1940_Literate.xls"), "wb") as f:
            f.write(content)
    rows = parse_raw_literacy_xls(content)
    logging.info(f"Parsed {len(rows)} rows from GCS raw literacy input file.")
    return rows


def parse_2010_illiterate_race_xls(
        content_bytes: bytes) -> List[Dict[str, Any]]:
    """Parses Brazil_2010_llliterate_race.xls across all sheets and municipalities."""
    sheet_race = {
        "tab3A": "Total",
        "tab3B": "Branca",
        "tab3C": "Preta",
        "tab3D": "Parda",
        "tab3E": "Amarela",
        "tab3F": "Indígena",
    }
    col_ages = {
        3: "15 anos ou mais",
        5: "15 a 24 anos",
        7: "25 a 39 anos",
        9: "40 a 59 anos",
        11: "60 anos ou mais",
    }
    rows = []
    xl = pd.ExcelFile(io.BytesIO(content_bytes))
    for sheet, race in sheet_race.items():
        if sheet not in xl.sheet_names:
            continue
        df = pd.read_excel(xl, sheet_name=sheet, header=None, skiprows=4)
        for idx in range(6, len(df)):
            code = str(df.iloc[idx, 0]).strip()
            code_lower = code.lower()
            if pd.isna(df.iloc[idx, 0]) or not code or code == "nan":
                continue
            if ("fonte" in code_lower and
                    "fonte boa" not in code_lower) or "nota" in code_lower:
                continue
            place = "Brazil" if code == "Brazil" else code
            for c_idx, age in col_ages.items():
                val = df.iloc[idx, c_idx]
                if pd.isna(val) or str(val).strip() in [
                        "-", "...", "..", "X", ""
                ]:
                    continue
                try:
                    val_int = int(round(float(val)))
                    rows.append({
                        "Ano": 2010,
                        "Localidade": place,
                        "FaixaEtaria": age,
                        "Raca": race,
                        "StatusAlfabetizacao": "Analfabeta",
                        "Sexo": "Total",
                        "Populacao": val_int,
                    })
                except (ValueError, TypeError):
                    continue
    if not rows:
        raise ValueError("Parsed 0 rows from Brazil_2010_llliterate_race.xls.")
    return rows


def fetch_2010_illiterate_race(
        raw_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Loads Brazil_2010_llliterate_race.xls from GCS."""
    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(
        "country/brazil/input_files/Brazil_2010_llliterate_race.xls")
    content = blob.download_as_bytes()
    if raw_dir:
        with open(os.path.join(raw_dir, "Brazil_2010_llliterate_race.xls"),
                  "wb") as f:
            f.write(content)
    return parse_2010_illiterate_race_xls(content)


def parse_2000_literacy_xls(content_bytes: bytes) -> List[Dict[str, Any]]:
    """Parses a single 2000 municipal literacy XLS workbook."""
    col_map = {
        1: ("10 anos ou mais", "Total"),
        2: ("10 anos ou mais", "Alfabetizada"),
        4: ("10 a 14 anos", "Total"),
        5: ("10 a 14 anos", "Alfabetizada"),
        7: ("15 a 19 anos", "Total"),
        8: ("15 a 19 anos", "Alfabetizada"),
        10: ("20 anos ou mais", "Total"),
        11: ("20 anos ou mais", "Alfabetizada"),
    }
    rows: List[Dict[str, Any]] = []
    df = pd.read_excel(io.BytesIO(content_bytes), header=None, skiprows=3)
    muni_start = None
    for idx in range(6, len(df)):
        val = df.iloc[idx, 0]
        if pd.notna(val) and "munic" in str(val).lower():
            muni_start = idx + 1
            break
    if muni_start is None:
        muni_start = 6
    code_col = 13 if df.shape[1] > 13 else None
    if code_col is None:
        for col_i in range(df.shape[1]):
            for row_i in range(min(8, len(df))):
                if ("código" in str(df.iloc[row_i, col_i]).lower() or
                        "codigo" in str(df.iloc[row_i, col_i]).lower()):
                    code_col = col_i
                    break
            if code_col is not None:
                break

    for idx in range(len(df)):
        val0 = str(df.iloc[idx, 0]).strip()
        if val0 == "Total":
            raw_code = (str(df.iloc[idx, code_col]).strip() if
                        (code_col is not None and
                         code_col < df.shape[1]) else "")
            if raw_code and raw_code.isnumeric():
                for c_idx, (age, status) in col_map.items():
                    if c_idx < df.shape[1]:
                        val = df.iloc[idx, c_idx]
                        if pd.notna(val) and str(val).strip() not in [
                                "-",
                                "...",
                                "..",
                                "X",
                                "",
                        ]:
                            try:
                                val_int = int(round(float(val)))
                                rows.append({
                                    "Ano": 2000,
                                    "Localidade": raw_code,
                                    "FaixaEtaria": age,
                                    "Raca": "Total",
                                    "StatusAlfabetizacao": status,
                                    "Sexo": "Total",
                                    "Populacao": val_int,
                                })
                            except (ValueError, TypeError):
                                pass
            break

    for idx in range(muni_start, len(df)):
        raw_code = (str(df.iloc[idx, code_col]).strip() if
                    (code_col is not None and code_col < df.shape[1]) else "")
        place = (raw_code if (raw_code and raw_code.isnumeric() and
                              len(raw_code) == 7) else str(df.iloc[idx,
                                                                   0]).strip())
        place_lower = place.lower()
        if (not place or pd.isna(df.iloc[idx, 0]) or place == "nan" or
            ("fonte" in place_lower and "fonte boa" not in place_lower) or
                "nota" in place_lower):
            continue
        for c_idx, (age, status) in col_map.items():
            if c_idx >= df.shape[1]:
                continue
            val = df.iloc[idx, c_idx]
            if pd.isna(val) or str(val).strip() in ["-", "...", "..", "X", ""]:
                continue
            try:
                val_int = int(round(float(val)))
                rows.append({
                    "Ano": 2000,
                    "Localidade": place,
                    "FaixaEtaria": age,
                    "Raca": "Total",
                    "StatusAlfabetizacao": status,
                    "Sexo": "Total",
                    "Populacao": val_int,
                })
            except (ValueError, TypeError):
                continue
    if not rows:
        raise ValueError("Parsed 0 rows from 2000 literacy XLS workbook.")
    return rows


def parse_2000_literacy_files() -> List[Dict[str, Any]]:
    """Loads 2000 municipal literacy workbooks across all states from GCS."""
    from google.cloud import storage

    rows: List[Dict[str, Any]] = []
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    blobs = list(
        bucket.list_blobs(
            prefix="country/brazil/input_files/Brazil_2000_literacy_input"))
    for b in blobs:
        if b.name.lower().endswith(".xls"):
            rows.extend(parse_2000_literacy_xls(b.download_as_bytes()))
    if not rows:
        raise RuntimeError("No 2000 literacy records loaded from GCS.")
    return rows


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census literacy data across past, present, and future censuses."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    raw_dir = _get_raw_dir(target_path)
    all_rows: List[Dict[str, Any]] = []

    try:
        # 1. Primary Source: Live SIDRA API (Table 9952 across all territorial levels incl. municipalities)
        for fname, url in TABLE_9952_API_URLS:
            raw_sidra = fetch_sidra_data(session,
                                         url,
                                         raw_file_path=os.path.join(
                                             raw_dir, fname))
            logging.info(
                f"Retrieved {len(raw_sidra) - 1} records from SIDRA Table 9952: {url}"
            )
            for r in raw_sidra[1:]:
                val_str = r.get("V")
                if val_str in ["-", "...", "..", "X", None, ""]:
                    continue
                try:
                    val = int(round(float(val_str)))
                except (ValueError, TypeError):
                    continue

                year_str = str(r.get("D3N", "2022")).strip()
                try:
                    year = int(year_str)
                except ValueError:
                    continue

                if str(r.get("NC", "")).strip() == "6":
                    loc = str(r.get("D1C", "")).strip()
                else:
                    loc = str(r.get("D1N", "")).strip()
                    if loc == "Brasil":
                        loc = "Brazil"

                status_raw = str(r.get("D4N", "Total")).strip()
                status = "Total"
                if "Alfabetizadas" in status_raw or "Alfabetizada" in status_raw:
                    status = "Alfabetizada"
                elif "Não alfabetizadas" in status_raw or "Analfabeta" in status_raw:
                    status = "Analfabeta"

                sexo_raw = str(r.get("D5N", "Total")).strip()
                sexo = "Total"
                if "Homens" in sexo_raw:
                    sexo = "Masculino"
                elif "Mulheres" in sexo_raw:
                    sexo = "Feminino"

                all_rows.append({
                    "Ano": year,
                    "Localidade": loc,
                    "FaixaEtaria": "15 anos ou mais",
                    "Raca": "Total",
                    "StatusAlfabetizacao": status,
                    "Sexo": sexo,
                    "Populacao": val,
                })

        # 2. Historical data from raw input files in GCS (1940)
        raw_rows = fetch_raw_input_files(raw_dir=raw_dir)
        all_rows.extend(raw_rows)

        # 3. 2010 Illiterate by Race & Age (all 5,564 municipalities)
        illit_2010_rows = fetch_2010_illiterate_race(raw_dir=raw_dir)
        all_rows.extend(illit_2010_rows)

        # 4. 2000 Municipal Literacy (all 5,564 municipalities)
        lit_2000_rows = parse_2000_literacy_files()
        all_rows.extend(lit_2000_rows)

    except Exception as e:
        if fallback_to_cached and os.path.isfile(target_path):
            logging.warning(
                f"Download failed ({e}). Falling back to cached copy: {target_path}"
            )
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(
            f"Error downloading Brazil Census literacy data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No literacy records retrieved from data sources.")

    df = pd.DataFrame(all_rows).drop_duplicates(
        subset=[
            "Ano",
            "Localidade",
            "FaixaEtaria",
            "Raca",
            "StatusAlfabetizacao",
            "Sexo",
        ],
        keep="last",
    )
    target_dir = os.path.dirname(os.path.abspath(target_path))
    os.makedirs(target_dir, exist_ok=True)

    with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=target_dir,
            suffix=".csv",
            encoding="utf-8",
            newline="",
    ) as tmp_file:
        tmp_path = tmp_file.name
        df.to_csv(tmp_file, index=False, encoding="utf-8")

    if not os.path.isfile(tmp_path) or os.path.getsize(tmp_path) == 0:
        if os.path.isfile(tmp_path):
            os.remove(tmp_path)
        raise RuntimeError(
            f"Atomic CSV write failed: {tmp_path} is missing or empty.")

    os.replace(tmp_path, target_path)
    logging.info(f"Wrote {len(df)} records to {target_path}")

    ensure_literacy_rates_file(session=session, raw_dir=raw_dir)

    return target_path


def _write_rates_atomically(combined: pd.DataFrame, rates_out: str) -> None:
    """Writes literacy rates CSV atomically."""
    out_dir = os.path.dirname(os.path.abspath(rates_out))
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=out_dir,
            suffix=".csv",
            encoding="utf-8",
            newline="",
    ) as tmp_file:
        tmp_path = tmp_file.name
        combined.to_csv(tmp_file, index=False, encoding="utf-8")
    os.replace(tmp_path, rates_out)


def _load_places_resolved_map() -> Dict[str, str]:
    """Loads ../brazil_places_resolved.csv mapping raw place strings/codes to dcid:<dcid>."""
    places_csv = os.path.join(SCRIPT_DIR, "..", "brazil_places_resolved.csv")
    mapping: Dict[str, str] = {}
    if os.path.isfile(places_csv):
        df = pd.read_csv(places_csv, dtype=str)
        for _, row in df.iterrows():
            name = str(row.get("name", "")).strip()
            dcid = str(row.get("dcid", "")).strip()
            if name and dcid:
                mapping[name] = dcid if dcid.startswith(
                    "dcid:") else f"dcid:{dcid}"
    return mapping


def _fetch_2022_literacy_rates_rows(
    session: requests.Session,
    raw_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetches and computes 2022 literacy & illiteracy rate observations across all territorial levels."""
    places_map = _load_places_resolved_map()
    rows_2022: List[Dict[str, Any]] = []

    def resolve_loc(r: Dict[str, Any]) -> Optional[str]:
        if str(r.get("NC", "")).strip() == "6":
            raw_loc = str(r.get("D1C", "")).strip()
        else:
            raw_loc = str(r.get("D1N", "")).strip()
            if raw_loc == "Brasil":
                raw_loc = "Brazil"
        return places_map.get(raw_loc)

    # 1. Table 9543: 15+ literacy rate (c287=100362) and 15-19 literacy rate (c287=93086)
    raw_9543 = fetch_sidra_data(
        session,
        TABLE_9543_RATES_URL,
        raw_file_path=os.path.join(raw_dir, "sidra_9543_rates.json")
        if raw_dir else None,
    )
    for r in raw_9543[1:]:
        val_str = r.get("V")
        if val_str in ["-", "...", "..", "X", None, ""]:
            continue
        try:
            rate_val = float(val_str)
        except (ValueError, TypeError):
            continue
        dcid = resolve_loc(r)
        if not dcid:
            continue
        c287 = str(r.get("D6C", "")).strip()
        if c287 == "100362":
            rows_2022.append({
                "observationAbout":
                    dcid,
                "observationDate":
                    2022,
                "variableMeasured":
                    "dcid:Count_Person_Illiterate_AsAFractionOf_Count_Person",
                "value":
                    round(100.0 - rate_val, 2),
                "unit":
                    "dcs:Percent",
                "scalingFactor":
                    100,
            })
        elif c287 == "93086":
            rows_2022.append({
                "observationAbout":
                    dcid,
                "observationDate":
                    2022,
                "variableMeasured":
                    "dcid:Count_Person_15To19Years_Literate_AsAFractionOf_Count_Person_15To19Years",
                "value":
                    round(rate_val, 2),
                "unit":
                    "dcs:Percent",
                "scalingFactor":
                    100,
            })

    # 2. Table 9542: Counts by age and literacy status for exact 20+, 15-24, 25-59, and 60+ rate calculation
    counts: Dict[str, Dict[str, Dict[str, int]]] = {}
    for fname, url in TABLE_9542_RATES_URLS:
        raw_9542 = fetch_sidra_data(
            session,
            url,
            raw_file_path=os.path.join(raw_dir, fname) if raw_dir else None,
        )
        for r in raw_9542[1:]:
            val_str = r.get("V")
            if val_str in ["-", "...", "..", "X", None, ""]:
                continue
            try:
                cnt_val = int(round(float(val_str)))
            except (ValueError, TypeError):
                continue
            dcid = resolve_loc(r)
            if not dcid:
                continue
            c59 = str(r.get("D6C", "")).strip()
            c287 = str(r.get("D7C", "")).strip()
            counts.setdefault(dcid, {}).setdefault(c59, {})[c287] = cnt_val

    single_60_64 = ["6613", "6614", "6615", "6616", "6617"]
    broad_25_64 = ["2999", "9482", "9483", "9484"]

    for dcid, by_status in counts.items():
        tot = by_status.get("93024", {})
        lit = by_status.get("1023", {})
        illit = by_status.get("1024", {})

        if ("100362" in tot and "93086" in tot and "100362" in lit and
                "93086" in lit):
            denom_20 = tot["100362"] - tot["93086"]
            num_20 = lit["100362"] - lit["93086"]
            if denom_20 > 0:
                rows_2022.append({
                    "observationAbout":
                        dcid,
                    "observationDate":
                        2022,
                    "variableMeasured":
                        "dcid:Count_Person_20OrMoreYears_Literate_AsAFractionOf_Count_Person_20OrMoreYears",
                    "value":
                        round(num_20 * 100.0 / denom_20, 2),
                    "unit":
                        "dcs:Percent",
                    "scalingFactor":
                        100,
                })

        if ("93086" in tot and "93087" in tot and "93086" in illit and
                "93087" in illit):
            denom_15_24 = tot["93086"] + tot["93087"]
            num_15_24 = illit["93086"] + illit["93087"]
            if denom_15_24 > 0:
                rows_2022.append({
                    "observationAbout":
                        dcid,
                    "observationDate":
                        2022,
                    "variableMeasured":
                        "dcid:Count_Person_15To24Years_Illiterate_AsAFractionOf_Count_Person_15To24Years",
                    "value":
                        round(num_15_24 * 100.0 / denom_15_24, 2),
                    "unit":
                        "dcs:Percent",
                    "scalingFactor":
                        100,
                })

        if all(c in tot for c in broad_25_64 + ["3000"]) and all(
                c in illit for c in broad_25_64 + ["3000"]):
            tot_60_64 = sum(tot.get(c, 0) for c in single_60_64)
            illit_60_64 = sum(illit.get(c, 0) for c in single_60_64)
            denom_25_59 = sum(tot[c] for c in broad_25_64) - tot_60_64
            num_25_59 = sum(illit[c] for c in broad_25_64) - illit_60_64
            if denom_25_59 > 0:
                rows_2022.append({
                    "observationAbout":
                        dcid,
                    "observationDate":
                        2022,
                    "variableMeasured":
                        "dcid:Count_Person_25To59Years_Illiterate_AsAFractionOf_Count_Person_25To59Years",
                    "value":
                        round(num_25_59 * 100.0 / denom_25_59, 2),
                    "unit":
                        "dcs:Percent",
                    "scalingFactor":
                        100,
                })

            denom_60_plus = tot["3000"] + tot_60_64
            num_60_plus = illit["3000"] + illit_60_64
            if denom_60_plus > 0:
                rows_2022.append({
                    "observationAbout":
                        dcid,
                    "observationDate":
                        2022,
                    "variableMeasured":
                        "dcid:Count_Person_60OrMoreYears_Illiterate_AsAFractionOf_Count_Person_60OrMoreYears",
                    "value":
                        round(num_60_plus * 100.0 / denom_60_plus, 2),
                    "unit":
                        "dcs:Percent",
                    "scalingFactor":
                        100,
                })

    return rows_2022


def ensure_literacy_rates_file(
    rates_out: Optional[str] = None,
    session: Optional[requests.Session] = None,
    raw_dir: Optional[str] = None,
) -> None:
    """Generates fractional literacy rate observations across 2000, 2010, and 2022."""
    from google.cloud import storage

    target_rates = rates_out or os.path.join(SCRIPT_DIR,
                                             "brazil_literacy_rates.csv")
    active_session = session or get_robust_session()

    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    b1 = bucket.blob(
        "country/brazil/input_files/Brazil_2000_2010_Illiterate_age.csv")
    b2 = bucket.blob("country/brazil/input_files/Brazil_2000_literate.csv")
    bytes1 = b1.download_as_bytes()
    bytes2 = b2.download_as_bytes()
    if raw_dir:
        with open(os.path.join(raw_dir, "Brazil_2000_2010_Illiterate_age.csv"),
                  "wb") as f:
            f.write(bytes1)
        with open(os.path.join(raw_dir, "Brazil_2000_literate.csv"), "wb") as f:
            f.write(bytes2)
    df1 = pd.read_csv(io.BytesIO(bytes1))
    df2 = pd.read_csv(io.BytesIO(bytes2))
    df2_rates = df2[df2["unit"] == "dcs:Percent"]
    hist_df = pd.concat([df1, df2_rates], ignore_index=True)
    hist_df["scalingFactor"] = 100

    rows_2022 = _fetch_2022_literacy_rates_rows(active_session, raw_dir=raw_dir)
    df_2022 = pd.DataFrame(rows_2022)
    combined = pd.concat([hist_df, df_2022], ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["observationAbout", "observationDate", "variableMeasured"],
        keep="last",
    )
    _write_rates_atomically(combined, target_rates)
    logging.info(
        f"Generated {len(combined)} rows in {target_rates} (historical GCS + live 2022 SIDRA)"
    )


def main(argv: List[str]) -> None:
    if len(argv) > 1:
        raise ValueError(f"Unrecognized command-line arguments: {argv[1:]}")

    target_file = FLAGS.output_file or DEFAULT_OUTPUT_FILE
    session = get_robust_session()
    saved_file = download_all_years(
        session=session,
        output_file=target_file,
        fallback_to_cached=FLAGS.fallback_to_cached,
    )
    logging.info(f"Literacy download completed successfully: {saved_file}")


if __name__ == "__main__":
    app.run(main)
