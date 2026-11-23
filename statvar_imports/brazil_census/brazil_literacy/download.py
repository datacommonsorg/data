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
"""Automated download script for Brazil Census Literacy live source data.

Downloads 2022+ literacy counts from official IBGE SIDRA REST API (Table 9952
across national, regional, state, and municipal levels), and syncs immutable
pre-2022 historical observations from GCS history/.
"""

import os
import sys
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
for _p in (PARENT_DIR, SCRIPT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from absl import app
from absl import flags
from absl import logging
from brazil_download_utils import define_download_flags
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
# Table 9952: População de 15 anos ou mais de idade por alfabetização e sexo (2022+ Census)
# Split by sex (c2/6794 Total, c2/4 Homens, c2/5 Mulheres) to stay under SIDRA's 50,000-row API cap across n6/all.
TABLE_9952_API_URLS = [
    (
        "sidra_9952_total_n6.json",
        f"{SIDRA_BASE_URL}/values/t/9952/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c59/all/c2/6794/c58/0/c2661/0/c1/0?formato=json",
    ),
    (
        "sidra_9952_male_n6.json",
        f"{SIDRA_BASE_URL}/values/t/9952/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c59/all/c2/4/c58/0/c2661/0/c1/0?formato=json",
    ),
    (
        "sidra_9952_female_n6.json",
        f"{SIDRA_BASE_URL}/values/t/9952/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c59/all/c2/5/c58/0/c2661/0/c1/0?formato=json",
    ),
]

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_HISTORY_BLOB = (
    "country/brazil/history/brazil_literacy/brazil_literacy_historical.csv")

FLAGS = flags.FLAGS

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, "brazil_literacy.csv")


def _get_raw_dir(target_path: str) -> str:
    """Returns a clean directory for archiving raw downloaded payloads."""
    return get_raw_dir(target_path, DEFAULT_OUTPUT_FILE, SCRIPT_DIR)


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads live 2022+ Brazil Census literacy counts and syncs history/."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    raw_dir = _get_raw_dir(target_path)
    history_dest = get_history_path(
        target_path,
        DEFAULT_OUTPUT_FILE,
        SCRIPT_DIR,
        "brazil_literacy_historical.csv",
    )
    all_rows: List[Dict[str, Any]] = []

    try:
        for fname, url in TABLE_9952_API_URLS:
            raw_sidra = fetch_sidra_data(
                session,
                url,
                raw_file_path=os.path.join(raw_dir, fname),
            )
            logging.info(
                f"Retrieved {len(raw_sidra) - 1} records from SIDRA Table 9952: {url}"
            )
            for r in raw_sidra[1:]:
                val_str = r.get("V")
                if val_str in ["-", "...", "..", "X", None, ""]:
                    continue
                try:
                    val = int(round(float(val_str)))
                except (ValueError, TypeError):
                    continue

                year_str = str(r.get("D3N", "2022")).strip() or "2022"
                try:
                    year = int(year_str)
                except ValueError:
                    continue
                if year < 2022:
                    continue

                loc = resolve_sidra_loc(r)
                if not loc:
                    continue

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

        if not all_rows:
            raise RuntimeError("No live 2022+ literacy count records fetched.")

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
            f"Error downloading Brazil Census literacy data: {e}") from e

    df = pd.DataFrame(all_rows).drop_duplicates(
        subset=[
            "Ano",
            "Localidade",
            "FaixaEtaria",
            "Raca",
            "StatusAlfabetizacao",
            "Sexo",
        ],
        keep="last",
    )
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
    logging.info(f"Literacy download completed successfully: {saved_file}")


if __name__ == "__main__":
    define_download_flags("brazil_literacy.csv")
    app.run(main)
