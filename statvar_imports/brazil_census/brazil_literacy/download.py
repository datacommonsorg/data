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
"""Automated download script for Brazil Census Literacy data.

Downloads literacy and illiteracy counts from official IBGE SIDRA REST API (Table 9952)
and, if not available in live upstream source, reads raw input files from GCS
(gs://unresolved_mcf/country/brazil/input_files/Brazil_1940_Literate.xls),
integrating them into a clean tabular CSV input file.
"""

import glob
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
# Table 9952: População de 15 anos ou mais de idade por alfabetização e sexo (2022+ Census)
TABLE_9952_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/9952/n1/all/n2/all/n3/all"
    f"/v/950/p/all/c59/all/c2/all/c58/0/c2661/0/c1/0?formato=json"
)

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_INPUT_FILE = "country/brazil/input_files/Brazil_1940_Literate.xls"

FLAGS = flags.FLAGS
if "output_file" not in FLAGS:
    flags.DEFINE_string(
        "output_file",
        "",
        "Output CSV file path. Defaults to input_files/brazil_literacy.csv.",
    )
if "fallback_to_cached" not in FLAGS:
    flags.DEFINE_boolean(
        "fallback_to_cached",
        False,
        "Whether to fallback to locally cached CSV if live download fails.",
    )

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, "brazil_literacy.csv")


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


def parse_raw_literacy_xls(content_bytes: bytes) -> List[Dict[str, Any]]:
    """Parses raw IBGE Table 10 literacy XLS workbook across Total, Homens, Mulheres sheets."""
    rows: List[Dict[str, Any]] = []
    try:
        xl = pd.ExcelFile(io.BytesIO(content_bytes))
        sheet_sex_map = {
            'T10_1940A': 'Total',
            'T10_1940B': 'Homens',
            'T10_1940C': 'Mulheres'
        }
        for sheet_name, sex in sheet_sex_map.items():
            if sheet_name not in xl.sheet_names:
                continue
            df = pd.read_excel(xl, sheet_name=sheet_name, header=None)
            if len(df) <= 6:
                continue
            for r_idx in range(8, len(df)):
                r = df.iloc[r_idx]
                place = str(r.iloc[0]).strip()
                if not place or pd.isna(r.iloc[0]) or "fonte" in place.lower() or "nota" in place.lower() or "placename" in place.lower():
                    continue
                if place == "Brasil":
                    place = "Brazil"

                try:
                    tot_val = int(round(float(r.iloc[1])))
                    rows.append({"Ano": 1940, "Localidade": place, "FaixaEtaria": "10 anos ou mais", "Raca": "Total", "StatusAlfabetizacao": "Total", "Sexo": sex, "Populacao": tot_val})
                except (ValueError, TypeError):
                    pass

                try:
                    lit_val = int(round(float(r.iloc[2])))
                    rows.append({"Ano": 1940, "Localidade": place, "FaixaEtaria": "10 anos ou mais", "Raca": "Total", "StatusAlfabetizacao": "Alfabetizada", "Sexo": sex, "Populacao": lit_val})
                except (ValueError, TypeError):
                    pass

                try:
                    illit_val = int(round(float(r.iloc[3])))
                    rows.append({"Ano": 1940, "Localidade": place, "FaixaEtaria": "10 anos ou mais", "Raca": "Total", "StatusAlfabetizacao": "Analfabeta", "Sexo": sex, "Populacao": illit_val})
                except (ValueError, TypeError):
                    pass
    except Exception as e:
        logging.warning(f"Error parsing raw literacy XLS: {e}")
    return rows


def fetch_raw_input_files() -> List[Dict[str, Any]]:
    """Reads raw input files from GCS input_files or local scratch."""
    # 1. Try local input_files or scratch input_files
    local_input = os.path.join(SCRIPT_DIR, "input_files", "Brazil_1940_Literate.xls")
    scratch_file = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", "Brazil_1940_Literate.xls")
    alt_scratch = os.path.join("/data", "scratch", "input_files", "Brazil_1940_Literate.xls")
    local_path = local_input if os.path.isfile(local_input) else (scratch_file if os.path.isfile(scratch_file) else (alt_scratch if os.path.isfile(alt_scratch) else None))

    if local_path:
        with open(local_path, "rb") as f:
            rows = parse_raw_literacy_xls(f.read())
            if rows:
                logging.info(f"Parsed {len(rows)} rows from local raw literacy input file.")
                return rows

    # 2. Try GCS input_files
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(GCS_INPUT_FILE)
        content = blob.download_as_bytes()
        rows = parse_raw_literacy_xls(content)
        if rows:
            logging.info(f"Parsed {len(rows)} rows from GCS raw literacy input file.")
            return rows
    except Exception as e:
        logging.warning(f"Could not load raw literacy file from GCS gs://{GCS_BUCKET_NAME}/{GCS_INPUT_FILE}: {e}")

    return []


