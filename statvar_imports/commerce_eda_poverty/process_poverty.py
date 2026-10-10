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

"""Preprocessing script for Commerce EDA Persistent Poverty Counties dataset.

This script ingests the raw Persistent Poverty Counties dataset (downloaded
from U.S. Economic Development Administration (EDA) / Department of Commerce),
standardizes geographic identifiers (5-digit county FIPS codes across 50 US
states, DC, and Puerto Rico, and 5-digit island territory codes), validates
poverty percentage rates across 1990, 2000, 2020, and 2021, and generates the
normalized cleaned CSV for stat_var_processor.py.

Why Preprocessing is Required (Why PV Map Alone is Insufficient):
1. Format Reshaping (Wide-to-Long): The raw EDA dataset is wide (one row per county
   with separate columns for 1990, 2000, and recent estimate). PV mapping requires
   a normalized long format where each row represents a single observation (GEOID,
   date, poverty_rate).
2. Dynamic & Heterogeneous Observation Dates: The "Most Recent Estimate" is not
   from a single survey year. For the 50 US states, DC, and Puerto Rico, the
   benchmark is SAIPE 2021. However, SAIPE does not cover island territories
   (American Samoa, Guam, Northern Mariana Islands, US Virgin Islands); their
   estimates come from the 2020 Island Areas Decennial Census. Preprocessing parses
   the survey year dynamically from the 'Data Source' note (or territory FIPS prefix)
   to assign 2020 vs 2021 per record. PV Map CSV configurations cannot conditionally
   extract and branch dates based on FIPS prefixes or free-text regex matching.
3. Metadata and Footnote Cleaning: Upstream Excel/CSV files contain non-tabular
   header titles, subtitle rows, and footnote rows at the bottom that must be skipped.
4. FIPS Code Standardization & Filtering: GEOIDs in raw files may lack leading zeros
   (e.g., 1001 -> 01001) or represent state-level rollups (e.g. 01000) that must be
   filtered out from county-level statistical variables.
"""

import datetime
import os
import re
import tempfile

from absl import app, flags, logging
import openpyxl
import pandas as pd

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_SOURCE_CSV = os.path.join(MODULE_DIR, "input_files", "Poverty.csv")
DEFAULT_SOURCE_XLSX = os.path.join(MODULE_DIR, "input_files", "EDA_FY23_PPCs.xlsx")
DEFAULT_RAW_CSV = os.path.join(MODULE_DIR, "output", "Poverty_original.csv")
CLEANED_CSV = os.path.join(MODULE_DIR, "output", "Poverty_cleaned.csv")

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "source_path",
    None,
    "Path to source file (.csv or .xlsx). If not specified, automatically "
    "resolves from input_files/Poverty.csv, input_files/EDA_FY23_PPCs.xlsx, "
    "or output/Poverty_original.csv.",
)
flags.DEFINE_string(
    "cleaned_csv_path", CLEANED_CSV, "Path to save cleaned output CSV."
)
flags.DEFINE_integer(
    "min_county_count", 3000, "Minimum number of valid counties expected."
)
flags.DEFINE_integer(
    "min_survey_year", 2020, "Minimum valid survey year for most recent estimate."
)
flags.DEFINE_integer(
    "max_survey_year",
    None,
    "Maximum valid survey year (defaults to current year).",
)

# Valid 2-digit US State and Territory FIPS codes
VALID_STATE_FIPS = {
    # 50 States + DC
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15",
    "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27",
    "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    "40", "41", "42", "44", "45", "46", "47", "48", "49", "50", "51", "53",
    "54", "55", "56",
    # Territories: AS, GU, MP, PR, VI
    "60", "66", "69", "72", "78",
}

# Island territories where most recent estimate is from 2020 Decennial Census
ISLAND_TERRITORY_FIPS = {"60", "66", "69", "78"}

COLUMN_RENAME_MAP = {
    "GEOID": "GEOID",
    "1990 Decennial Census, % in Poverty": "poverty_rate_1990",
    "2000 Decennial Census, % in Poverty": "poverty_rate_2000",
    "Most Recent Estimate, % in Poverty*": "poverty_rate_recent",
    "Most Recent Estimate, % in Poverty": "poverty_rate_recent",
}


def clean_geoid(val):
    """Standardizes GEOIDs to 5 digits and validates against US state FIPS.

    Rejects state summary entries of the form XX000.
    """
    if pd.isna(val):
        return None
    s = str(val).strip()
    match = re.match(r"^(\d+)(?:\.0+)?$", s)
    if not match:
        return None
    digits = match.group(1)
    if len(digits) == 4:
        digits = digits.zfill(5)
    if len(digits) == 5 and digits[:2] in VALID_STATE_FIPS and digits[2:] != "000":
        return digits
    return None


