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
"""Automated download script for Brazil Census Population by Residence (Urban/Rural) data.

Downloads resident population by urban and rural residence classification from official IBGE sources:
1. Live IBGE SIDRA REST API:
   - Table 9923 (2022 Census População residente por situação do domicílio across n1/n2/n3/n6)
   - Table 608 (2010 Census População residente por situação do domicílio e sexo across n1/n2/n3/n6)
2. Historical census files from GCS (1940, 1991, 2000).
"""

import io
import json
import os
import shutil
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from absl import app, flags, logging
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

SIDRA_BASE_URL = "https://apisidra.ibge.gov.br"
# Table 9923: População residente por situação do domicílio (2022)
# Includes municipal level (n6/all) alongside macro levels (n1, n2, n3).
TABLE_9923_API_URL = f"{SIDRA_BASE_URL}/values/t/9923/n1/all/n2/all/n3/all/n6/all/v/93/p/all/c1/all?formato=json"

# Table 608: População residente por situação do domicílio e sexo (2010)
# Split into two queries to stay within SIDRA's 50,000 value limit:
# 1) Total sex across all levels (national, regional, state, municipal) = ~16.8k values
# 2) Male and Female sex split across macro levels (national, regional, state) = ~200 values
TABLE_608_API_URLS = [
    (
        "sidra_608_total_n6.json",
        f"{SIDRA_BASE_URL}/values/t/608/n1/all/n2/all/n3/all/n6/all/v/93/p/all/c1/all/c2/0?formato=json",
    ),
    (
        "sidra_608_sex_macro.json",
        f"{SIDRA_BASE_URL}/values/t/608/n1/all/n2/all/n3/all/v/93/p/all/c1/all/c2/4,5?formato=json",
    ),
]
TABLE_608_API_URL = TABLE_608_API_URLS[0][1]

FLAGS = flags.FLAGS
if "output_file" not in FLAGS:
    flags.DEFINE_string(
        "output_file",
        "",
        "Output CSV file path. Defaults to input_files/brazil_population_by_residence.csv.",
    )
if "fallback_to_cached" not in FLAGS:
    flags.DEFINE_boolean(
        "fallback_to_cached",
        False,
        "Whether to fallback to locally cached CSV if live download fails.",
    )

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR,
                                   "brazil_population_by_residence.csv")


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
    """Returns a clean directory for archiving raw downloaded payloads."""
    if os.path.abspath(target_path) == os.path.abspath(DEFAULT_OUTPUT_FILE):
        raw_dir = os.path.join(SCRIPT_DIR, "raw_files")
    else:
        raw_dir = os.path.join(os.path.dirname(os.path.abspath(target_path)),
                               "raw_files")
    shutil.rmtree(raw_dir, ignore_errors=True)
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


def parse_raw_residence_xls(content_bytes: bytes,
                            year: int) -> List[Dict[str, Any]]:
    """Parses raw IBGE Table 1 residence XLS workbook."""
    rows: List[Dict[str, Any]] = []
    df = pd.read_excel(io.BytesIO(content_bytes))
    if len(df) <= 6:
        raise ValueError(
            f"Residence XLS workbook for {year} has fewer than 7 rows.")
    header_row = df.iloc[6]
    col_map: Dict[int, Tuple[str, str]] = {}
    for idx, c in enumerate(header_row):
        c_str = str(c).lower()
        if "toral population" in c_str or "total population" in c_str:
            col_map[idx] = ("Total", "Total")
        elif "total male" in c_str:
            col_map[idx] = ("Total", "Masculino")
        elif "total female" in c_str:
            col_map[idx] = ("Total", "Feminino")
        elif "total urban" in c_str:
            col_map[idx] = ("Urbana", "Total")
        elif "urban male" in c_str:
            col_map[idx] = ("Urbana", "Masculino")
        elif "urban" in c_str and ("frmale" in c_str or "female" in c_str):
            col_map[idx] = ("Urbana", "Feminino")
        elif "total rural" in c_str:
            col_map[idx] = ("Rural", "Total")
        elif "rural male" in c_str:
            col_map[idx] = ("Rural", "Masculino")
        elif "rural female" in c_str:
            col_map[idx] = ("Rural", "Feminino")

    for r_idx in range(7, len(df)):
        r = df.iloc[r_idx]
        place = str(r.iloc[0]).strip()
        if (not place or pd.isna(r.iloc[0]) or
            ("fonte" in place.lower() and "fonte boa" not in place.lower()) or
                "nota" in place.lower()):
            continue
        if place == "Brasil":
            place = "Brazil"

        for c_idx, (situacao, sexo) in col_map.items():
            val = r.iloc[c_idx]
            if pd.isna(val) or str(val).strip() in ["-", "...", "..", "X", ""]:
                continue
            try:
                val_int = int(round(float(val)))
            except (ValueError, TypeError):
                continue
            rows.append({
                "Ano": year,
                "Localidade": place,
                "Situacao": situacao,
                "Sexo": sexo,
                "Populacao": val_int,
            })
    if not rows:
        raise ValueError(
            f"Parsed 0 rows from residence XLS workbook for {year}.")
    return rows


