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
"""Automated download script for Brazil Census Population by Age and Sex data.

Downloads resident population by detailed age and sex from official IBGE sources:
1. Live IBGE SIDRA REST API:
   - Table 9514: População residente por sexo e idade (2022 Census)
2. Raw historical census workbooks from GCS (1940, 1991, 2000):
   - Brazil_1940_age_sex.xls
   - Brazil_2000_age_sex.xls
   - POPU91*.XLS (1991 Census across all 27 Brazilian states)
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
# Table 9514: População residente por sexo e idade (v/93 = População residente, c2/all = Sexo, c287/100362 = Total age)
TABLE_9514_API_URL = f"{SIDRA_BASE_URL}/values/t/9514/n1/all/n2/all/n3/all/v/93/p/all/c2/all/c287/all?formato=json"

COHORTS_0_14 = ['0 a 4 anos', '5 a 9 anos', '10 a 14 anos']
COHORTS_15_59 = [
    '15 a 19 anos', '20 a 24 anos', '25 a 29 anos', '30 a 34 anos', '35 a 39 anos',
    '40 a 44 anos', '45 a 49 anos', '50 a 54 anos', '55 a 59 anos'
]

FLAGS = flags.FLAGS
if "output_file" not in FLAGS:
    flags.DEFINE_string(
        "output_file",
        "",
        "Output CSV file path. Defaults to input_files/brazil_population_by_age_and_sex.csv.",
    )
if "fallback_to_cached" not in FLAGS:
    flags.DEFINE_boolean(
        "fallback_to_cached",
        False,
        "Whether to fallback to locally cached CSV if live download fails.",
    )

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, "brazil_population_by_age_and_sex.csv")


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


def compute_broad_age_aggregations(rows: List[Dict[str, str]], year: str) -> List[Dict[str, str]]:
    """Computes De 0 a 14 anos, De 15 a 59 anos, and De 60 anos ou mais from 5-year cohorts."""
    lookup: Dict[str, Dict[str, int]] = {}
    for r in rows:
        if r["Ano"] != year:
            continue
        key = f"{r['Localidade']}||{r['Sexo']}"
        if key not in lookup:
            lookup[key] = {}
        idade = r["Idade"]
        try:
            val = int(round(float(r["Populacao"].replace(",", "."))))
            lookup[key][idade] = val
        except (ValueError, TypeError):
            continue

    agg_rows: List[Dict[str, str]] = []
    for key, idade_dict in lookup.items():
        localidade, sexo = key.split("||", 1)

        # 0 to 14
        if any(c in idade_dict for c in COHORTS_0_14):
            sum_0_14 = sum(idade_dict.get(c, 0) for c in COHORTS_0_14)
            agg_rows.append({
                "Ano": year,
                "Localidade": localidade,
                "Idade": "De 0 a 14 anos",
                "Sexo": sexo,
                "Populacao": str(sum_0_14),
            })

        # 15 to 59
        if any(c in idade_dict for c in COHORTS_15_59):
            sum_15_59 = sum(idade_dict.get(c, 0) for c in COHORTS_15_59)
            agg_rows.append({
                "Ano": year,
                "Localidade": localidade,
                "Idade": "De 15 a 59 anos",
                "Sexo": sexo,
                "Populacao": str(sum_15_59),
            })

        # 60 and older: avoid double counting 80-99 if both 5-year and 10-year cohorts exist
        has_5yr_80_plus = any(c in idade_dict for c in ['80 a 84 anos', '85 a 89 anos', '90 a 94 anos', '95 a 99 anos'])
        cohorts_60 = ['60 a 64 anos', '65 a 69 anos', '70 a 74 anos', '75 a 79 anos', '100 anos ou mais']
        if has_5yr_80_plus:
            cohorts_60 += ['80 a 84 anos', '85 a 89 anos', '90 a 94 anos', '95 a 99 anos']
        else:
            cohorts_60 += ['80 a 89 anos', '90 a 99 anos']

        if any(c in idade_dict for c in cohorts_60):
            sum_60_plus = sum(idade_dict.get(c, 0) for c in cohorts_60)
            agg_rows.append({
                "Ano": year,
                "Localidade": localidade,
                "Idade": "De 60 anos ou mais",
                "Sexo": sexo,
                "Populacao": str(sum_60_plus),
            })

    return agg_rows


def parse_raw_hist_age_sex_xls(content_bytes: bytes, year: int) -> List[Dict[str, str]]:
    """Parses raw historical IBGE Table 4/5 age and sex XLS workbooks (1940, 2000)."""
    rows: List[Dict[str, str]] = []
    try:
        xls = pd.ExcelFile(io.BytesIO(content_bytes))
        sheet_sex = [
            (xls.sheet_names[0], 'Total'),
            (xls.sheet_names[1], 'Homens'),
            (xls.sheet_names[2], 'Mulheres'),
        ]
        idade_cols = {
            1: 'Total',
            2: 'De 0 a 14 anos',
            3: 'De 15 a 59 anos',
            4: 'De 60 anos ou mais',
        }
        for sname, sex in sheet_sex:
            df = pd.read_excel(xls, sheet_name=sname)
            for r_idx in range(7, len(df)):
                place = str(df.iloc[r_idx, 0]).strip()
                if not place or pd.isna(df.iloc[r_idx, 0]) or 'continua' in place.lower():
                    continue
                if place == 'Brasil':
                    place = 'Brazil'
                for col_i, idade in idade_cols.items():
                    if col_i >= df.shape[1]:
                        continue
                    val = df.iloc[r_idx, col_i]
                    if pd.isna(val) or str(val).strip() in ['-', '...', '..', '']:
                        continue
                    try:
                        val_int = int(round(float(val)))
                        rows.append({
                            'Ano': str(year),
                            'Localidade': place,
                            'Idade': idade,
                            'Sexo': sex,
                            'Populacao': str(val_int),
                        })
                    except (ValueError, TypeError):
                        pass
    except Exception as e:
        logging.warning(f"Error parsing {year} age/sex XLS: {e}")
    return rows


def parse_raw_1991_popu_age_sex(content_bytes: bytes, map_91: Dict[str, str]) -> List[Dict[str, str]]:
    """Parses raw 1991 POPU state workbook for age/sex import (Idade='Total')."""
    rows: List[Dict[str, str]] = []
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
            place_resolved = map_91.get(place_raw, place_raw)

            f_int = None
            m_int = None
            try:
                f_int = int(round(float(fem_val)))
                rows.append({"Ano": "1991", "Localidade": place_resolved, "Idade": "Total", "Sexo": "Mulheres", "Populacao": str(f_int)})
            except (ValueError, TypeError):
                pass
            try:
                m_int = int(round(float(masc_val)))
                rows.append({"Ano": "1991", "Localidade": place_resolved, "Idade": "Total", "Sexo": "Homens", "Populacao": str(m_int)})
            except (ValueError, TypeError):
                pass
            if f_int is not None and m_int is not None:
                rows.append({"Ano": "1991", "Localidade": place_resolved, "Idade": "Total", "Sexo": "Total", "Populacao": str(f_int + m_int)})
    except Exception as e:
        logging.warning(f"Error parsing 1991 POPU workbook: {e}")
    return rows


def load_1991_mapping() -> Dict[str, str]:
    """Loads 1991 place mapping from local scratch or GCS."""
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


def fetch_raw_historical_files() -> List[Dict[str, str]]:
    """Loads 1940, 1991, and 2000 historical age and sex records from raw input workbooks."""
    rows: List[Dict[str, str]] = []

    # 1. 1940 & 2000 raw age/sex workbooks
    for year, fname in [(1940, "Brazil_1940_age_sex.xls"), (2000, "Brazil_2000_age_sex.xls")]:
        scratch_p = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", fname)
        alt_p = os.path.join("/data", "scratch", "input_files", fname)
        local_path = scratch_p if os.path.isfile(scratch_p) else (alt_p if os.path.isfile(alt_p) else None)

        if local_path:
            with open(local_path, "rb") as f:
                rows.extend(parse_raw_hist_age_sex_xls(f.read(), year))
        else:
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket("unresolved_mcf")
                blob = bucket.blob(f"country/brazil/input_files/{fname}")
                content = blob.download_as_bytes()
                rows.extend(parse_raw_hist_age_sex_xls(content, year))
            except Exception as e:
                logging.warning(f"Could not load {fname} from GCS: {e}")

    # 2. 1991 raw POPU workbooks
    map_91 = load_1991_mapping()
    cand_dirs = [
        os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", "Brazil_1991_gender"),
        os.path.join("/data", "scratch", "input_files", "Brazil_1991_gender"),
    ]
    found_1991 = False
    for d in cand_dirs:
        if os.path.isdir(d):
            popu_files = sorted(glob.glob(os.path.join(d, "POPU91*.XLS")) + glob.glob(os.path.join(d, "*.xls")))
            for pf in popu_files:
                with open(pf, "rb") as f:
                    rows.extend(parse_raw_1991_popu_age_sex(f.read(), map_91))
                    found_1991 = True
            if found_1991:
                break
    if not found_1991:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket("unresolved_mcf")
            blobs = list(bucket.list_blobs(prefix="country/brazil/input_files/POPU91"))
            for b in blobs:
                if b.name.upper().endswith(".XLS"):
                    content = b.download_as_bytes()
                    rows.extend(parse_raw_1991_popu_age_sex(content, map_91))
        except Exception as e:
            logging.warning(f"Could not load 1991 POPU workbooks from GCS: {e}")

    return rows


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census population by age and sex across all census years."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    all_rows: List[Dict[str, str]] = []

    try:
        # 1. Historical data from raw input workbooks (1940, 1991, 2000)
        # Added first so live SIDRA API records take precedence on overlapping keys in drop_duplicates(keep="last").
        raw_rows = fetch_raw_historical_files()
        all_rows.extend(raw_rows)
        logging.info(f"Loaded {len(raw_rows)} raw historical age/sex records for 1940, 1991, and 2000.")

        # 2. Live SIDRA API (Table 9514 for 2022+)
        raw_json = fetch_sidra_data(session, TABLE_9514_API_URL)
        sidra_2022_rows: List[Dict[str, str]] = []
        for r in raw_json[1:]:
            loc = str(r.get("D1N", "")).strip()
            if loc == "Brasil":
                loc = "Brazil"
            sidra_2022_rows.append({
                "Ano": str(r.get("D3N", "2022")).strip(),
                "Localidade": loc,
                "Idade": str(r.get("D5N", "")).strip(),
                "Sexo": str(r.get("D4N", "")).strip(),
                "Populacao": str(r.get("V", "")).strip(),
            })
        all_rows.extend(sidra_2022_rows)

        # 3. Compute broad age aggregations (0To14, 15To59, 60OrMore) for 2022
        agg_rows = compute_broad_age_aggregations(sidra_2022_rows, "2022")
        all_rows.extend(agg_rows)

    except Exception as e:
        if fallback_to_cached and os.path.isfile(target_path):
            logging.warning(f"Live fetch failed ({e}). Fallback to existing: {target_path}")
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(f"Error downloading Brazil Census age/sex data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No age/sex records retrieved from data sources.")

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["Ano", "Localidade", "Idade", "Sexo"], keep="last")
    target_dir = os.path.dirname(os.path.abspath(target_path))
    os.makedirs(target_dir, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        dir=target_dir,
        suffix=".csv",
        encoding="utf-8",
        newline="",
    ) as tmp:
        tmp_path = tmp.name
        df.to_csv(tmp, index=False, encoding="utf-8")

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
        logging.info(f"Successfully generated Brazil Census age/sex data at: {saved_file}")
    except Exception as e:
        logging.error(f"Fatal error executing Brazil Census age/sex download: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app.run(main)
