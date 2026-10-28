# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for download_current_year_data.py."""

import csv
import os
import sys
import tempfile
import unittest

# Ensure the parent directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from download_current_year_data import (
    EXPECTED_AGES,
    EXPECTED_DISTRICTS,
    EXPECTED_HISTORICAL_AGES,
    to_num,
    validate_file_format,
    validate_historical_file_format,
)


class DownloadCurrentYearDataTest(unittest.TestCase):

    def test_to_num(self):
        self.assertEqual(to_num("123"), 123)
        self.assertEqual(to_num(" 456 "), 456)
        self.assertEqual(to_num("-"), 0)
        self.assertEqual(to_num("0"), 0)

    def _create_mock_csv(self, year=2025, tamper_type=None):
        rows = [
            [
                ("POPULATION BY DISTRICTS, AGE, PLACE OF RESIDENCE AND SEX"
                 f" AS OF 31.12.{year} (MOCK)"),
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ],
            [
                "Districts Age (years)",
                "Total",
                "",
                "",
                "Urban residence",
                "",
                "",
                "Rural residence",
                "",
                "",
            ],
            [
                "",
                "Total",
                "Male",
                "Female",
                "Total",
                "Male",
                "Female",
                "Total",
                "Male",
                "Female",
            ],
        ]
        n_ages = len(EXPECTED_AGES)
        for d in EXPECTED_DISTRICTS:
            d_tot = 100 * n_ages
            d_m = 60 * n_ages
            d_fem = 40 * n_ages
            d_urb = 70 * n_ages
            d_urb_m = 42 * n_ages
            d_urb_fem = 28 * n_ages
            d_rur = 30 * n_ages
            d_rur_m = 18 * n_ages
            d_rur_fem = 12 * n_ages
            if tamper_type == "district_row_sex" and d == EXPECTED_DISTRICTS[0]:
                d_fem = 100  # breaks d_tot == d_m + d_fem

            rows.append([
                d,
                str(d_tot),
                str(d_m),
                str(d_fem),
                str(d_urb),
                str(d_urb_m),
                str(d_urb_fem),
                str(d_rur),
                str(d_rur_m),
                str(d_rur_fem),
            ])
            for a in EXPECTED_AGES:
                tot = 100
                m = 60
                fem = 40
                urb_tot = 70
                urb_m = 42
                urb_fem = 28
                rur_tot = 30
                rur_m = 18
                rur_fem = 12

                if (tamper_type == "arithmetic_residence"
                        and d == EXPECTED_DISTRICTS[0]
                        and a == EXPECTED_AGES[0]):
                    rur_tot = 50  # 70 + 50 != 100
                elif (tamper_type == "arithmetic_sex"
                      and d == EXPECTED_DISTRICTS[0]
                      and a == EXPECTED_AGES[0]):
                    fem = 30  # 60 + 30 != 100
                elif (tamper_type == "arithmetic_urban_sex"
                      and d == EXPECTED_DISTRICTS[0]
                      and a == EXPECTED_AGES[0]):
                    urb_fem = 20  # 42 + 20 != 70
                elif (tamper_type == "arithmetic_rural_sex"
                      and d == EXPECTED_DISTRICTS[0]
                      and a == EXPECTED_AGES[0]):
                    rur_fem = 10  # 18 + 10 != 30

                row = [
                    a,
                    str(tot),
                    str(m),
                    str(fem),
                    str(urb_tot),
                    str(urb_m),
                    str(urb_fem),
                    str(rur_tot),
                    str(rur_m),
                    str(rur_fem),
                ]
                rows.append(row)

        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".csv",
            newline="",
            dir="/tmp",
        )
        writer = csv.writer(temp_file)
        writer.writerows(rows)
        temp_file.close()
        return temp_file.name

    def test_validate_file_format_success(self):
        csv_path = self._create_mock_csv(year=2025)
        try:
            self.assertTrue(validate_file_format(csv_path, expected_year=2025))
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_file_format_district_row_failure(self):
        csv_path = self._create_mock_csv(year=2025,
                                         tamper_type="district_row_sex")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn(
                "Total (2200) != Male (1320) + Female (100)",
                str(ctx.exception),
            )
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_file_format_arithmetic_residence_failure(self):
        csv_path = self._create_mock_csv(year=2025,
                                         tamper_type="arithmetic_residence")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn(
                "Total (100) != Urban (70) + Rural (50)",
                str(ctx.exception),
            )
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_file_format_arithmetic_sex_failure(self):
        csv_path = self._create_mock_csv(year=2025,
                                         tamper_type="arithmetic_sex")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn(
                "Total (100) != Male (60) + Female (30)",
                str(ctx.exception),
            )
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_file_format_urban_sex_failure(self):
        csv_path = self._create_mock_csv(year=2025,
                                         tamper_type="arithmetic_urban_sex")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn(
                "Urban (70) != Urban Male (42) + Urban Female (20)",
                str(ctx.exception),
            )
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_file_format_rural_sex_failure(self):
        csv_path = self._create_mock_csv(year=2025,
                                         tamper_type="arithmetic_rural_sex")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn(
                "Rural (30) != Rural Male (18) + Rural Female (10)",
                str(ctx.exception),
            )
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_historical_file_format(self):
        rows = [
            ["POPULATION BY DISTRICTS, AGE AND SEX AS OF 31.12.", "", "", ""],
            ["Districts", "Population as of 31.12.2011", "", ""],
            ["Age (years)", "Total", "Male", "Female"],
        ]
        n_ages = len(EXPECTED_HISTORICAL_AGES)
        for d in EXPECTED_DISTRICTS:
            rows.append(
                [d, str(100 * n_ages),
                 str(48 * n_ages),
                 str(52 * n_ages)])
            for a in EXPECTED_HISTORICAL_AGES:
                rows.append([a, "100", "48", "52"])

        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".csv",
            newline="",
            dir="/tmp",
        )
        writer = csv.writer(temp_file)
        writer.writerows(rows)
        temp_file.close()
        try:
            self.assertTrue(validate_historical_file_format(temp_file.name))
        finally:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)


if __name__ == "__main__":
    unittest.main()
