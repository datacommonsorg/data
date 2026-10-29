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
"""Automated download script for Brazil Census Education data.

Downloads educational enrollment data directly from official IBGE sources:
1. Live IBGE SIDRA REST API (Table 1972) for 2000, 2010, and future censuses.
2. Official IBGE Census Downloads Portal (https://ftp.ibge.gov.br/Censos/Censo_Demografico_2000/educacao/Municipios/)
   for municipal-level education workbooks.
3. Fallback to raw input files from GCS (gs://unresolved_mcf/country/brazil/input_files/Brazil_2000_education_input/*.xls)
   if live upstream servers are unreachable.
"""

import glob
import io
import json
import os
import sys
import tempfile
import zipfile
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
# Table 1972: Pessoas que frequentavam escola ou creche por rede e nível de ensino
TABLE_1972_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/1972/n1/all/n2/all/n3/all"
    f"/v/690/p/all/c11797/all/c11798/all?formato=json"
)

IBGE_FTP_2000_EDUCATION_BASE = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2000/educacao/Municipios/"
GCS_BUCKET_NAME = "unresolved_mcf"
GCS_INPUT_DIR = "country/brazil/input_files/Brazil_2000_education_input"

UF_CODES_2000 = [
    "ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma",
    "mg", "ms", "mt", "pa", "pb", "pe", "pi", "pr", "rj", "rn",
    "ro", "rr", "rs", "sc", "se", "sp", "to"
]

DCID_TO_PLACE_NAME = {
    'country/BRA': 'Brasil',
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

RAW_COL_TO_NIVEL = {
    'Total Student': 'Total',
    'Student Nursery': 'Creche',
    'Student PreKindergarten': 'Pré-escolar',
    'Student AdultEducation': 'Educação de Jovens e Adultos',
    'Student PrimaryEducation': 'Fundamental',
    'Student BRA_HighSchool': 'Médio',
    'Student PreEntranceExam': 'Pré-vestibular',
    'Student BachelorsDegree': 'Superior Graduação',
    'Student MastersDegreeOrHigher': 'Pós-graduação',
}

FLAGS = flags.FLAGS
if "output_file" not in FLAGS:
    flags.DEFINE_string(
        "output_file",
        "",
        "Output CSV file path. Defaults to input_files/brazil_education.csv.",
    )
if "fallback_to_cached" not in FLAGS:
    flags.DEFINE_boolean(
        "fallback_to_cached",
        False,
        "Whether to fallback to locally cached CSV if live download fails.",
    )

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, "brazil_education.csv")


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


def load_municipal_mapping() -> Dict[str, str]:
    """Loads place code mapping to wikidata ID."""
    candidate_paths = [
        os.path.join(SCRIPT_DIR, "..", "..", "scratch", "intermediate_files", "muncial_state_brazil_mapping.json"),
        os.path.join("/data", "scratch", "intermediate_files", "muncial_state_brazil_mapping.json"),
        os.path.join(SCRIPT_DIR, "..", "..", "..", "scratch", "intermediate_files", "muncial_state_brazil_mapping.json"),
    ]
    for p in candidate_paths:
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}