def _extract_dataframe_from_excel(excel_path):
    """Extracts Underlying_Data sheet from an Excel workbook into a DataFrame."""
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    try:
        sheet_names = wb.sheetnames
        target_sheet = None
        if "Underlying_Data" in sheet_names:
            target_sheet = "Underlying_Data"
        else:
            for name in sheet_names:
                if any(
                    k in name.lower()
                    for k in ["underlying", "poverty", "data", "ppc"]
                ):
                    target_sheet = name
                    break
            if not target_sheet:
                target_sheet = sheet_names[0]
            logging.warning(
                "Worksheet 'Underlying_Data' not found in %s; falling back "
                "to '%s'.",
                sheet_names,
                target_sheet,
            )
        ws = wb[target_sheet]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise ValueError(f"Excel sheet '{target_sheet}' is empty.")

        # Find row with GEOID header dynamically across all rows
        header_idx = None
        for idx, r in enumerate(rows):
            row_str = [str(c).strip() for c in r if c is not None]
            if any(c.upper() == "GEOID" for c in row_str):
                header_idx = idx
                break

        if header_idx is None:
            raise ValueError(
                f"Could not find header row containing 'GEOID' in sheet "
                f"'{target_sheet}' of {excel_path}"
            )

        headers = [
            ("" if c is None else str(c).strip()) for c in rows[header_idx]
        ]
        data_rows = []
        for r in rows[header_idx + 1:]:
            if not any(r):
                continue
            data_rows.append(
                [
                    ("" if c is None else str(c).strip())
                    for c in r[: len(headers)]
                ]
            )

        return pd.DataFrame(data_rows, columns=headers)
    finally:
        wb.close()


def resolve_source_file_path(requested_path=None):
    """Finds the raw source file, raising FileNotFoundError if missing."""
    if requested_path:
        if os.path.exists(requested_path) and os.path.getsize(requested_path) > 0:
            return requested_path
        raise FileNotFoundError(
            f"Specified source file not found or empty: {requested_path}"
        )

    candidates = [
        DEFAULT_SOURCE_CSV,
        DEFAULT_SOURCE_XLSX,
        DEFAULT_RAW_CSV,
    ]
    for candidate in candidates:
        if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
            return candidate

    raise FileNotFoundError(
        "No downloaded source file found. Please run download_poverty.py first "
        f"to fetch the dataset, or specify --source_path. Checked: {candidates}"
    )


