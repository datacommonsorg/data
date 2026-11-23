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
"""Automated download script for Brazil Census Population by Religion live data.

Downloads 2022+ resident population (10+ years) by religious affiliation from
official IBGE SIDRA REST API (Table 9537 across n1/n2/n3/n6) and syncs
immutable pre-2022 historical observations from GCS history/.
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
# Table 9537: População residente de 10 anos ou mais de idade por religião (2022+ across n1/n2/n3/n6)
TABLE_9537_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/9537/n1/all/n2/all/n3/all/n6/all"
    f"/v/140/p/all/c133/all/c2/0/c58/0?formato=json")

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_HISTORY_BLOB = ("country/brazil/history/brazil_population_by_religion/"
                    "brazil_population_by_religion_historical.csv")

FLAGS = flags.FLAGS

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR,
                                   "brazil_population_by_religion.csv")


def _get_raw_dir(target_path: str) -> str:
    """Returns a clean directory for archiving raw downloaded payloads."""
    return get_raw_dir(target_path, DEFAULT_OUTPUT_FILE, SCRIPT_DIR)


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads live 2022+ Brazil Census religion data and syncs historical CSV."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    raw_dir = _get_raw_dir(target_path)
    history_dest = get_history_path(
        target_path,
        DEFAULT_OUTPUT_FILE,
        SCRIPT_DIR,
        "brazil_population_by_religion_historical.csv",
    )
    all_rows: List[Dict[str, Any]] = []

    try:
        raw_sidra = fetch_sidra_data(
            session,
            TABLE_9537_API_URL,
            raw_file_path=os.path.join(raw_dir, "sidra_9537_2022_n6.json"),
        )
        logging.info(
            f"Retrieved {len(raw_sidra) - 1} records from SIDRA Table 9537.")
        other_rel_acc: Dict[str, int] = {}
        nao_declarada_acc: Dict[str, int] = {}
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
            if year < 2022:
                continue

            loc = resolve_sidra_loc(r)
            if not loc:
                continue

            rel_raw = str(r.get("D4N", "Total")).strip()
            if rel_raw == "Total":
                # Table 9537 reports population aged 10+ years, so skip emitting Total
                # to avoid conflicting with all-ages Count_Person in 2022.
                continue
            elif "Católica Apostólica Romana" in rel_raw:
                all_rows.append({
                    "Ano": year,
                    "Localidade": loc,
                    "Religiao": "Católica Apostólica Romana",
                    "Populacao": val,
                })
            elif "Evangélica" in rel_raw or "Evangélicas" in rel_raw:
                all_rows.append({
                    "Ano": year,
                    "Localidade": loc,
                    "Religiao": "Evangélica",
                    "Populacao": val,
                })
            elif "Sem religião" in rel_raw:
                all_rows.append({
                    "Ano": year,
                    "Localidade": loc,
                    "Religiao": "Sem Religião",
                    "Populacao": val,
                })
            elif "Sem declaração" in rel_raw or "Não sabe" in rel_raw:
                key = f"{year}||{loc}"
                nao_declarada_acc[key] = nao_declarada_acc.get(key, 0) + val
            else:
                key = f"{year}||{loc}"
                other_rel_acc[key] = other_rel_acc.get(key, 0) + val

        for key, val in nao_declarada_acc.items():
            y_str, l_str = key.split("||", 1)
            all_rows.append({
                "Ano": int(y_str),
                "Localidade": l_str,
                "Religiao": "Não Declarada",
                "Populacao": val,
            })

        for key, val in other_rel_acc.items():
            y_str, l_str = key.split("||", 1)
            all_rows.append({
                "Ano": int(y_str),
                "Localidade": l_str,
                "Religiao": "Outras Religiões",
                "Populacao": val,
            })

        if not all_rows:
            raise RuntimeError("No live 2022+ religion records retrieved.")

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
            f"Error downloading Brazil Census religion data: {e}") from e

    df = pd.DataFrame(all_rows).drop_duplicates(
        subset=["Ano", "Localidade", "Religiao"], keep="last")
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
    logging.info(f"Religion download completed successfully: {saved_file}")


if __name__ == "__main__":
    define_download_flags("brazil_population_by_religion.csv")
    app.run(main)
