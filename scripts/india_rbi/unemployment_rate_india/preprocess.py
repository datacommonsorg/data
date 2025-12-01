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
    "Dadra and Nagar Haveli and Daman and Diu": "IN-DN_DD",
    "all India": "IN",
    "all-India": "IN",
    "ALL INDIA": "IN"
}

DATASETS = [{
    "data_file": "T_13091EFB2ADFEA47CAA069BEE53BD82F14.xlsx",
    "sheet_no": 0,
    "statisticalVariable": "dcs:UnemploymentRate_Person_Urban_Male"
}, {
    "data_file": "T_13091EFB2ADFEA47CAA069BEE53BD82F14.xlsx",
    "sheet_no": 1,
    "statisticalVariable": "dcs:UnemploymentRate_Person_Urban_Female"
}, {
    "data_file": "T_13091EFB2ADFEA47CAA069BEE53BD82F14.xlsx",
    "sheet_no": 2,
    "statisticalVariable": "dcs:UnemploymentRate_Person_Urban"
}, {
    "data_file": "T_123C6CE499AEFB461E8242E14098242CA5.xlsx",
    "sheet_no": 0,
    "statisticalVariable": "dcs:UnemploymentRate_Person_Rural_Male"
}, {
    "data_file": "T_123C6CE499AEFB461E8242E14098242CA5.xlsx",
    "sheet_no": 1,
    "statisticalVariable": "dcs:UnemploymentRate_Person_Rural_Female"
}, {
    "data_file": "T_123C6CE499AEFB461E8242E14098242CA5.xlsx",
    "sheet_no": 2,
    "statisticalVariable": "dcs:UnemploymentRate_Person_Rural"
}]

FINANCIAL_YEAR_TO_OBSERVATION_DATE_MAPPING = {
    "1993-94": "1994-03",
    "1999-00": "2000-03",
    "2004-05": "2005-03",
    "2009-10": "2010-03",
    "2011-12": "2012-03",
    "2017-18": "2018-03",
    "2018-19": "2019-03"
}


class UnempolymentRateIndiaLoader:
    COLUMN_HEADERS = ["territory", "value", "period", "statisticalVariable"]

    def __init__(self, source, sheet_no, statisticalVariable):
        self.source = source
        self.sheet_no = sheet_no
        self.statisticalVariable = statisticalVariable
        self.raw_df = None
        self.clean_df = None

    def load(self):
        df = pd.read_excel(self.source, self.sheet_no)
        # Column headers in row 3, grab them
        headers = df.iloc[3]

        # The actual data is between the 4th and 41st row
        df = df.iloc[4:40]

        # Set the headers as df column name
        df.columns = headers
        self.raw_df = df

    def _setup_location(self):
        self.clean_df["territory"] = self.clean_df["territory"].apply(
            lambda x: INDIA_ISO_CODES[x])

    def _make_column_numerical(self, column):
        self.clean_df[column] = self.clean_df[column].astype(str).str.replace(
            ',', '')
        self.clean_df[column].loc[self.clean_df[column] == '.'] = np.nan
        self.clean_df[column].loc[self.clean_df[column] == '-'] = np.nan
        self.clean_df[column] = pd.to_numeric(self.clean_df[column],
                                              errors='coerce')

    def process(self):
        # Create a new dataframe with required columns
        self.clean_df = pd.DataFrame(columns=self.COLUMN_HEADERS)

        for period_column_name in [
                "1993-94", "1999-00", "2004-05", "2009-10", "2011-12",
                "2017-18", "2018-19"
        ]:
            df = pd.DataFrame()
            df = self.raw_df[["State/Union Territory", period_column_name]]
            # Its for the financial year. For example 1993-94 means
            # One year period from 1993-04-01 to 1994-03-31
            # Which is same as 1994-03, with period "PY1"
            df["period"] = FINANCIAL_YEAR_TO_OBSERVATION_DATE_MAPPING[
                period_column_name]
            df["statisticalVariable"] = self.statisticalVariable
            # Rename columns
            df.columns = self.COLUMN_HEADERS
            self.clean_df = pd.concat([self.clean_df, df])

        self._make_column_numerical("value")
        # Setup place ISO codes
        self._setup_location()
        # Remove rows with value is NAN
        self.clean_df = self.clean_df.dropna(axis=0, how='any')
        # The value is Per 1000, convert to per 100
        self.clean_df["value"] = self.clean_df["value"] / 10

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
                                 "./UnemploymentRate_India.csv")
    if path.exists(csv_file_path):
        os.remove(csv_file_path)

    for dataset in DATASETS:
        data_file = dataset["data_file"]
        sheet_no = dataset["sheet_no"]
        statisticalVariable = dataset["statisticalVariable"]
        data_file_path = os.path.join(
            os.path.dirname(__file__),
            "data/{data_file}".format(data_file=data_file),
        )
        loader = UnempolymentRateIndiaLoader(data_file_path, sheet_no,
                                             statisticalVariable)
        loader.load()
        loader.process()
        loader.save(csv_file_path)


if __name__ == "__main__":
    main()
