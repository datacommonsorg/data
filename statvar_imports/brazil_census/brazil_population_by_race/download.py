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
"""Automated download script for Brazil Census Population by Race live source data.

Downloads 2022+ race/color demographic data from official IBGE SIDRA REST API
(Table 9605 across n1/n2/n3/n6) and syncs immutable pre-2022 historical
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
from brazil_download_utils import discover_sidra_period_batches
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
# Table 9605: População residente por cor ou raça (2022+ across n1/n2/n3/n6 plus macro p/all)
TABLE_9605_API_URL = (f"{SIDRA_BASE_URL}/values/t/9605/n1/all/n2/all/n3/all"
                      f"/v/93/p/all/c86/all?formato=json")
TABLE_9605_PERIOD_PROBE_URL = (
    f"{SIDRA_BASE_URL}/values/t/9605/n1/1/v/93/p/all/c86/95251?formato=json")
TABLE_9605_N6_TEMPLATE = (f"{SIDRA_BASE_URL}/values/t/9605/n6/all"
                          f"/v/93/p/{{period}}/c86/all?formato=json")

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_HISTORY_BLOB = ("country/brazil/history/brazil_population_by_race/"
                    "brazil_population_by_race_historical.csv")

FLAGS = flags.FLAGS
if "output_file" not in FLAGS:
    flags.DEFINE_string(
        "output_file",
        "",
        "Output CSV file path. Defaults to input_files/brazil_population_by_race.csv.",
    )
if "fallback_to_cached" not in FLAGS:
    flags.DEFINE_boolean(
        "fallback_to_cached",
        False,
        "Whether to fallback to locally cached CSV if live download fails.",
    )

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR,
                                   "brazil_population_by_race.csv")


def _get_raw_dir(target_path: str) -> str:
    """Returns a clean directory for archiving raw downloaded payloads."""
    return get_raw_dir(target_path, DEFAULT_OUTPUT_FILE, SCRIPT_DIR)


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads live 2022+ Brazil Census race data and syncs historical CSV."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    raw_dir = _get_raw_dir(target_path)
    history_dest = get_history_path(
        target_path,
        DEFAULT_OUTPUT_FILE,
        SCRIPT_DIR,
        "brazil_population_by_race_historical.csv",
    )
    all_rows: List[Dict[str, Any]] = []

    try:
        period_batches = discover_sidra_period_batches(
            session,
            TABLE_9605_PERIOD_PROBE_URL,
            min_year=2022,
            batch_size=1,
            raw_file_path=os.path.join(raw_dir, "sidra_9605_probe.json"),
        )
        if not period_batches:
            raise RuntimeError(
                "No >=2022 periods discovered from SIDRA Table 9605.")
        api_urls = [(
            f"sidra_9605_{batch[0]}_n6.json",
            TABLE_9605_N6_TEMPLATE.format(period=batch[0]),
        ) for batch in period_batches
                   ] + [("sidra_9605_macro_all.json", TABLE_9605_API_URL)]
        for fname, url in api_urls:
            raw_sidra = fetch_sidra_data(
                session,
                url,
                raw_file_path=os.path.join(raw_dir, fname),
            )
            logging.info(
                f"Retrieved {len(raw_sidra) - 1} records from SIDRA Table 9605: {url}"
            )
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

                cor_raw = str(r.get("D4N", "Total")).strip()
                if cor_raw in ["Sem declaração", "Não declarada"]:
                    continue

                all_rows.append({
                    "Ano": year,
                    "Localidade": loc,
                    "Cor": cor_raw,
                    "Populacao": val,
                })

        if not all_rows:
            raise RuntimeError("No live 2022+ race records retrieved.")

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
            f"Error downloading Brazil Census race data: {e}") from e

    df = pd.DataFrame(all_rows).drop_duplicates(
        subset=["Ano", "Localidade", "Cor"], keep="last")
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
    logging.info(f"Race download completed successfully: {saved_file}")


if __name__ == "__main__":
    app.run(main)
