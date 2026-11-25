# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Preprocesses extracted CRDC Harassment or Bullying CSVs for StatVar import."""

from glob import glob
import os
import re
import shutil

from absl import logging
import pandas as pd

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT_DIR = os.path.join(_SCRIPT_PATH, "input_files")
DEFAULT_OUTPUT_DIR = os.path.join(_SCRIPT_PATH, "preprocessed_files")
DELIMITER = ","

_CHARS_TO_REMOVE_RE = re.compile(r"[`'\"]")
_YEAR_FROM_FILENAME_RE = re.compile(r"(\D|^)(\d{4})(\D|$)")


def extract_year_from_filename(filename: str) -> str | None:
    """Extracts a four-digit year (YYYY) from the filename."""
    match = _YEAR_FROM_FILENAME_RE.search(filename)
    if match:
        return match.group(2)
    return None


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Removes backticks/quotes and strips whitespace from headers and cells."""
    df = df.copy()
    df.columns = [
        _CHARS_TO_REMOVE_RE.sub("", str(col)).strip() for col in df.columns
    ]

    for col in df.columns:
        if pd.api.types.is_object_dtype(
                df[col]) or pd.api.types.is_string_dtype(df[col]):
            # Preserve missing values as empty strings rather than literal 'nan'.
            s = df[col].fillna("").astype(str)
            s = s.str.replace(_CHARS_TO_REMOVE_RE, "", regex=True).str.strip()
            if col.upper() == "COMBOKEY":
                s = s.str.replace(r"^(\d+)\.0$", r"\1", regex=True)
            df[col] = s

    return df


def _read_source_file(filepath: str, sep: str = DELIMITER) -> pd.DataFrame:
    """Reads a CSV or Excel file with all columns preserved as strings."""
    file_extension = os.path.splitext(filepath)[1].lower()
    if file_extension == ".csv":
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                return pd.read_csv(
                    filepath,
                    sep=sep,
                    dtype=str,
                    low_memory=False,
                    keep_default_na=False,
                    encoding=encoding,
                )
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Unable to decode CSV file: {filepath}")
    if file_extension in (".xlsx", ".xls"):
        engine = "openpyxl" if file_extension == ".xlsx" else None
        return pd.read_excel(
            filepath,
            sheet_name=0,
            dtype=str,
            keep_default_na=False,
            engine=engine,
        )
    raise ValueError(
        f"Unsupported file format ({file_extension}) for {filepath}. "
        "Only CSV, XLSX, and XLS are supported.")


def process_file(filepath: str, year: str | None, output_dir: str) -> str:
    """Cleans one CRDC file, inserts 'Year', and writes atomically to output_dir."""
    if not year:
        raise ValueError(
            f"Could not extract 4-digit survey year from filename: {filepath}")

    logging.info("Processing '%s' (Year=%s)...", filepath, year)
    df = _read_source_file(filepath)
    if df.empty:
        raise ValueError(f"Input file '{filepath}' has 0 data rows.")

    df = clean_dataframe(df)
    cols = df.columns.tolist()
    if not cols:
        raise ValueError(f"Could not identify columns in '{filepath}'.")

    if "Year" not in df.columns:
        df["Year"] = year

    is_2010_file = year == "2010"
    if is_2010_file and "NA" not in df.columns:
        df["NA"] = ""

    first_col = cols[0]
    new_cols = [first_col, "Year"]
    cols_to_exclude = {first_col, "Year"}
    if is_2010_file:
        new_cols.append("NA")
        cols_to_exclude.add("NA")

    remaining_cols = [c for c in df.columns if c not in cols_to_exclude]
    df = df[new_cols + remaining_cols]

    os.makedirs(output_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(filepath))[0]
    out_path = os.path.join(output_dir, f"{stem}.csv")
    tmp_path = f"{out_path}.tmp"
    df.to_csv(tmp_path, index=False, sep=DELIMITER)
    os.replace(tmp_path, out_path)
    logging.info("Wrote preprocessed CSV '%s' (%d rows).", out_path, len(df))
    return out_path


def run_preprocess(
    input_dir: str = DEFAULT_INPUT_DIR,
    output_dir: str = DEFAULT_OUTPUT_DIR,
) -> list[str]:
    """Preprocesses all CRDC files from input_dir into output_dir."""
    logging.info("Starting preprocessing from '%s' to '%s'...", input_dir,
                 output_dir)
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    file_paths = sorted(
        f for f in glob(os.path.join(input_dir, "*"))
        if os.path.isfile(f) and not os.path.basename(f).startswith("."))
    if not file_paths:
        raise RuntimeError(f"No input files found in '{input_dir}'.")

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    written: list[str] = []
    for filepath in file_paths:
        year = extract_year_from_filename(os.path.basename(filepath))
        written.append(process_file(filepath, year, output_dir))

    logging.info("Preprocessing complete. Produced %d file(s) in '%s'.",
                 len(written), output_dir)
    return written


def main() -> None:
    logging.set_verbosity(logging.INFO)
    run_preprocess()


if __name__ == "__main__":
    main()
