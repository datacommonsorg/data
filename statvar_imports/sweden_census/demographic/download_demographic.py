# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Downloads Sweden Census Category 1 (Demographic / Population) data from SCB PxWeb API.

Dynamically discovers years, regions, age brackets, gender, and marital status
from Statistics Sweden (SCB) PxWeb REST API v1 metadata (`BefolkningR1860N` and
`BefolkningR1860NCKM` for National 1860-latest; `BefolkningNy` and
`BefolkningCKM` for Sub-National 1968-latest) and `sweden_places_resolved.csv`,
and writes all 23 wide-format CSVs into `input_files/`.
"""

import collections
import csv
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(_SCRIPT_DIR, "../../../util"))

import download_util  # pylint: disable=g-import-not-at-top

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "output_dir",
    os.path.join(_SCRIPT_DIR, "input_files"),
    "Output directory for generated raw wide-format CSV files.",
    allow_override=True,
)
flags.DEFINE_string(
    "places_resolved_csv",
    os.path.join(_SCRIPT_DIR, "sweden_places_resolved.csv"),
    "Path to sweden_places_resolved.csv used to derive NUTS1/NUTS2/NUTS3 hierarchy.",
)
flags.DEFINE_integer(
    "start_year_national",
    1860,
    "First year to include for National BefolkningR1860N files.",
)
flags.DEFINE_integer(
    "start_year_subnational",
    1968,
    "First year to include for Sub-National BefolkningNy files.",
)
flags.DEFINE_integer(
    "end_year",
    None,
    "Optional last year to include (defaults to latest available year in SCB API).",
)

NATIONAL_API_URL = (
    "https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101A/BefolkningR1860N"
)
NATIONAL_CKM_API_URL = (
    "https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101A/BefolkningR1860NCKM"
)
SUBNATIONAL_API_URL = (
    "https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101A/BefolkningNy"
)
SUBNATIONAL_CKM_API_URL = (
    "https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101A/BefolkningCKM"
)
REQUEST_SLEEP_SECONDS = 1.2


def fetch_metadata(api_url: str) -> Dict[str, Any]:
    """Fetches PxWeb table metadata from the SCB API endpoint using download_util."""
    logging.info("Fetching SCB metadata from %s", api_url)
    content_bytes = download_util.request_url(
        url=api_url,
        method="GET",
        output="bytes",
        timeout=60,
        retries=5,
        retry_secs=5,
    )
    if not content_bytes:
        raise RuntimeError(f"Empty metadata response from SCB API: {api_url}")
    if isinstance(content_bytes, dict):
        return content_bytes
    text = (content_bytes.decode("utf-8-sig") if isinstance(
        content_bytes, bytes) else str(content_bytes))
    return json.loads(text)


def query_scb_chunk(
    api_url: str,
    query_items: Sequence[Tuple[str, Sequence[str]]],
) -> List[Dict[str, Any]]:
    """Executes a JSON POST query against an SCB PxWeb endpoint using download_util."""
    payload = {
        "query": [{
            "code": code,
            "selection": {
                "filter": "item",
                "values": list(vals)
            }
        } for code, vals in query_items],
        "response": {
            "format": "json"
        },
    }
    time.sleep(REQUEST_SLEEP_SECONDS)
    content_bytes = download_util.request_url(
        url=api_url,
        params=payload,
        method="POST",
        output="bytes",
        timeout=180,
        retries=5,
        retry_secs=5,
    )
    if not content_bytes:
        raise RuntimeError(f"Failed to download SCB POST chunk from {api_url}")
    if isinstance(content_bytes, dict):
        return content_bytes.get("data", [])
    text = (content_bytes.decode("utf-8-sig") if isinstance(
        content_bytes, bytes) else str(content_bytes))
    return json.loads(text).get("data", [])


def _parse_int_value(raw_val: Any) -> int:
    """Parses a numeric string from SCB API, treating '..' or '-' as 0."""
    if raw_val is None:
        return 0
    val_str = str(raw_val).strip()
    if not val_str or val_str in ("..", "-", ".", "None"):
        return 0
    try:
        return int(float(val_str))
    except ValueError:
        return 0


def _age_to_bracket(age_code: str, max_open_age: int) -> Optional[str]:
    """Maps a single-year SCB age code ('0'..'110+' or '100+1') to its 10-year age bracket label."""
    code = age_code.strip()
    if code == "100+1":
        digits = "100"
    elif "+" in code:
        prefix, suffix = code.split("+", 1)
        if suffix or not prefix.isdigit():
            return None
        digits = prefix
    else:
        if not code.isdigit():
            return None
        digits = code
    age = int(digits)
    if age < 5:
        return "0-4 år"
    if age >= max_open_age:
        return f"{max_open_age}+ år"
    low = ((age - 5) // 10) * 10 + 5
    return f"{low}-{low + 9} år"


def _load_nuts_hierarchy(
    places_csv_path: str,
) -> Tuple[Dict[str, Tuple[str, str, str]], Dict[str, List[str]]]:
    """Loads NUTS1/2/3 region lists and County-name -> (NUTS3, NUTS2, NUTS1) map from places CSV."""
    nuts_code_to_label: Dict[str, str] = {}
    nuts_groups: Dict[str, List[str]] = {"nuts1": [], "nuts2": [], "nuts3": []}

    with open(places_csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            place_name = row["place_name"].strip()
            dcid = row["dcid"].strip()
            if not dcid.startswith("nuts/SE"):
                continue
            nuts_code = dcid.removeprefix("nuts/")
            nuts_code_to_label[nuts_code] = place_name
            if len(nuts_code) == 3:
                nuts_groups["nuts1"].append(place_name)
            elif len(nuts_code) == 4:
                nuts_groups["nuts2"].append(place_name)
            elif len(nuts_code) == 5:
                nuts_groups["nuts3"].append(place_name)

    county_name_to_nuts: Dict[str, Tuple[str, str, str]] = {}
    for nuts3_label in nuts_groups["nuts3"]:
        nuts3_code, county_name = nuts3_label.split(" ", 1)
        nuts2_label = nuts_code_to_label[nuts3_code[:4]]
        nuts1_label = nuts_code_to_label[nuts3_code[:3]]
        county_name_to_nuts[county_name] = (nuts3_label, nuts2_label,
                                            nuts1_label)

    return county_name_to_nuts, nuts_groups


def _write_csv(file_path: str, rows: Sequence[Sequence[str]]) -> None:
    """Atomically writes rows to a UTF-8 CSV file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    tmp_path = f"{file_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
        raise RuntimeError(f"Generated empty CSV file: {tmp_path}")
    os.replace(tmp_path, file_path)
    logging.info("Wrote %s (%d rows)", file_path, len(rows))


