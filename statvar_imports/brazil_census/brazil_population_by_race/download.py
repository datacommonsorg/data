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
and, if not available in live upstream source, reads raw input files from GCS
(gs://unresolved_mcf/country/brazil/input_files/Brazil_1940_Race.xls and Brazil_2000_Race.xls),
integrating them into a clean tabular CSV input file.
"""

import io
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
# Table 9605: População residente por cor ou raça (2010, 2022, 2030+ via p/all)
TABLE_9605_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/9605/n1/all/n2/all/n3/all"
    f"/v/93/p/all/c86/all?formato=json"
)

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_RACE_1940_FILE = "country/brazil/input_files/Brazil_1940_Race.xls"
GCS_RACE_2000_FILE = "country/brazil/input_files/Brazil_2000_Race.xls"

DCID_TO_PLACE_NAME = {
    'country/BRA': 'Brazil',
    'wikidataId/Q478465': 'Norte',
    'wikidataId/Q1136194': 'Nordeste',
    'wikidataId/Q1088815': 'Sudeste',
    'wikidataId/Q1060042': 'Sul',
    'wikidataId/Q980175': 'Centro-Oeste',
    'wikidataId/Q40780': 'Acre',
    'wikidataId/Q40885': 'Alagoas',
    'wikidataId/Q40130': 'Amapá',
    'wikidataId/Q40040': 'Amazonas',
    'wikidataId/Q40430': 'Bahia',
    'wikidataId/Q40123': 'Ceará',
    'wikidataId/Q119158': 'Distrito Federal',
    'wikidataId/Q43233': 'Espírito Santo',
    'wikidataId/Q41587': 'Goiás',
    'wikidataId/Q42362': 'Maranhão',
    'wikidataId/Q42824': 'Mato Grosso',
    'wikidataId/Q43319': 'Mato Grosso do Sul',
    'wikidataId/Q39109': 'Minas Gerais',
    'wikidataId/Q39517': 'Pará',
    'wikidataId/Q38088': 'Paraíba',
    'wikidataId/Q15499': 'Paraná',
    'wikidataId/Q40942': 'Pernambuco',
    'wikidataId/Q42722': 'Piauí',
    'wikidataId/Q41428': 'Rio de Janeiro',
    'wikidataId/Q43255': 'Rio Grande do Norte',
    'wikidataId/Q40030': 'Rio Grande do Sul',
    'wikidataId/Q43235': 'Rondônia',
    'wikidataId/Q42508': 'Roraima',
    'wikidataId/Q41115': 'Santa Catarina',
    'wikidataId/Q175': 'São Paulo',
    'wikidataId/Q43783': 'Sergipe',
    'wikidataId/Q43695': 'Tocantins'
}

COR_MAP = {
    'Total': 'Total',
    'Branca': 'Branca',
    'Preta': 'Preta',
    'Amarela': 'Amarela',
    'Parda': 'Parda',
    'Indígena': 'Indígena',
}

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
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, "brazil_population_by_race.csv")


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


def fetch_sidra_data(session: requests.Session, url: str) -> List[Dict[str, Any]]:
    """Fetches raw JSON payload from IBGE SIDRA REST API."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    logging.info(f"Dispatching outbound HTTP request: url={url}")
    res = session.get(url, headers=headers, timeout=90)
    res.raise_for_status()
    raw_json = res.json()
    if not isinstance(raw_json, list) or len(raw_json) < 2:
        raise RuntimeError(f"Invalid or empty response payload from SIDRA API: {url}")
    return raw_json


def parse_raw_race_xls(content_bytes: bytes, year: int) -> List[Dict[str, Any]]:
    """Parses raw IBGE race XLS workbook."""
    rows: List[Dict[str, Any]] = []
    try:
        df = pd.read_excel(io.BytesIO(content_bytes))
        if len(df) <= 5:
            return rows
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
            elif "sem declaração" in c_str or "sem declaracao" in c_str or "sem declara" in c_str:
                col_map[idx] = "Sem declaração"

        for r_idx in range(6, len(df)):
            r = df.iloc[r_idx]
            place = str(r.iloc[0]).strip()
            if not place or pd.isna(r.iloc[0]) or "fonte" in place.lower() or "nota" in place.lower():
                continue
            if place == "Brasil":
                place = "Brazil"

            for c_idx, cor in col_map.items():
                val = r.iloc[c_idx]
                if pd.isna(val):
                    continue
                try:
                    val_int = int(round(float(val)))
                except (ValueError, TypeError):
                    continue
                rows.append({"Ano": year, "Localidade": place, "Cor": cor, "Populacao": val_int})
    except Exception as e:
        logging.warning(f"Error parsing raw race XLS: {e}")
    return rows


def fetch_raw_input_files() -> List[Dict[str, Any]]:
    """Reads raw input files from GCS input_files or local scratch."""
    rows: List[Dict[str, Any]] = []
    year_files = [(1940, GCS_RACE_1940_FILE), (2000, GCS_RACE_2000_FILE)]

    for year, gcs_blob in year_files:
        basename = os.path.basename(gcs_blob)
        scratch_file = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", basename)
        alt_scratch = os.path.join("/data", "scratch", "input_files", basename)
        local_path = scratch_file if os.path.isfile(scratch_file) else (alt_scratch if os.path.isfile(alt_scratch) else None)

        if local_path:
            with open(local_path, "rb") as f:
                r = parse_raw_race_xls(f.read(), year)
                rows.extend(r)
        else:
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket(GCS_BUCKET_NAME)
                blob = bucket.blob(gcs_blob)
                content = blob.download_as_bytes()
                r = parse_raw_race_xls(content, year)
                rows.extend(r)
            except Exception as e:
                logging.warning(f"Could not load raw race file from GCS gs://{GCS_BUCKET_NAME}/{gcs_blob}: {e}")

    return rows


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census race data across past, present, and future censuses."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    all_rows: List[Dict[str, Any]] = []

    try:
        # 1. Primary Source: Live SIDRA API (Table 9605)
        try:
            raw_sidra = fetch_sidra_data(session, TABLE_9605_API_URL)
            logging.info(f"Retrieved {len(raw_sidra) - 1} records from SIDRA Table 9605.")
            for r in raw_sidra[1:]:
                val_str = r.get("V")
                if val_str in ["-", "...", "..", None, ""]:
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
            logging.warning(f"Live SIDRA Table 9605 query failed: {e}")

        # 2. Historical data from raw input files in GCS input_files
        raw_rows = fetch_raw_input_files()
        all_rows.extend(raw_rows)

    except Exception as e:
        if fallback_to_cached and os.path.isfile(target_path):
            logging.warning(f"Download failed ({e}). Falling back to cached copy: {target_path}")
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(f"Error downloading Brazil Census race data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No race records retrieved from data sources.")

    if os.path.abspath(target_path) == os.path.abspath(DEFAULT_OUTPUT_FILE) and os.path.isfile(target_path):
        try:
            cached_df = pd.read_csv(target_path, low_memory=False)
            all_rows = cached_df.to_dict("records") + all_rows
        except Exception:
            pass
    df = pd.DataFrame(all_rows).drop_duplicates(subset=["Ano", "Localidade", "Cor"], keep="last")
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
        raise RuntimeError(f"Atomic CSV write failed: {tmp_path} is missing or empty.")

    os.replace(tmp_path, target_path)
    logging.info(f"Wrote {len(df)} records to {target_path}")

    counters_dir = os.path.join(os.path.dirname(target_dir), "counters")
    os.makedirs(counters_dir, exist_ok=True)
    counters_file = os.path.join(counters_dir, "brazil_population_by_race_counters.csv")
    with open(counters_file, "w", encoding="utf-8") as f:
        f.write(f"key,value\nnum_rows_processed,{len(df)}\nnum_places,{df['Localidade'].nunique()}\nnum_statvars,7\n")

    return target_path


def main(argv: List[str]) -> None:
    if len(argv) > 1:
        logging.error(f"Unrecognized command-line arguments: {argv[1:]}")
        sys.exit(1)

    target_file = FLAGS.output_file or DEFAULT_OUTPUT_FILE
    session = get_robust_session()

    try:
        saved_file = download_all_years(
            session=session,
            output_file=target_file,
            fallback_to_cached=FLAGS.fallback_to_cached,
        )
        logging.info(f"Race download completed successfully: {saved_file}")
    except Exception as e:
        logging.fatal(f"Fatal error downloading Brazil Census race data: {e}", exc_info=True)


if __name__ == "__main__":
    app.run(main)
