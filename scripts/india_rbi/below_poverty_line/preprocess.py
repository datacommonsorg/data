# Copyright 2020 Google LLC
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

import json
import csv
import pandas as pd
import numpy as np
import urllib.request

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
    "Telengana": "IN-TG",
    "Telangana": "IN-TG",
    "Tripura": "IN-TR",
    "Uttarakhand": "IN-UT",
    "Uttar Pradesh": "IN-UP",
    "West Bengal": "IN-WB",
    "Andaman and Nicobar Islands": "IN-AN",
    "Andaman & Nicobar Islands": "IN-AN",
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
    "Dadra and Nagar Haveli and Daman and Diu": "IN-DH",
    "Telangana": "IN-TG",
    "All India": "IN"
}


class BelowPovertyLineDataLoader:
    COLUMN_HEADERS = [
        "year", "territory", "count_person_rural", "percentage_person_rural",
        "poverty_line_rural", "count_person_urban", "percentage_person_urban",
        "poverty_line_urban", "count_person_combined",
        "percentage_person_combined"
    ]

    def __init__(self, source):
        self.source = source
        self.raw_df = None
        self.clean_df = None

    def download(self):
        df = pd.read_excel(self.source)
        #Drop title rows in the top and empty rows after 39.
        #The actual data is between 2nd and 40th row. So keep only them.
        df = df.iloc[2:40]
        #There is an empty column at column index 19. We don't need it. So drop it.
        df = df.drop(df.columns[0], axis=1)
        self.raw_df = df.drop(df.columns[19], axis=1)

    def _setup_location(self):
        self.clean_df["territory"] = self.clean_df["territory"].apply(
            lambda x: INDIA_ISO_CODES[x])

    def _make_column_numerical(self, column):
        self.clean_df[column] = self.clean_df[column].astype(str).str.replace(
            ',', '')
        self.clean_df[column].loc[self.clean_df[column] == '.'] = np.nan
        self.clean_df[column] = pd.to_numeric(self.clean_df[column])

    def process(self):
        #Get yearly date and set the date
        df2004_05 = self._process_yearly_dataframe(year="2005-03",
                                                   start_index=0)
        df2009_10 = self._process_yearly_dataframe(year="2010-03",
                                                   start_index=10)
        df2011_12 = self._process_yearly_dataframe(year="2012-03",
                                                   start_index=20)
        self.clean_df = pd.concat([df2004_05, df2009_10, df2011_12])

        self._make_column_numerical("count_person_rural")
        self._make_column_numerical("percentage_person_rural")
        self._make_column_numerical("poverty_line_rural")
        self._make_column_numerical("count_person_urban")
        self._make_column_numerical("percentage_person_urban")
        self._make_column_numerical("poverty_line_urban")
        self._make_column_numerical("count_person_combined")
        self._make_column_numerical("percentage_person_combined")

        #Count columns are in thousands, hence multiply them by 1000
        self.clean_df[
            "count_person_rural"] = self.clean_df["count_person_rural"] * 1000
        self.clean_df[
            "count_person_urban"] = self.clean_df["count_person_urban"] * 1000
        self.clean_df["count_person_combined"] = self.clean_df[
            "count_person_combined"] * 1000

        #setup state codes
        self._setup_location()

    def _process_yearly_dataframe(self, year, start_index):
        df_frame = self.raw_df.iloc[:, start_index:start_index + 10]
        df_frame = df_frame.iloc[2:40]
        df_frame.iloc[:, 0] = year
        df_frame.columns = self.COLUMN_HEADERS
        return df_frame

    def save(self, csv_file_path="BelowPovertyLine_India.csv"):
        self.clean_df.to_csv(csv_file_path, index=False, header=True)


def main():
    """Runs the program."""
    SOURCE_XLSX_FILE_URL = "https://rbidocs.rbi.org.in/rdocs/Publications/DOCs/154T_HB15092019609736EE47614B23BFD377A47FFC1A5D.XLSX"
    loader = BelowPovertyLineDataLoader(SOURCE_XLSX_FILE_URL)
    loader.download()
    loader.process()
    loader.save()


if __name__ == '__main__':
    main()
