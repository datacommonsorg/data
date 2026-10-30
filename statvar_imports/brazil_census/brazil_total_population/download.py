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
"""Automated download script for Brazil Census Total Population data.

Downloads resident population counts directly from official IBGE sources:
1. Live IBGE SIDRA REST API (Table 9514 for 2022+ and Table 1378 for 2010).
2. Raw input workbooks from GCS input_files / local scratch:
   - Brazil_2022_Muncipal_POP.xlsx (all 5,570 Brazilian municipalities)
   - POP2022_Brasil_e_UFs.xls (National & State 2022 counts)
   - POPU91*.XLS (1991 Census across all 27 Brazilian states)
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
# Table 9514: População residente por sexo (2022+ Census)
TABLE_9514_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/9514/n1/all/n2/all/n3/all"
    f"/v/93/p/all/c2/all/c287/0/c286/113635?formato=json"
)
# Table 1378: População residente por sexo (2010 Census)
TABLE_1378_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/1378/n1/all/n2/all/n3/all"
    f"/v/93/p/all/c1/0/c2/all/c287/0/c455/0?formato=json"
)

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_POP_2022_FILE = "country/brazil/input_files/POP2022_Brasil_e_UFs.xls"
GCS_MUNI_2022_FILE = "country/brazil/input_files/Brazil_2022_Muncipal_POP.xlsx"

FLAGS = flags.FLAGS
if "output_file" not in FLAGS:
    flags.DEFINE_string(
        "output_file",
        "",
        "Output CSV file path. Defaults to input_files/brazil_total_population.csv.",
    )
if "fallback_to_cached" not in FLAGS:
    flags.DEFINE_boolean(
        "fallback_to_cached",
        False,
        "Whether to fallback to locally cached CSV if live download fails.",
    )

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, "brazil_total_population.csv")


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


def load_place_mappings() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Loads municipal mapping and 1991 place mapping."""
    base_dirs = [
        os.path.join(SCRIPT_DIR, "..", "..", "scratch", "intermediate_files"),
        os.path.join("/data", "scratch", "intermediate_files"),
        os.path.join(SCRIPT_DIR, "..", "..", "..", "scratch", "intermediate_files"),
    ]
    muni_map: Dict[str, str] = {}
    map_91: Dict[str, str] = {}
    for d in base_dirs:
        muni_path = os.path.join(d, "muncial_state_brazil_mapping.json")
        path_91 = os.path.join(d, "Brazil_Place_Mapping_1991.json")
        if os.path.isfile(muni_path) and not muni_map:
            with open(muni_path, "r", encoding="utf-8") as f:
                muni_map = json.load(f)
        if os.path.isfile(path_91) and not map_91:
            with open(path_91, "r", encoding="utf-8") as f:
                map_91 = json.load(f)
    if not muni_map or not map_91:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET_NAME)
            if not muni_map:
                b = bucket.blob("country/brazil/intermediate_files/muncial_state_brazil_mapping.json")
                muni_map = json.loads(b.download_as_text())
            if not map_91:
                b = bucket.blob("country/brazil/intermediate_files/Brazil_Place_Mapping_1991.json")
                map_91 = json.loads(b.download_as_text())
        except Exception as e:
            logging.warning(f"Could not load place mappings from GCS: {e}")
    return muni_map, map_91


def parse_raw_pop_xls(content_bytes: bytes) -> List[Dict[str, Any]]:
    """Parses raw IBGE POP2022_Brasil_e_UFs XLS workbook."""
    rows: List[Dict[str, Any]] = []
    try:
        df = pd.read_excel(io.BytesIO(content_bytes))
        for r_idx in range(1, len(df)):
            r = df.iloc[r_idx]
            place_raw = str(r.iloc[0]).strip()
            if not place_raw or pd.isna(r.iloc[0]) or "fonte" in place_raw.lower() or "nota" in place_raw.lower():
                continue
            place = place_raw.replace("Região ", "").strip()
            if place == "Brasil":
                place = "Brazil"

            val = r.iloc[1] if len(r) > 1 and not pd.isna(r.iloc[1]) else (r.iloc[2] if len(r) > 2 else None)
            if pd.isna(val) or val is None:
                continue
            try:
                val_int = int(round(float(val)))
            except (ValueError, TypeError):
                continue

            rows.append({"Ano": 2022, "Localidade": place, "Sexo": "Total", "Populacao": val_int})
    except Exception as e:
        logging.warning(f"Error parsing raw pop XLS: {e}")
    return rows