def preprocess_poverty(
    src_path=DEFAULT_SOURCE_CSV,
    dst_path=CLEANED_CSV,
    min_county_count=3000,
    min_survey_year=2020,
    max_survey_year=None,
):
    """Preprocesses the raw Poverty dataset into normalized cleaned CSV."""
    logging.info("Preprocessing source Poverty dataset from %s...", src_path)
    if max_survey_year is None:
        max_survey_year = datetime.date.today().year
    if not os.path.exists(src_path) or os.path.getsize(src_path) == 0:
        raise ValueError(f"Source file does not exist or is empty: {src_path}")

    if src_path.lower().endswith((".xlsx", ".xls")):
        df = _extract_dataframe_from_excel(src_path)
    else:
        # Detect header row index by scanning lines until 'GEOID' is found
        skip = None
        with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f):
                if "GEOID" in line.upper():
                    skip = idx
                    break
        if skip is None:
            raise ValueError(
                "Could not find header row containing 'GEOID' in CSV file: "
                f"{src_path}"
            )
        df = pd.read_csv(src_path, skiprows=skip, dtype=str)

    if df.empty:
        raise ValueError(f"File not read properly into dataframe: {src_path}")

    # Strip column headers to avoid fragile whitespace issues
    df.columns = df.columns.str.strip()

    # Check if at least GEOID and the poverty columns are found
    if "GEOID" not in df.columns:
        raise ValueError("Missing required column 'GEOID' in source dataset")

    # Rename columns to standard names (including future <YEAR> Decennial cols)
    rename_dict = {}
    for col in df.columns:
        clean_col = col.rstrip("*").strip()
        matched = False
        for k, v in COLUMN_RENAME_MAP.items():
            if col == k or clean_col == k.rstrip("*").strip():
                rename_dict[col] = v
                matched = True
                break
        if not matched:
            hist_match = re.match(
                r"^(\d{4})\b.*%\s*in\s*Poverty", clean_col, flags=re.IGNORECASE
            )
            if hist_match:
                rename_dict[col] = f"poverty_rate_{hist_match.group(1)}"

    # Guard against silent year corruption if Data Source column is present
    data_source_cols = [c for c in df.columns if "data source" in c.lower()]
    df = df.rename(columns=rename_dict)

    required_cols = [
        "GEOID",
        "poverty_rate_1990",
        "poverty_rate_2000",
        "poverty_rate_recent",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns in source dataset: {missing}"
        )

    # Standardize and validate GEOIDs
    df["GEOID"] = df["GEOID"].apply(clean_geoid)
    df = df.dropna(subset=["GEOID"])

    is_territory = df["GEOID"].str[:2].isin(ISLAND_TERRITORY_FIPS)
    default_years = pd.Series("2021", index=df.index).where(
        ~is_territory, "2020"
    )

    if data_source_cols:
        ds_col = data_source_cols[0]
        ds_vals = df[ds_col].fillna("").astype(str).str.strip()
        has_ds = (ds_vals != "") & (ds_vals.str.lower() != "nan")
        extracted_years = ds_vals.str.findall(r"\b(?:19|20)\d{2}\b").str[-1]
        unrecognized_mask = has_ds & extracted_years.isna()
        if unrecognized_mask.any():
            bad_idx = unrecognized_mask.idxmax()
            raise ValueError(
                f"Unrecognized survey year in {ds_col} "
                f"('{ds_vals.loc[bad_idx]}') for GEOID "
                f"{df.loc[bad_idx, 'GEOID']}"
            )
        yr_numeric = pd.to_numeric(extracted_years, errors="coerce")
        out_of_range_mask = has_ds & (
            (yr_numeric < min_survey_year) | (yr_numeric > max_survey_year)
        )
        if out_of_range_mask.any():
            bad_idx = out_of_range_mask.idxmax()
            bad_yr = int(yr_numeric.loc[bad_idx])
            raise ValueError(
                f"Unexpected survey year {bad_yr} in {ds_col} for GEOID "
                f"{df.loc[bad_idx, 'GEOID']} (expected between "
                f"{min_survey_year} and {max_survey_year})"
            )
        recent_years = default_years.where(~has_ds, extracted_years)
    else:
        recent_years = default_years

    # Identify all historical year columns dynamically
    historical_year_cols = sorted(
        [
            (re.match(r"^poverty_rate_(\d{4})$", c).group(1), c)
            for c in df.columns
            if re.match(r"^poverty_rate_(\d{4})$", c)
        ],
        key=lambda x: int(x[0]),
    )

    # Coerce and validate poverty values within [0.0, 100.0]
    raw_poverty_cols = [c for _, c in historical_year_cols] + [
        "poverty_rate_recent"
    ]
    for col in raw_poverty_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.strip(), errors="coerce")
        invalid_mask = df[col].notna() & ((df[col] < 0.0) | (df[col] > 100.0))
        if invalid_mask.any():
            logging.warning(
                "Found %d out-of-bounds values in %s; setting to NaN",
                invalid_mask.sum(),
                col,
            )
            df.loc[invalid_mask, col] = None

    # Keep counties that have at least one valid poverty rate observation
    df = df.dropna(subset=raw_poverty_cols, how="all")

    # Verify sanity threshold on valid county count
    if len(df) < min_county_count:
        raise ValueError(
            f"Sanity check failed: Expected at least {min_county_count} "
            f"counties, but found {len(df)}."
        )

    # Reshape wide-to-long using vectorized pd.melt() and pd.concat()
    df = df.copy()
    df["_row_order"] = range(len(df))
    hist_rename = {col: yr for yr, col in historical_year_cols}
    hist_df = df[["_row_order", "GEOID"] + list(hist_rename.keys())].rename(
        columns=hist_rename
    )
    melted_hist = pd.melt(
        hist_df,
        id_vars=["_row_order", "GEOID"],
        value_vars=list(hist_rename.values()),
        var_name="year",
        value_name="poverty_rate",
    )
    recent_df = pd.DataFrame(
        {
            "_row_order": df["_row_order"],
            "GEOID": df["GEOID"],
            "year": recent_years.loc[df.index].astype(str),
            "poverty_rate": df["poverty_rate_recent"],
        }
    )
    combined = pd.concat([melted_hist, recent_df], ignore_index=True)
    combined = combined.dropna(subset=["poverty_rate"])
    combined["poverty_rate"] = combined["poverty_rate"].astype(float)
    combined = combined.drop_duplicates(
        subset=["_row_order", "year"], keep="last"
    )
    combined["_year_num"] = combined["year"].astype(int)
    combined = combined.sort_values(
        by=["_row_order", "_year_num"], kind="mergesort"
    )
    df = combined[["GEOID", "year", "poverty_rate"]].reset_index(drop=True)

    # Atomic write to destination file
    dst_dir = os.path.dirname(os.path.abspath(dst_path))
    os.makedirs(dst_dir, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=dst_dir,
            delete=False,
            suffix=".tmp",
            encoding="utf-8",
            newline="",
        ) as tmp_file:
            temp_path = tmp_file.name
            df.to_csv(tmp_file, index=False)

        os.replace(temp_path, dst_path)
        temp_path = None
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    logging.info("Poverty dataset cleaned and saved successfully to %s!", dst_path)
    logging.info("Shape: %s", df.shape)
    return dst_path


def main(argv):
    """Main entrypoint for preprocessing the poverty dataset."""
    del argv  # Unused
    try:
        source_path = resolve_source_file_path(FLAGS.source_path)
        preprocess_poverty(
            src_path=source_path,
            dst_path=FLAGS.cleaned_csv_path,
            min_county_count=FLAGS.min_county_count,
            min_survey_year=FLAGS.min_survey_year,
            max_survey_year=FLAGS.max_survey_year,
        )
    except Exception as e:
        logging.fatal(
            "Failed to preprocess Commerce EDA Poverty dataset: %s",
            e,
            exc_info=True,
        )


if __name__ == "__main__":
    app.run(main)
