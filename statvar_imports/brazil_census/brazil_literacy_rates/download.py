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
"""Automated download script for Brazil Census Literacy & Illiteracy Rates.

Downloads 2022+ literacy and illiteracy rates from official IBGE SIDRA REST API
(Tables 9543 and 9542 across national, regional, state, and municipal levels),
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
from brazil_download_utils import sync_historical_csv
from brazil_download_utils import write_df_atomically
import pandas as pd
import requests

SIDRA_BASE_URL = "https://apisidra.ibge.gov.br"
# Table 9543 & Table 9542 for 2022+ literacy & illiteracy rates across all territorial levels (n1/n2/n3/n6)
TABLE_9543_RATES_URL = (
    f"{SIDRA_BASE_URL}/values/t/9543/n1/all/n2/all/n3/all/n6/all"
    f"/v/2513/p/all/c2/6794/c86/95251/c287/100362,93086?formato=json")
TABLE_9542_RATES_URLS = [
    (
        "sidra_9542_rates_p1a.json",
        f"{SIDRA_BASE_URL}/values/t/9542/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c2/6794/c86/95251/c59/93024/c287/100362,93086,93087?formato=json",
    ),
    (
        "sidra_9542_rates_p1b.json",
        f"{SIDRA_BASE_URL}/values/t/9542/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c2/6794/c86/95251/c59/1023,1024/c287/100362,93086,93087?formato=json",
    ),
    (
        "sidra_9542_rates_p2a.json",
        f"{SIDRA_BASE_URL}/values/t/9542/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c2/6794/c86/95251/c59/93024/c287/2999,9482,9483,9484,3000?formato=json",
    ),
    (
        "sidra_9542_rates_p2b.json",
        f"{SIDRA_BASE_URL}/values/t/9542/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c2/6794/c86/95251/c59/1024/c287/2999,9482,9483,9484,3000?formato=json",
    ),
    (
        "sidra_9542_rates_p3a.json",
        f"{SIDRA_BASE_URL}/values/t/9542/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c2/6794/c86/95251/c59/93024/c287/6613,6614,6615,6616,6617?formato=json",
    ),
    (
        "sidra_9542_rates_p3b.json",
        f"{SIDRA_BASE_URL}/values/t/9542/n1/all/n2/all/n3/all/n6/all/v/950/p/all/c2/6794/c86/95251/c59/1024/c287/6613,6614,6615,6616,6617?formato=json",
    ),
]

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_HISTORY_BLOB = (
    "country/brazil/history/brazil_literacy_rates/brazil_literacy_rates_historical.csv"
)

FLAGS = flags.FLAGS
if "output_file" not in FLAGS:
    flags.DEFINE_string(
        "output_file",
        "",
        "Output CSV file path. Defaults to input_files/brazil_literacy_rates.csv.",
    )
if "fallback_to_cached" not in FLAGS:
    flags.DEFINE_boolean(
        "fallback_to_cached",
        False,
        "Whether to fallback to locally cached CSV if live download fails.",
    )

DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR,
                                   "brazil_literacy_rates.csv")


def _load_places_resolved_map() -> Dict[str, str]:
    """Loads ../brazil_places_resolved.csv mapping raw place strings/codes to dcid:<dcid>."""
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


def _make_rate_row(
    dcid: str,
    year: int,
    variable_measured: str,
    value: float,
) -> Dict[str, Any]:
    """Builds a normalized PVMAP-ready literacy/illiteracy rate row."""
    return {
        "observationAbout": dcid,
        "observationDate": year,
        "variableMeasured": variable_measured,
        "value": round(value, 2),
        "unit": "dcs:Percent",
        "scalingFactor": 100,
    }


def _fetch_2022_literacy_rates_rows(
    session: requests.Session,
    raw_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetches and computes 2022+ literacy & illiteracy rate observations across all territorial levels."""
    places_map = _load_places_resolved_map()
    rows_2022: List[Dict[str, Any]] = []

    def resolve_loc(r: Dict[str, Any]) -> Optional[str]:
        if str(r.get("NC", "")).strip() == "6":
            raw_loc = str(r.get("D1C", "")).strip()
            # 5101837 (Boa Esperança do Norte - MT, incorporated 2024) has Q123021065
            # which is not yet indexed in Data Commons KG geos/, causing
            # Existence_MissingReference_observationAbout lint errors if emitted.
            if raw_loc == "5101837":
                logging.warning(
                    "Skipping unindexed 2024 municipality 5101837 (%s) in SIDRA literacy rates.",
                    r.get("D1N", ""),
                )
                return None
        else:
            raw_loc = str(r.get("D1N", "")).strip()
            if raw_loc == "Brasil":
                raw_loc = "Brazil"
        resolved = places_map.get(raw_loc)
        if not resolved:
            raise ValueError(
                f"Unresolved place identifier in SIDRA literacy rates: {raw_loc!r}"
            )
        return resolved

    # 1. Table 9543: 15+ literacy rate (c287=100362) and 15-19 literacy rate (c287=93086)
    raw_9543 = fetch_sidra_data(
        session,
        TABLE_9543_RATES_URL,
        raw_file_path=os.path.join(raw_dir, "sidra_9543_rates.json")
        if raw_dir else None,
    )
    for r in raw_9543[1:]:
        val_str = r.get("V")
        if val_str in ["-", "...", "..", "X", None, ""]:
            continue
        try:
            rate_val = float(val_str)
            year = int(str(r.get("D3N", "")).strip())
        except (ValueError, TypeError):
            continue
        if year < 2022:
            continue
        dcid = resolve_loc(r)
        if not dcid:
            continue
        c287 = str(r.get("D6C", "")).strip()
        if c287 == "100362":
            rows_2022.append(
                _make_rate_row(
                    dcid,
                    year,
                    "dcid:Count_Person_Illiterate_AsAFractionOf_Count_Person",
                    100.0 - rate_val,
                ))
        elif c287 == "93086":
            rows_2022.append(
                _make_rate_row(
                    dcid,
                    year,
                    "dcid:Count_Person_15To19Years_Literate_AsAFractionOf_Count_Person_15To19Years",
                    rate_val,
                ))

    # 2. Table 9542: Counts by age and literacy status for exact 20+, 15-24, 25-59, and 60+ rate calculation
    counts: Dict[Tuple[int, str], Dict[str, Dict[str, int]]] = {}
    for fname, url in TABLE_9542_RATES_URLS:
        raw_9542 = fetch_sidra_data(
            session,
            url,
            raw_file_path=os.path.join(raw_dir, fname) if raw_dir else None,
        )
        for r in raw_9542[1:]:
            val_str = r.get("V")
            if val_str in ["-", "...", "..", "X", None, ""]:
                continue
            try:
                cnt_val = int(round(float(val_str)))
                year = int(str(r.get("D3N", "")).strip())
            except (ValueError, TypeError):
                continue
            if year < 2022:
                continue
            dcid = resolve_loc(r)
            if not dcid:
                continue
            c59 = str(r.get("D6C", "")).strip()
            c287 = str(r.get("D7C", "")).strip()
            counts.setdefault((year, dcid), {}).setdefault(c59,
                                                           {})[c287] = cnt_val

    single_60_64 = ["6613", "6614", "6615", "6616", "6617"]
    broad_25_64 = ["2999", "9482", "9483", "9484"]

    for (year, dcid), by_status in counts.items():
        tot = by_status.get("93024", {})
        lit = by_status.get("1023", {})
        illit = by_status.get("1024", {})

        if ("100362" in tot and "93086" in tot and "100362" in lit and
                "93086" in lit):
            denom_20 = tot["100362"] - tot["93086"]
            num_20 = lit["100362"] - lit["93086"]
            if denom_20 > 0:
                rows_2022.append(
                    _make_rate_row(
                        dcid,
                        year,
                        "dcid:Count_Person_20OrMoreYears_Literate_AsAFractionOf_Count_Person_20OrMoreYears",
                        num_20 * 100.0 / denom_20,
                    ))

        if ("93086" in tot and "93087" in tot and "93086" in illit and
                "93087" in illit):
            denom_15_24 = tot["93086"] + tot["93087"]
            num_15_24 = illit["93086"] + illit["93087"]
            if denom_15_24 > 0:
                rows_2022.append(
                    _make_rate_row(
                        dcid,
                        year,
                        "dcid:Count_Person_15To24Years_Illiterate_AsAFractionOf_Count_Person_15To24Years",
                        num_15_24 * 100.0 / denom_15_24,
                    ))

        if all(c in tot for c in broad_25_64 + ["3000"]) and all(
                c in illit for c in broad_25_64 + ["3000"]):
            tot_60_64 = sum(tot.get(c, 0) for c in single_60_64)
            illit_60_64 = sum(illit.get(c, 0) for c in single_60_64)
            denom_25_59 = sum(tot[c] for c in broad_25_64) - tot_60_64
            num_25_59 = sum(illit[c] for c in broad_25_64) - illit_60_64
            if denom_25_59 > 0:
                rows_2022.append(
                    _make_rate_row(
                        dcid,
                        year,
                        "dcid:Count_Person_25To59Years_Illiterate_AsAFractionOf_Count_Person_25To59Years",
                        num_25_59 * 100.0 / denom_25_59,
                    ))

            denom_60_plus = tot["3000"] + tot_60_64
            num_60_plus = illit["3000"] + illit_60_64
            if denom_60_plus > 0:
                rows_2022.append(
                    _make_rate_row(
                        dcid,
                        year,
                        "dcid:Count_Person_60OrMoreYears_Illiterate_AsAFractionOf_Count_Person_60OrMoreYears",
                        num_60_plus * 100.0 / denom_60_plus,
                    ))

    return rows_2022


def download_all_years(
    session: requests.Session,
    output_file: Optional[str] = None,
    fallback_to_cached: bool = False,
) -> str:
    """Downloads live 2022+ Brazil Census literacy & illiteracy rates and syncs history/."""
    target_path = output_file or DEFAULT_OUTPUT_FILE
    raw_dir = get_raw_dir(target_path, DEFAULT_OUTPUT_FILE, SCRIPT_DIR)
    history_dest = get_history_path(
        target_path,
        DEFAULT_OUTPUT_FILE,
        SCRIPT_DIR,
        "brazil_literacy_rates_historical.csv",
    )

    try:
        rows_2022 = _fetch_2022_literacy_rates_rows(session, raw_dir=raw_dir)
        if not rows_2022:
            raise RuntimeError("No live 2022+ literacy rate records fetched.")

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
            f"Error downloading Brazil Census literacy rates: {e}") from e

    df_2022 = pd.DataFrame(rows_2022).drop_duplicates(
        subset=["observationAbout", "observationDate", "variableMeasured"],
        keep="last",
    )
    write_df_atomically(df_2022, target_path)
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
        f"Literacy rates download completed successfully: {saved_file}")


if __name__ == "__main__":
    app.run(main)