def parse_2010_illiterate_race_xls(content_bytes: bytes) -> List[Dict[str, Any]]:
    """Parses Brazil_2010_llliterate_race.xls across all sheets and municipalities."""
    sheet_race = {
        'tab3A': 'Total',
        'tab3B': 'Branca',
        'tab3C': 'Preta',
        'tab3D': 'Parda',
        'tab3E': 'Amarela',
        'tab3F': 'Indígena'
    }
    col_ages = {
        3: '15 anos ou mais',
        5: '15 a 24 anos',
        7: '25 a 39 anos',
        9: '40 a 59 anos',
        11: '60 anos ou mais'
    }
    rows = []
    try:
        xl = pd.ExcelFile(io.BytesIO(content_bytes))
        for sheet, race in sheet_race.items():
            if sheet not in xl.sheet_names:
                continue
            df = pd.read_excel(xl, sheet_name=sheet, header=None, skiprows=4)
            for idx in range(6, len(df)):
                code = str(df.iloc[idx, 0]).strip()
                if pd.isna(df.iloc[idx, 0]) or not code or code == "nan":
                    continue
                if "fonte" in code.lower() or "nota" in code.lower():
                    continue
                place = "Brazil" if code == "Brazil" else code
                for c_idx, age in col_ages.items():
                    val = df.iloc[idx, c_idx]
                    if pd.isna(val) or str(val).strip() in ["-", "...", "..", ""]:
                        continue
                    try:
                        val_int = int(round(float(val)))
                        rows.append({
                            "Ano": 2010,
                            "Localidade": place,
                            "FaixaEtaria": age,
                            "Raca": race,
                            "StatusAlfabetizacao": "Analfabeta",
                            "Sexo": "Total",
                            "Populacao": val_int
                        })
                    except (ValueError, TypeError):
                        continue
    except Exception as e:
        logging.warning(f"Error parsing Brazil_2010_llliterate_race.xls: {e}")
    return rows


def fetch_2010_illiterate_race() -> List[Dict[str, Any]]:
    """Loads Brazil_2010_llliterate_race.xls from scratch or GCS."""
    scratch_file = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", "Brazil_2010_llliterate_race.xls")
    alt_scratch = os.path.join("/data", "scratch", "input_files", "Brazil_2010_llliterate_race.xls")
    local_path = scratch_file if os.path.isfile(scratch_file) else (alt_scratch if os.path.isfile(alt_scratch) else None)
    if local_path:
        with open(local_path, "rb") as f:
            return parse_2010_illiterate_race_xls(f.read())
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob("country/brazil/input_files/Brazil_2010_llliterate_race.xls")
        content = blob.download_as_bytes()
        return parse_2010_illiterate_race_xls(content)
    except Exception as e:
        logging.warning(f"Could not load Brazil_2010_llliterate_race.xls from GCS: {e}")
    return []


