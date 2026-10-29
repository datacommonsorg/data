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
"""Automated download script for Brazil Census Population by Residence data.

Downloads urban/rural residence demographic data from official IBGE SIDRA REST API
(Table 9923 for 2022+ and Table 608 for 2010) and, if not available in live upstream source,
reads raw input files from GCS (gs://unresolved_mcf/country/brazil/input_files/Brazil_1940_2000_Residence/*.xls),
integrating them into a clean tabular CSV input file.
"""

import glob
import io
import json
import os
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
# Table 9923: População residente por situação do domicílio (2022+ Census)
TABLE_9923_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/9923/n1/all/n2/all/n3/all"
    f"/v/93/p/all/c1/all?formato=json"
)
# Table 608: População residente por situação do domicílio (2010 Census)
TABLE_608_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/608/n1/all/n2/all/n3/all"
    f"/v/93/p/all/c1/all?formato=json"
)

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_RESIDENCE_DIR = "country/brazil/input_files/Brazil_1940_2000_Residence"

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
        "Output CSV file path. Defaults to input_files/brazil_population_by_residence.csv.",
    )
if "fallback_to_cached" not in FLAGS:
    flags.DEFINE_boolean(
        "fallback_to_cached",
        False,
        "Whether to fallback to locally cached CSV if live download fails.",
    )

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, "brazil_population_by_residence.csv")


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


def parse_raw_residence_xls(content_bytes: bytes, year: int) -> List[Dict[str, Any]]:
    """Parses raw IBGE residence XLS workbook (tab001 / tab002)."""
    rows: List[Dict[str, Any]] = []
    try:
        df = pd.read_excel(io.BytesIO(content_bytes))
        if len(df) <= 6:
            return rows
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
            if not place or pd.isna(r.iloc[0]) or ("fonte" in place.lower() and "fonte boa" not in place.lower()):
                continue
            if place == "Brasil":
                place = "Brazil"

            for c_idx, (situacao, sexo) in col_map.items():
                val = r.iloc[c_idx]
                if pd.isna(val):
                    continue
                try:
                    val_int = int(round(float(val)))
                except (ValueError, TypeError):
                    continue
                rows.append({"Ano": year, "Localidade": place, "Situacao": situacao, "Sexo": sexo, "Populacao": val_int})
    except Exception as e:
        logging.warning(f"Error parsing raw residence XLS: {e}")
    return rows


def parse_raw_1991_pops(content_bytes: bytes, map_91: Dict[str, str]) -> List[Dict[str, Any]]:
    """Parses raw 1991 POPS state workbook (Rural and Urbana)."""
    rows: List[Dict[str, Any]] = []
    try:
        df = pd.read_excel(io.BytesIO(content_bytes))
        for r_idx in range(1, len(df)):
            row = df.iloc[r_idx]
            place_raw = str(row.iloc[0]).strip()
            place_lower = place_raw.lower()
            if not place_raw or pd.isna(row.iloc[0]) or ("fonte" in place_lower and "fonte boa" not in place_lower) or "nota" in place_lower:
                continue
            if len(row) < 3:
                continue

            rural_val = row.iloc[1]
            urban_val = row.iloc[2]
            place_resolved = map_91.get(place_raw, place_raw).replace("dcid:", "")

            r_int = None
            u_int = None
            try:
                r_int = int(round(float(rural_val)))
                rows.append({"Ano": 1991, "Localidade": place_resolved, "Situacao": "Rural", "Sexo": "Total", "Populacao": r_int})
            except (ValueError, TypeError):
                pass
            try:
                u_int = int(round(float(urban_val)))
                rows.append({"Ano": 1991, "Localidade": place_resolved, "Situacao": "Urbana", "Sexo": "Total", "Populacao": u_int})
            except (ValueError, TypeError):
                pass
            if r_int is not None and u_int is not None:
                rows.append({"Ano": 1991, "Localidade": place_resolved, "Situacao": "Total", "Sexo": "Total", "Populacao": r_int + u_int})
    except Exception as e:
        logging.warning(f"Error parsing 1991 POPS XLS: {e}")
    return rows


def parse_raw_2010_residence_xls(content_bytes: bytes) -> List[Dict[str, Any]]:
    """Parses raw Brazil_2010_Residence.xls workbook across tab2A, tab2B, tab2C for all 5,564 municipalities."""
    rows: List[Dict[str, Any]] = []
    try:
        for sheet, sit in [('tab2A', 'Total'), ('tab2B', 'Urbana'), ('tab2C', 'Rural')]:
            df = pd.read_excel(io.BytesIO(content_bytes), sheet_name=sheet, header=None, skiprows=4)
            for idx in range(5, len(df)):
                code = str(df.iloc[idx, 0]).strip()
                val = df.iloc[idx, 3]
                if pd.isna(df.iloc[idx, 0]) or not code or code == "nan":
                    continue
                code_lower = code.lower()
                if ("fonte" in code_lower and "fonte boa" not in code_lower) or "nota" in code_lower:
                    continue
                try:
                    val_int = int(round(float(val)))
                    rows.append({
                        "Ano": 2010,
                        "Localidade": code,
                        "Situacao": sit,
                        "Sexo": "Total",
                        "Populacao": val_int
                    })
                except (ValueError, TypeError):
                    continue
    except Exception as e:
        logging.warning(f"Error parsing Brazil_2010_Residence.xls: {e}")
    return rows


