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
"""Automated download script for Brazil Census Total Population live data.

Downloads 2022+ resident population counts directly from official IBGE SIDRA
REST API (Table 9514 for 2022+ Census by sex and Table 6579 for annual
post-2022 estimates across n1/n2/n3/n6) and syncs immutable pre-2022 historical
observations from GCS history/.
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
# Table 9514: População residente por sexo (2022+ Census across n1/n2/n3/n6)
TABLE_9514_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/9514/n1/all/n2/all/n3/all/n6/all"
    f"/v/93/p/all/c2/all/c287/100362/c286/113635?formato=json")
# Table 6579: EstimaPop — População residente estimada (annual post-2022 estimates across n1/n2/n3/n6)
TABLE_6579_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/6579/n1/all/n2/all/n3/all/n6/all"
    f"/v/9324/p/last%205?formato=json")

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_HISTORY_BLOB = ("country/brazil/history/brazil_total_population/"
                    "brazil_total_population_historical.csv")

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


def _get_raw_dir(target_path: str) -> str:
    """Returns a clean directory for archiving raw downloaded payloads."""
    return get_raw_dir(target_path, DEFAULT_OUTPUT_FILE, SCRIPT_DIR)


def _load_local_places_map() -> Dict[str, str]:
    """Loads ../brazil_places_resolved.csv mapping 7-digit IBGE codes to dcid:<dcid>."""
    places_csv = os.path.join(SCRIPT_DIR, "..", "brazil_places_resolved.csv")
    mapping: Dict[str, str] = {}
    if os.path.isfile(places_csv):
        df = pd.read_csv(places_csv, dtype=str)
        for _, row in df.iterrows():
            name = str(row.get("place_name", row.get("name", ""))).strip()
            dcid = str(row.get("dcid", "")).strip()
            if name and dcid:
                mapping[name] = dcid if dcid.startswith(
                    "dcid:") else f"dcid:{dcid}"
    return mapping


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads live 2022+ Brazil Census total population & estimates and syncs history/."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    raw_dir = _get_raw_dir(target_path)
    history_dest = get_history_path(
        target_path,
        DEFAULT_OUTPUT_FILE,
        SCRIPT_DIR,
        "brazil_total_population_historical.csv",
    )
    all_rows: List[Dict[str, Any]] = []

    try:
        muni_map = _load_local_places_map()

        # 1. 2022+ Census from SIDRA API (Table 9514)
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

            year_str = str(r.get("D3N", "2022")).strip() or "2022"
            try:
                year = int(year_str)
            except ValueError:
                continue
            if year < 2022:
                continue

            # 5101837 (Boa Esperança do Norte - MT, incorporated 2024) has Q123021065
            # which is not yet indexed in Data Commons KG geos/.
            loc = resolve_sidra_loc(r, muni_map=muni_map, skip_5101837=True)
            if not loc:
                continue

            sexo = str(r.get("D4N", "Total")).strip()
            all_rows.append({
                "Ano": year,
                "Localidade": loc,
                "Sexo": sexo,
                "Populacao": val,
            })

        # 2. Annual post-2022 population estimates from SIDRA API (Table 6579)
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

            loc = resolve_sidra_loc(r, muni_map=muni_map, skip_5101837=True)
            if not loc:
                continue

            all_rows.append({
                "Ano": year,
                "Localidade": loc,
                "Sexo": "Total",
                "Populacao": val,
            })

        if not all_rows:
            raise RuntimeError(
                "No live 2022+ total population records retrieved.")

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
            f"Error downloading Brazil Census total population data: {e}"
        ) from e

    df = pd.DataFrame(all_rows).drop_duplicates(
        subset=["Ano", "Localidade", "Sexo"], keep="last")
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
    logging.info(
        f"Total population download completed successfully: {saved_file}")


if __name__ == "__main__":
    app.run(main)
