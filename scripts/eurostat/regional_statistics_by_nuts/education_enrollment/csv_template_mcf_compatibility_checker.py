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

import pandas as pd


def test_col_names(cleaned_csv, tmcf):
    """ check if all the column names specified in the template mcf
        is found in the CSV file"""
    cols = pd.read_csv(cleaned_csv, nrows=0).columns
    with open(tmcf, "r") as file:
        for line in file:
            if " C:" in line:
                col_name = line[:-1].split("->")[1]
                assert col_name in cols
