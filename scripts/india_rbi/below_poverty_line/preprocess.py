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

INDIA_ISO_CODES = {}
INDIA_ISO_CODES["Andhra Pradesh"] = "IN-AP"
INDIA_ISO_CODES["Arunachal Pradesh"] = "IN-AR"
INDIA_ISO_CODES["Assam"] = "IN-AS"
INDIA_ISO_CODES["Bihar"] = "IN-BR"
INDIA_ISO_CODES["Chattisgarh"] = "IN-CT"
INDIA_ISO_CODES["Chhattisgarh"] = "IN-CT"
INDIA_ISO_CODES["Goa"] = "IN-GA"
INDIA_ISO_CODES["Gujarat"] = "IN-GJ"
INDIA_ISO_CODES["Haryana"] = "IN-HR"
INDIA_ISO_CODES["Himachal Pradesh"] = "IN-HP"
INDIA_ISO_CODES["Jharkhand"] = "IN-JH"
INDIA_ISO_CODES["Jharkhand#"] = "IN-JH"
INDIA_ISO_CODES["Karnataka"] = "IN-KA"
INDIA_ISO_CODES["Kerala"] = "IN-KL"
INDIA_ISO_CODES["Madhya Pradesh"] = "IN-MP"
INDIA_ISO_CODES["Madhya Pradesh#"] = "IN-MP"
INDIA_ISO_CODES["Maharashtra"] = "IN-MH"
INDIA_ISO_CODES["Manipur"] = "IN-MN"
INDIA_ISO_CODES["Meghalaya"] = "IN-ML"
INDIA_ISO_CODES["Mizoram"] = "IN-MZ"
INDIA_ISO_CODES["Nagaland"] = "IN-NL"
INDIA_ISO_CODES["Nagaland#"] = "IN-NL"
INDIA_ISO_CODES["Odisha"] = "IN-OR"
INDIA_ISO_CODES["Punjab"] = "IN-PB"
INDIA_ISO_CODES["Rajasthan"] = "IN-RJ"
INDIA_ISO_CODES["Sikkim"] = "IN-SK"
INDIA_ISO_CODES["Tamil Nadu"] = "IN-TN"
INDIA_ISO_CODES["Telengana"] = "IN-TG"
INDIA_ISO_CODES["Telangana***"] = "IN-TG"
INDIA_ISO_CODES["Telengana***"] = "IN-TG"
INDIA_ISO_CODES["Tripura"] = "TIN-R"
INDIA_ISO_CODES["Uttarakhand"] = "IN-UT"
INDIA_ISO_CODES["Uttar Pradesh"] = "IN-UP"
INDIA_ISO_CODES["West Bengal"] = "IN-WB"
INDIA_ISO_CODES["Andaman and Nicobar Islands"] = "IN-AN"
INDIA_ISO_CODES["Andaman & Nicobar Islands"] = "IN-AN"
INDIA_ISO_CODES["Chandigarh"] = "IN-CH"
INDIA_ISO_CODES["Dadra and Nagar Haveli"] = "IN-DN"
INDIA_ISO_CODES["Dadra & Nagar Haveli"] = "IN-DN"
INDIA_ISO_CODES["Dadar Nagar Haveli"] = "IN-DN"
INDIA_ISO_CODES["Daman and Diu"] = "IN-DD"
INDIA_ISO_CODES["Daman & Diu"] = "IN-DD"
INDIA_ISO_CODES["Delhi"] = "IN-DL"
INDIA_ISO_CODES["Jammu and Kashmir"] = "IN-JK"
INDIA_ISO_CODES["Jammu & Kashmir"] = "IN-JK"
INDIA_ISO_CODES["Ladakh"] = "IN-LA"
INDIA_ISO_CODES["Lakshadweep"] = "IN-LD"
INDIA_ISO_CODES["Lakshwadeep"] = "IN-LD"
INDIA_ISO_CODES["Pondicherry"] = "IN-PY"
INDIA_ISO_CODES["Puducherry"] = "IN-PY"
INDIA_ISO_CODES["Dadra and Nagar Haveli and Daman and Diu"] = "IN-DN_DD"
INDIA_ISO_CODES["Telangana"] = "IN-TG"


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
        #Drop title rows and empty rows
        df = df.iloc[2:40]
        #Remove emprty columns
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
        combined_df = df2004_05.append(df2009_10)
        self.clean_df = combined_df.append(df2011_12)

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

        self.clean_df.drop(
            self.clean_df.index[self.clean_df.territory == "All India"],
            inplace=True)

        #setup state codes
        self._setup_location()

    def _process_yearly_dataframe(self, year, start_index):
        df_frame = self.raw_df.iloc[:, start_index:start_index + 10]
        df_frame = df_frame.iloc[2:40]
        df_frame.iloc[:, 0] = year
        df_frame.columns = self.COLUMN_HEADERS
        return df_frame

    def save(self, csv_file_path="BelowPovertyLine_India.csv"):
        print(self.clean_df)
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
