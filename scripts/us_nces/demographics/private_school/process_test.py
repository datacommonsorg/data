# Copyright 2020 Google LLC
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
"""Unit tests for NCES Private School processing pipeline (PSS public-use format)."""

import csv
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

# Ensure the process module can be imported
MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(0, MODULE_DIR)
# pylint: disable=wrong-import-position
from config import CSV_DUPLICATE_NAME, ELSI_58_COLUMN_TEMPLATE
from process import NCESPrivateSchool
# pylint: enable=wrong-import-position

TEST_DATASET_DIR = os.path.join(MODULE_DIR, "test_data", "sample_input")
EXPECTED_FILES_DIR = os.path.join(MODULE_DIR, "test_data", "sample_output")


class TestProcess(unittest.TestCase):
    """Tests the NCESPrivateSchool processing script on PSS public-use CSV files."""

    test_data_files = sorted(os.listdir(TEST_DATASET_DIR))

    ip_data = [
        os.path.join(TEST_DATASET_DIR, file_name)
        for file_name in test_data_files
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._tmp_dir = tempfile.TemporaryDirectory()
        tmp_dir = cls._tmp_dir.name
        cleaned_csv_file_path = os.path.join(
            tmp_dir, "us_nces_demographics_private_school.csv")
        mcf_file_path = os.path.join(tmp_dir,
                                     "us_nces_demographics_private_school.mcf")
        tmcf_file_path = os.path.join(
            tmp_dir, "us_nces_demographics_private_school.tmcf")
        csv_path_place = os.path.join(tmp_dir,
                                      "us_nces_demographics_private_place.csv")
        tmcf_path_place = os.path.join(
            tmp_dir, "us_nces_demographics_private_place.tmcf")
        dup_csv_path_place = os.path.join(tmp_dir, CSV_DUPLICATE_NAME)

        loader = NCESPrivateSchool(cls.ip_data, cleaned_csv_file_path,
                                   mcf_file_path, tmcf_file_path,
                                   csv_path_place, dup_csv_path_place,
                                   tmcf_path_place)

        with patch(
                "common.us_education.dc_api_is_defined_dcid",
                side_effect=lambda nodes, *args, **kwargs:
            {n: True for n in nodes},
        ):
            loader.generate_csv()
            loader.generate_mcf()
            loader.generate_tmcf()

        with open(cleaned_csv_file_path, encoding="utf-8-sig") as csv_file:
            cls.actual_csv_data = csv_file.read()

        with open(mcf_file_path, encoding="UTF-8") as mcf_file:
            cls.actual_mcf_data = mcf_file.read()

        with open(tmcf_file_path, encoding="UTF-8") as tmcf_file:
            cls.actual_tmcf_data = tmcf_file.read()

        with open(csv_path_place, encoding="utf-8-sig") as csv_file:
            cls.actual_csv_place = csv_file.read()

        with open(tmcf_path_place, encoding="UTF-8") as tmcf_file:
            cls.actual_tmcf_place = tmcf_file.read()

    @classmethod
    def tearDownClass(cls):
        cls._tmp_dir.cleanup()
        super().tearDownClass()

    def test_mcf_tmcf_files(self):
        """Tests that generated MCF and TMCF match expected test files."""
        expected_mcf_file_path = os.path.join(
            EXPECTED_FILES_DIR, "us_nces_demographics_private_school.mcf")
        expected_tmcf_file_path = os.path.join(
            EXPECTED_FILES_DIR, "us_nces_demographics_private_school.tmcf")
        expected_tmcf_place_path = os.path.join(
            EXPECTED_FILES_DIR, "us_nces_demographics_private_place.tmcf")

        with open(expected_mcf_file_path, encoding="UTF-8") as f:
            expected_mcf_data = f.read()
        with open(expected_tmcf_file_path, encoding="UTF-8") as f:
            expected_tmcf_data = f.read()
        with open(expected_tmcf_place_path, encoding="UTF-8") as f:
            expected_tmcf_place = f.read()

        self.assertEqual(expected_mcf_data.strip(),
                         self.actual_mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(),
                         self.actual_tmcf_data.strip())
        self.assertEqual(expected_tmcf_place.strip(),
                         self.actual_tmcf_place.strip())

    def test_create_csv(self):
        """Tests that generated CSV files match expected test files."""
        expected_csv_file_path = os.path.join(
            EXPECTED_FILES_DIR, "us_nces_demographics_private_school.csv")
        with open(expected_csv_file_path, encoding="utf-8") as f:
            expected_csv_data = f.read()
        self.assertEqual(expected_csv_data.strip(),
                         self.actual_csv_data.strip())

        expected_csv_place_path = os.path.join(
            EXPECTED_FILES_DIR, "us_nces_demographics_private_place.csv")
        with open(expected_csv_place_path, encoding="utf-8") as f:
            expected_csv_place = f.read()
        self.assertEqual(expected_csv_place.strip(),
                         self.actual_csv_place.strip())

    def test_pss_public_use_normalization(self):
        """Tests PSS public-use CSV normalization and end-to-end processing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample_pss_path = os.path.join(tmp_dir, "pss1920_pu.csv")
            headers = [
                "PFNLWT", "PPIN", "PINST", "PADDRS", "PCITY", "PSTABB", "PZIP",
                "PZIP4", "PCNTY", "PCNTNM", "PSTANSI", "PPHONE", "LOGR2020",
                "HIGR2020", "P335", "F_P335", "P415", "F_P415", "LEVEL",
                "RELIG", "ORIENT", "F_P440", "UCOMMTYP", "P135", "P140",
                "F_P140", "P145", "P150", "F_P150", "P155", "P160", "F_P160",
                "P165", "P170", "F_P170", "P175", "P180", "F_P180", "P185",
                "P190", "F_P190", "P195", "P200", "F_P200", "P205", "P210",
                "F_P210", "P215", "P220", "F_P220", "P225", "P230", "F_P230",
                "P235", "P240", "F_P240", "P245", "P250", "F_P250", "P255",
                "P260", "F_P260", "P265", "P270", "F_P270", "P275", "P280",
                "F_P280", "P285", "P290", "F_P290", "P295", "P300", "F_P300",
                "P305", "F_P305", "NUMSTUDS", "P310", "F_P310", "P_INDIAN",
                "P316", "F_P316", "P_ASIAN", "P318", "F_P318", "P_PACIFIC",
                "P320", "F_P320", "P_HISP", "P325", "F_P325", "P_BLACK", "P330",
                "F_P330", "P_WHITE", "P332", "F_P332", "P_TR", "NUMTEACH",
                "F_P410", "STTCH_RT"
            ]
            row1 = {
                "PFNLWT": "1.0",
                "PPIN": "00000001",
                "PINST": "ST JOHN LUTHERAN SCHOOL",
                "PADDRS": "100 MAIN ST",
                "PCITY": "BIRMINGHAM",
                "PSTABB": "AL",
                "PZIP": "35203",
                "PZIP4": "1234",
                "PCNTY": "073",
                "PCNTNM": "JEFFERSON",
                "PSTANSI": "01",
                "PPHONE": "2055551234",
                "LOGR2020": "2",
                "HIGR2020": "7",
                "P335": "1",
                "F_P335": "0",
                "P415": "1",
                "F_P415": "0",
                "LEVEL": "1",
                "RELIG": "2",
                "ORIENT": "20",
                "F_P440": "0",
                "UCOMMTYP": "1",
                "P135": "2",
                "P140": "",
                "F_P140": "0",
                "P145": "1",
                "P150": "20",
                "F_P150": "0",
                "P155": "1",
                "P160": "15",
                "F_P160": "0",
                "P165": "2",
                "P170": "",
                "F_P170": "0",
                "P175": "2",
                "P180": "",
                "F_P180": "0",
                "P185": "1",
                "P190": "10",
                "F_P190": "0",
                "P195": "1",
                "P200": "12",
                "F_P200": "0",
                "P205": "2",
                "P210": "",
                "F_P210": "0",
                "P215": "2",
                "P220": "",
                "F_P220": "0",
                "P225": "2",
                "P230": "",
                "F_P230": "0",
                "P235": "2",
                "P240": "",
                "F_P240": "0",
                "P245": "2",
                "P250": "",
                "F_P250": "0",
                "P255": "2",
                "P260": "",
                "F_P260": "0",
                "P265": "2",
                "P270": "",
                "F_P270": "0",
                "P275": "2",
                "P280": "",
                "F_P280": "0",
                "P285": "2",
                "P290": "",
                "F_P290": "0",
                "P295": "2",
                "P300": "",
                "F_P300": "0",
                "P305": "57",
                "F_P305": "0",
                "NUMSTUDS": "37",
                "P310": "0",
                "F_P310": "0",
                "P_INDIAN": "0.0",
                "P316": "2",
                "F_P316": "0",
                "P_ASIAN": "5.40540540540541",
                "P318": "0",
                "F_P318": "0",
                "P_PACIFIC": "0.0",
                "P320": "3",
                "F_P320": "0",
                "P_HISP": "8.10810810810811",
                "P325": "5",
                "F_P325": "0",
                "P_BLACK": "13.5135135135135",
                "P330": "27",
                "F_P330": "0",
                "P_WHITE": "72.972972972973",
                "P332": "0",
                "F_P332": "0",
                "P_TR": "0.0",
                "NUMTEACH": "4.5",
                "F_P410": "0",
                "STTCH_RT": "8.22222222222222",
            }
            row2 = dict(row1)
            row2.update({
                "PPIN": "00000002",
                "PZIP4": "",
                "F_P415": "4",
                "F_P310": "4",
                "F_P316": "4",
                "F_P318": "4",
                "F_P320": "4",
                "F_P325": "4",
                "F_P330": "4",
                "F_P332": "4",
            })

            with open(sample_pss_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerow(row1)
                writer.writerow(row2)

            pss_out_csv = os.path.join(tmp_dir, "pss_out.csv")
            pss_out_mcf = os.path.join(tmp_dir, "pss_out.mcf")
            pss_out_tmcf = os.path.join(tmp_dir, "pss_out.tmcf")
            pss_place_csv = os.path.join(tmp_dir, "pss_place.csv")
            pss_dup_csv = os.path.join(tmp_dir, "pss_dup.csv")
            pss_place_tmcf = os.path.join(tmp_dir, "pss_place.tmcf")

            loader = NCESPrivateSchool(
                [sample_pss_path],
                pss_out_csv,
                pss_out_mcf,
                pss_out_tmcf,
                pss_place_csv,
                pss_dup_csv,
                pss_place_tmcf,
            )
            elsi_df = loader.input_file_to_df(sample_pss_path)
            expected_cols = [
                c.format(school_year="2019-20") for c in ELSI_58_COLUMN_TEMPLATE
            ]
            self.assertEqual(list(elsi_df.columns), expected_cols)
            self.assertEqual(
                elsi_df.loc[0,
                            "ANSI/FIPS County Code [Private School] 2019-20"],
                "01073")
            self.assertEqual(elsi_df.loc[0, "ZIP + 4 [Private School] 2019-20"],
                             "352031234")
            self.assertEqual(elsi_df.loc[1, "ZIP + 4 [Private School] 2019-20"],
                             "35203")
            self.assertEqual(
                elsi_df.loc[0,
                            "School Community Type [Private School] 2019-20"],
                "1-City (ulocale = 11 or 12 or 13)")
            self.assertEqual(
                elsi_df.loc[0,
                            "Religious Orientation [Private School] 2019-20"],
                "Lutheran Church \u2013 Missouri Synod")
            self.assertEqual(
                elsi_df.loc[
                    0,
                    "Prekindergarten and Kindergarten Students [Private School] 2019-20"],
                "35")
            self.assertEqual(
                elsi_df.loc[0, "Grades 1-8 Students [Private School] 2019-20"],
                "22")
            self.assertEqual(
                elsi_df.loc[0, "Grades 9-12 Students [Private School] 2019-20"],
                "†")
            self.assertEqual(
                elsi_df.loc[0, "Grade 9 Students [Private School] 2019-20"],
                "–")
            self.assertEqual(
                elsi_df.loc[
                    0,
                    "Percentage of Asian or Asian/Pacific Islander Students [Private School] 2019-20"],
                "5.41")
            self.assertEqual(
                elsi_df.loc[0, "Pupil/Teacher Ratio [Private School] 2019-20"],
                "8.22")
            self.assertEqual(
                elsi_df.loc[1, "School Type [Private School] 2019-20"],
                "1-Regular Elementary or Secondary")
            self.assertEqual(
                elsi_df.loc[1, "White Students [Private School] 2019-20"], "27")
            self.assertEqual(
                elsi_df.loc[
                    1, "Percentage of White Students [Private School] 2019-20"],
                "72.97")

            with patch(
                    "common.us_education.dc_api_is_defined_dcid",
                    side_effect=lambda nodes, *args, **kwargs:
                {n: True for n in nodes},
            ):
                loader.generate_csv()
                loader.generate_mcf()
                loader.generate_tmcf()
            self.assertTrue(os.path.exists(pss_out_csv))
            self.assertTrue(os.path.exists(pss_place_csv))

    def test_race_percentage_over_100_filtered(self):
        """Tests that race percentages > 100.0% from upstream anomalies are filtered as '†'."""
        df = pd.DataFrame({
            "p_asian": ["250.0", "50.5", "100.0", "100.01", ""],
            "p_white": ["125.0", "0.0", "75.25", "-5.0", "88.88"],
        })
        s_asian = NCESPrivateSchool._format_float_col(df,
                                                      "p_asian",
                                                      is_percentage=True)
        self.assertEqual(s_asian.tolist(), ["†", "50.5", "100.0", "†", "†"])

        s_white = NCESPrivateSchool._format_float_col(df,
                                                      "p_white",
                                                      is_percentage=True)
        self.assertEqual(s_white.tolist(), ["†", "0.0", "75.25", "†", "88.88"])

        # Non-percentage columns (like pupil/teacher ratio) allow values > 100
        df_ratio = pd.DataFrame({"sttch_rt": ["125.0", "250.0"]})
        s_ratio = NCESPrivateSchool._format_float_col(df_ratio,
                                                      "sttch_rt",
                                                      is_percentage=False)
        self.assertEqual(s_ratio.tolist(), ["125.0", "250.0"])

    def test_mode_isolation(self):
        """Tests that --mode=place and --mode=stats cleanly isolate outputs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cleaned_csv = os.path.join(tmp_dir, "stats.csv")
            mcf = os.path.join(tmp_dir, "stats.mcf")
            tmcf = os.path.join(tmp_dir, "stats.tmcf")
            place_csv = os.path.join(tmp_dir, "place.csv")
            dup_csv = os.path.join(tmp_dir, "dup.csv")
            place_tmcf = os.path.join(tmp_dir, "place.tmcf")

            # Mode 'place': generates place outputs, skips stats outputs
            place_loader = NCESPrivateSchool(self.ip_data, cleaned_csv, mcf,
                                             tmcf, place_csv, dup_csv,
                                             place_tmcf)
            place_loader.set_generate_statvars_flag(False)
            place_loader.set_generate_places_flag(True)

            with patch("common.us_education.dc_api_is_defined_dcid",
                       side_effect=lambda nodes, *args, **kwargs:
                       {n: True for n in nodes}):
                place_loader.generate_csv()
                place_loader.generate_mcf()
                place_loader.generate_tmcf()

            self.assertTrue(os.path.exists(place_csv))
            self.assertTrue(os.path.exists(place_tmcf))
            self.assertFalse(os.path.exists(cleaned_csv))
            self.assertFalse(os.path.exists(mcf))
            self.assertFalse(os.path.exists(tmcf))

            # Mode 'stats': generates stats outputs, skips place outputs
            stats_cleaned_csv = os.path.join(tmp_dir, "stats_only.csv")
            stats_mcf = os.path.join(tmp_dir, "stats_only.mcf")
            stats_tmcf = os.path.join(tmp_dir, "stats_only.tmcf")
            stats_place_csv = os.path.join(tmp_dir, "place_only.csv")
            stats_dup_csv = os.path.join(tmp_dir, "dup_only.csv")
            stats_place_tmcf = os.path.join(tmp_dir, "place_only.tmcf")

            stats_loader = NCESPrivateSchool(self.ip_data, stats_cleaned_csv,
                                             stats_mcf, stats_tmcf,
                                             stats_place_csv, stats_dup_csv,
                                             stats_place_tmcf)
            stats_loader.set_generate_statvars_flag(True)
            stats_loader.set_generate_places_flag(False)

            with patch("common.us_education.dc_api_is_defined_dcid",
                       side_effect=lambda nodes, *args, **kwargs:
                       {n: True for n in nodes}):
                stats_loader.generate_csv()
                stats_loader.generate_mcf()
                stats_loader.generate_tmcf()

            self.assertTrue(os.path.exists(stats_cleaned_csv))
            self.assertTrue(os.path.exists(stats_mcf))
            self.assertTrue(os.path.exists(stats_tmcf))
            self.assertFalse(os.path.exists(stats_place_csv))
            self.assertFalse(os.path.exists(stats_place_tmcf))

    def test_multi_year_place_coalescing(self):
        """Tests that _transform_private_place coalesces non-null attributes across survey years."""
        loader = NCESPrivateSchool([], "dummy.csv", "dummy.mcf", "dummy.tmcf",
                                   "dummy_place.csv", "dummy_dup.csv",
                                   "dummy_place.tmcf")

        place_df_2019 = pd.DataFrame([{
            "school_state_code": "nces/A0108845",
            "year": 2019,
            "Private_School_Name": "†",
            "PhoneNumber": "",
            "Physical_Address": "123 MAIN ST",
            "City": "BIRMINGHAM",
            "State_Abbr": "AL",
            "ZIP": "35203",
            "ZIP4": "352031234",
            "County_code": "01073",
            "State_code": "01",
            "Lowest_Grade": "Prekindergarten",
            "Highest_Grade": "8th grade",
            "SchoolGrade": "1-Elementary",
            "School_Type": "1-Regular Elementary or Secondary",
            "School_Religion": "Roman Catholic",
            "Coeducational": "1-Coed",
        }])
        place_df_1997 = pd.DataFrame([{
            "school_state_code": "nces/A0108845",
            "year": 1997,
            "Private_School_Name": "ST PATRICK SCHOOL",
            "PhoneNumber": "2055551234",
            "Physical_Address": "",
            "City": "BIRMINGHAM",
            "State_Abbr": "AL",
            "ZIP": "35203",
            "ZIP4": "",
            "County_code": "01073",
            "State_code": "01",
            "Lowest_Grade": "Prekindergarten",
            "Highest_Grade": "8th grade",
            "SchoolGrade": "1-Elementary",
            "School_Type": "1-Regular Elementary or Secondary",
            "School_Religion": "Roman Catholic",
            "Coeducational": "1-Coed",
        }])

        with patch("common.us_education.dc_api_is_defined_dcid",
                   side_effect=lambda nodes, *args, **kwargs:
                   {n: True for n in nodes}):
            loader._place_dfs = [place_df_2019, place_df_1997]
            loader._transform_private_place()

        res = loader._final_df_place
        self.assertEqual(len(res), 1)
        row = res.iloc[0]
        # Restored name and phone from 1997 (title-cased by _transform_private_place)
        self.assertEqual(row["Private_School_Name"], "St Patrick School")
        self.assertEqual(row["PhoneNumber"], "2055551234")
        # Retained address from 2019
        self.assertIn("123 Main St", row["Physical_Address"])
        self.assertFalse(row["Physical_Address"].startswith(" "))


if __name__ == '__main__':
    unittest.main()
