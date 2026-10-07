# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
This Python Script Load the datasets, cleans it
and generates cleaned CSV, MCF, TMCF file.
Before running this module, run download.py script, it downloads
required input files, creates necessary folders for processing.
Folder information
input_files - downloaded files (from US nces website) are placed here
output_files - output files (mcf, tmcf and csv are written here)
"""

import os
import re
import sys
import warnings
from absl import app
from absl import flags
from absl import logging
import numpy as np
import pandas as pd

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)
MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(1, MODULE_DIR + '/../..')
from common.us_education import USEducation
from config import *

FLAGS = flags.FLAGS
flags.DEFINE_enum(
    'mode',
    'all',
    ['all', 'place', 'stats'],
    'Execution mode: "place" for place entities only, "stats" for demographic'
    ' observations only, "all" for both.',
)
flags.DEFINE_string(
    "input_path",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "gcs_folder"),
    "Path to directory containing input_files folder.",
)


class NCESPrivateSchool(USEducation):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """
    _import_name = SCHOOL_TYPE
    _split_headers_using_school_type = SPLIT_HEADER_ON_SCHOOL_TYPE
    _include_columns = POSSIBLE_DATA_COLUMNS
    _exclude_columns = EXCLUDE_DATA_COLUMNS
    _include_col_place = POSSIBLE_PLACE_COLUMNS
    _exclude_col_place = EXCLUDE_PLACE_COLUMNS
    _generate_statvars = True
    _observation_period = OBSERVATION_PERIOD
    _exclude_list = EXCLUDE_LIST
    _school_id = DROP_BY_VALUE
    _renaming_columns = RENAMING_PRIVATE_COLUMNS

    def set_include_columns(self, columns: list):
        self._include_columns = columns

    def set_exclude_columns(self, columns: list):
        self._exclude_columns = columns

    def set_generate_statvars_flag(self, flag: bool):
        self._generate_statvars = flag

    @staticmethod
    def _map_code_col(series: pd.Series, code_map: dict) -> pd.Series:
        """Maps integer code strings (including zero-padded '01'-'09') to labels."""
        norm = series.str.strip().apply(lambda v: (v.lstrip("0") or "0")
                                        if v != "" else "")
        return norm.map(code_map).fillna("†")

    @staticmethod
    def _compute_grade_col(df: pd.DataFrame,
                           items: list,
                           not_offered_str: str = "–") -> pd.Series:
        """Computes a grade count or grade-span subtotal column from PSS items.

        Args:
            df: Raw PSS DataFrame with lowercase column names (strings).
            items: List of (offered_col, count_col) tuples.
            not_offered_str: Symbol emitted when none of the constituent grades
                are offered ('†' for grade-span subtotals, '–' for individual
                grade columns).

        Returns:
            pd.Series formatted with exact integer strings, or not_offered_str
            if none of the constituent grades are offered.
        """
        offered_masks = []
        item_counts = []
        for o, c in items:
            o_offered = df[o].str.strip() == "1"
            c_num = pd.to_numeric(df[c].str.strip(), errors="coerce")
            c_valid = c_num.notna() & (c_num >= 0)
            offered_masks.append(o_offered | c_valid)
            item_counts.append(
                np.where(
                    o_offered | c_valid,
                    c_num.clip(lower=0).fillna(0).round().astype(np.int64),
                    0,
                )
            )
        any_offered = np.logical_or.reduce(offered_masks)
        total = sum(item_counts)
        total_str = pd.Series(total, index=df.index).astype(str)
        return pd.Series(
            np.where(~any_offered, not_offered_str, total_str),
            index=df.index,
        )

    @staticmethod
    def _format_int_col(df: pd.DataFrame, count_col: str) -> pd.Series:
        """Formats an integer count column from raw PSS survey values."""
        if count_col not in df.columns:
            return pd.Series("†", index=df.index)
        raw_str = df[count_col].str.strip()
        num = pd.to_numeric(raw_str, errors="coerce")
        is_missing = (raw_str == "") | num.isna() | (num < 0)
        int_str = num.clip(lower=0).fillna(0).round().astype(np.int64).astype(str)
        return pd.Series(
            np.where(is_missing, "†", int_str),
            index=df.index,
        )

    @staticmethod
    def _format_float_col(df: pd.DataFrame, val_col: str) -> pd.Series:
        """Formats a float percentage/ratio column rounded to 2 decimals."""
        if val_col not in df.columns:
            return pd.Series("†", index=df.index)
        raw_str = df[val_col].str.strip()
        num = pd.to_numeric(raw_str, errors="coerce")
        is_missing = (raw_str == "") | num.isna() | (num < 0)
        num_str = num.round(2).astype(str)
        return pd.Series(
            np.where(is_missing, "†", num_str),
            index=df.index,
        )

    def input_file_to_df(self, f_path: str) -> pd.DataFrame:
        """Reads and normalizes a PSS public-use CSV file into a DataFrame."""
        try:
            df = pd.read_csv(f_path,
                             dtype=str,
                             encoding="utf-8",
                             keep_default_na=False)
        except (UnicodeDecodeError, UnicodeError):
            df = pd.read_csv(f_path,
                             dtype=str,
                             encoding="cp1252",
                             keep_default_na=False)

        # Step 1: Strip BOM/whitespace and normalize all column headers to lowercase.
        df.columns = [
            c.strip().lstrip("\ufeff\xef\xbb\xbf").lower() for c in df.columns
        ]

        # Step 2: Resolve cross-year column aliases (e.g. r*/s* in 1997/1999,
        # pstfip/rstfip/sstfips, commtype/ucommtyp, p315/p316).
        for canonical_col, aliases in PSS_COLUMN_ALIASES.items():
            if canonical_col not in df.columns:
                matched = next((a for a in aliases if a in df.columns), None)
                if matched:
                    df[canonical_col] = df[matched]
                else:
                    df[canonical_col] = ""

        # Compute p_black in survey cycles (1997-2015) where p325 and numstuds
        # exist without a pre-computed p_black column.
        if "p_black" not in df.columns and "p325" in df.columns:
            p325_num = pd.to_numeric(df["p325"].str.strip(), errors="coerce")
            numstuds_num = pd.to_numeric(df["numstuds"].str.strip(),
                                         errors="coerce")
            valid_ratio = (numstuds_num > 0) & p325_num.notna()
            df["p_black"] = np.where(
                valid_ratio,
                ((p325_num / numstuds_num) * 100.0).astype(str),
                "",
            )

        # Extract school_year (e.g. '2019-20') from filename or ^logr(\d+)$ header.
        logr_col = next((c for c in df.columns if c.startswith("logr")), None)
        higr_col = next((c for c in df.columns if c.startswith("higr")), None)
        end_year = None
        if logr_col:
            match = re.match(r"^logr(?:19|20)?(\d{2})$", logr_col)
            if match:
                yy = int(match.group(1))
                century = 1900 if yy >= 80 else 2000
                end_year = century + yy
        if end_year is None:
            fn_match = re.search(r"(?:txt_)?pss(\d{2})(\d{2})(?:_pu)?",
                                 os.path.basename(f_path), re.IGNORECASE)
            if not fn_match:
                raise ValueError(
                    f"Cannot determine school year from headers or filename: {f_path}"
                )
            yy1 = fn_match.group(1)
            century = "19" if int(yy1) >= 80 else "20"
            start_year = int(century + yy1)
            end_year = start_year + 1
        start_year = end_year - 1
        school_year = f"{start_year}-{str(end_year)[2:]}"

        pstansi_clean = df["pstansi"].str.strip()
        pcnty_clean = df["pcnty"].str.strip()
        state_fips_2 = pd.Series(
            np.where(pstansi_clean != "", pstansi_clean.str.zfill(2), ""),
            index=df.index,
        )
        state_name = state_fips_2.map(PSS_STATE_FIPS_TO_NAME).fillna("†")
        state_name = pd.Series(
            np.where(state_fips_2 == "", "†", state_name),
            index=df.index,
        )
        county_fips_5 = pd.Series(
            np.where(
                (state_fips_2 != "") & (pcnty_clean != ""),
                state_fips_2 + pcnty_clean.str.zfill(3),
                "",
            ),
            index=df.index,
        )

        raw_zip_digits = df["pzip"].str.strip().str.replace("-",
                                                            "",
                                                            regex=False)
        raw_zip4 = df["pzip4"].str.strip()
        pzip = pd.Series(
            np.where(raw_zip_digits != "", raw_zip_digits.str[:5].str.zfill(5), ""),
            index=df.index,
        )
        zip_plus_4 = pd.Series(
            np.where(
                pzip == "",
                "",
                np.where(
                    raw_zip4 != "",
                    pzip + raw_zip4.str.zfill(4),
                    np.where(raw_zip_digits.str.len() > 5, raw_zip_digits, pzip),
                ),
            ),
            index=df.index,
        )

        coed_col = self._map_code_col(df["p335"], PSS_COED_MAP)
        school_type_col = self._map_code_col(df["p415"], PSS_SCHOOL_TYPE_MAP)
        school_level_col = self._map_code_col(df["level"], PSS_SCHOOL_LEVEL_MAP)
        relig_affil_col = self._map_code_col(df["relig"], PSS_RELIG_AFFIL_MAP)
        comm_type_col = self._map_code_col(df["ucommtyp"], PSS_COMM_TYPE_MAP)
        orient_col = self._map_code_col(df["orient"], PSS_ORIENT_MAP)

        logr_series = df[logr_col] if logr_col and logr_col in df.columns else pd.Series("", index=df.index)
        higr_series = df[higr_col] if higr_col and higr_col in df.columns else pd.Series("", index=df.index)

        # Constituent item definitions for grade counts and subtotals.
        kg_items = [
            ("p155", "p160"),
            ("p165", "p170"),
            ("p175", "p180"),
        ]
        pk_kg_items = [("p145", "p150")] + kg_items
        gr_1_8_items = [
            ("p185", "p190"),
            ("p195", "p200"),
            ("p205", "p210"),
            ("p215", "p220"),
            ("p225", "p230"),
            ("p235", "p240"),
            ("p245", "p250"),
            ("p255", "p260"),
        ]
        gr_9_12_items = [
            ("p265", "p270"),
            ("p275", "p280"),
            ("p285", "p290"),
            ("p295", "p300"),
        ]

        cols_data = {
            "Private School Name":
                df["pinst"].str.strip(),
            "State Name [Private School] Latest available year":
                state_name,
            f"State Name [Private School] {school_year}":
                state_name,
            "ANSI/FIPS State Code [Private School] Latest available year":
                state_fips_2,
            f"Private School Name [Private School] {school_year}":
                df["pinst"].str.strip(),
            "School ID - NCES Assigned [Private School] Latest available year":
                df["ppin"].str.strip(),
            f"County Name [Private School] {school_year}":
                df["pcntnm"].str.strip(),
            f"ANSI/FIPS County Code [Private School] {school_year}":
                county_fips_5,
            f"Phone Number [Private School] {school_year}":
                df["pphone"].str.strip(),
            f"Physical Address [Private School] {school_year}":
                df["paddrs"].str.strip(),
            f"City [Private School] {school_year}":
                df["pcity"].str.strip(),
            "State Abbr [Private School] Latest available year":
                df["pstabb"].str.strip(),
            f"ZIP [Private School] {school_year}":
                pzip,
            f"ZIP + 4 [Private School] {school_year}":
                zip_plus_4,
            f"Lowest Grade Taught [Private School] {school_year}":
                self._map_code_col(logr_series, PSS_GRADE_CODE_MAP),
            f"Highest Grade Taught [Private School] {school_year}":
                self._map_code_col(higr_series, PSS_GRADE_CODE_MAP),
            f"Coeducational [Private School] {school_year}":
                coed_col,
            f"School Type [Private School] {school_year}":
                school_type_col,
            f"School Level [Private School] {school_year}":
                school_level_col,
            f"School's Religious Affiliation or Orientation [Private School] {school_year}":
                relig_affil_col,
            f"School Community Type [Private School] {school_year}":
                comm_type_col,
            f"Religious Orientation [Private School] {school_year}":
                orient_col,
            f"Total Students (Ungraded & PK-12) [Private School] {school_year}":
                self._format_int_col(df, "p305"),
            f"Total Students (Ungraded & K-12) [Private School] {school_year}":
                self._format_int_col(df, "numstuds"),
            f"Prekindergarten and Kindergarten Students [Private School] {school_year}":
                self._compute_grade_col(df, pk_kg_items, not_offered_str="†"),
            f"Grades 1-8 Students [Private School] {school_year}":
                self._compute_grade_col(df, gr_1_8_items, not_offered_str="†"),
            f"Grades 9-12 Students [Private School] {school_year}":
                self._compute_grade_col(df, gr_9_12_items, not_offered_str="†"),
            f"Prekindergarten Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p145", "p150")],
                                        not_offered_str="–"),
            f"Kindergarten Students [Private School] {school_year}":
                self._compute_grade_col(df, kg_items, not_offered_str="–"),
            f"Grade 1 Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p185", "p190")],
                                        not_offered_str="–"),
            f"Grade 2 Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p195", "p200")],
                                        not_offered_str="–"),
            f"Grade 3 Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p205", "p210")],
                                        not_offered_str="–"),
            f"Grade 4 Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p215", "p220")],
                                        not_offered_str="–"),
            f"Grade 5 Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p225", "p230")],
                                        not_offered_str="–"),
            f"Grade 6 Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p235", "p240")],
                                        not_offered_str="–"),
            f"Grade 7 Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p245", "p250")],
                                        not_offered_str="–"),
            f"Grade 8 Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p255", "p260")],
                                        not_offered_str="–"),
            f"Grade 9 Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p265", "p270")],
                                        not_offered_str="–"),
            f"Grade 10 Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p275", "p280")],
                                        not_offered_str="–"),
            f"Grade 11 Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p285", "p290")],
                                        not_offered_str="–"),
            f"Grade 12 Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p295", "p300")],
                                        not_offered_str="–"),
            f"Ungraded Students [Private School] {school_year}":
                self._compute_grade_col(df, [("p135", "p140")],
                                        not_offered_str="–"),
            f"American Indian/Alaska Native Students [Private School] {school_year}":
                self._format_int_col(df, "p310"),
            f"Percentage of American Indian/Alaska Native Students [Private School] {school_year}":
                self._format_float_col(df, "p_indian"),
            f"Asian or Asian/Pacific Islander Students [Private School] {school_year}":
                self._format_int_col(df, "p316"),
            f"Percentage of Asian or Asian/Pacific Islander Students [Private School] {school_year}":
                self._format_float_col(df, "p_asian"),
            f"Hispanic Students [Private School] {school_year}":
                self._format_int_col(df, "p320"),
            f"Percentage of Hispanic Students [Private School] {school_year}":
                self._format_float_col(df, "p_hisp"),
            f"Black or African American Students [Private School] {school_year}":
                self._format_int_col(df, "p325"),
            f"Percentage of Black Students [Private School] {school_year}":
                self._format_float_col(df, "p_black"),
            f"White Students [Private School] {school_year}":
                self._format_int_col(df, "p330"),
            f"Percentage of White Students [Private School] {school_year}":
                self._format_float_col(df, "p_white"),
            f"Nat. Hawaiian or Other Pacific Isl. Students [Private School] {school_year}":
                self._format_int_col(df, "p318"),
            f"Percentage of Nat. Hawaiian or Other Pacific Isl. Students [Private School] {school_year}":
                self._format_float_col(df, "p_pacific"),
            f"Two or More Races Students [Private School] {school_year}":
                self._format_int_col(df, "p332"),
            f"Percentage of Two or More Races Students [Private School] {school_year}":
                self._format_float_col(df, "p_tr"),
            f"Pupil/Teacher Ratio [Private School] {school_year}":
                self._format_float_col(df, "sttch_rt"),
            f"Full-Time Equivalent (FTE) Teachers [Private School] {school_year}":
                self._format_float_col(df, "numteach"),
        }

        ordered_cols = [
            col.format(school_year=school_year)
            for col in ELSI_58_COLUMN_TEMPLATE
        ]
        return pd.DataFrame(cols_data, columns=ordered_cols)


