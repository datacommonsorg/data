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
"""Automated download script for Brazil Census Population by Race data.

Downloads race/color demographic data from official IBGE SIDRA REST API (Table 9605)
across national, regional, state, and municipal (n6/all) levels, and reads historical
1940 and 2000 raw input workbooks from GCS
(gs://unresolved_mcf/country/brazil/input_files/Brazil_1940_Race.xls and Brazil_2000_Race.xls),
integrating them into a clean tabular CSV input file.
"""

import io
import json
import os
import shutil
import sys
import tempfile
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from absl import app
from absl import flags
from absl import logging
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

SIDRA_BASE_URL = "https://apisidra.ibge.gov.br"
# Table 9605: População residente por cor ou raça (2010 and 2022 across n1/n2/n3/n6, plus macro p/all)
TABLE_9605_API_URL = (f"{SIDRA_BASE_URL}/values/t/9605/n1/all/n2/all/n3/all"
                      f"/v/93/p/all/c86/all?formato=json")
TABLE_9605_API_URLS = [
    (
        "sidra_9605_2010_n6.json",
        f"{SIDRA_BASE_URL}/values/t/9605/n1/all/n2/all/n3/all/n6/all/v/93/p/2010/c86/all?formato=json",
    ),
    (
        "sidra_9605_2022_n6.json",
        f"{SIDRA_BASE_URL}/values/t/9605/n1/all/n2/all/n3/all/n6/all/v/93/p/2022/c86/all?formato=json",
    ),
    ("sidra_9605_macro_all.json", TABLE_9605_API_URL),
]

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_RACE_1940_FILE = "country/brazil/input_files/Brazil_1940_Race.xls"
GCS_RACE_2000_FILE = "country/brazil/input_files/Brazil_2000_Race.xls"

FLAGS = flags.FLAGS
if "output_file" not in FLAGS:
    flags.DEFINE_string(
        "output_file",
        "",
        "Output CSV file path. Defaults to input_files/brazil_population_by_race.csv.",
    )
if "fallback_to_cached" not in FLAGS:
    flags.DEFINE_boolean(
        "fallback_to_cached",
        False,
        "Whether to fallback to locally cached CSV if live download fails.",
    )

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR,
                                   "brazil_population_by_race.csv")


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


def parse_raw_race_xls(content_bytes: bytes, year: int) -> List[Dict[str, Any]]:
    """Parses raw IBGE race XLS workbook."""
    rows: List[Dict[str, Any]] = []
    df = pd.read_excel(io.BytesIO(content_bytes))
    if len(df) <= 5:
        raise ValueError(f"Race XLS workbook for {year} has fewer than 6 rows.")
    row4 = df.iloc[4].tolist()
    row5 = df.iloc[5].tolist()
    col_map: Dict[int, str] = {}
    for idx, (c4, c5) in enumerate(zip(row4, row5)):
        c_str = (str(c4) + " " + str(c5)).lower()
        if "total" in c_str:
            col_map[idx] = "Total"
        elif "branca" in c_str or "white" in c_str:
            col_map[idx] = "Branca"
        elif "preta" in c_str or "black" in c_str:
            col_map[idx] = "Preta"
        elif "amarela" in c_str or "yellow" in c_str:
            col_map[idx] = "Amarela"
        elif "parda" in c_str or "brown" in c_str:
            col_map[idx] = "Parda"
        elif "indígena" in c_str or "indigenous" in c_str:
            col_map[idx] = "Indígena"
        elif ("sem declaração" in c_str or "sem declaracao" in c_str or
              "sem declara" in c_str):
            col_map[idx] = "Sem declaração"

    for r_idx in range(6, len(df)):
        r = df.iloc[r_idx]
        place = str(r.iloc[0]).strip()
        place_lower = place.lower()
        if (not place or pd.isna(r.iloc[0]) or
            ("fonte" in place_lower and "fonte boa" not in place_lower) or
                "nota" in place_lower):
            continue
        if place == "Brasil":
            place = "Brazil"

        for c_idx, cor in col_map.items():
            # Table 7 (2000 Race) reports Sample estimates (169,872,856 for Brazil);
            # skip Total for 2000 so Universe Count_Person (169,799,170) is authoritative.
            if cor == "Total" and year == 2000:
                continue
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
                "Cor": cor,
                "Populacao": val_int,
            })
    if not rows:
        raise ValueError(
            f"Parsed 0 rows from raw race XLS workbook for {year}.")
    return rows


def fetch_raw_input_files(
        raw_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Reads raw 1940 and 2000 race workbooks from GCS input_files."""
    from google.cloud import storage

    rows: List[Dict[str, Any]] = []
    year_files = [(1940, GCS_RACE_1940_FILE), (2000, GCS_RACE_2000_FILE)]
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)

    for year, gcs_blob in year_files:
        blob = bucket.blob(gcs_blob)
        content = blob.download_as_bytes()
        if raw_dir:
            raw_path = os.path.join(raw_dir, os.path.basename(gcs_blob))
            with open(raw_path, "wb") as f:
                f.write(content)
        parsed = parse_raw_race_xls(content, year)
        rows.extend(parsed)

    if not rows:
        raise RuntimeError("No historical race records loaded from GCS.")
    return rows


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census race data across past, present, and future censuses."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    raw_dir = _get_raw_dir(target_path)
    all_rows: List[Dict[str, Any]] = []

    try:
        # 1. Historical data from raw input files in GCS input_files
        # Appended first so live SIDRA records take precedence in drop_duplicates(keep="last").
        raw_rows = fetch_raw_input_files(raw_dir=raw_dir)
        all_rows.extend(raw_rows)

        # 2. Primary Source: Live SIDRA API (Table 9605 across n1/n2/n3/n6)
        for fname, url in TABLE_9605_API_URLS:
            raw_sidra = fetch_sidra_data(session,
                                         url,
                                         raw_file_path=os.path.join(
                                             raw_dir, fname))
            logging.info(
                f"Retrieved {len(raw_sidra) - 1} records from SIDRA Table 9605: {url}"
            )
            for r in raw_sidra[1:]:
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

                cor_raw = str(r.get("D4N", "Total")).strip()
                if cor_raw in ["Sem declaração", "Não declarada"]:
                    continue

                all_rows.append({
                    "Ano": year,
                    "Localidade": loc,
                    "Cor": cor_raw,
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
            f"Error downloading Brazil Census race data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No race records retrieved from data sources.")

    df = pd.DataFrame(all_rows).drop_duplicates(
        subset=["Ano", "Localidade", "Cor"], keep="last")
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
    logging.info(f"Race download completed successfully: {saved_file}")


if __name__ == "__main__":
    app.run(main)
