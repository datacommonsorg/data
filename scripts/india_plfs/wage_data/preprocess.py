# Copyright 2021 Google LLC
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
"""Classes and methods to import Average wage/salary earnings from Periodic Labour Force Survey (PLFS)"""

__author__ = ["Thejesh GN (i@thejeshgn.com)"]

import os
import json
import csv
import pandas as pd
import numpy as np
import urllib.request
from os import path
from india.geo.states import IndiaStatesMapper

DATASETS = [
    {
        "period": "2017-07",
        "data_file": "Table_42_07_09_2017.xlsx",
        "data_rows": 37
    },
    {
        "period": "2017-10",
        "data_file": "Table_42_10_12_2017.xlsx",
        "data_rows": 37
    },
    {
        "period": "2018-01",
        "data_file": "Table_42_01_03_2018.xlsx",
        "data_rows": 37
    },
    {
        "period": "2018-04",
        "data_file": "Table_42_04_06_2018.xlsx",
        "data_rows": 37
    },
    {
        "period": "2018-07",
        "data_file": "Table_42_07_09_2018.xlsx",
        "data_rows": 37
    },
    {
        "period": "2018-10",
        "data_file": "Table_42_10_12_2018.xlsx",
        "data_rows": 37
    },
    {
        "period": "2019-01",
        "data_file": "Table_42_01_03_2019.xlsx",
        "data_rows": 37
    },
    {
        "period": "2019-04",
        "data_file": "Table_42_04_06_2019.xlsx",
        "data_rows": 37
    },
]


class PLFSWageDataLoader:
    COLUMN_HEADERS = [
        "period",
        "territory",
        "wage_rural_male",
        "wage_rural_female",
        "wage_rural_person",
        "wage_urban_male",
        "wage_urban_female",
        "wage_urban_person",
        "wage_total_male",
        "wage_total_female",
        "wage_total_person",
    ]

    def __init__(self, source, period, data_rows):
        self.source = source
        self.period = period
        self.data_rows = data_rows
        self.raw_df = None
        self.clean_df = None

    def load(self):
        if self.source.endswith("xlsx"):
            df = pd.read_excel(self.source)
        else:
            df = pd.read_csv(self.source)
        # Drop title rows in the top and  rows after `data_rows`.
        # The actual data is between 4nd and (4 + data_rows) row. So keep only them.
        df = df.iloc[4:(4 + self.data_rows)]

        # Cell value zero(0) indicates no sample observation
        # in the respective category
        df = df.replace(0, '')
        df = df.replace("0", '')

        self.raw_df = df

    def _setup_location(self):
        self.clean_df["territory"] = self.clean_df["territory"].apply(
            IndiaStatesMapper.get_state_name_to_iso_code_mapping)

    def _make_column_numerical(self, column):
        self.clean_df[column] = self.clean_df[column].astype(str).str.replace(
            ",", "")
        self.clean_df[column] = pd.to_numeric(self.clean_df[column])

    def process(self):
        # Set the date or period
        self.clean_df = self.raw_df
        self.clean_df.insert(loc=0, column="period", value=self.period)

        # Rename columns
        self.clean_df.columns = self.COLUMN_HEADERS

        self._make_column_numerical("wage_rural_male")
        self._make_column_numerical("wage_rural_female")
        self._make_column_numerical("wage_rural_person")
        self._make_column_numerical("wage_urban_male")
        self._make_column_numerical("wage_urban_female")
        self._make_column_numerical("wage_urban_person")
        self._make_column_numerical("wage_total_male")
        self._make_column_numerical("wage_total_female")
        self._make_column_numerical("wage_total_person")

        # Setup place ISO codes
        self._setup_location()

    def save(self, csv_file_path):
        if path.exists(csv_file_path):
            # If the file exists then append to the same
            self.clean_df.to_csv(csv_file_path,
                                 mode='a',
                                 index=False,
                                 header=False)
        else:
            self.clean_df.to_csv(csv_file_path, index=False, header=True)


def main():
    """Runs the program."""

    # If the final output csv already exists
    # Remove it, so it can be regenerated
    csv_file_path = os.path.join(os.path.dirname(__file__),
                                 "./PLFSWageData_India.csv")
    if path.exists(csv_file_path):
        os.remove(csv_file_path)

    for dataset in DATASETS:
        period = dataset["period"]
        data_file = dataset["data_file"]
        data_rows = dataset["data_rows"]
        data_file_path = os.path.join(
            os.path.dirname(__file__),
            "data/{data_file}".format(data_file=data_file),
        )
        loader = PLFSWageDataLoader(data_file_path, period, data_rows)
        loader.load()
        loader.process()
        loader.save(csv_file_path)


if __name__ == "__main__":
    main()
