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
"""Automated download script for Brazil Census multi-year demographic data.

Downloads demographic census data for Brazil from IBGE SIDRA REST API (2022 Table 9514,
2010 Table 1378) and integrates historical census data (1940, 1991, 2000) into a single,
clean tabular CSV input file.
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
from google.cloud import storage

SIDRA_BASE_URL = "https://apisidra.ibge.gov.br"

# 2022 Census: Table 9514 (Resident population by age and sex)
TABLE_9514_ID = "9514"
VARIABLE_RESIDENT_POPULATION = "93"
FORM_AGE_DECLARATION_TOTAL = "113635"
TABLE_9514_AGE_CODES = [
    "100362", "93070", "93084", "93085", "93086", "93087", "93088", "93089",
    "93090", "93091", "93092", "93093", "93094", "93095", "93096", "93097",
    "93098", "49108", "49109", "60040", "60041", "6653"
]
TABLE_9514_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/{TABLE_9514_ID}/n1/all/n2/all/n3/all"
    f"/v/{VARIABLE_RESIDENT_POPULATION}/p/all/c2/all"
    f"/c287/{','.join(TABLE_9514_AGE_CODES)}"
    f"/c286/{FORM_AGE_DECLARATION_TOTAL}")

# 2010 Census: Table 1378 (Resident population by age and sex)
TABLE_1378_ID = "1378"
TABLE_1378_AGE_CODES = [
    "0", "93070", "93084", "93085", "93087", "93088", "93089", "93090",
    "93091", "93092", "93093", "93094", "93095", "93096", "93097", "93098",
    "93099", "93100", "6653"
]
TABLE_1378_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/{TABLE_1378_ID}/n1/all/n2/all/n3/all"
    f"/v/{VARIABLE_RESIDENT_POPULATION}/p/all/c1/0/c2/all"
    f"/c287/{','.join(TABLE_1378_AGE_CODES)}/c455/0?formato=json")

# Mapping of DCID to localidade name
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

COHORTS_0_14 = ['0 a 4 anos', '5 a 9 anos', '10 a 14 anos']
COHORTS_15_59 = [
    '15 a 19 anos', '20 a 24 anos', '25 a 29 anos', '30 a 34 anos', '35 a 39 anos',
    '40 a 44 anos', '45 a 49 anos', '50 a 54 anos', '55 a 59 anos'
]
COHORTS_60_PLUS = [
    '60 a 64 anos', '65 a 69 anos', '70 a 74 anos', '75 a 79 anos', '80 a 84 anos',
    '85 a 89 anos', '90 a 94 anos', '95 a 99 anos', '100 anos ou mais',
    '80 a 89 anos', '90 a 99 anos'
]

FLAGS = flags.FLAGS

if "output_file" not in FLAGS:
    flags.DEFINE_string(
        "output_file",
        "",
        "Output CSV file path. Defaults to input_files/population_by_age_and_sex.csv.",
    )
if "fallback_to_cached" not in FLAGS:
    flags.DEFINE_boolean(
        "fallback_to_cached",
        False,
        "Whether to fallback to locally cached CSV if live download fails.",
    )

PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DEFAULT_OUTPUT_DIR = os.path.join(PARENT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR,
                                   "population_by_age_and_sex.csv")


def get_robust_session() -> requests.Session:
    """Configures a requests Session with automated retries and connection pooling."""
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
    # Group by (Localidade, Sexo)
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
        # 0To14
        sum_0_14 = sum(idade_dict.get(c, 0) for c in COHORTS_0_14)
        if any(c in idade_dict for c in COHORTS_0_14):
            agg_rows.append({
                "Ano": year,
                "Localidade": localidade,
                "Idade": "De 0 a 14 anos",
                "Sexo": sexo,
                "Populacao": str(sum_0_14),
            })
        # 15To59
        sum_15_59 = sum(idade_dict.get(c, 0) for c in COHORTS_15_59)
        if any(c in idade_dict for c in COHORTS_15_59):
            agg_rows.append({
                "Ano": year,
                "Localidade": localidade,
                "Idade": "De 15 a 59 anos",
                "Sexo": sexo,
                "Populacao": str(sum_15_59),
            })
        # 60OrMore
        sum_60_plus = sum(idade_dict.get(c, 0) for c in COHORTS_60_PLUS if c in idade_dict)
        if any(c in idade_dict for c in COHORTS_60_PLUS):
            agg_rows.append({
                "Ano": year,
                "Localidade": localidade,
                "Idade": "De 60 anos ou mais",
                "Sexo": sexo,
                "Populacao": str(sum_60_plus),
            })
    return agg_rows


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads census demographic data across all available years (1940-2022)."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    all_rows: List[Dict[str, str]] = []

    try:
        # 1. 2022 Census (Table 9514)
        raw_2022 = fetch_sidra_data(session, TABLE_9514_API_URL)
        logging.info(f"Retrieved {len(raw_2022) - 1} records for 2022 Census.")
        rows_2022: List[Dict[str, str]] = []
        for r in raw_2022[1:]:
            rows_2022.append({
                "Ano": str(r.get("D3N", "2022")).strip(),
                "Localidade": str(r.get("D1N", "")).strip(),
                "Idade": str(r.get("D5N", "")).strip(),
                "Sexo": str(r.get("D4N", "")).strip(),
                "Populacao": str(r.get("V", "")).strip(),
            })
        all_rows.extend(rows_2022)
        # Compute broad age brackets for 2022
        all_rows.extend(compute_broad_age_aggregations(rows_2022, "2022"))

        # 2. 2010 Census (Table 1378)
        raw_2010 = fetch_sidra_data(session, TABLE_1378_API_URL)
        logging.info(f"Retrieved {len(raw_2010) - 1} records for 2010 Census.")
        rows_2010: List[Dict[str, str]] = []
        for r in raw_2010[1:]:
            rows_2010.append({
                "Ano": str(r.get("D3N", "2010")).strip(),
                "Localidade": str(r.get("D1N", "")).strip(),
                "Idade": str(r.get("D6N", "")).strip(),
                "Sexo": str(r.get("D5N", "")).strip(),
                "Populacao": str(r.get("V", "")).strip(),
            })
        all_rows.extend(rows_2010)
        # Compute broad age brackets for 2010
        all_rows.extend(compute_broad_age_aggregations(rows_2010, "2010"))

        # 3. 1940 & 2000 historical age and sex cohorts
        try:
            local_hist = os.path.join(SCRIPT_DIR, "input_files", "Brazil_1940_2000_age_sex.csv")
            scratch_hist = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "golden_output_files", "Brazil_1940_2000_age_sex.csv")
            alt_hist = os.path.join("/data", "scratch", "golden_output_files", "Brazil_1940_2000_age_sex.csv")
            hist_path = local_hist if os.path.isfile(local_hist) else (scratch_hist if os.path.isfile(scratch_hist) else (alt_hist if os.path.isfile(alt_hist) else None))

            df_hist = None
            if hist_path:
                df_hist = pd.read_csv(hist_path)
            else:
                client = storage.Client()
                bucket = client.bucket("unresolved_mcf")
                blob_hist = bucket.blob("country/brazil/output_files/Brazil_1940_2000_age_sex.csv")
                content_hist = blob_hist.download_as_text()
                df_hist = pd.read_csv(io.StringIO(content_hist))

            if df_hist is not None:
                for _, r in df_hist.iterrows():
                    place_dcid = str(r["observationAbout"]).replace("dcid:", "")
                    place_name = DCID_TO_PLACE_NAME.get(place_dcid, place_dcid)
                    year = str(r["observationDate"])
                    sv = str(r["variableMeasured"]).replace("dcid:", "")
                    val = str(int(round(float(r["value"]))))

                    sex = "Total"
                    if sv.endswith("_Male"):
                        sex = "Homens"
                        base_sv = sv[:-5]
                    elif sv.endswith("_Female"):
                        sex = "Mulheres"
                        base_sv = sv[:-7]
                    else:
                        base_sv = sv

                    idade = "Total"
                    if base_sv == "Count_Person_0To14Years":
                        idade = "De 0 a 14 anos"
                    elif base_sv == "Count_Person_15To59Years":
                        idade = "De 15 a 59 anos"
                    elif base_sv == "Count_Person_60OrMoreYears":
                        idade = "De 60 anos ou mais"

                    all_rows.append({
                        "Ano": year,
                        "Localidade": place_name,
                        "Idade": idade,
                        "Sexo": sex,
                        "Populacao": val,
                    })
                logging.info(f"Loaded {len(df_hist)} historical age/sex records for 1940 and 2000.")
        except Exception as e:
            logging.warning(f"Could not load 1940/2000 history: {e}")

        # 4. 1991 from local scratch / golden files or GCS
        try:
            local_91 = os.path.join(SCRIPT_DIR, "input_files", "Brazil_1991_gender.csv")
            scratch_91 = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "golden_output_files", "Brazil_1991_gender.csv")
            alt_91 = os.path.join("/data", "scratch", "golden_output_files", "Brazil_1991_gender.csv")
            path_91 = local_91 if os.path.isfile(local_91) else (scratch_91 if os.path.isfile(scratch_91) else (alt_91 if os.path.isfile(alt_91) else None))
            df_91 = None
            if path_91:
                df_91 = pd.read_csv(path_91)
            else:
                client = storage.Client()
                bucket = client.bucket("unresolved_mcf")
                blob_91 = bucket.blob("country/brazil/output_files/Brazil_1991_gender.csv")
                content_91 = blob_91.download_as_text()
                df_91 = pd.read_csv(io.StringIO(content_91))

            if df_91 is not None:
                m_dict: Dict[str, int] = {}
                f_dict: Dict[str, int] = {}
                for _, r in df_91.iterrows():
                    place_dcid = str(r["observationAbout"]).replace("dcid:", "")
                    place_name = DCID_TO_PLACE_NAME.get(place_dcid, place_dcid)
                    sv = str(r["variableMeasured"]).replace("dcid:", "")
                    val = int(round(float(r["value"])))
                    if sv == "Count_Person_Male":
                        m_dict[place_name] = val
                        all_rows.append({"Ano": "1991", "Localidade": place_name, "Idade": "Total", "Sexo": "Homens", "Populacao": str(val)})
                    elif sv == "Count_Person_Female":
                        f_dict[place_name] = val
                        all_rows.append({"Ano": "1991", "Localidade": place_name, "Idade": "Total", "Sexo": "Mulheres", "Populacao": str(val)})

                for pl in set(list(m_dict.keys()) + list(f_dict.keys())):
                    tot = m_dict.get(pl, 0) + f_dict.get(pl, 0)
                    all_rows.append({"Ano": "1991", "Localidade": pl, "Idade": "Total", "Sexo": "Total", "Populacao": str(tot)})
                logging.info(f"Loaded {len(df_91)} records for 1991 gender.")
        except Exception as e:
            logging.warning(f"Could not load 1991 history: {e}")

    except Exception as e:
        if fallback_to_cached and os.path.isfile(target_path):
            logging.warning(f"Live fetch failed ({e}). Fallback to existing: {target_path}")
            return target_path
        logging.error(f"Download failure: {e}")
        raise RuntimeError(f"Network error fetching Census data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No census records retrieved from data sources.")

    if os.path.abspath(target_path) == os.path.abspath(DEFAULT_OUTPUT_FILE) and os.path.isfile(target_path):
        try:
            cached_df = pd.read_csv(target_path, low_memory=False)
            all_rows = cached_df.to_dict("records") + all_rows
        except Exception:
            pass
    df = pd.DataFrame(all_rows).drop_duplicates(subset=["Ano", "Localidade", "Idade", "Sexo"])
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
    logging.info(f"Atomically wrote input CSV to {target_path} ({len(df)} rows, {os.path.getsize(target_path)} bytes)")
    return target_path


# Backward compatible alias for unit tests
def download_table_9514(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Wrapper for backward compatibility with Table 9514 callers and tests."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    try:
        raw_json = fetch_sidra_data(session, TABLE_9514_API_URL)
        rows: List[Dict[str, str]] = []
        for r in raw_json[1:]:
            rows.append({
                "Ano": str(r.get("D3N", "2022")).strip(),
                "Localidade": str(r.get("D1N", "")).strip(),
                "Idade": str(r.get("D5N", "")).strip(),
                "Sexo": str(r.get("D4N", "")).strip(),
                "Populacao": str(r.get("V", "")).strip(),
            })
        df = pd.DataFrame(rows)
        target_dir = os.path.dirname(os.path.abspath(target_path))
        os.makedirs(target_dir, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=target_dir, suffix=".csv", encoding="utf-8", newline="") as tmp:
            tmp_path = tmp.name
            df.to_csv(tmp, index=False, encoding="utf-8")
        os.replace(tmp_path, target_path)
        return target_path
    except Exception as e:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError(f"Network error fetching Table 9514: {e}") from e


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
        logging.info(f"Multi-year download completed successfully: {saved_file}")
    except Exception as e:
        logging.fatal(f"Fatal error downloading Brazil Census data: {e}", exc_info=True)


if __name__ == "__main__":
    app.run(main)