def parse_raw_municipal_2022(content_bytes: bytes, mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """Parses raw Brazil_2022_Muncipal_POP.xlsx workbook."""
    rows: List[Dict[str, Any]] = []
    try:
        df = pd.read_excel(io.BytesIO(content_bytes))
        for _, r in df.iterrows():
            cod_uf = str(r.get("COD. UF", "")).strip()
            cod_muni = str(r.get("COD. MUNIC", "")).strip().zfill(5)
            full_code = cod_uf + cod_muni
            muni_name = str(r.get("NOME DO MUNICÍPIO", "")).strip()
            pop_str = str(r.get("POPULAÇÃO", "")).replace(",", "").replace(".", "").strip()
            try:
                pop = int(pop_str)
            except (ValueError, TypeError):
                continue
            place_id = mapping.get(full_code, muni_name)
            clean_place = place_id.replace("dcid:", "")
            rows.append({"Ano": 2022, "Localidade": clean_place, "Sexo": "Total", "Populacao": pop})
    except Exception as e:
        logging.warning(f"Error parsing raw 2022 municipal POP xlsx: {e}")
    return rows


def parse_raw_1991_popu(content_bytes: bytes, map_91: Dict[str, str]) -> List[Dict[str, Any]]:
    """Parses raw 1991 POPU state workbook."""
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

            fem_val = row.iloc[1]
            masc_val = row.iloc[2]
            place_resolved = map_91.get(place_raw, place_raw).replace("dcid:", "")

            f_int = None
            m_int = None
            try:
                f_int = int(round(float(fem_val)))
                rows.append({"Ano": 1991, "Localidade": place_resolved, "Sexo": "Mulheres", "Populacao": f_int})
            except (ValueError, TypeError):
                pass
            try:
                m_int = int(round(float(masc_val)))
                rows.append({"Ano": 1991, "Localidade": place_resolved, "Sexo": "Homens", "Populacao": m_int})
            except (ValueError, TypeError):
                pass
            if f_int is not None and m_int is not None:
                rows.append({"Ano": 1991, "Localidade": place_resolved, "Sexo": "Total", "Populacao": f_int + m_int})
    except Exception as e:
        logging.warning(f"Error parsing 1991 POPU XLS: {e}")
    return rows


def fetch_raw_input_files() -> List[Dict[str, Any]]:
    """Reads raw input files from local scratch or GCS input_files."""
    rows: List[Dict[str, Any]] = []
    muni_map, map_91 = load_place_mappings()

    # 1. 2022 Municipal POP
    scratch_muni = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", "Brazil_2022_Muncipal_POP.xlsx")
    alt_muni = os.path.join("/data", "scratch", "input_files", "Brazil_2022_Muncipal_POP.xlsx")
    muni_path = scratch_muni if os.path.isfile(scratch_muni) else (alt_muni if os.path.isfile(alt_muni) else None)
    if muni_path:
        with open(muni_path, "rb") as f:
            rows.extend(parse_raw_municipal_2022(f.read(), muni_map))
    else:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(GCS_MUNI_2022_FILE)
            content = blob.download_as_bytes()
            rows.extend(parse_raw_municipal_2022(content, muni_map))
        except Exception as e:
            logging.warning(f"Could not load {GCS_MUNI_2022_FILE} from GCS: {e}")

    # 2. 2022 UFs POP
    scratch_uf = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", "POP2022_Brasil_e_UFs.xls")
    alt_uf = os.path.join("/data", "scratch", "input_files", "POP2022_Brasil_e_UFs.xls")
    uf_path = scratch_uf if os.path.isfile(scratch_uf) else (alt_uf if os.path.isfile(alt_uf) else None)
    if uf_path:
        with open(uf_path, "rb") as f:
            rows.extend(parse_raw_pop_xls(f.read()))
    else:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(GCS_POP_2022_FILE)
            content = blob.download_as_bytes()
            rows.extend(parse_raw_pop_xls(content))
        except Exception as e:
            logging.warning(f"Could not load {GCS_POP_2022_FILE} from GCS: {e}")

    # 3. 1991 POPU state files
    scratch_dir = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files")
    alt_dir = os.path.join("/data", "scratch", "input_files")
    input_dir = scratch_dir if os.path.isdir(scratch_dir) else (alt_dir if os.path.isdir(alt_dir) else None)
    found_1991 = False
    if input_dir:
        popu_files = sorted(glob.glob(os.path.join(input_dir, "POPU91*.XLS")) + glob.glob(os.path.join(input_dir, "Brazil_1991_gender", "*.xls")))
        for pf in popu_files:
            with open(pf, "rb") as f:
                rows.extend(parse_raw_1991_popu(f.read(), map_91))
                found_1991 = True
    if not found_1991:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET_NAME)
            blobs = list(bucket.list_blobs(prefix="country/brazil/input_files/POPU91"))
            for b in blobs:
                if b.name.upper().endswith(".XLS"):
                    content = b.download_as_bytes()
                    rows.extend(parse_raw_1991_popu(content, map_91))
        except Exception as e:
            logging.warning(f"Could not load 1991 POPU files from GCS: {e}")

    return rows


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census total population data across past, present, and future censuses."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    all_rows: List[Dict[str, Any]] = []

    try:
        # 1. 2022+ Census from SIDRA API (Table 9514)
        try:
            raw_2022 = fetch_sidra_data(session, TABLE_9514_API_URL)
            logging.info(f"Retrieved {len(raw_2022) - 1} records from SIDRA Table 9514.")
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

                sexo = str(r.get("D4N", "Total")).strip()
                all_rows.append({"Ano": year, "Localidade": loc, "Sexo": sexo, "Populacao": val})
        except Exception as e:
            logging.warning(f"Live SIDRA Table 9514 query failed: {e}")

        # 2. 2010 Census from SIDRA API (Table 1378)
        try:
            raw_2010 = fetch_sidra_data(session, TABLE_1378_API_URL)
            logging.info(f"Retrieved {len(raw_2010) - 1} records from SIDRA Table 1378.")
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

                sexo = str(r.get("D5N", "Total")).strip()
                all_rows.append({"Ano": 2010, "Localidade": loc, "Sexo": sexo, "Populacao": val})
        except Exception as e:
            logging.warning(f"Live SIDRA Table 1378 query failed: {e}")

        # 3. Raw input files from GCS / local scratch (including Brazil_2022_Muncipal_POP.xlsx and POPU91*.XLS)
        raw_rows = fetch_raw_input_files()
        all_rows.extend(raw_rows)

    except Exception as e:
        if fallback_to_cached and os.path.isfile(target_path):
            logging.warning(f"Download failed ({e}). Falling back to cached copy: {target_path}")
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(f"Error downloading Brazil Census total population data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No population records retrieved from data sources.")

    if os.path.abspath(target_path) == os.path.abspath(DEFAULT_OUTPUT_FILE) and os.path.isfile(target_path):
        try:
            cached_df = pd.read_csv(target_path, low_memory=False)
            all_rows = cached_df.to_dict("records") + all_rows
        except Exception:
            pass
    df = pd.DataFrame(all_rows).drop_duplicates(subset=["Ano", "Localidade", "Sexo"], keep="last")
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
    counters_file = os.path.join(counters_dir, "brazil_total_population_counters.csv")
    with open(counters_file, "w", encoding="utf-8") as f:
        f.write(f"key,value\nnum_rows_processed,{len(df)}\nnum_places,{df['Localidade'].nunique()}\nnum_statvars,3\n")

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
        logging.info(f"Total population download completed successfully: {saved_file}")
    except Exception as e:
        logging.fatal(f"Fatal error downloading Brazil Census total population data: {e}", exc_info=True)


if __name__ == "__main__":
    app.run(main)