def parse_raw_education_xls(file_content: bytes, mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """Parses raw IBGE Table 4.1.1 education XLS workbook."""
    rows: List[Dict[str, Any]] = []
    try:
        df = pd.read_excel(io.BytesIO(file_content))
        if len(df) <= 6:
            return rows
        header_row = df.iloc[6]
        col_map: Dict[int, str] = {}
        code_idx = None
        for idx, c in enumerate(header_row):
            c_str = str(c).strip()
            if "Código da Unidade Geográfica" in c_str:
                code_idx = idx
            elif c_str in RAW_COL_TO_NIVEL:
                col_map[idx] = RAW_COL_TO_NIVEL[c_str]

        for r_idx in range(7, len(df)):
            r = df.iloc[r_idx]
            code = r.iloc[code_idx] if code_idx is not None else None
            if pd.isna(code):
                continue
            try:
                code_int = int(code)
            except (ValueError, TypeError):
                continue

            place_resolved = mapping.get(str(code_int))
            if not place_resolved:
                continue

            clean_place = place_resolved.replace("dcid:", "")
            clean_place = DCID_TO_PLACE_NAME.get(clean_place, clean_place)

            for c_idx, nivel in col_map.items():
                val = r.iloc[c_idx]
                if pd.isna(val):
                    continue
                try:
                    val_int = int(round(float(val)))
                except (ValueError, TypeError):
                    continue

                rows.append({
                    "Ano": 2000,
                    "Localidade": clean_place,
                    "RedeEnsino": "Total",
                    "NivelEnsino": nivel,
                    "Estudantes": val_int,
                })
    except Exception as e:
        logging.warning(f"Error parsing raw education XLS: {e}")
    return rows


def fetch_from_ibge_ftp_or_input_files(session: requests.Session) -> List[Dict[str, Any]]:
    """Fetches municipal education workbooks from live IBGE FTP or raw input files."""
    rows: List[Dict[str, Any]] = []
    mapping = load_municipal_mapping()

    # 1. Primary: Attempt live download from official IBGE FTP portal
    try:
        logging.info("Attempting download of 2000 Census education workbooks from official IBGE FTP portal...")
        for uf in UF_CODES_2000:
            zip_url = f"{IBGE_FTP_2000_EDUCATION_BASE}{uf}.zip"
            res = session.get(zip_url, timeout=30)
            if res.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                    for name in z.namelist():
                        if name.endswith(".xls") and "010100" in name:
                            content = z.read(name)
                            rows.extend(parse_raw_education_xls(content, mapping))
        if rows:
            logging.info(f"Successfully downloaded and parsed {len(rows)} records from live IBGE FTP portal.")
            return rows
    except Exception as e:
        logging.warning(f"Live IBGE FTP download failed ({e}). Checking raw input files...")

    # 2. Secondary: Try local scratch input_files
    scratch_dir = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", "Brazil_2000_education_input")
    alt_scratch = os.path.join("/data", "scratch", "input_files", "Brazil_2000_education_input")
    local_dir = scratch_dir if os.path.isdir(scratch_dir) else (alt_scratch if os.path.isdir(alt_scratch) else None)

    if local_dir:
        xls_files = sorted(glob.glob(os.path.join(local_dir, "*.xls")))
        for fpath in xls_files:
            with open(fpath, "rb") as f:
                rows.extend(parse_raw_education_xls(f.read(), mapping))
        if rows:
            logging.info(f"Parsed {len(rows)} rows from local raw education input files.")
            return rows

    # 3. Tertiary: Try GCS raw input_files
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blobs = list(bucket.list_blobs(prefix=GCS_INPUT_DIR))
        for b in blobs:
            if b.name.endswith(".xls"):
                content = b.download_as_bytes()
                rows.extend(parse_raw_education_xls(content, mapping))
        if rows:
            logging.info(f"Parsed {len(rows)} rows from GCS raw education input files.")
            return rows
    except Exception as e:
        logging.warning(f"Could not load raw education files from GCS gs://{GCS_BUCKET_NAME}/{GCS_INPUT_DIR}: {e}")

    return rows


IBGE_STATE_CODE_TO_NAME = {
    "11": "Rondônia",
    "12": "Acre",
    "13": "Amazonas",
    "14": "Roraima",
    "15": "Pará",
    "16": "Amapá",
    "17": "Tocantins",
    "21": "Maranhão",
    "22": "Piauí",
    "23": "Ceará",
    "24": "Rio Grande do Norte",
    "25": "Paraíba",
    "26": "Pernambuco",
    "27": "Alagoas",
    "28": "Sergipe",
    "29": "Bahia",
    "31": "Minas Gerais",
    "32": "Espírito Santo",
    "33": "Rio de Janeiro",
    "35": "São Paulo",
    "41": "Paraná",
    "42": "Santa Catarina",
    "43": "Rio Grande do Sul",
    "50": "Mato Grosso do Sul",
    "51": "Mato Grosso",
    "52": "Goiás",
    "53": "Distrito Federal",
}

RAW_2010_COL_TO_NIVEL = {
    1: 'Total',
    2: 'Creche',
    3: 'Pré-escolar',
    4: 'Classe de alfabetização',
    5: 'Educação de Jovens e Adultos',
    6: 'Fundamental',
    7: 'Médio',
    8: 'Superior Graduação',
    9: 'Pós-graduação',
}


def parse_2010_education_file(content_bytes: bytes, rede: str) -> List[Dict[str, Any]]:
    """Parses a 2010 education state XLS workbook (public or private)."""
    rows = []
    try:
        df = pd.read_excel(io.BytesIO(content_bytes), header=None, skiprows=3)
        header_idx = None
        for idx in range(10):
            val = str(df.iloc[idx, 1]).strip()
            if "Student PublicSchool" in val or "Student PrivateSchool" in val:
                header_idx = idx
                break
        if header_idx is None:
            return rows
        muni_start = None
        for idx in range(header_idx + 1, len(df)):
            val = df.iloc[idx, 0]
            if pd.notna(val) and "munic" in str(val).lower():
                muni_start = idx + 1
                break
        if muni_start is None:
            muni_start = header_idx + 1
        code_col = 10 if df.shape[1] > 10 else None
        if code_col is None:
            for col_i in range(df.shape[1]):
                for row_i in range(header_idx + 1):
                    if "código" in str(df.iloc[row_i, col_i]).lower() or "codigo" in str(df.iloc[row_i, col_i]).lower():
                        code_col = col_i
                        break
                if code_col is not None:
                    break

        for idx in range(len(df)):
            val0 = str(df.iloc[idx, 0]).strip()
            if val0 == "Total":
                raw_code = str(df.iloc[idx, code_col]).strip() if (code_col is not None and code_col < df.shape[1]) else ""
                if raw_code and raw_code.isnumeric() and len(raw_code) == 2:
                    state_loc = IBGE_STATE_CODE_TO_NAME.get(raw_code, raw_code)
                    for c_idx, nivel in RAW_2010_COL_TO_NIVEL.items():
                        if nivel != "Classe de alfabetização":
                            continue
                        if c_idx < df.shape[1]:
                            val = df.iloc[idx, c_idx]
                            if pd.notna(val) and str(val).strip() not in ["-", "...", "..", ""]:
                                try:
                                    val_int = int(round(float(val)))
                                    rows.append({
                                        "Ano": 2010,
                                        "Localidade": state_loc,
                                        "RedeEnsino": rede,
                                        "NivelEnsino": nivel,
                                        "Estudantes": val_int,
                                    })
                                except (ValueError, TypeError):
                                    pass
                break

        for idx in range(muni_start, len(df)):
            raw_code = str(df.iloc[idx, code_col]).strip() if (code_col is not None and code_col < df.shape[1]) else ""
            is_muni_code = raw_code.isnumeric() and len(raw_code) == 7
            place = raw_code if is_muni_code else str(df.iloc[idx, 0]).strip()
            if not place or (pd.isna(df.iloc[idx, 0]) and not is_muni_code):
                continue
            if place == "nan" or "fonte" in place.lower() or "nota" in place.lower():
                continue
            for c_idx, nivel in RAW_2010_COL_TO_NIVEL.items():
                if c_idx >= df.shape[1]:
                    continue
                val = df.iloc[idx, c_idx]
                if pd.isna(val) or str(val).strip() in ["-", "...", "..", ""]:
                    continue
                try:
                    val_int = int(round(float(val)))
                    rows.append({
                        "Ano": 2010,
                        "Localidade": place,
                        "RedeEnsino": rede,
                        "NivelEnsino": nivel,
                        "Estudantes": val_int,
                    })
                except (ValueError, TypeError):
                    continue
    except Exception as e:
        logging.warning(f"Error parsing 2010 education XLS ({rede}): {e}")
    return rows


def fetch_2010_education_files() -> List[Dict[str, Any]]:
    """Loads 2010 municipal education workbooks across all states for public and private schools."""
    rows = []
    for folder, rede in [
        ("Brazil_2010_education_public_input", "Pública"),
        ("Brazil_2010_education_private_input", "Particular"),
    ]:
        scratch_dir = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", folder)
        alt_scratch = os.path.join("/data", "scratch", "input_files", folder)
        local_dir = scratch_dir if os.path.isdir(scratch_dir) else (alt_scratch if os.path.isdir(alt_scratch) else None)

        if local_dir:
            xls_files = sorted(glob.glob(os.path.join(local_dir, "*.xls")))
            for fpath in xls_files:
                with open(fpath, "rb") as f:
                    rows.extend(parse_2010_education_file(f.read(), rede))
        else:
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket(GCS_BUCKET_NAME)
                blobs = list(bucket.list_blobs(prefix=f"country/brazil/input_files/{folder}"))
                for b in blobs:
                    if b.name.endswith(".xls"):
                        content = b.download_as_bytes()
                        rows.extend(parse_2010_education_file(content, rede))
            except Exception as e:
                logging.warning(f"Could not load 2010 education files from GCS for {folder}: {e}")
    return rows


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census education data across past, present, and future censuses."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    all_rows: List[Dict[str, Any]] = []

    try:
        # 1. Live SIDRA API (Table 1972)
        try:
            raw_sidra = fetch_sidra_data(session, TABLE_1972_API_URL)
            logging.info(f"Retrieved {len(raw_sidra) - 1} records from SIDRA Table 1972.")
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
                rede = str(r.get("D4N", "Total")).strip()
                nivel_raw = str(r.get("D5N", "Total")).strip()

                nivel = "Total"
                if "Creche" in nivel_raw:
                    nivel = "Creche"
                elif "Pré-escolar" in nivel_raw:
                    nivel = "Pré-escolar"
                elif "fundamental" in nivel_raw.lower():
                    nivel = "Fundamental"
                elif "médio" in nivel_raw.lower():
                    nivel = "Médio"
                elif "graduação" in nivel_raw.lower():
                    nivel = "Superior Graduação"
                elif "mestrado" in nivel_raw.lower() or "doutorado" in nivel_raw.lower():
                    nivel = "Pós-graduação"
                elif "adultos" in nivel_raw.lower():
                    nivel = "Educação de Jovens e Adultos"

                all_rows.append({
                    "Ano": year,
                    "Localidade": loc,
                    "RedeEnsino": rede,
                    "NivelEnsino": nivel,
                    "Estudantes": val,
                })
        except Exception as e:
            logging.warning(f"Live SIDRA Table 1972 query failed: {e}")

        # 2. Historical & Municipal data from live IBGE FTP portal or raw input files
        raw_input_rows = fetch_from_ibge_ftp_or_input_files(session)
        all_rows.extend(raw_input_rows)

        # 3. 2010 Municipal Education workbooks (Public and Private)
        rows_2010 = fetch_2010_education_files()
        all_rows.extend(rows_2010)

    except Exception as e:
        if fallback_to_cached and os.path.isfile(target_path):
            logging.warning(f"Download failed ({e}). Falling back to cached copy: {target_path}")
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(f"Error downloading Brazil Census education data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No education records retrieved from data sources.")

    if os.path.abspath(target_path) == os.path.abspath(DEFAULT_OUTPUT_FILE) and os.path.isfile(target_path):
        try:
            cached_df = pd.read_csv(target_path, low_memory=False)
            all_rows = cached_df.to_dict("records") + all_rows
        except Exception:
            pass
    df = pd.DataFrame(all_rows).drop_duplicates(subset=["Ano", "Localidade", "RedeEnsino", "NivelEnsino"])
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
    counters_file = os.path.join(counters_dir, "brazil_education_counters.csv")
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
        logging.info(f"Education download completed successfully: {saved_file}")
    except Exception as e:
        logging.fatal(f"Fatal error downloading Brazil Census education data: {e}", exc_info=True)


if __name__ == "__main__":
    app.run(main)