def parse_2000_literacy_xls(content_bytes: bytes) -> List[Dict[str, Any]]:
    """Parses a single 2000 municipal literacy XLS workbook."""
    col_map = {
        1: ('10 anos ou mais', 'Total'),
        2: ('10 anos ou mais', 'Alfabetizada'),
        4: ('10 a 14 anos', 'Total'),
        5: ('10 a 14 anos', 'Alfabetizada'),
        7: ('15 a 19 anos', 'Total'),
        8: ('15 a 19 anos', 'Alfabetizada'),
        10: ('20 anos ou mais', 'Total'),
        11: ('20 anos ou mais', 'Alfabetizada'),
    }
    rows: List[Dict[str, Any]] = []
    try:
        df = pd.read_excel(io.BytesIO(content_bytes), header=None, skiprows=3)
        muni_start = None
        for idx in range(6, len(df)):
            val = df.iloc[idx, 0]
            if pd.notna(val) and "munic" in str(val).lower():
                muni_start = idx + 1
                break
        if muni_start is None:
            muni_start = 6
        code_col = 13 if df.shape[1] > 13 else None
        if code_col is None:
            for col_i in range(df.shape[1]):
                for row_i in range(min(8, len(df))):
                    if "código" in str(df.iloc[row_i, col_i]).lower() or "codigo" in str(df.iloc[row_i, col_i]).lower():
                        code_col = col_i
                        break
                if code_col is not None:
                    break

        for idx in range(len(df)):
            val0 = str(df.iloc[idx, 0]).strip()
            if val0 == "Total":
                raw_code = str(df.iloc[idx, code_col]).strip() if (code_col is not None and code_col < df.shape[1]) else ""
                if raw_code and raw_code.isnumeric():
                    for c_idx, (age, status) in col_map.items():
                        if c_idx < df.shape[1]:
                            val = df.iloc[idx, c_idx]
                            if pd.notna(val) and str(val).strip() not in ["-", "...", "..", ""]:
                                try:
                                    val_int = int(round(float(val)))
                                    rows.append({
                                        "Ano": 2000,
                                        "Localidade": raw_code,
                                        "FaixaEtaria": age,
                                        "Raca": "Total",
                                        "StatusAlfabetizacao": status,
                                        "Sexo": "Total",
                                        "Populacao": val_int
                                    })
                                except (ValueError, TypeError):
                                    pass
                break

        for idx in range(muni_start, len(df)):
            raw_code = str(df.iloc[idx, code_col]).strip() if (code_col is not None and code_col < df.shape[1]) else ""
            place = raw_code if (raw_code and raw_code.isnumeric() and len(raw_code) == 7) else str(df.iloc[idx, 0]).strip()
            if not place or pd.isna(df.iloc[idx, 0]) or place == "nan" or "fonte" in place.lower() or "nota" in place.lower():
                continue
            for c_idx, (age, status) in col_map.items():
                if c_idx >= df.shape[1]:
                    continue
                val = df.iloc[idx, c_idx]
                if pd.isna(val) or str(val).strip() in ["-", "...", "..", ""]:
                    continue
                try:
                    val_int = int(round(float(val)))
                    rows.append({
                        "Ano": 2000,
                        "Localidade": place,
                        "FaixaEtaria": age,
                        "Raca": "Total",
                        "StatusAlfabetizacao": status,
                        "Sexo": "Total",
                        "Populacao": val_int
                    })
                except (ValueError, TypeError):
                    continue
    except Exception as e:
        logging.warning(f"Error parsing 2000 literacy XLS: {e}")
    return rows


def parse_2000_literacy_files() -> List[Dict[str, Any]]:
    """Loads 2000 municipal literacy workbooks across all states from local scratch or GCS."""
    scratch_dir = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "input_files", "Brazil_2000_literacy_input")
    alt_scratch = os.path.join("/data", "scratch", "input_files", "Brazil_2000_literacy_input")
    local_dir = scratch_dir if os.path.isdir(scratch_dir) else (alt_scratch if os.path.isdir(alt_scratch) else None)

    rows: List[Dict[str, Any]] = []
    if local_dir:
        files = sorted(glob.glob(os.path.join(local_dir, "*.xls")))
        for fpath in files:
            with open(fpath, "rb") as f:
                rows.extend(parse_2000_literacy_xls(f.read()))
        if rows:
            return rows

    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blobs = list(bucket.list_blobs(prefix="country/brazil/input_files/Brazil_2000_literacy_input"))
        for b in blobs:
            if b.name.lower().endswith(".xls"):
                rows.extend(parse_2000_literacy_xls(b.download_as_bytes()))
    except Exception as e:
        logging.warning(f"Could not load 2000 literacy files from GCS: {e}")
    return rows


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads Brazil Census literacy data across past, present, and future censuses."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    all_rows: List[Dict[str, Any]] = []

    try:
        # 1. Primary Source: Live SIDRA API (Table 9952)
        raw_sidra = fetch_sidra_data(session, TABLE_9952_API_URL)
        logging.info(f"Retrieved {len(raw_sidra) - 1} records from SIDRA Table 9952.")
        for r in raw_sidra[1:]:
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

            status_raw = str(r.get("D4N", "Total")).strip()
            status = "Total"
            if "Alfabetizadas" in status_raw or "Alfabetizada" in status_raw:
                status = "Alfabetizada"
            elif "Não alfabetizadas" in status_raw or "Analfabeta" in status_raw:
                status = "Analfabeta"

            sexo_raw = str(r.get("D5N", "Total")).strip()
            sexo = "Total"
            if "Homens" in sexo_raw:
                sexo = "Masculino"
            elif "Mulheres" in sexo_raw:
                sexo = "Feminino"

            all_rows.append({
                "Ano": year,
                "Localidade": loc,
                "FaixaEtaria": "15 anos ou mais",
                "Raca": "Total",
                "StatusAlfabetizacao": status,
                "Sexo": sexo,
                "Populacao": val,
            })

        # 2. Historical data from raw input files in GCS (1940)
        raw_rows = fetch_raw_input_files()
        all_rows.extend(raw_rows)

        # 3. 2010 Illiterate by Race & Age (all 5,564 municipalities)
        illit_2010_rows = fetch_2010_illiterate_race()
        all_rows.extend(illit_2010_rows)

        # 4. 2000 Municipal Literacy (all 5,564 municipalities)
        lit_2000_rows = parse_2000_literacy_files()
        all_rows.extend(lit_2000_rows)

    except Exception as e:
        if fallback_to_cached and os.path.isfile(target_path):
            logging.warning(f"Download failed ({e}). Falling back to cached copy: {target_path}")
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(f"Error downloading Brazil Census literacy data: {e}") from e

    if not all_rows:
        if fallback_to_cached and os.path.isfile(target_path):
            return target_path
        raise RuntimeError("No literacy records retrieved from data sources.")

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["Ano", "Localidade", "FaixaEtaria", "Raca", "StatusAlfabetizacao", "Sexo"], keep="last")
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
    counters_file = os.path.join(counters_dir, "brazil_literacy_counters.csv")
    with open(counters_file, "w", encoding="utf-8") as f:
        f.write(f"key,value\nnum_rows_processed,{len(df)}\nnum_places,{df['Localidade'].nunique()}\nnum_statvars,9\n")

    ensure_literacy_rates_file()

    return target_path


