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

import csv
import os
import pandas as pd
import unittest
from india.formatters import CodeFormatter


class TestPreprocess(unittest.TestCase):

    def test_format_lgd_state_code(self):
        self.assertEqual(CodeFormatter.format_lgd_state_code("01"), "01")
        self.assertEqual(CodeFormatter.format_lgd_state_code("9"), "09")
        self.assertEqual(CodeFormatter.format_lgd_state_code("00"), "")

    def test_format_lgd_district_code(self):
        self.assertEqual(CodeFormatter.format_lgd_district_code("001"), "001")
        self.assertEqual(CodeFormatter.format_lgd_district_code("09"), "009")
        self.assertEqual(CodeFormatter.format_lgd_district_code("000"), "")

    def test_format_census2011_code(self):
        self.assertEqual(CodeFormatter.format_census2011_code("001"), "001")
        self.assertEqual(CodeFormatter.format_census2011_code("09"), "009")
        self.assertEqual(CodeFormatter.format_census2011_code("000"), "")

    def test_format_census2001_district_code(self):
        self.assertEqual(
            CodeFormatter.format_census2001_district_code("01", "02"), "01.02")
        self.assertEqual(
            CodeFormatter.format_census2001_district_code("9", "02"), "09.02")
        self.assertEqual(
            CodeFormatter.format_census2001_district_code("09", "1"), "09.01")
        self.assertEqual(
            CodeFormatter.format_census2001_district_code("09", "05"), "09.05")
        self.assertEqual(
            CodeFormatter.format_census2001_district_code("00", "00"), "")
        self.assertEqual(
            CodeFormatter.format_census2001_district_code("01", "00"), "")
        self.assertEqual(
            CodeFormatter.format_census2001_district_code("00", "01"), "")
