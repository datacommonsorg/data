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
1. Live IBGE SIDRA REST API:
   - Table 1972 for 2000 and 2010 (by education level and public/private school network).
   - Tables 10057, 10058, 10059 for 2022 (student attendance across 3 age cohorts: 0-5, 6-17, 18+ across n1/n2/n3/n6).
2. Official IBGE Census Downloads Portal (https://ftp.ibge.gov.br/Censos/Censo_Demografico_2000/educacao/Municipios/)
   for municipal-level education workbooks.
3. Historical raw input files from GCS (gs://unresolved_mcf/country/brazil/input_files/Brazil_2000_education_input/*.xls
   and Brazil_2010_education_{public,private}_input/*.xls).
"""

import io
import json
import os
import shutil
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from absl import app, flags, logging
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

SIDRA_BASE_URL = "https://apisidra.ibge.gov.br"
# Table 1972: Pessoas que frequentavam escola ou creche por rede e nível de ensino (2000, 2010)
TABLE_1972_API_URL = (f"{SIDRA_BASE_URL}/values/t/1972/n1/all/n2/all/n3/all"
                      f"/v/690/p/all/c11797/all/c11798/all?formato=json")

# 2022 SIDRA Education tables across 3 disjoint age cohorts (chunked by c11798 to stay <50,000 rows across n6/all):
# Table 10057: Pessoas de até 5 anos (v/13282)
# Table 10058: Pessoas de 6 a 17 anos (v/13283)
# Table 10059: Pessoas de 18 anos ou mais (v/13284)
TABLE_2022_EDUCATION_SPECS: List[Tuple[str, str, str, str]] = [
    ("sidra_10057_n6.json", "10057", "13282", "all"),
    (
        "sidra_10058_p1_n6.json",
        "10058",
        "13283",
        "95300,95301,107454,7905,7906",
    ),
    ("sidra_10058_p2_n6.json", "10058", "13283", "7907,7908,7909,95307"),
    (
        "sidra_10059_p1_n6.json",
        "10059",
        "13284",
        "95300,7905,7906,7907,7908",
    ),
    ("sidra_10059_p2_n6.json", "10059", "13284", "7909,95307,7911,7912"),
]

D4C_2022_TO_NIVEL: Dict[str, str] = {
    "95300": "Total",
    "95301": "Creche",
    "107454": "Pré-escolar",
    "7905": "Educação de Jovens e Adultos",
    "7907": "Educação de Jovens e Adultos",
    "7909": "Educação de Jovens e Adultos",
    "7906": "Fundamental",
    "7908": "Médio",
    "95307": "Superior Graduação",
    "7911": "Pós-graduação",
    "7912": "Pós-graduação",
}

IBGE_FTP_2000_EDUCATION_BASE = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2000/educacao/Municipios/"
)
GCS_BUCKET_NAME = "unresolved_mcf"
GCS_INPUT_DIR = "country/brazil/input_files/Brazil_2000_education_input"

UF_CODES_2000 = [
    "ac",
    "al",
    "am",
    "ap",
    "ba",
    "ce",
    "df",
    "es",
    "go",
    "ma",
    "mg",
    "ms",
    "mt",
    "pa",
    "pb",
    "pe",
    "pi",
    "pr",
    "rj",
    "rn",
    "ro",
    "rr",
    "rs",
    "sc",
    "se",
    "sp",
    "to",
]

RAW_COL_TO_NIVEL = {
    "Total Student": "Total",
    "Student Nursery": "Creche",
    "Student PreKindergarten": "Pré-escolar",
    "Student AdultEducation": "Educação de Jovens e Adultos",
    "Student PrimaryEducation": "Fundamental",
    "Student BRA_HighSchool": "Médio",
    "Student PreEntranceExam": "Pré-vestibular",
    "Student BachelorsDegree": "Superior Graduação",
    "Student MastersDegreeOrHigher": "Pós-graduação",
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


def load_municipal_mapping(raw_dir: Optional[str] = None) -> Dict[str, str]:
    """Loads place code mapping to wikidata ID from GCS."""
    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(
        "country/brazil/intermediate_files/muncial_state_brazil_mapping.json")
    text = blob.download_as_text()
    if raw_dir:
        with open(
                os.path.join(raw_dir, "muncial_state_brazil_mapping.json"),
                "w",
                encoding="utf-8",
        ) as f:
            f.write(text)
    mapping = json.loads(text)
    if not mapping:
        raise RuntimeError("Loaded empty municipal mapping from GCS.")
    return mapping


def parse_raw_education_xls(file_content: bytes,
                            mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """Parses raw IBGE Table 4.1.1 education XLS workbook."""
    rows: List[Dict[str, Any]] = []
    df = pd.read_excel(io.BytesIO(file_content))
    if len(df) <= 6:
        raise ValueError("2000 education XLS workbook has fewer than 7 rows.")
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

        for c_idx, nivel in col_map.items():
            val = r.iloc[c_idx]
            if pd.isna(val) or str(val).strip() in ["-", "...", "..", "X", ""]:
                continue
            try:
                val_int = int(round(float(val)))
            except (ValueError, TypeError):
                continue

            rows.append({
                "Ano": 2000,
                "Localidade": place_resolved,
                "RedeEnsino": "Total",
                "NivelEnsino": nivel,
                "Estudantes": val_int,
            })
    if not rows:
        raise ValueError("Parsed 0 rows from 2000 education XLS workbook.")
    return rows


def fetch_from_ibge_ftp_or_input_files(
    session: requests.Session,
    raw_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetches municipal education workbooks from live IBGE FTP or GCS raw input files."""
    mapping = load_municipal_mapping(raw_dir=raw_dir)

    # 1. Primary: Attempt complete live download from official IBGE FTP portal.
    # Stage rows and raw payloads until all 27 UFs succeed so partial FTP failures
    # never leak into raw_dir or mix with GCS fallback rows.
    ftp_rows: List[Dict[str, Any]] = []
    ftp_blobs: List[Tuple[str, bytes]] = []
    try:
        logging.info(
            "Attempting download of 2000 Census education workbooks from official IBGE FTP portal..."
        )
        downloaded_ufs = 0
        for uf in UF_CODES_2000:
            zip_url = f"{IBGE_FTP_2000_EDUCATION_BASE}{uf}.zip"
            res = session.get(zip_url, timeout=30)
            res.raise_for_status()
            uf_has_xls = False
            with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                for name in z.namelist():
                    if name.endswith(".xls") and "010100" in name:
                        content = z.read(name)
                        ftp_rows.extend(
                            parse_raw_education_xls(content, mapping))
                        ftp_blobs.append((os.path.basename(name), content))
                        uf_has_xls = True
            if uf_has_xls:
                downloaded_ufs += 1
        if downloaded_ufs == len(UF_CODES_2000) and ftp_rows:
            if raw_dir:
                for fname, content in ftp_blobs:
                    with open(os.path.join(raw_dir, fname), "wb") as f:
                        f.write(content)
            logging.info(
                f"Successfully downloaded and parsed {len(ftp_rows)} records from live IBGE FTP portal."
            )
            return ftp_rows
        logging.warning(
            f"Incomplete IBGE FTP download ({downloaded_ufs}/{len(UF_CODES_2000)} UFs). Falling back to GCS raw input files..."
        )
    except Exception as e:
        logging.warning(
            f"Live IBGE FTP download failed ({e}). Falling back to GCS raw input files..."
        )

    # 2. Secondary: GCS raw input_files
    from google.cloud import storage

    rows: List[Dict[str, Any]] = []
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix=GCS_INPUT_DIR))
    for b in blobs:
        if b.name.endswith(".xls"):
            content = b.download_as_bytes()
            if raw_dir:
                with open(os.path.join(raw_dir, os.path.basename(b.name)),
                          "wb") as f:
                    f.write(content)
            rows.extend(parse_raw_education_xls(content, mapping))
    if not rows:
        raise RuntimeError(
            f"No 2000 education rows loaded from FTP or GCS gs://{GCS_BUCKET_NAME}/{GCS_INPUT_DIR}."
        )
    logging.info(f"Parsed {len(rows)} rows from GCS raw education input files.")
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

STATE_CODE_TO_SIGLA = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}

RAW_2010_COL_TO_NIVEL = {
    1: "Total",
    2: "Creche",
    3: "Pré-escolar",
    4: "Classe de alfabetização",
    5: "Educação de Jovens e Adultos",
    6: "Fundamental",
    7: "Médio",
    8: "Superior Graduação",
    9: "Pós-graduação",
}


def parse_2010_education_file(content_bytes: bytes,
                              rede: str) -> List[Dict[str, Any]]:
    """Parses a 2010 education state XLS workbook (public or private)."""
    rows = []
    df = pd.read_excel(io.BytesIO(content_bytes), header=None, skiprows=3)
    header_idx = None
    for idx in range(10):
        val = str(df.iloc[idx, 1]).strip()
        if "Student PublicSchool" in val or "Student PrivateSchool" in val:
            header_idx = idx
            break
    if header_idx is None:
        raise ValueError(
            f"Could not find header row in 2010 education XLS ({rede}).")
    code_col = 10 if df.shape[1] > 10 else None
    if code_col is None:
        for col_i in range(df.shape[1]):
            for row_i in range(header_idx + 1):
                if ("código" in str(df.iloc[row_i, col_i]).lower() or
                        "codigo" in str(df.iloc[row_i, col_i]).lower()):
                    code_col = col_i
                    break
            if code_col is not None:
                break

    first_7 = None
    if code_col is not None and code_col < df.shape[1]:
        for idx in range(header_idx + 1, len(df)):
            raw_code = str(df.iloc[idx, code_col]).strip()
            if raw_code.isnumeric() and len(raw_code) == 7:
                first_7 = idx
                break

    muni_start = first_7
    if muni_start is None:
        for idx in range(header_idx + 1, len(df)):
            val = df.iloc[idx, 0]
            if pd.notna(val) and "munic" in str(val).lower():
                muni_start = idx + 1
                break
    if muni_start is None:
        muni_start = header_idx + 1

    state_code = ""
    for idx in range(len(df)):
        val0 = str(df.iloc[idx, 0]).strip()
        if val0 == "Total":
            raw_code = (str(df.iloc[idx, code_col]).strip() if
                        (code_col is not None and
                         code_col < df.shape[1]) else "")
            if raw_code and raw_code.isnumeric() and len(raw_code) == 2:
                state_code = raw_code
                state_loc = IBGE_STATE_CODE_TO_NAME.get(raw_code, raw_code)
                for c_idx, nivel in RAW_2010_COL_TO_NIVEL.items():
                    if nivel != "Classe de alfabetização":
                        continue
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
        raw_code = (str(df.iloc[idx, code_col]).strip() if
                    (code_col is not None and code_col < df.shape[1]) else "")
        is_muni_code = raw_code.isnumeric() and len(raw_code) == 7
        val0 = "" if pd.isna(df.iloc[idx, 0]) else str(df.iloc[idx, 0]).strip()
        if is_muni_code:
            place = raw_code
        else:
            if not val0:
                continue
            val0_lower = val0.lower()
            if (val0_lower == "nan" or "continua" in val0_lower or
                ("fonte" in val0_lower and "fonte boa" not in val0_lower) or
                    "nota" in val0_lower):
                continue
            sigla = STATE_CODE_TO_SIGLA.get(state_code, "")
            place = f"{val0} - {sigla}" if sigla else val0
        for c_idx, nivel in RAW_2010_COL_TO_NIVEL.items():
            if c_idx >= df.shape[1]:
                continue
            val = df.iloc[idx, c_idx]
            if pd.isna(val) or str(val).strip() in ["-", "...", "..", "X", ""]:
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
    if not rows:
        raise ValueError(f"Parsed 0 rows from 2010 education XLS ({rede}).")
    return rows


def fetch_2010_education_files(
        raw_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Loads 2010 municipal education workbooks across all states for public and private schools."""
    from google.cloud import storage

    rows = []
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    for folder, rede in [
        ("Brazil_2010_education_public_input", "Pública"),
        ("Brazil_2010_education_private_input", "Particular"),
    ]:
        blobs = list(
            bucket.list_blobs(prefix=f"country/brazil/input_files/{folder}"))
        folder_rows = []
        for b in blobs:
            if b.name.endswith(".xls"):
                content = b.download_as_bytes()
                if raw_dir:
                    with open(os.path.join(raw_dir, os.path.basename(b.name)),
                              "wb") as f:
                        f.write(content)
                folder_rows.extend(parse_2010_education_file(content, rede))
        if not folder_rows:
            raise RuntimeError(
                f"No 2010 education rows loaded from GCS for {folder}.")
        rows.extend(folder_rows)
    return rows


def fetch_2022_education_sidra(
    session: requests.Session,
    raw_dir: Optional[str] = None,
) -> Dict[Tuple[int, str, str, str], int]:
    """Fetches 2022 student attendance by education level from SIDRA Tables 10057, 10058, 10059.

  Sums student counts across the three disjoint age cohorts:
  - Table 10057: Pessoas de até 5 anos (v/13282)
  - Table 10058: Pessoas de 6 a 17 anos (v/13283)
  - Table 10059: Pessoas de 18 anos ou mais (v/13284)
  providing complete 2022 observations for RedeEnsino='Total' across all territorial levels (n1/n2/n3/n6).
  """
    sidra_2022_acc: Dict[Tuple[int, str, str, str], int] = {}
    for fname, tid, vid, c11798_codes in TABLE_2022_EDUCATION_SPECS:
        url = f"{SIDRA_BASE_URL}/values/t/{tid}/n1/all/n2/all/n3/all/n6/all/v/{vid}/p/all/c11798/{c11798_codes}?formato=json"
        raw_data = fetch_sidra_data(
            session,
            url,
            raw_file_path=os.path.join(raw_dir, fname) if raw_dir else None,
        )
        for r in raw_data[1:]:
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

            d4c = str(r.get("D4C", "")).strip()
            nivel = D4C_2022_TO_NIVEL.get(d4c)
            if not nivel:
                continue

            key = (year, loc, "Total", nivel)
            sidra_2022_acc[key] = sidra_2022_acc.get(key, 0) + val
    return sidra_2022_acc


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census education data across past, present, and future censuses."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    raw_dir = _get_raw_dir(target_path)
    all_rows: List[Dict[str, Any]] = []

    try:
        # 1. Historical & Municipal data from live IBGE FTP portal or GCS raw input files (2000)
        raw_input_rows = fetch_from_ibge_ftp_or_input_files(session,
                                                            raw_dir=raw_dir)
        all_rows.extend(raw_input_rows)

        # 2. 2010 Municipal Education workbooks (Public and Private)
        rows_2010 = fetch_2010_education_files(raw_dir=raw_dir)
        all_rows.extend(rows_2010)

        # 3. Live SIDRA API (Table 1972 for 2000 and 2010)
        # Added after historical files so authoritative live SIDRA rows take precedence in drop_duplicates(keep="last").
        raw_sidra = fetch_sidra_data(
            session,
            TABLE_1972_API_URL,
            raw_file_path=os.path.join(raw_dir, "sidra_1972_macro.json"),
        )
        logging.info(
            f"Retrieved {len(raw_sidra) - 1} records from SIDRA Table 1972.")
        sidra_acc: Dict[tuple, int] = {}
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

            loc = str(r.get("D1N", "")).strip()
            if loc == "Brasil":
                loc = "Brazil"
            rede = str(r.get("D4N", "Total")).strip()
            d5c = str(r.get("D5C", "")).strip()
            nivel_raw = str(r.get("D5N", "")).strip()

            nivel = None
            if d5c == "0" or (not d5c and nivel_raw == "Total"):
                nivel = "Total"
            elif d5c == "95301" or (not d5c and nivel_raw == "Creche"):
                nivel = "Creche"
            elif d5c in ("95302", "107454") or (not d5c and nivel_raw in (
                    "Pré-escolar",
                    "Pré-escolar ou classe de alfabetização",
            )):
                nivel = "Pré-escolar"
            elif d5c == "7904" or (not d5c and
                                   nivel_raw == "Classe de alfabetização"):
                nivel = "Classe de alfabetização"
            elif d5c in ("95303", "7905") or (not d5c and nivel_raw in (
                    "Alfabetização de adultos",
                    "Alfabetização de jovens e adultos",
                    "Educação de Jovens e Adultos",
            )):
                nivel = "Educação de Jovens e Adultos"
            elif d5c in ("95304", "7906") or (not d5c and nivel_raw in (
                    "Fundamental",
                    "Regular de ensino fundamental",
            )):
                nivel = "Fundamental"
            elif d5c in ("95305", "7908") or (not d5c and nivel_raw in (
                    "Médio",
                    "Regular do ensino médio",
            )):
                nivel = "Médio"
            elif d5c == "95306" or (not d5c and nivel_raw == "Pré-vestibular"):
                nivel = "Pré-vestibular"
            elif d5c == "95307" or (not d5c and nivel_raw in (
                    "Superior de graduação",
                    "Superior Graduação",
            )):
                nivel = "Superior Graduação"
            elif d5c in ("95308", "7911", "7912") or (not d5c and nivel_raw in (
                    "Mestrado ou doutorado",
                    "Mestrado",
                    "Doutorado",
                    "Pós-graduação",
            )):
                nivel = "Pós-graduação"

            if nivel is None:
                continue
            if nivel == "Pré-vestibular" and rede != "Total":
                continue
            if nivel == "Classe de alfabetização" and rede == "Total":
                continue

            key = (year, loc, rede, nivel)
            sidra_acc[key] = sidra_acc.get(key, 0) + val

        for (year, loc, rede, nivel), val in sidra_acc.items():
            all_rows.append({
                "Ano": year,
                "Localidade": loc,
                "RedeEnsino": rede,
                "NivelEnsino": nivel,
                "Estudantes": val,
            })

        # 4. Live 2022 Census Education from SIDRA Tables 10057, 10058, 10059
        sidra_2022_acc = fetch_2022_education_sidra(session, raw_dir=raw_dir)
        for (year, loc, rede, nivel), val in sidra_2022_acc.items():
            all_rows.append({
                "Ano": year,
                "Localidade": loc,
                "RedeEnsino": rede,
                "NivelEnsino": nivel,
                "Estudantes": val,
            })

    except Exception as e:
        if fallback_to_cached and os.path.isfile(target_path):
            logging.warning(
                f"Download failed ({e}). Falling back to cached copy: {target_path}"
            )
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(
            f"Error downloading Brazil Census education data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No education records retrieved from data sources.")

    df = pd.DataFrame(all_rows).drop_duplicates(
        subset=["Ano", "Localidade", "RedeEnsino", "NivelEnsino"], keep="last")
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
        f"Successfully generated Brazil Census education data at: {saved_file}")


if __name__ == "__main__":
    app.run(main)