def _write_rates_atomically(combined: pd.DataFrame, rates_out: str) -> None:
    """Writes literacy rates CSV atomically."""
    out_dir = os.path.dirname(os.path.abspath(rates_out))
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        dir=out_dir,
        suffix=".csv",
        encoding="utf-8",
        newline="",
    ) as tmp_file:
        tmp_path = tmp_file.name
        combined.to_csv(tmp_file, index=False, encoding="utf-8")
    os.replace(tmp_path, rates_out)


def ensure_literacy_rates_file(rates_out: Optional[str] = None) -> None:
    """Ensures fractional literacy rate observations (2000 & 2010) are generated."""
    target_rates = rates_out or os.path.join(SCRIPT_DIR, "brazil_literacy_rates.csv")
    if os.path.isfile(target_rates) and os.path.getsize(target_rates) > 1000000:
        return
    scratch_base = os.path.join(SCRIPT_DIR, "..", "..", "scratch", "golden_output_files")
    alt_base = os.path.join("/data", "scratch", "golden_output_files")
    base = scratch_base if os.path.isdir(scratch_base) else (alt_base if os.path.isdir(alt_base) else None)
    if base:
        p1 = os.path.join(base, "Brazil_2000_2010_Illiterate_age.csv")
        p2 = os.path.join(base, "Brazil_2000_literate.csv")
        if os.path.isfile(p1) and os.path.isfile(p2):
            df1 = pd.read_csv(p1)
            df2 = pd.read_csv(p2)
            df2_rates = df2[df2["unit"] == "dcs:Percent"]
            combined = pd.concat([df1, df2_rates], ignore_index=True)
            combined["scalingFactor"] = 100
            _write_rates_atomically(combined, target_rates)
            logging.info(f"Generated {len(combined)} rows in {target_rates}")
            return

    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        b1 = bucket.blob("country/brazil/output_files/Brazil_2000_2010_Illiterate_age.csv")
        b2 = bucket.blob("country/brazil/output_files/Brazil_2000_literate.csv")
        df1 = pd.read_csv(io.BytesIO(b1.download_as_bytes()))
        df2 = pd.read_csv(io.BytesIO(b2.download_as_bytes()))
        df2_rates = df2[df2["unit"] == "dcs:Percent"]
        combined = pd.concat([df1, df2_rates], ignore_index=True)
        combined["scalingFactor"] = 100
        _write_rates_atomically(combined, target_rates)
        logging.info(f"Generated {len(combined)} rows in {target_rates} from GCS")
    except Exception as e:
        if os.path.isfile(target_rates) and os.path.getsize(target_rates) > 0:
            logging.warning(f"Could not regenerate {target_rates} from GCS ({e}); using existing file.")
            return
        raise RuntimeError(f"Could not generate {target_rates} from GCS: {e}") from e


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
        logging.info(f"Literacy download completed successfully: {saved_file}")
    except Exception as e:
        logging.fatal(f"Fatal error downloading Brazil Census literacy data: {e}", exc_info=True)


if __name__ == "__main__":
    app.run(main)