def _build_sheet(
    title: str,
    dim_headers: Sequence[str],
    years: Sequence[str],
    data_rows: Sequence[Sequence[str]],
) -> List[List[str]]:
    """Constructs a 3-header-row SCB wide-format table."""
    total_cols = max(1, len(dim_headers)) + len(years)
    header_row = (list(dim_headers) if dim_headers else [""]) + list(years)
    return [
        [title] + [""] * (total_cols - 1),
        [""] * total_cols,
        header_row,
        *[list(r) for r in data_rows],
    ]


def download_and_write_national_files(
    output_dir: str,
    start_year: int = 1860,
    end_year: Optional[int] = None,
) -> List[str]:
    """Downloads National population (1860-2024 from BefolkningR1860N and 2025+ from BefolkningR1860NCKM) and writes 4 CSVs."""
    meta = fetch_metadata(NATIONAL_API_URL)
    var_map = {v["code"]: v for v in meta.get("variables", [])}

    hist_years = sorted(
        (y for y in var_map["Tid"]["values"]
         if y.isdigit() and int(y) >= start_year and int(y) <= 2024 and (
             end_year is None or int(y) <= end_year)),
        key=int,
    )
    sex_items = [(c, t.strip()) for c, t in zip(
        var_map["Kon"]["values"],
        var_map["Kon"].get("valueTexts", var_map["Kon"]["values"]),
    ) if c in ("1", "2")]
    all_sexes = [c for c, _ in sex_items]
    contents_code = var_map["ContentsCode"]["values"][0]

    available_hist_ages = var_map["Alder"]["values"]
    hist_single_ages: List[str] = []
    age_code_to_bracket: Dict[str, str] = {}
    age_brackets: List[str] = []
    for age_code in available_hist_ages:
        bracket = _age_to_bracket(age_code, max_open_age=105)
        if bracket is not None:
            hist_single_ages.append(age_code)
            age_code_to_bracket[age_code] = bracket
            if bracket not in age_brackets:
                age_brackets.append(bracket)

    hist_tot_age = "tot" if "tot" in available_hist_ages else None
    hist_query_ages = (hist_single_ages +
                       [hist_tot_age] if hist_tot_age else hist_single_ages)

    bracket_sex_year: Dict[Tuple[str, str, str],
                           int] = collections.defaultdict(int)
    total_sex_year: Dict[Tuple[str, str], int] = collections.defaultdict(int)

    for i in range(0, len(hist_years), 60):
        year_chunk = hist_years[i:i + 60]
        data = query_scb_chunk(
            NATIONAL_API_URL,
            [
                ("Alder", hist_query_ages),
                ("Kon", all_sexes),
                ("ContentsCode", [contents_code]),
                ("Tid", year_chunk),
            ],
        )
        for row in data:
            age_code, sex_code, year = row["key"][:3]
            val = _parse_int_value(row["values"][0])
            if hist_tot_age and age_code == hist_tot_age:
                total_sex_year[(sex_code, year)] += val
            else:
                bracket = age_code_to_bracket.get(age_code)
                if bracket is not None:
                    bracket_sex_year[(bracket, sex_code, year)] += val
                    if not hist_tot_age:
                        total_sex_year[(sex_code, year)] += val

    # Discover and fetch 2025+ years from BefolkningR1860NCKM
    ckm_years: List[str] = []
    if end_year is None or end_year >= 2025:
        meta_ckm = fetch_metadata(NATIONAL_CKM_API_URL)
        var_ckm = {v["code"]: v for v in meta_ckm.get("variables", [])}
        ckm_years = sorted(
            (y for y in var_ckm.get("Tid", {}).get("values", [])
             if y.isdigit() and int(y) >= max(start_year, 2025) and y not in
             hist_years and (end_year is None or int(y) <= end_year)),
            key=int,
        )
        if ckm_years:
            ckm_contents = var_ckm["ContentsCode"]["values"][0]
            available_ckm_ages = var_ckm["Alder"]["values"]
            ckm_single_ages: List[str] = []
            ckm_age_to_bracket: Dict[str, str] = {}
            for age_code in available_ckm_ages:
                # In CKM tables, ages go up to 99 + '100+1' (mapped to 95-104 år)
                bracket = _age_to_bracket(age_code, max_open_age=105)
                if bracket is not None:
                    ckm_single_ages.append(age_code)
                    ckm_age_to_bracket[age_code] = bracket
                    if bracket not in age_brackets:
                        age_brackets.append(bracket)
            ckm_tot_age = ("TotSA" if "TotSA" in available_ckm_ages else
                           ("tot" if "tot" in available_ckm_ages else None))
            ckm_query_ages = (ckm_single_ages + [ckm_tot_age]
                              if ckm_tot_age else ckm_single_ages)

            for i in range(0, len(ckm_years), 60):
                year_chunk = ckm_years[i:i + 60]
                data = query_scb_chunk(
                    NATIONAL_CKM_API_URL,
                    [
                        ("Alder", ckm_query_ages),
                        ("Kon", all_sexes),
                        ("ContentsCode", [ckm_contents]),
                        ("Tid", year_chunk),
                    ],
                )
                for row in data:
                    age_code, sex_code, year = row["key"][:3]
                    val = _parse_int_value(row["values"][0])
                    if ckm_tot_age and age_code == ckm_tot_age:
                        total_sex_year[(sex_code, year)] += val
                    else:
                        bracket = ckm_age_to_bracket.get(age_code)
                        if bracket is not None:
                            bracket_sex_year[(bracket, sex_code, year)] += val
                            if not ckm_tot_age:
                                total_sex_year[(sex_code, year)] += val

    all_years = sorted(hist_years + ckm_years, key=int)

    # 1. population_country.csv
    _write_csv(
        os.path.join(output_dir, "population_country.csv"),
        _build_sheet(
            "Folkmängd efter år",
            [],
            all_years,
            [[""] + [
                str(sum(total_sex_year[(s, y)] for s, _ in sex_items))
                for y in all_years
            ]],
        ),
    )

    # 2. population_gender_country.csv
    _write_csv(
        os.path.join(output_dir, "population_gender_country.csv"),
        _build_sheet(
            "Folkmängd efter kön och år",
            ["kön"],
            all_years,
            [[sex_label] +
             [str(total_sex_year[(sex_code, y)]) for y in all_years]
             for sex_code, sex_label in sex_items],
        ),
    )

    # 3. population_age_country.csv
    _write_csv(
        os.path.join(output_dir, "population_age_country.csv"),
        _build_sheet(
            "Folkmängd efter ålder och år",
            ["ålder"],
            all_years,
            [[b] + [
                str(sum(bracket_sex_year[(b, s, y)] for s, _ in sex_items))
                for y in all_years
            ] for b in age_brackets],
        ),
    )

    # 4. population_age_gender_country.csv
    _write_csv(
        os.path.join(output_dir, "population_age_gender_country.csv"),
        _build_sheet(
            "Folkmängd efter ålder, kön och år",
            ["ålder", "kön"],
            all_years,
            [[b, sex_label] +
             [str(bracket_sex_year[(b, sex_code, y)]) for y in all_years]
             for b in age_brackets for sex_code, sex_label in sex_items],
        ),
    )
    return all_years


