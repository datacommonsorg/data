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
    to_num,
    validate_file_format,
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
                f"POPULATION BY DISTRICTS, AGE, PLACE OF RESIDENCE AND SEX AS OF 31.12.{year} (MOCK)",
                "", "", "", "", "", "", "", "", ""
            ],
            [
                "Districts Age (years)", "Total", "", "", "Urban residence",
                "", "", "Rural residence", "", ""
            ],
            [
                "", "Total", "Male", "Female", "Total", "Male", "Female",
                "Total", "Male", "Female"
            ],
        ]
        for d in EXPECTED_DISTRICTS:
            rows.append([d, "", "", "", "", "", "", "", "", ""])
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

                if tamper_type == "arithmetic_residence" and d == EXPECTED_DISTRICTS[
                        0] and a == EXPECTED_AGES[0]:
                    rur_tot = 50  # 70 + 50 != 100
                elif tamper_type == "arithmetic_sex" and d == EXPECTED_DISTRICTS[
                        0] and a == EXPECTED_AGES[0]:
                    fem = 30  # 60 + 30 != 100

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

        temp_file = tempfile.NamedTemporaryFile(mode="w",
                                                delete=False,
                                                suffix=".csv",
                                                newline="",
                                                dir="/tmp")
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

    def test_validate_file_format_arithmetic_residence_failure(self):
        csv_path = self._create_mock_csv(year=2025,
                                         tamper_type="arithmetic_residence")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn("Total (100) != Urban (70) + Rural (50)",
                          str(ctx.exception))
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_file_format_arithmetic_sex_failure(self):
        csv_path = self._create_mock_csv(year=2025,
                                         tamper_type="arithmetic_sex")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn("Total (100) != Male (60) + Female (30)",
                          str(ctx.exception))
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)


if __name__ == "__main__":
    unittest.main()