def parse_raw_1991_residence(content_bytes: bytes,
                             map_91: Dict[str, str]) -> List[Dict[str, Any]]:
    """Parses raw 1991 residence workbook."""
    rows: List[Dict[str, Any]] = []
    df = pd.read_excel(io.BytesIO(content_bytes))
    for r_idx in range(1, len(df)):
        row = df.iloc[r_idx]
        place_raw = str(row.iloc[0]).strip()
        place_lower = place_raw.lower()
        if (not place_raw or pd.isna(row.iloc[0]) or
            ("fonte" in place_lower and "fonte boa" not in place_lower) or
                "nota" in place_lower):
            continue
        if len(row) < 3:
            continue

        rural_val = row.iloc[1]
        urban_val = row.iloc[2]
        place_resolved = map_91.get(place_raw, place_raw)

        u_int = None
        r_int = None
        try:
            u_int = int(round(float(urban_val)))
            rows.append({
                "Ano": 1991,
                "Localidade": place_resolved,
                "Situacao": "Urbana",
                "Sexo": "Total",
                "Populacao": u_int,
            })
        except (ValueError, TypeError):
            pass
        try:
            r_int = int(round(float(rural_val)))
            rows.append({
                "Ano": 1991,
                "Localidade": place_resolved,
                "Situacao": "Rural",
                "Sexo": "Total",
                "Populacao": r_int,
            })
        except (ValueError, TypeError):
            pass
        if u_int is not None and r_int is not None:
            rows.append({
                "Ano": 1991,
                "Localidade": place_resolved,
                "Situacao": "Total",
                "Sexo": "Total",
                "Populacao": u_int + r_int,
            })
    if not rows:
        raise ValueError("Parsed 0 rows from 1991 residence XLS workbook.")
    return rows


def load_1991_mapping(raw_dir: Optional[str] = None) -> Dict[str, str]:
    """Loads 1991 place name mapping to resolved DCIDs from GCS."""
    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket("unresolved_mcf")
    blob = bucket.blob(
        "country/brazil/intermediate_files/Brazil_Place_Mapping_1991.json")
    text = blob.download_as_text()
    if raw_dir:
        with open(
                os.path.join(raw_dir, "Brazil_Place_Mapping_1991.json"),
                "w",
                encoding="utf-8",
        ) as f:
            f.write(text)
    mapping = json.loads(text)
    if not mapping:
        raise RuntimeError("Loaded empty 1991 place mapping from GCS.")
    return mapping


def parse_raw_residence_gender_xls(content_bytes: bytes,
                                   year: int) -> List[Dict[str, Any]]:
    """Backward-compatible alias for parse_raw_residence_xls."""
    return parse_raw_residence_xls(content_bytes, year)