def download_and_write_subnational_files(
    output_dir: str,
    places_csv_path: str = os.path.join(_SCRIPT_DIR,
                                        "sweden_places_resolved.csv"),
    start_year: int = 1968,
    end_year: Optional[int] = None,
) -> List[str]:
    """Downloads Sub-National population (1968-2024 from BefolkningNy and 2025+ from BefolkningCKM) and writes 19 CSVs."""
    county_name_to_nuts, nuts_groups = _load_nuts_hierarchy(places_csv_path)
    meta = fetch_metadata(SUBNATIONAL_API_URL)
    var_map = {v["code"]: v for v in meta.get("variables", [])}

    hist_years = sorted(
        (y for y in var_map["Tid"]["values"]
         if y.isdigit() and int(y) >= start_year and int(y) <= 2024 and (
             end_year is None or int(y) <= end_year)),
        key=int,
    )

    county_codes: List[str] = []
    county_code_to_nuts: Dict[str, Tuple[str, str, str]] = {}
    muni_codes: List[str] = []
    muni_code_to_label: Dict[str, str] = {}

    for code, text in zip(var_map["Region"]["values"],
                          var_map["Region"]["valueTexts"]):
        if code == "00":
            continue
        clean_text = text.removeprefix(code).strip()
        if len(code) == 2 and clean_text in county_name_to_nuts:
            county_codes.append(code)
            county_code_to_nuts[code] = county_name_to_nuts[clean_text]
        elif len(code) == 4:
            muni_codes.append(code)
            muni_code_to_label[code] = f"{code} {clean_text}"

    if len(county_codes) != 21 or len(muni_codes) != 290:
        raise RuntimeError(
            f"Expected 21 counties and 290 municipalities in SCB metadata, "
            f"found {len(county_codes)} counties and {len(muni_codes)} municipalities."
        )

    marital_items = [(c, t.strip())
                     for c, t in zip(
                         var_map["Civilstand"]["values"],
                         var_map["Civilstand"].get(
                             "valueTexts", var_map["Civilstand"]["values"]),
                     ) if c != "SC"]
    all_marital = [c for c, _ in marital_items]

    sex_items = [(c, t.strip()) for c, t in zip(
        var_map["Kon"]["values"],
        var_map["Kon"].get("valueTexts", var_map["Kon"]["values"]),
    ) if c in ("1", "2")]
    all_sexes = [c for c, _ in sex_items]
    contents_code = ("BE0101N1"
                     if "BE0101N1" in var_map["ContentsCode"]["values"] else
                     var_map["ContentsCode"]["values"][0])

    single_ages: List[str] = []
    age_code_to_bracket: Dict[str, str] = {}
    age_brackets: List[str] = []
    available_ages = var_map["Alder"]["values"]
    for age_code in available_ages:
        bracket = _age_to_bracket(age_code, max_open_age=95)
        if bracket is not None:
            single_ages.append(age_code)
            age_code_to_bracket[age_code] = bracket
            if bracket not in age_brackets:
                age_brackets.append(bracket)

    tot_age_code = "tot" if "tot" in available_ages else None
    county_query_ages = (single_ages +
                         [tot_age_code] if tot_age_code else single_ages)

    ms_sex_year: Dict[Tuple[str, str, str, str],
                      int] = collections.defaultdict(int)
    age_ms_sex_year: Dict[Tuple[str, str, str, str, str],
                          int] = (collections.defaultdict(int))

    # 1A. Fetch 21 Counties from BefolkningNy (1968-2024) by single-year ages + 'tot'
    for i in range(0, len(hist_years), 5):
        year_chunk = hist_years[i:i + 5]
        data = query_scb_chunk(
            SUBNATIONAL_API_URL,
            [
                ("Region", county_codes),
                ("Civilstand", all_marital),
                ("Alder", county_query_ages),
                ("Kon", all_sexes),
                ("ContentsCode", [contents_code]),
                ("Tid", year_chunk),
            ],
        )
        for row in data:
            c_code, ms_code, age_code, sex_code, year = row["key"][:5]
            val = _parse_int_value(row["values"][0])
            if tot_age_code and age_code == tot_age_code:
                for reg_label in county_code_to_nuts[c_code]:
                    ms_sex_year[(reg_label, ms_code, sex_code, year)] += val
            else:
                bracket = age_code_to_bracket.get(age_code)
                if bracket is not None:
                    for reg_label in county_code_to_nuts[c_code]:
                        age_ms_sex_year[(reg_label, ms_code, bracket, sex_code,
                                         year)] += val
                        if not tot_age_code:
                            ms_sex_year[(reg_label, ms_code, sex_code,
                                         year)] += val

    # 2A. Fetch 290 Municipalities from BefolkningNy (1968-2024) with Alder='tot'
    muni_ages = [tot_age_code] if tot_age_code is not None else single_ages
    muni_year_chunk = 20 if tot_age_code is not None else 1
    for i in range(0, len(hist_years), muni_year_chunk):
        year_chunk = hist_years[i:i + muni_year_chunk]
        data = query_scb_chunk(
            SUBNATIONAL_API_URL,
            [
                ("Region", muni_codes),
                ("Civilstand", all_marital),
                ("Alder", muni_ages),
                ("Kon", all_sexes),
                ("ContentsCode", [contents_code]),
                ("Tid", year_chunk),
            ],
        )
        for row in data:
            m_code, ms_code, _, sex_code, year = row["key"][:5]
            reg_label = muni_code_to_label[m_code]
            ms_sex_year[(reg_label, ms_code, sex_code,
                         year)] += _parse_int_value(row["values"][0])

    # 1B & 2B. Discover and fetch 2025+ years from BefolkningCKM
    ckm_years: List[str] = []
    if end_year is None or end_year >= 2025:
        meta_ckm = fetch_metadata(SUBNATIONAL_CKM_API_URL)
        var_ckm = {v["code"]: v for v in meta_ckm.get("variables", [])}
        ckm_years = sorted(
            (y for y in var_ckm.get("Tid", {}).get("values", [])
             if y.isdigit() and int(y) >= max(start_year, 2025) and y not in
             hist_years and (end_year is None or int(y) <= end_year)),
            key=int,
        )
        if ckm_years:
            ckm_contents = ("000007ME"
                            if "000007ME" in var_ckm["ContentsCode"]["values"]
                            else var_ckm["ContentsCode"]["values"][0])
            available_ckm_ages = var_ckm["Alder"]["values"]
            ckm_single_ages: List[str] = []
            ckm_age_to_bracket: Dict[str, str] = {}
            for age_code in available_ckm_ages:
                bracket = _age_to_bracket(age_code, max_open_age=95)
                if bracket is not None:
                    ckm_single_ages.append(age_code)
                    ckm_age_to_bracket[age_code] = bracket
                    if bracket not in age_brackets:
                        age_brackets.append(bracket)
            ckm_tot_age = ("TotSA" if "TotSA" in available_ckm_ages else
                           ("tot" if "tot" in available_ckm_ages else None))
            ckm_county_ages = (ckm_single_ages + [ckm_tot_age]
                               if ckm_tot_age else ckm_single_ages)

            # 1B. Fetch 21 Counties from BefolkningCKM (2025+)
            for i in range(0, len(ckm_years), 5):
                year_chunk = ckm_years[i:i + 5]
                data = query_scb_chunk(
                    SUBNATIONAL_CKM_API_URL,
                    [
                        ("Region", county_codes),
                        ("Civilstand", all_marital),
                        ("Alder", ckm_county_ages),
                        ("Kon", all_sexes),
                        ("ContentsCode", [ckm_contents]),
                        ("Tid", year_chunk),
                    ],
                )
                for row in data:
                    c_code, ms_code, age_code, sex_code, year = row["key"][:5]
                    val = _parse_int_value(row["values"][0])
                    if ckm_tot_age and age_code == ckm_tot_age:
                        for reg_label in county_code_to_nuts[c_code]:
                            ms_sex_year[(reg_label, ms_code, sex_code,
                                         year)] += val
                    else:
                        bracket = ckm_age_to_bracket.get(age_code)
                        if bracket is not None:
                            for reg_label in county_code_to_nuts[c_code]:
                                age_ms_sex_year[(reg_label, ms_code, bracket,
                                                 sex_code, year)] += val
                                if not ckm_tot_age:
                                    ms_sex_year[(reg_label, ms_code, sex_code,
                                                 year)] += val

            # 2B. Fetch 290 Municipalities from BefolkningCKM (2025+)
            ckm_muni_ages = ([ckm_tot_age]
                             if ckm_tot_age is not None else ckm_single_ages)
            ckm_muni_chunk = 20 if ckm_tot_age is not None else 1
            for i in range(0, len(ckm_years), ckm_muni_chunk):
                year_chunk = ckm_years[i:i + ckm_muni_chunk]
                data = query_scb_chunk(
                    SUBNATIONAL_CKM_API_URL,
                    [
                        ("Region", muni_codes),
                        ("Civilstand", all_marital),
                        ("Alder", ckm_muni_ages),
                        ("Kon", all_sexes),
                        ("ContentsCode", [ckm_contents]),
                        ("Tid", year_chunk),
                    ],
                )
                for row in data:
                    m_code, ms_code, _, sex_code, year = row["key"][:5]
                    reg_label = muni_code_to_label[m_code]
                    ms_sex_year[(reg_label, ms_code, sex_code,
                                 year)] += _parse_int_value(row["values"][0])

    all_years = sorted(hist_years + ckm_years, key=int)

    title = "Folkmängd efter region, civilstånd, ålder, kön och år"
    region_groups = {
        **nuts_groups,
        "municipality": [muni_code_to_label[c] for c in muni_codes],
    }

    for geo, regions in region_groups.items():
        # 1. population_{geo}.csv
        _write_csv(
            os.path.join(output_dir, f"population_{geo}.csv"),
            _build_sheet(
                title,
                ["region"],
                all_years,
                [[reg] + [
                    str(
                        sum(ms_sex_year[(reg, ms_c, s_c, y)]
                            for ms_c, _ in marital_items
                            for s_c, _ in sex_items)) for y in all_years
                ] for reg in regions],
            ),
        )

        # 2. population_gender_{geo}.csv
        _write_csv(
            os.path.join(output_dir, f"population_gender_{geo}.csv"),
            _build_sheet(
                title,
                ["region", "kön"],
                all_years,
                [[reg, sex_label] + [
                    str(
                        sum(ms_sex_year[(reg, ms_c, sex_code, y)]
                            for ms_c, _ in marital_items)) for y in all_years
                ] for reg in regions for sex_code, sex_label in sex_items],
            ),
        )

        # 3. population_maritalstatus_{geo}.csv
        _write_csv(
            os.path.join(output_dir, f"population_maritalstatus_{geo}.csv"),
            _build_sheet(
                title,
                ["region", "civilstånd"],
                all_years,
                [[reg, ms_label] + [
                    str(
                        sum(ms_sex_year[(reg, ms_code, s_c, y)]
                            for s_c, _ in sex_items)) for y in all_years
                ] for reg in regions for ms_code, ms_label in marital_items],
            ),
        )

        # 4. population_maritalstatus_gender_{geo}.csv
        _write_csv(
            os.path.join(output_dir,
                         f"population_maritalstatus_gender_{geo}.csv"),
            _build_sheet(
                title,
                ["region", "civilstånd", "kön"],
                all_years,
                [[reg, ms_label, sex_label] + [
                    str(ms_sex_year[(reg, ms_code, sex_code, y)])
                    for y in all_years
                ] for reg in regions for ms_code, ms_label in marital_items
                 for sex_code, sex_label in sex_items],
            ),
        )

        # 5. population_age_maritalstatus_gender_{geo}.csv (nuts1, nuts2, nuts3)
        if geo in ("nuts1", "nuts2", "nuts3"):
            _write_csv(
                os.path.join(output_dir,
                             f"population_age_maritalstatus_gender_{geo}.csv"),
                _build_sheet(
                    title,
                    ["region", "civilstånd", "ålder", "kön"],
                    all_years,
                    [[reg, ms_label, b, sex_label] + [
                        str(age_ms_sex_year[(reg, ms_code, b, sex_code, y)])
                        for y in all_years
                    ] for reg in regions for ms_code, ms_label in marital_items
                     for b in age_brackets
                     for sex_code, sex_label in sex_items],
                ),
            )

    return all_years


def main(argv: List[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")

    os.makedirs(FLAGS.output_dir, exist_ok=True)

    nat_years = download_and_write_national_files(
        output_dir=FLAGS.output_dir,
        start_year=FLAGS.start_year_national,
        end_year=FLAGS.end_year,
    )
    sub_years = download_and_write_subnational_files(
        output_dir=FLAGS.output_dir,
        places_csv_path=FLAGS.places_resolved_csv,
        start_year=FLAGS.start_year_subnational,
        end_year=FLAGS.end_year,
    )
    if os.path.exists("http_cache.sqlite"):
        try:
            os.remove("http_cache.sqlite")
        except OSError:
            pass
    logging.info(
        "Successfully generated all 23 Demographic raw input CSVs in %s "
        "(National: %s..%s, Sub-National: %s..%s).",
        FLAGS.output_dir,
        nat_years[0],
        nat_years[-1],
        sub_years[0],
        sub_years[-1],
    )


if __name__ == "__main__":
    app.run(main)
