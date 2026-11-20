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
"""Automated download script for Brazil Census Education live source data.

Downloads 2022+ educational enrollment counts from official IBGE SIDRA REST API
Tables 10057, 10058, and 10059 across all territorial levels (n1/n2/n3/n6),
and syncs immutable pre-2022 historical observations from GCS history/.
"""

import os
import sys
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
for _p in (PARENT_DIR, SCRIPT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from absl import app
from absl import flags
from absl import logging
from brazil_download_utils import fetch_sidra_data
from brazil_download_utils import get_history_path
from brazil_download_utils import get_raw_dir
from brazil_download_utils import get_robust_session
from brazil_download_utils import resolve_sidra_loc
from brazil_download_utils import sync_historical_csv
from brazil_download_utils import write_df_atomically
import pandas as pd
import requests

SIDRA_BASE_URL = "https://apisidra.ibge.gov.br"

# 2022+ SIDRA Education tables across 3 disjoint age cohorts (chunked by c11798 to stay <50,000 rows across n6/all):
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

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_HISTORY_BLOB = (
    "country/brazil/history/brazil_education/brazil_education_historical.csv")

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


def _get_raw_dir(target_path: str) -> str:
    """Returns a clean directory for archiving raw downloaded payloads."""
    return get_raw_dir(target_path, DEFAULT_OUTPUT_FILE, SCRIPT_DIR)


def fetch_2022_education_sidra(
    session: requests.Session,
    raw_dir: Optional[str] = None,
) -> Dict[Tuple[int, str, str, str], int]:
    """Fetches 2022+ student attendance by education level from SIDRA Tables 10057, 10058, 10059."""
    sidra_2022_acc: Dict[Tuple[int, str, str, str], int] = {}
    for fname, tid, vid, c11798_codes in TABLE_2022_EDUCATION_SPECS:
        url = (f"{SIDRA_BASE_URL}/values/t/{tid}/n1/all/n2/all/n3/all/n6/all"
               f"/v/{vid}/p/all/c11798/{c11798_codes}?formato=json")
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
            if year < 2022:
                continue

            loc = resolve_sidra_loc(r)
            if not loc:
                continue

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
    """Downloads live 2022+ Brazil Census education data and syncs historical CSV."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    raw_dir = _get_raw_dir(target_path)
    history_dest = get_history_path(
        target_path,
        DEFAULT_OUTPUT_FILE,
        SCRIPT_DIR,
        "brazil_education_historical.csv",
    )
    all_rows: List[Dict[str, Any]] = []

    try:
        sidra_2022_acc = fetch_2022_education_sidra(session, raw_dir=raw_dir)
        for (year, loc, rede, nivel), val in sidra_2022_acc.items():
            all_rows.append({
                "Ano": year,
                "Localidade": loc,
                "RedeEnsino": rede,
                "NivelEnsino": nivel,
                "Estudantes": val,
            })

        if not all_rows:
            raise RuntimeError("No live 2022+ education records retrieved.")

        sync_historical_csv(
            GCS_HISTORY_BLOB,
            history_dest,
            gcs_bucket_name=GCS_BUCKET_NAME,
            fallback_to_cached=fallback_to_cached,
        )
    except Exception as e:
        if fallback_to_cached and os.path.isfile(
                target_path) and os.path.isfile(history_dest):
            logging.warning(
                f"Download failed ({e}). Falling back to cached copy: {target_path}"
            )
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(
            f"Error downloading Brazil Census education data: {e}") from e

    df = pd.DataFrame(all_rows).drop_duplicates(
        subset=["Ano", "Localidade", "RedeEnsino", "NivelEnsino"], keep="last")
    write_df_atomically(df, target_path)
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
    logging.info(f"Education download completed successfully: {saved_file}")


if __name__ == "__main__":
    app.run(main)
