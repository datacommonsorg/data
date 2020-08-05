# Copyright 2020 Google LLC
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
"""test functions for the template mcf"""

import pandas as pd


def test_col_names(csv_path, tmcf_path):
    """ check if all the column names specified in the template mcf
        is found in the CSV file"""
    cols = pd.read_csv(csv_path, nrows=0).columns
    with open(tmcf_path, "r") as file:
        for line in file:
            if " C:" in line:
                col_name = line[:-1].split("->")[1]
            assert col_name in cols


if __name__ == "__main__":
    test_col_names("ISTAT_region.csv", "ISTAT_region.tmcf")
    test_col_names("ISTAT_province.csv", "ISTAT_province.tmcf")
    test_col_names("ISTAT_municipal.csv", "ISTAT_municipal.tmcf")