def fetch_raw_input_files() -> List[Dict[str, Any]]:
    """Reads raw input files from GCS input_files or local scratch."""
    rows: List[Dict[str, Any]] = []
    year_files = [(1940, "tab001.xls"), (2000, "tab002.xls")]

    for year, fname in year_files:
        scratch_file = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", "Brazil_1940_2000_Residence", fname)
        alt_scratch = os.path.join("/data", "scratch", "input_files", "Brazil_1940_2000_Residence", fname)
        local_path = scratch_file if os.path.isfile(scratch_file) else (alt_scratch if os.path.isfile(alt_scratch) else None)

        if local_path:
            with open(local_path, "rb") as f:
                r = parse_raw_residence_xls(f.read(), year)
                rows.extend(r)
        else:
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket(GCS_BUCKET_NAME)
                blob_path = f"{GCS_RESIDENCE_DIR}/{fname}"
                blob = bucket.blob(blob_path)
                content = blob.download_as_bytes()
                r = parse_raw_residence_xls(content, year)
                rows.extend(r)
            except Exception as e:
                logging.warning(f"Could not load raw residence file from GCS gs://{GCS_BUCKET_NAME}/{GCS_RESIDENCE_DIR}/{fname}: {e}")

    # Load 2010 municipal residence workbook
    r2010_scratch = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", "Brazil_2010_Residence.xls")
    r2010_alt = os.path.join("/data", "scratch", "input_files", "Brazil_2010_Residence.xls")
    r2010_path = r2010_scratch if os.path.isfile(r2010_scratch) else (r2010_alt if os.path.isfile(r2010_alt) else None)
    if r2010_path:
        with open(r2010_path, "rb") as f:
            rows.extend(parse_raw_2010_residence_xls(f.read()))
    else:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob("country/brazil/input_files/Brazil_2010_Residence.xls")
            content = blob.download_as_bytes()
            rows.extend(parse_raw_2010_residence_xls(content))
        except Exception as e:
            logging.warning(f"Could not load Brazil_2010_Residence.xls from GCS gs://{GCS_BUCKET_NAME}/country/brazil/input_files/Brazil_2010_Residence.xls: {e}")

    # Load 1991 POPS files across all states
    map_91 = {}
    for d in [os.path.join(SCRIPT_DIR, "..", "..", "scratch", "intermediate_files"), os.path.join("/data", "scratch", "intermediate_files")]:
        p91 = os.path.join(d, "Brazil_Place_Mapping_1991.json")
        if os.path.isfile(p91):
            with open(p91, "r", encoding="utf-8") as f:
                map_91 = json.load(f)
            break

    input_dirs = [os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files"), os.path.join("/data", "scratch", "input_files")]
    for idir in input_dirs:
        if os.path.isdir(idir):
            pops_files = sorted(glob.glob(os.path.join(idir, "POPS91*.XLS")) + glob.glob(os.path.join(idir, "Brazil_1991_residence", "*.xls")))
            for pf in pops_files:
                with open(pf, "rb") as f:
                    rows.extend(parse_raw_1991_pops(f.read(), map_91))
            break

    return rows


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census residence data across past, present, and future censuses."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    all_rows: List[Dict[str, Any]] = []

    try:
        # 1. Modern 2022+ Censuses from SIDRA API (Table 9923)
        try:
            raw_2022 = fetch_sidra_data(session, TABLE_9923_API_URL)
            logging.info(f"Retrieved {len(raw_2022) - 1} records from SIDRA Table 9923.")
            for r in raw_2022[1:]:
                val_str = r.get("V")
                if val_str in ["-", "...", "..", None, ""]:
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
            logging.warning(f"Live SIDRA Table 9923 query failed: {e}")

        # 2. 2010 Census from SIDRA API (Table 608)
        try:
            raw_2010 = fetch_sidra_data(session, TABLE_608_API_URL)
            logging.info(f"Retrieved {len(raw_2010) - 1} records from SIDRA Table 608.")
            for r in raw_2010[1:]:
                val_str = r.get("V")
                if val_str in ["-", "...", "..", None, ""]:
                    continue
                try:
                    val = int(round(float(val_str)))
                except (ValueError, TypeError):
                    continue

                loc = str(r.get("D1N", "")).strip()
                if loc == "Brasil":
                    loc = "Brazil"

                situacao = str(r.get("D4N", "Total")).strip()
                all_rows.append({
                    "Ano": 2010,
                    "Localidade": loc,
                    "Situacao": situacao,
                    "Sexo": "Total",
                    "Populacao": val,
                })
        except Exception as e:
            logging.warning(f"Live SIDRA Table 608 query failed: {e}")

        # 3. Historical data from raw input files in GCS input_files
        raw_rows = fetch_raw_input_files()
        all_rows.extend(raw_rows)

    except Exception as e:
        if fallback_to_cached and os.path.isfile(target_path):
            logging.warning(f"Download failed ({e}). Falling back to cached copy: {target_path}")
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(f"Error downloading Brazil Census residence data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No residence records retrieved from data sources.")

    if os.path.abspath(target_path) == os.path.abspath(DEFAULT_OUTPUT_FILE) and os.path.isfile(target_path):
        try:
            cached_df = pd.read_csv(target_path, low_memory=False)
            all_rows = cached_df.to_dict("records") + all_rows
        except Exception:
            pass
    df = pd.DataFrame(all_rows).drop_duplicates(subset=["Ano", "Localidade", "Situacao", "Sexo"])
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
    counters_file = os.path.join(counters_dir, "brazil_population_by_residence_counters.csv")
    with open(counters_file, "w", encoding="utf-8") as f:
        f.write(f"key,value\nnum_rows_processed,{len(df)}\nnum_places,{df['Localidade'].nunique()}\nnum_statvars,9\n")

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
        logging.info(f"Residence download completed successfully: {saved_file}")
    except Exception as e:
        logging.fatal(f"Fatal error downloading Brazil Census residence data: {e}", exc_info=True)


if __name__ == "__main__":
    app.run(main)
