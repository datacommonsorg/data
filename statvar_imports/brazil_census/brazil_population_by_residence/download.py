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
   - Table 9923 (2022 Census População residente por situação do domicílio)
   - Table 608 (2010 Census População residente por situação do domicílio e sexo)
2. Fallback to raw historical census files from GCS (1940, 1991, 2000).
"""

import glob
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
# Table 9923: População residente por situação do domicílio (2022)
# Includes municipal level (n6/all) alongside macro levels (n1, n2, n3).
TABLE_9923_API_URL = f"{SIDRA_BASE_URL}/values/t/9923/n1/all/n2/all/n3/all/n6/all/v/93/p/all/c1/all?formato=json"

# Table 608: População residente por situação do domicílio e sexo (2010)
# Split into two queries to stay within SIDRA's 50,000 value limit:
# 1) Total sex across all levels (national, regional, state, municipal) = ~16.8k values
# 2) Male and Female sex split across macro levels (national, regional, state) = ~200 values
TABLE_608_API_URLS = [
    f"{SIDRA_BASE_URL}/values/t/608/n1/all/n2/all/n3/all/n6/all/v/93/p/all/c1/all/c2/0?formato=json",
    f"{SIDRA_BASE_URL}/values/t/608/n1/all/n2/all/n3/all/v/93/p/all/c1/all/c2/4,5?formato=json",
]
TABLE_608_API_URL = TABLE_608_API_URLS[0]

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
    """Parses raw IBGE Table 1 residence XLS workbook."""
    rows: List[Dict[str, Any]] = []
    try:
        df = pd.read_excel(io.BytesIO(content_bytes))
        if len(df) <= 5:
            return rows
        header_row = df.iloc[5]
        col_map: Dict[int, tuple] = {}
        for idx, c in enumerate(header_row):
            c_str = str(c).strip()
            if "Total" in c_str and "Urbana" not in c_str and "Rural" not in c_str:
                col_map[idx] = ("Total", "Total")
            elif "Urbana" in c_str:
                col_map[idx] = ("Urbana", "Total")
            elif "Rural" in c_str:
                col_map[idx] = ("Rural", "Total")

        for r_idx in range(6, len(df)):
            r = df.iloc[r_idx]
            place = str(r.iloc[0]).strip()
            if not place or pd.isna(r.iloc[0]) or "fonte" in place.lower():
                continue
            if place == "Brasil":
                place = "Brazil"

            for c_idx, (sit, sex) in col_map.items():
                val = r.iloc[c_idx]
                if pd.isna(val):
                    continue
                try:
                    val_int = int(round(float(val)))
                except (ValueError, TypeError):
                    continue
                rows.append({"Ano": year, "Localidade": place, "Situacao": sit, "Sexo": sex, "Populacao": val_int})
    except Exception as e:
        logging.warning(f"Error parsing raw residence XLS: {e}")
    return rows


def parse_raw_1991_residence(content_bytes: bytes, map_91: Dict[str, str]) -> List[Dict[str, Any]]:
    """Parses raw 1991 residence workbook."""
    rows: List[Dict[str, Any]] = []
    try:
        df = pd.read_excel(io.BytesIO(content_bytes))
        for r_idx in range(1, len(df)):
            row = df.iloc[r_idx]
            place_raw = str(row.iloc[0]).strip()
            if not place_raw or pd.isna(row.iloc[0]) or "fonte" in place_raw.lower() or "nota" in place_raw.lower():
                continue
            if len(row) < 3:
                continue

            urb_val = row.iloc[1]
            rur_val = row.iloc[2]
            place_resolved = map_91.get(place_raw, place_raw)

            u_int = None
            r_int = None
            try:
                u_int = int(round(float(urb_val)))
                rows.append({"Ano": 1991, "Localidade": place_resolved, "Situacao": "Urbana", "Sexo": "Total", "Populacao": u_int})
            except (ValueError, TypeError):
                pass
            try:
                r_int = int(round(float(rur_val)))
                rows.append({"Ano": 1991, "Localidade": place_resolved, "Situacao": "Rural", "Sexo": "Total", "Populacao": r_int})
            except (ValueError, TypeError):
                pass
            if u_int is not None and r_int is not None:
                rows.append({"Ano": 1991, "Localidade": place_resolved, "Situacao": "Total", "Sexo": "Total", "Populacao": u_int + r_int})
    except Exception as e:
        logging.warning(f"Error parsing 1991 residence XLS: {e}")
    return rows


def load_1991_mapping() -> Dict[str, str]:
    """Loads 1991 place name mapping to resolved DCIDs."""
    cand = [
        os.path.join(SCRIPT_DIR, "..", "..", "scratch", "intermediate_files", "Brazil_Place_Mapping_1991.json"),
        os.path.join("/data", "scratch", "intermediate_files", "Brazil_Place_Mapping_1991.json"),
    ]
    for c in cand:
        if os.path.isfile(c):
            with open(c, "r", encoding="utf-8") as f:
                return json.load(f)
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket("unresolved_mcf")
        blob = bucket.blob("country/brazil/intermediate_files/Brazil_Place_Mapping_1991.json")
        return json.loads(blob.download_as_text())
    except Exception as e:
        logging.warning(f"Could not load 1991 mapping from GCS: {e}")
    return {}


def parse_raw_residence_gender_xls(content_bytes: bytes, year: int) -> List[Dict[str, Any]]:
    """Parses raw IBGE Table 1 residence by sex XLS workbook."""
    rows: List[Dict[str, Any]] = []
    try:
        df = pd.read_excel(io.BytesIO(content_bytes))
        if len(df) <= 5:
            return rows
        header_row = df.iloc[5]
        col_map: Dict[int, tuple] = {}
        for idx, c in enumerate(header_row):
            c_str = str(c).strip()
            if "Total" in c_str and "Urbana" not in c_str and "Rural" not in c_str:
                col_map[idx] = ("Total", "Total")
            elif "Homens" in c_str and "Urbana" not in c_str and "Rural" not in c_str:
                col_map[idx] = ("Total", "Masculino")
            elif "Mulheres" in c_str and "Urbana" not in c_str and "Rural" not in c_str:
                col_map[idx] = ("Total", "Feminino")
            elif "Urbana Total" in c_str or ("Urbana" in c_str and "Total" in c_str):
                col_map[idx] = ("Urbana", "Total")
            elif "Urbana Homens" in c_str or ("Urbana" in c_str and "Homens" in c_str):
                col_map[idx] = ("Urbana", "Masculino")
            elif "Urbana Mulheres" in c_str or ("Urbana" in c_str and "Mulheres" in c_str):
                col_map[idx] = ("Urbana", "Feminino")
            elif "Rural Total" in c_str or ("Rural" in c_str and "Total" in c_str):
                col_map[idx] = ("Rural", "Total")
            elif "Rural Homens" in c_str or ("Rural" in c_str and "Homens" in c_str):
                col_map[idx] = ("Rural", "Masculino")
            elif "Rural Mulheres" in c_str or ("Rural" in c_str and "Mulheres" in c_str):
                col_map[idx] = ("Rural", "Feminino")

        for r_idx in range(6, len(df)):
            r = df.iloc[r_idx]
            place = str(r.iloc[0]).strip()
            if not place or pd.isna(r.iloc[0]) or "fonte" in place.lower():
                continue
            if place == "Brasil":
                place = "Brazil"

            for c_idx, (sit, sex) in col_map.items():
                val = r.iloc[c_idx]
                if pd.isna(val):
                    continue
                try:
                    val_int = int(round(float(val)))
                except (ValueError, TypeError):
                    continue
                rows.append({"Ano": year, "Localidade": place, "Situacao": sit, "Sexo": sex, "Populacao": val_int})
    except Exception as e:
        logging.warning(f"Error parsing raw residence gender XLS: {e}")
    return rows


def fetch_raw_input_files() -> List[Dict[str, Any]]:
    """Reads raw input files from GCS input_files or local scratch."""
    rows: List[Dict[str, Any]] = []
    year_files = [(1940, "Brazil_1940_Residence.xls"), (2000, "Brazil_2000_Residence.xls")]

    for year, fname in year_files:
        scratch_file = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", "Brazil_1940_2000_Residence", fname)
        alt_scratch = os.path.join("/data", "scratch", "input_files", "Brazil_1940_2000_Residence", fname)
        local_path = scratch_file if os.path.isfile(scratch_file) else (alt_scratch if os.path.isfile(alt_scratch) else None)

        if local_path:
            with open(local_path, "rb") as f:
                rows.extend(parse_raw_residence_xls(f.read(), year))
        else:
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket("unresolved_mcf")
                blob = bucket.blob(f"country/brazil/input_files/Brazil_1940_2000_Residence/{fname}")
                content = blob.download_as_bytes()
                rows.extend(parse_raw_residence_xls(content, year))
            except Exception as e:
                logging.warning(f"Could not load {fname} from GCS: {e}")

    # Historical Residence by Gender (1940, 2000)
    for year, tab_name in [(1940, "Brazil_AA1_1940_2000_tab001.xls"), (2000, "Brazil_AA1_1940_2000_tab002.xls")]:
        scratch_file = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", tab_name)
        alt_scratch = os.path.join("/data", "scratch", "input_files", tab_name)
        local_path = scratch_file if os.path.isfile(scratch_file) else (alt_scratch if os.path.isfile(alt_scratch) else None)
        if local_path:
            with open(local_path, "rb") as f:
                rows.extend(parse_raw_residence_gender_xls(f.read(), year))
        else:
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket("unresolved_mcf")
                blob = bucket.blob(f"country/brazil/input_files/{tab_name}")
                content = blob.download_as_bytes()
                rows.extend(parse_raw_residence_gender_xls(content, year))
            except Exception as e:
                logging.warning(f"Could not load {tab_name} from GCS: {e}")

    # 1991 Residence
    map_91 = load_1991_mapping()
    cand_dirs = [
        os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", "Brazil_1991_residence"),
        os.path.join("/data", "scratch", "input_files", "Brazil_1991_residence"),
    ]
    found_1991 = False
    for d in cand_dirs:
        if os.path.isdir(d):
            pops_files = sorted(glob.glob(os.path.join(d, "POPS91*.XLS")) + glob.glob(os.path.join(d, "*.xls")))
            for pf in pops_files:
                with open(pf, "rb") as f:
                    rows.extend(parse_raw_1991_residence(f.read(), map_91))
                    found_1991 = True
            if found_1991:
                break
    if not found_1991:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket("unresolved_mcf")
            blobs = list(bucket.list_blobs(prefix="country/brazil/input_files/POPS91"))
            for b in blobs:
                if b.name.upper().endswith(".XLS"):
                    content = b.download_as_bytes()
                    rows.extend(parse_raw_1991_residence(content, map_91))
        except Exception as e:
            logging.warning(f"Could not load 1991 POPS files from GCS: {e}")

    return rows


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census residence data across all census years."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    all_rows: List[Dict[str, Any]] = []

    try:
        # 1. Historical data from raw input files in GCS input_files (1940, 1991, 2000)
        raw_rows = fetch_raw_input_files()
        all_rows.extend(raw_rows)

        # 2. 2010 Census from SIDRA API (Table 608)
        # Added after historical files so authoritative live SIDRA rows take precedence in drop_duplicates(keep="last").
        # Classification c1 is Situação (Total, Urbana, Rural) and c2 is Sexo (Total, Homens, Mulheres).
        sexo_map = {"Homens": "Masculino", "Mulheres": "Feminino", "Total": "Total"}
        for url in TABLE_608_API_URLS:
            raw_2010 = fetch_sidra_data(session, url)
            logging.info(f"Retrieved {len(raw_2010) - 1} records from SIDRA Table 608 query: {url}")
            for r in raw_2010[1:]:
                val_str = r.get("V")
                if val_str in ["-", "...", "..", None, ""]:
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
            logging.warning(f"Download failed ({e}). Falling back to cached copy: {target_path}")
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(f"Error downloading Brazil Census residence data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No residence records retrieved from data sources.")

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["Ano", "Localidade", "Situacao", "Sexo"], keep="last")
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
        logging.info(f"Successfully generated Brazil Census residence data at: {saved_file}")
    except Exception as e:
        logging.error(f"Fatal error executing Brazil Census residence download: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app.run(main)
