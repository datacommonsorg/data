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
"""Automated download script for Brazil Census Population by Religion data.

Downloads religion demographic data from official IBGE SIDRA REST API (Table 9537)
and, if not available in live upstream source, reads raw input files from GCS
(gs://unresolved_mcf/country/brazil/input_files/Brazil_1940_2000_religion/*.xls),
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
# Table 9537: População residente por religião (2022+ Census)
TABLE_9537_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/9537/n1/all/n2/all/n3/all"
    f"/v/140/p/all/c133/all/c2/0/c58/0?formato=json"
)

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_RELIGION_DIR = "country/brazil/input_files/Brazil_1940_2000_religion"

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

FLAGS = flags.FLAGS
if "output_file" not in FLAGS:
    flags.DEFINE_string(
        "output_file",
        "",
        "Output CSV file path. Defaults to input_files/brazil_population_by_religion.csv.",
    )
if "fallback_to_cached" not in FLAGS:
    flags.DEFINE_boolean(
        "fallback_to_cached",
        False,
        "Whether to fallback to locally cached CSV if live download fails.",
    )

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, "brazil_population_by_religion.csv")


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


def parse_raw_religion_xls(content_bytes: bytes, year: int) -> List[Dict[str, Any]]:
    """Parses raw IBGE Table 8 religion XLS workbook."""
    rows: List[Dict[str, Any]] = []
    try:
        df = pd.read_excel(io.BytesIO(content_bytes))
        if len(df) <= 5:
            return rows
        header_row = df.iloc[5]
        col_map: Dict[int, str] = {}
        for idx, c in enumerate(header_row):
            c_str = str(c).strip()
            if "Total" in c_str:
                col_map[idx] = "Total"
            elif "RomanCatholicismApostolic" in c_str or "Católica" in c_str:
                col_map[idx] = "Católica Apostólica Romana"
            elif "Evangelical" in c_str or "Evangélica" in c_str:
                col_map[idx] = "Evangélica"
            elif "OtherReligion" in c_str or "Outras" in c_str:
                col_map[idx] = "Outras Religiões"
            elif "NoReligion" in c_str or "Sem religião" in c_str:
                col_map[idx] = "Sem Religião"
            elif "ReligionNotStated" in c_str or "Não declarada" in c_str or "Sem declaração" in c_str:
                col_map[idx] = "Não Declarada"

        for r_idx in range(6, len(df)):
            r = df.iloc[r_idx]
            place = str(r.iloc[0]).strip()
            if not place or pd.isna(r.iloc[0]) or "fonte" in place.lower():
                continue
            if place == "Brasil":
                place = "Brazil"

            for c_idx, rel in col_map.items():
                val = r.iloc[c_idx]
                if pd.isna(val):
                    continue
                try:
                    val_int = int(round(float(val)))
                except (ValueError, TypeError):
                    continue
                rows.append({"Ano": year, "Localidade": place, "Religiao": rel, "Populacao": val_int})
    except Exception as e:
        logging.warning(f"Error parsing raw religion XLS: {e}")
    return rows


def fetch_raw_input_files() -> List[Dict[str, Any]]:
    """Reads raw input files from GCS input_files or local scratch."""
    rows: List[Dict[str, Any]] = []
    year_files = [(1940, "Brazil_1940_religion.xls"), (2000, "Brazil_2000_religion.xls")]

    for year, fname in year_files:
        scratch_file = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", "Brazil_1940_2000_religion", fname)
        alt_scratch = os.path.join("/data", "scratch", "input_files", "Brazil_1940_2000_religion", fname)
        local_path = scratch_file if os.path.isfile(scratch_file) else (alt_scratch if os.path.isfile(alt_scratch) else None)

        if local_path:
            with open(local_path, "rb") as f:
                r = parse_raw_religion_xls(f.read(), year)
                rows.extend(r)
        else:
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket(GCS_BUCKET_NAME)
                blob_path = f"{GCS_RELIGION_DIR}/{fname}"
                blob = bucket.blob(blob_path)
                content = blob.download_as_bytes()
                r = parse_raw_religion_xls(content, year)
                rows.extend(r)
            except Exception as e:
                logging.warning(f"Could not load raw religion file from GCS gs://{GCS_BUCKET_NAME}/{GCS_RELIGION_DIR}/{fname}: {e}")

    return rows


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census religion data across past, present, and future censuses."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    all_rows: List[Dict[str, Any]] = []

    try:
        # 1. Primary Source: Live SIDRA API (Table 9537)
        raw_sidra = fetch_sidra_data(session, TABLE_9537_API_URL)
        logging.info(f"Retrieved {len(raw_sidra) - 1} records from SIDRA Table 9537.")
        other_rel_acc: Dict[str, int] = {}
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

            rel_raw = str(r.get("D4N", "Total")).strip()
            if rel_raw == "Total":
                # Table 9537 reports population aged 10+ years, so skip emitting Total
                # to avoid conflicting with all-ages Count_Person in 2022.
                continue
            elif "Católica Apostólica Romana" in rel_raw:
                all_rows.append({"Ano": year, "Localidade": loc, "Religiao": "Católica Apostólica Romana", "Populacao": val})
            elif "Evangélica" in rel_raw or "Evangélicas" in rel_raw:
                all_rows.append({"Ano": year, "Localidade": loc, "Religiao": "Evangélica", "Populacao": val})
            elif "Sem religião" in rel_raw:
                all_rows.append({"Ano": year, "Localidade": loc, "Religiao": "Sem Religião", "Populacao": val})
            elif "Sem declaração" in rel_raw or "Não sabe" in rel_raw:
                all_rows.append({"Ano": year, "Localidade": loc, "Religiao": "Não Declarada", "Populacao": val})
            else:
                key = f"{year}||{loc}"
                other_rel_acc[key] = other_rel_acc.get(key, 0) + val

        for key, val in other_rel_acc.items():
            y_str, l_str = key.split("||", 1)
            all_rows.append({"Ano": int(y_str), "Localidade": l_str, "Religiao": "Outras Religiões", "Populacao": val})

        # 2. Historical data from raw input files in GCS input_files
        raw_rows = fetch_raw_input_files()
        all_rows.extend(raw_rows)

    except Exception as e:
        if fallback_to_cached and os.path.isfile(target_path):
            logging.warning(f"Download failed ({e}). Falling back to cached copy: {target_path}")
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(f"Error downloading Brazil Census religion data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No religion records retrieved from data sources.")

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["Ano", "Localidade", "Religiao"], keep="last")
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
    counters_file = os.path.join(counters_dir, "brazil_population_by_religion_counters.csv")
    with open(counters_file, "w", encoding="utf-8") as f:
        f.write(f"key,value\nnum_rows_processed,{len(df)}\nnum_places,{df['Localidade'].nunique()}\nnum_statvars,6\n")

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
        logging.info(f"Religion download completed successfully: {saved_file}")
    except Exception as e:
        logging.fatal(f"Fatal error downloading Brazil Census religion data: {e}", exc_info=True)


if __name__ == "__main__":
    app.run(main)
