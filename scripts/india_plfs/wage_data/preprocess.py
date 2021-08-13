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

INDIA_ISO_CODES = {
    "Andhra Pradesh": "IN-AP",
    "Arunachal Pradesh": "IN-AR",
    "Assam": "IN-AS",
    "Bihar": "IN-BR",
    "Chattisgarh": "IN-CT",
    "Chhattisgarh": "IN-CT",
    "Goa": "IN-GA",
    "Gujarat": "IN-GJ",
    "Haryana": "IN-HR",
    "Himachal Pradesh": "IN-HP",
    "Jharkhand": "IN-JH",
    "Jharkhand#": "IN-JH",
    "Karnataka": "IN-KA",
    "Kerala": "IN-KL",
    "Madhya Pradesh": "IN-MP",
    "Madhya Pradesh#": "IN-MP",
    "Maharashtra": "IN-MH",
    "Manipur": "IN-MN",
    "Meghalaya": "IN-ML",
    "Mizoram": "IN-MZ",
    "Nagaland": "IN-NL",
    "Nagaland#": "IN-NL",
    "Odisha": "IN-OR",
    "Punjab": "IN-PB",
    "Rajasthan": "IN-RJ",
    "Sikkim": "IN-SK",
    "Tamil Nadu": "IN-TN",
    "Tamilnadu": "IN-TN",
    "Telengana": "IN-TG",
    "Telangana": "IN-TG",
    "Tripura": "IN-TR",
    "Uttarakhand": "IN-UT",
    "Uttar Pradesh": "IN-UP",
    "West Bengal": "IN-WB",
    "Andaman and Nicobar Islands": "IN-AN",
    "Andaman & Nicobar Islands": "IN-AN",
    "Andaman & N. Island": "IN-AN",
    "A & N Islands": "IN-AN",
    "Chandigarh": "IN-CH",
    "Dadra and Nagar Haveli": "IN-DN",
    "Dadra & Nagar Haveli": "IN-DN",
    "Dadar Nagar Haveli": "IN-DN",
    "Daman and Diu": "IN-DD",
    "Daman & Diu": "IN-DD",
    "Delhi": "IN-DL",
    "Jammu and Kashmir": "IN-JK",
    "Jammu & Kashmir": "IN-JK",
    "Ladakh": "IN-LA",
    "Lakshadweep": "IN-LD",
    "Lakshwadeep": "IN-LD",
    "Pondicherry": "IN-PY",
    "Puducherry": "IN-PY",
    "Puduchery": "IN-PY",
    "Dadra and Nagar Haveli and Daman and Diu": "IN-DH",
    "Telangana": "IN-TG",
    "all India": "IN",
    "all-India": "IN",
}

DATASETS = [
    {
        "period": "2017-07",
        "data_file": "Table_42_07_09_2017"
    },
    {
        "period": "2017-10",
        "data_file": "Table_42_10_12_2017"
    },
    {
        "period": "2018-01",
        "data_file": "Table_42_01_03_2018"
    },
    {
        "period": "2018-04",
        "data_file": "Table_42_04_06_2018"
    },
    {
        "period": "2018-07",
        "data_file": "Table_42_07_09_2018"
    },
    {
        "period": "2018-10",
        "data_file": "Table_42_10_12_2018"
    },
    {
        "period": "2019-01",
        "data_file": "Table_42_01_03_2019"
    },
    {
        "period": "2019-04",
        "data_file": "Table_42_04_06_2019"
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

    def __init__(self, source, period):
        self.source = source
        self.period = period
        self.raw_df = None
        self.clean_df = None

    def load(self):
        df = pd.read_excel(self.source)
        # Drop title rows in the top and  rows after 41.
        # The actual data is between 4nd and 41st row. So keep only them.
        df = df.iloc[4:41]
        self.raw_df = df

    def _setup_location(self):
        self.clean_df["territory"] = self.clean_df["territory"].apply(
            lambda x: INDIA_ISO_CODES[x])

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
        data_file_path = os.path.join(
            os.path.dirname(__file__),
            "data/{data_file}.xlsx".format(data_file=data_file),
        )
        loader = PLFSWageDataLoader(data_file_path, period)
        loader.load()
        loader.process()
        loader.save(csv_file_path)


if __name__ == "__main__":
    main()