def fetch_raw_input_files(
        raw_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Reads raw 1940, 1991, and 2000 residence input files from GCS."""
    from google.cloud import storage

    rows: List[Dict[str, Any]] = []
    year_files = [(1940, "tab001.xls"), (2000, "tab002.xls")]
    client = storage.Client()
    bucket = client.bucket("unresolved_mcf")

    for year, fname in year_files:
        blob = bucket.blob(
            f"country/brazil/input_files/Brazil_1940_2000_Residence/{fname}")
        content = blob.download_as_bytes()
        if raw_dir:
            with open(os.path.join(raw_dir, fname), "wb") as f:
                f.write(content)
        rows.extend(parse_raw_residence_xls(content, year))

    # 1991 Residence
    map_91 = load_1991_mapping(raw_dir=raw_dir)
    blobs = list(
        bucket.list_blobs(
            prefix="country/brazil/input_files/Brazil_1991_residence/POPS91"))
    rows_1991: List[Dict[str, Any]] = []
    for b in blobs:
        bname = os.path.basename(b.name)
        if bname.upper().endswith(".XLS"):
            content = b.download_as_bytes()
            if raw_dir:
                with open(os.path.join(raw_dir, bname), "wb") as f:
                    f.write(content)
            rows_1991.extend(parse_raw_1991_residence(content, map_91))
    if not rows_1991:
        raise RuntimeError("No 1991 POPS residence records loaded from GCS.")
    rows.extend(rows_1991)

    return rows


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census residence data across all census years."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    raw_dir = _get_raw_dir(target_path)
    all_rows: List[Dict[str, Any]] = []

    try:
        # 1. Historical data from raw input files in GCS input_files (1940, 1991, 2000)
        raw_rows = fetch_raw_input_files(raw_dir=raw_dir)
        all_rows.extend(raw_rows)

        # 2. 2010 Census from SIDRA API (Table 608)
        # Added after historical files so authoritative live SIDRA rows take precedence in drop_duplicates(keep="last").
        # Classification c1 is Situação (Total, Urbana, Rural) and c2 is Sexo (Total, Homens, Mulheres).
        sexo_map = {
            "Homens": "Masculino",
            "Mulheres": "Feminino",
            "Total": "Total"
        }
        for fname, url in TABLE_608_API_URLS:
            raw_2010 = fetch_sidra_data(session,
                                        url,
                                        raw_file_path=os.path.join(
                                            raw_dir, fname))
            logging.info(
                f"Retrieved {len(raw_2010) - 1} records from SIDRA Table 608 query: {url}"
            )
            for r in raw_2010[1:]:
                val_str = r.get("V")
                if val_str in ["-", "...", "..", "X", None, ""]:
                    continue
                try:
                    val = int(round(float(val_str)))
                except (ValueError, TypeError):
                    continue

                if str(r.get("NC", "")).strip() == "6":
                    loc = str(r.get("D1C", "")).strip()
                else:
                    loc = str(r.get("D1N", "")).strip()
                    if loc == "Brasil":
                        loc = "Brazil"

                situacao = str(r.get("D4N", "Total")).strip()
                sexo_raw = str(r.get("D5N", "Total")).strip()
                sexo = sexo_map.get(sexo_raw, "Total")
                all_rows.append({
                    "Ano": 2010,
                    "Localidade": loc,
                    "Situacao": situacao,
                    "Sexo": sexo,
                    "Populacao": val,
                })

        # 3. 2022+ Census from SIDRA API (Table 9923)
        raw_2022 = fetch_sidra_data(
            session,
            TABLE_9923_API_URL,
            raw_file_path=os.path.join(raw_dir, "sidra_9923_2022_n6.json"),
        )
        logging.info(
            f"Retrieved {len(raw_2022) - 1} records from SIDRA Table 9923.")
        for r in raw_2022[1:]:
            val_str = r.get("V")
            if val_str in ["-", "...", "..", "X", None, ""]:
                continue
            try:
                val = int(round(float(val_str)))
            except (ValueError, TypeError):
                continue

            year_str = str(r.get("D3N", "")).strip()
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

            situacao = str(r.get("D4N", "Total")).strip()
            all_rows.append({
                "Ano": year,
                "Localidade": loc,
                "Situacao": situacao,
                "Sexo": "Total",
                "Populacao": val,
            })

    except Exception as e:
        if fallback_to_cached and os.path.isfile(target_path):
            logging.warning(
                f"Download failed ({e}). Falling back to cached copy: {target_path}"
            )
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(
            f"Error downloading Brazil Census residence data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No residence records retrieved from data sources.")

    df = pd.DataFrame(all_rows).drop_duplicates(
        subset=["Ano", "Localidade", "Situacao", "Sexo"], keep="last")
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

    return target_path


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
    logging.info(
        f"Successfully generated Brazil Census residence data at: {saved_file}")


if __name__ == "__main__":
    app.run(main)
