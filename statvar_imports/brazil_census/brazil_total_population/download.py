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
1. Live IBGE SIDRA REST API:
   - Table 9514 (2022+ Census resident population by sex across n1/n2/n3/n6)
   - Table 1378 (2010 Census resident population by sex across n1/n2/n3; municipal sex disaggregations are provided by brazil_population_by_age_and_sex)
   - Table 6579 (2024–2026+ annual resident population estimates across n1/n2/n3/n6)
2. Historical input workbooks from GCS input_files:
   - Brazil_2022_Muncipal_POP.xlsx (all 5,570 Brazilian municipalities)
   - POP2022_Brasil_e_UFs.xls (National & State 2022 counts)
   - POPU91*.XLS (1991 Census across all 27 Brazilian states)
"""

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
# Table 9514: População residente por sexo (2022+ Census across n1/n2/n3/n6)
TABLE_9514_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/9514/n1/all/n2/all/n3/all/n6/all"
    f"/v/93/p/all/c2/all/c287/100362/c286/113635?formato=json")
# Table 1378: População residente por sexo (2010 Census)
TABLE_1378_API_URL = (f"{SIDRA_BASE_URL}/values/t/1378/n1/all/n2/all/n3/all"
                      f"/v/93/p/all/c1/0/c2/all/c287/0/c455/0?formato=json")
# Table 6579: EstimaPop — População residente estimada (annual post-2022 estimates across n1/n2/n3/n6)
TABLE_6579_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/6579/n1/all/n2/all/n3/all/n6/all"
    f"/v/9324/p/last%205?formato=json")

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
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR,
                                   "brazil_total_population.csv")


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


def load_place_mappings(
    raw_dir: Optional[str] = None,) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Loads municipal mapping and 1991 place mapping from GCS."""
    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    b_muni = bucket.blob(
        "country/brazil/intermediate_files/muncial_state_brazil_mapping.json")
    b_91 = bucket.blob(
        "country/brazil/intermediate_files/Brazil_Place_Mapping_1991.json")
    muni_text = b_muni.download_as_text()
    map_91_text = b_91.download_as_text()
    if raw_dir:
        with open(
                os.path.join(raw_dir, "muncial_state_brazil_mapping.json"),
                "w",
                encoding="utf-8",
        ) as f:
            f.write(muni_text)
        with open(
                os.path.join(raw_dir, "Brazil_Place_Mapping_1991.json"),
                "w",
                encoding="utf-8",
        ) as f:
            f.write(map_91_text)
    muni_map = json.loads(muni_text)
    map_91 = json.loads(map_91_text)
    if not muni_map or not map_91:
        raise RuntimeError("Loaded empty place mappings from GCS.")
    return muni_map, map_91


def parse_raw_pop_xls(content_bytes: bytes) -> List[Dict[str, Any]]:
    """Parses raw IBGE POP2022_Brasil_e_UFs XLS workbook."""
    rows: List[Dict[str, Any]] = []
    df = pd.read_excel(io.BytesIO(content_bytes))
    for r_idx in range(1, len(df)):
        r = df.iloc[r_idx]
        place_raw = str(r.iloc[0]).strip()
        place_lower = place_raw.lower()
        if (not place_raw or pd.isna(r.iloc[0]) or
            ("fonte" in place_lower and "fonte boa" not in place_lower) or
                "nota" in place_lower):
            continue
        place = place_raw.replace("Região ", "").strip()
        if place in (
                "Unidades da Federação",
                "Grandes Regiões",
                "Brasil e Unidades da Federação",
        ):
            continue
        if place == "Brasil":
            place = "Brazil"

        val = (r.iloc[1] if len(r) > 1 and not pd.isna(r.iloc[1]) else
               (r.iloc[2] if len(r) > 2 else None))
        if pd.isna(val) or val is None or str(val).strip() in [
                "-",
                "...",
                "..",
                "X",
                "",
        ]:
            continue
        try:
            val_int = int(round(float(val)))
        except (ValueError, TypeError):
            continue

        rows.append({
            "Ano": 2022,
            "Localidade": place,
            "Sexo": "Total",
            "Populacao": val_int,
        })
    if not rows:
        raise ValueError("Parsed 0 rows from POP2022_Brasil_e_UFs.xls.")
    return rows