def main(argv):
    """Main entry point for NCES Private School processing."""
    del argv  # Unused
    try:
        logging.set_verbosity(logging.INFO)
        logging.info(
            f"Main Method Starts For Private School (mode={FLAGS.mode})")
        gcs_output_dir_local = FLAGS.input_path
        input_path_base = os.path.join(gcs_output_dir_local, "input_files")
        os.makedirs(input_path_base, exist_ok=True)
        input_files_to_process = []
        if os.path.exists(input_path_base):
            for root, _, files in os.walk(input_path_base):
                for file_name in sorted(files):
                    fn_lower = file_name.lower()
                    if fn_lower.endswith(".csv") and "pss" in fn_lower and not fn_lower.startswith("elsi_"):
                        input_files_to_process.append(
                            os.path.join(root, file_name))

        if not input_files_to_process:
            raise FileNotFoundError(
                f"No CSV files found in {input_path_base} or its year subfolders. "
                "Please ensure download.py has been run and placed files correctly."
            )
        output_file_path = os.path.join(gcs_output_dir_local, "output_files")
        os.makedirs(output_file_path, exist_ok=True)

        output_file_path_place = os.path.join(gcs_output_dir_local,
                                              "output_place")
        os.makedirs(output_file_path_place, exist_ok=True)

        cleaned_csv_path = os.path.join(output_file_path, CSV_FILE_NAME)
        mcf_path = os.path.join(output_file_path, MCF_FILE_NAME)
        tmcf_path = os.path.join(output_file_path, TMCF_FILE_NAME)
        cleaned_csv_place = os.path.join(output_file_path_place, CSV_FILE_PLACE)
        duplicate_csv_place = os.path.join(output_file_path_place,
                                           CSV_DUPLICATE_NAME)
        tmcf_path_place = os.path.join(output_file_path_place, TMCF_FILE_PLACE)

        loader = NCESPrivateSchool(input_files_to_process, cleaned_csv_path,
                                   mcf_path, tmcf_path, cleaned_csv_place,
                                   duplicate_csv_place, tmcf_path_place)

        if FLAGS.mode == 'place':
            loader._generate_statvars = False
            loader._generate_places = True
        elif FLAGS.mode == 'stats':
            loader._generate_statvars = True
            loader._generate_places = False

        loader.generate_csv()
        loader.generate_mcf()
        loader.generate_tmcf()
        logging.info("Main Method Completed For Private School")
    except Exception as e:
        logging.fatal(
            f"Error While Running Private School Process: {e}",
            exc_info=True)


if __name__ == '__main__':
    app.run(main)
