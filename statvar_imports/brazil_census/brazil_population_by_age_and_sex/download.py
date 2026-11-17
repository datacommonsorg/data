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
"""Automated download script for Brazil Census Population by Age and Sex live data.

Downloads 2022+ resident population by sex and 5-year age brackets from official
IBGE SIDRA REST API (Table 9514 across n1/n2/n3 and municipal 10-14 / 15-19
brackets across n6/all), and syncs immutable pre-2022 historical observations
from GCS history/.
"""

import os
import sys
from typing import Dict, List, Optional

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
# Table 9514: População residente por sexo e idade (2022+ Census)
# /c286/113635 selects "Total" for Forma de declaração da idade to avoid duplicates.
TABLE_9514_AGE_CODES = [
    "100362",
    "93070",
    "93084",
    "93085",
    "93086",
    "93087",
    "93088",
    "93089",
    "93090",
    "93091",
    "93092",
    "93093",
    "93094",
    "93095",
    "93096",
    "93097",
    "93098",
    "49108",
    "49109",
    "60040",
    "60041",
    "6653",
]
TABLE_9514_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/9514/n1/all/n2/all/n3/all/v/93/p/all/c2/all"
    f"/c287/{','.join(TABLE_9514_AGE_CODES)}/c286/113635?formato=json")
TABLE_9514_MUNI_API_URL = (
    f"{SIDRA_BASE_URL}/values/t/9514/n6/all/v/93/p/all/c2/6794"
    f"/c287/93085,93086/c286/113635?formato=json")

COHORTS_0_14 = ["0 a 4 anos", "5 a 9 anos", "10 a 14 anos"]
COHORTS_15_59 = [
    "15 a 19 anos",
    "20 a 24 anos",
    "25 a 29 anos",
    "30 a 34 anos",
    "35 a 39 anos",
    "40 a 44 anos",
    "45 a 49 anos",
    "50 a 54 anos",
    "55 a 59 anos",
]
COHORTS_80_99_5YR = [
    "80 a 84 anos",
    "85 a 89 anos",
    "90 a 94 anos",
    "95 a 99 anos",
]
COHORTS_80_99_10YR = ["80 a 89 anos", "90 a 99 anos"]
COHORTS_60_79_100 = [
    "60 a 64 anos",
    "65 a 69 anos",
    "70 a 74 anos",
    "75 a 79 anos",
    "100 anos ou mais",
]

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_HISTORY_BLOB = ("country/brazil/history/brazil_population_by_age_and_sex/"
                    "brazil_population_by_age_and_sex_historical.csv")

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
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR,
                                   "brazil_population_by_age_and_sex.csv")


def _get_raw_dir(target_path: str) -> str:
    """Returns a clean directory for archiving raw downloaded payloads."""
    return get_raw_dir(target_path, DEFAULT_OUTPUT_FILE, SCRIPT_DIR)


def compute_broad_age_aggregations(rows: List[Dict[str, str]],
                                   year: str) -> List[Dict[str, str]]:
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

        if all(c in idade_dict for c in COHORTS_0_14):
            sum_0_14 = sum(idade_dict[c] for c in COHORTS_0_14)
            agg_rows.append({
                "Ano": year,
                "Localidade": localidade,
                "Idade": "De 0 a 14 anos",
                "Sexo": sexo,
                "Populacao": str(sum_0_14),
            })

        if all(c in idade_dict for c in COHORTS_15_59):
            sum_15_59 = sum(idade_dict[c] for c in COHORTS_15_59)
            agg_rows.append({
                "Ano": year,
                "Localidade": localidade,
                "Idade": "De 15 a 59 anos",
                "Sexo": sexo,
                "Populacao": str(sum_15_59),
            })

        has_5yr_80_plus = all(c in idade_dict for c in COHORTS_80_99_5YR)
        cohorts_60 = list(COHORTS_60_79_100)
        if has_5yr_80_plus:
            cohorts_60 += COHORTS_80_99_5YR
        else:
            cohorts_60 += COHORTS_80_99_10YR

        if all(c in idade_dict for c in cohorts_60):
            sum_60_plus = sum(idade_dict[c] for c in cohorts_60)
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
    """Downloads live 2022+ Brazil Census age/sex data and syncs historical CSV."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    raw_dir = _get_raw_dir(target_path)
    history_dest = get_history_path(
        target_path,
        DEFAULT_OUTPUT_FILE,
        SCRIPT_DIR,
        "brazil_population_by_age_and_sex_historical.csv",
    )
    all_rows: List[Dict[str, str]] = []

    try:
        sidra_2022_rows: List[Dict[str, str]] = []
        for fname, url in [
            ("sidra_9514_macro.json", TABLE_9514_API_URL),
            ("sidra_9514_muni.json", TABLE_9514_MUNI_API_URL),
        ]:
            raw_json = fetch_sidra_data(
                session,
                url,
                raw_file_path=os.path.join(raw_dir, fname),
            )
            for r in raw_json[1:]:
                val = str(r.get("V", "")).strip()
                if val in ["-", "...", "..", "X", None, ""]:
                    continue
                year_str = str(r.get("D3N", "2022")).strip() or "2022"
                try:
                    if int(year_str) < 2022:
                        continue
                except ValueError:
                    continue

                loc = resolve_sidra_loc(r)
                if not loc:
                    continue

                sidra_2022_rows.append({
                    "Ano": year_str,
                    "Localidade": loc,
                    "Idade": str(r.get("D5N", "")).strip(),
                    "Sexo": str(r.get("D4N", "")).strip(),
                    "Populacao": val,
                })
        all_rows.extend(sidra_2022_rows)

        for year_str in sorted(
            {r["Ano"] for r in sidra_2022_rows if r.get("Ano")}):
            all_rows.extend(
                compute_broad_age_aggregations(
                    [r for r in sidra_2022_rows if r["Ano"] == year_str],
                    year_str,
                ))

        if not all_rows:
            raise RuntimeError("No live 2022+ age/sex records fetched.")

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
                f"Live fetch failed ({e}). Fallback to existing: {target_path}")
            return target_path
        logging.error(f"Download error: {e}")
        raise RuntimeError(
            f"Error downloading Brazil Census age/sex data: {e}") from e

    df = pd.DataFrame(all_rows).drop_duplicates(
        subset=["Ano", "Localidade", "Idade", "Sexo"], keep="last")
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
    logging.info(f"Age/Sex download completed successfully: {saved_file}")


if __name__ == "__main__":
    app.run(main)