def parse_raw_municipal_2022(content_bytes: bytes,
                             mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """Parses raw Brazil_2022_Muncipal_POP.xlsx workbook."""
    rows: List[Dict[str, Any]] = []
    df = pd.read_excel(io.BytesIO(content_bytes))
    for _, r in df.iterrows():
        cod_uf = str(r.get("COD. UF", "")).strip()
        cod_muni = str(r.get("COD. MUNIC", "")).strip().zfill(5)
        full_code = cod_uf + cod_muni
        muni_name = str(r.get("NOME DO MUNICÍPIO", "")).strip()
        pop_str = (str(r.get("POPULAÇÃO",
                             "")).replace(",", "").replace(".", "").strip())
        try:
            pop = int(pop_str)
        except (ValueError, TypeError):
            continue
        place_id = mapping.get(full_code, muni_name).replace("dcid:", "")
        rows.append({
            "Ano": 2022,
            "Localidade": place_id,
            "Sexo": "Total",
            "Populacao": pop,
        })
    if not rows:
        raise ValueError("Parsed 0 rows from Brazil_2022_Muncipal_POP.xlsx.")
    return rows


def parse_raw_1991_popu(content_bytes: bytes,
                        map_91: Dict[str, str]) -> List[Dict[str, Any]]:
    """Parses raw 1991 POPU state workbook."""
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

        fem_val = row.iloc[1]
        masc_val = row.iloc[2]
        place_resolved = map_91.get(place_raw, place_raw).replace("dcid:", "")

        f_int = None
        m_int = None
        try:
            f_int = int(round(float(fem_val)))
            rows.append({
                "Ano": 1991,
                "Localidade": place_resolved,
                "Sexo": "Mulheres",
                "Populacao": f_int,
            })
        except (ValueError, TypeError):
            pass
        try:
            m_int = int(round(float(masc_val)))
            rows.append({
                "Ano": 1991,
                "Localidade": place_resolved,
                "Sexo": "Homens",
                "Populacao": m_int,
            })
        except (ValueError, TypeError):
            pass
        if f_int is not None and m_int is not None:
            rows.append({
                "Ano": 1991,
                "Localidade": place_resolved,
                "Sexo": "Total",
                "Populacao": f_int + m_int,
            })
    if not rows:
        raise ValueError("Parsed 0 rows from 1991 POPU workbook.")
    return rows


def fetch_raw_input_files(
        raw_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Reads raw input files from GCS input_files."""
    from google.cloud import storage

    rows: List[Dict[str, Any]] = []
    muni_map, map_91 = load_place_mappings(raw_dir=raw_dir)
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)

    # 1. 2022 Municipal POP
    blob_muni = bucket.blob(GCS_MUNI_2022_FILE)
    content_muni = blob_muni.download_as_bytes()
    if raw_dir:
        with open(os.path.join(raw_dir, "Brazil_2022_Muncipal_POP.xlsx"),
                  "wb") as f:
            f.write(content_muni)
    rows.extend(parse_raw_municipal_2022(content_muni, muni_map))

    # 2. 2022 UFs POP
    blob_uf = bucket.blob(GCS_POP_2022_FILE)
    content_uf = blob_uf.download_as_bytes()
    if raw_dir:
        with open(os.path.join(raw_dir, "POP2022_Brasil_e_UFs.xls"), "wb") as f:
            f.write(content_uf)
    rows.extend(parse_raw_pop_xls(content_uf))

    # 3. 1991 POPU state files
    blobs = list(
        bucket.list_blobs(
            prefix="country/brazil/input_files/Brazil_1991_gender/POPU91"))
    rows_1991: List[Dict[str, Any]] = []
    for b in blobs:
        bname = os.path.basename(b.name)
        if bname.upper().endswith(".XLS"):
            content = b.download_as_bytes()
            if raw_dir:
                with open(os.path.join(raw_dir, bname), "wb") as f:
                    f.write(content)
            rows_1991.extend(parse_raw_1991_popu(content, map_91))
    if not rows_1991:
        raise RuntimeError("No 1991 POPU records loaded from GCS.")
    rows.extend(rows_1991)

    return rows


def _load_local_places_map() -> Dict[str, str]:
    """Loads ../brazil_places_resolved.csv mapping 7-digit IBGE codes to DCIDs."""
    places_csv = os.path.join(SCRIPT_DIR, "..", "brazil_places_resolved.csv")
    mapping: Dict[str, str] = {}
    if os.path.isfile(places_csv):
        df = pd.read_csv(places_csv, dtype=str)
        for _, row in df.iterrows():
            name = str(row.get("place_name", row.get("name", ""))).strip()
            dcid = str(row.get("dcid", "")).strip().replace("dcid:", "")
            if name and dcid:
                mapping[name] = dcid
    return mapping


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census total population data across past, present, and future censuses."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    raw_dir = _get_raw_dir(target_path)
    all_rows: List[Dict[str, Any]] = []

    try:
        # 1. Raw input files from GCS (including Brazil_2022_Muncipal_POP.xlsx and POPU91*.XLS)
        raw_rows = fetch_raw_input_files(raw_dir=raw_dir)
        all_rows.extend(raw_rows)
        muni_map = _load_local_places_map()

        # 2. 2022+ Census from SIDRA API (Table 9514) — authoritative final census values override preliminary XLS
        raw_2022 = fetch_sidra_data(
            session,
            TABLE_9514_API_URL,
            raw_file_path=os.path.join(raw_dir, "sidra_9514_2022_n6.json"),
        )
        logging.info(
            f"Retrieved {len(raw_2022) - 1} records from SIDRA Table 9514.")
        for r in raw_2022[1:]:
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

            nc = str(r.get("NC", "")).strip()
            d1c = str(r.get("D1C", "")).strip()
            if nc == "6" and d1c:
                loc = muni_map.get(d1c, d1c).replace("dcid:", "")
            else:
                loc = str(r.get("D1N", "")).strip()
                if loc == "Brasil":
                    loc = "Brazil"

            sexo = str(r.get("D4N", "Total")).strip()
            all_rows.append({
                "Ano": year,
                "Localidade": loc,
                "Sexo": sexo,
                "Populacao": val,
            })

        # 3. 2010 Census from SIDRA API (Table 1378)
        raw_2010 = fetch_sidra_data(
            session,
            TABLE_1378_API_URL,
            raw_file_path=os.path.join(raw_dir, "sidra_1378_2010_macro.json"),
        )
        logging.info(
            f"Retrieved {len(raw_2010) - 1} records from SIDRA Table 1378.")
        for r in raw_2010[1:]:
            val_str = r.get("V")
            if val_str in ["-", "...", "..", "X", None, ""]:
                continue
            try:
                val = int(round(float(val_str)))
            except (ValueError, TypeError):
                continue

            loc = str(r.get("D1N", "")).strip()
            if loc == "Brasil":
                loc = "Brazil"

            sexo = str(r.get("D5N", "Total")).strip()
            all_rows.append({
                "Ano": 2010,
                "Localidade": loc,
                "Sexo": sexo,
                "Populacao": val,
            })

        # 4. Annual post-2022 population estimates from SIDRA API (Table 6579 across n1/n2/n3/n6)
        raw_6579 = fetch_sidra_data(
            session,
            TABLE_6579_API_URL,
            raw_file_path=os.path.join(raw_dir, "sidra_6579_estimates_n6.json"),
        )
        logging.info(
            f"Retrieved {len(raw_6579) - 1} records from SIDRA Table 6579.")
        for r in raw_6579[1:]:
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
            if year <= 2022:
                continue

            nc = str(r.get("NC", "")).strip()
            d1c = str(r.get("D1C", "")).strip()
            if nc == "6" and d1c:
                loc = muni_map.get(d1c, d1c).replace("dcid:", "")
            else:
                loc = str(r.get("D1N", "")).strip()
                if loc == "Brasil":
                    loc = "Brazil"

            all_rows.append({
                "Ano": year,
                "Localidade": loc,
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
            f"Error downloading Brazil Census total population data: {e}"
        ) from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No population records retrieved from data sources.")

    df = pd.DataFrame(all_rows).drop_duplicates(
        subset=["Ano", "Localidade", "Sexo"], keep="last")
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
        f"Total population download completed successfully: {saved_file}")


if __name__ == "__main__":
    app.run(main)
