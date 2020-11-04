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
    "Andhra Pradesh": "dcid:wikidataId/Q1159",
    "Arunachal Pradesh": "dcid:wikidataId/Q1162",
    "Assam": "dcid:wikidataId/Q1164",
    "Bihar": "dcid:wikidataId/Q1165",
    "Chattisgarh": "dcid:wikidataId/Q1168",
    "Chhattisgarh": "dcid:wikidataId/Q1168",
    "Goa": "dcid:wikidataId/Q1171",
    "Gujarat": "dcid:wikidataId/Q1061",
    "Haryana": "dcid:wikidataId/Q1174",
    "Himachal Pradesh": "dcid:wikidataId/Q1177",
    "Jharkhand": "dcid:wikidataId/Q1184",
    "Karnataka": "dcid:wikidataId/Q1185",
    "Kerala": "dcid:wikidataId/Q1186",
    "Madhya Pradesh": "dcid:wikidataId/Q1188",
    "Maharashtra": "dcid:wikidataId/Q1191",
    "Manipur": "dcid:wikidataId/Q1193",
    "Meghalaya": "dcid:wikidataId/Q1195",
    "Mizoram": "dcid:wikidataId/Q1502",
    "Nagaland": "dcid:wikidataId/Q1599",
    "Odisha": "dcid:wikidataId/Q22048",
    "Punjab": "dcid:wikidataId/Q22424",
    "Rajasthan": "dcid:wikidataId/Q1437",
    "Sikkim": "dcid:wikidataId/Q1505",
    "Tamil Nadu": "dcid:wikidataId/Q1445",
    "Telengana": "dcid:wikidataId/Q677037",
    "Telangana": "dcid:wikidataId/Q677037",
    "Tripura": "dcid:wikidataId/Q1363",
    "Uttarakhand": "dcid:wikidataId/Q1499",
    "Uttar Pradesh": "dcid:wikidataId/Q1498",
    "West Bengal": "dcid:wikidataId/Q1356",
    "Andaman and Nicobar Islands": "dcid:wikidataId/Q40888",
    "Andaman & Nicobar Islands": "dcid:wikidataId/Q40888",
    "Chandigarh": "dcid:wikidataId/Q43433",
    "Dadra and Nagar Haveli": "dcid:wikidataId/Q46107",
    "Dadra & Nagar Haveli": "dcid:wikidataId/Q46107",
    "Dadar Nagar Haveli": "dcid:wikidataId/Q46107",
    "Daman and Diu": "dcid:wikidataId/Q66710",
    "Daman & Diu": "dcid:wikidataId/Q66710",
    "Delhi": "dcid:wikidataId/Q1353",
    "Jammu and Kashmir": "dcid:wikidataId/Q66278313",
    "Jammu & Kashmir": "dcid:wikidataId/Q66278313",
    "Ladakh": "dcid:wikidataId/Q200667",
    "Lakshadweep": "dcid:wikidataId/Q26927",
    "Lakshwadeep": "dcid:wikidataId/Q26927",
    "Pondicherry": "dcid:wikidataId/Q639421",
    "Puducherry": "dcid:wikidataId/Q639421",
    "All India": "dcid:country/IND"
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
