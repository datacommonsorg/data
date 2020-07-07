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

'''
Downloading and converting BLS CPI raw csv files to csv files of two columns:
"date" and "cpi", where "date" is of the form "YYYY-MM" and "cpi" is numeric.

Usage: python3 generate_csv.py
'''


from io import StringIO

import requests
import frozendict
import pandas as pd


# Dict from series names to download links
CSV_URLS = frozendict.frozendict({
    "cpi_u_1913_2020":
        "https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems",
    "cpi_w_1913_2020":
        "https://download.bls.gov/pub/time.series/cw/cw.data.1.AllItems",
    "c_cpi_u_1999_2020":
        "https://download.bls.gov/pub/time.series/su/su.data.1.AllItems"
})

# Dict from series names to series IDs
SERIES_IDS = frozendict.frozendict({
    "cpi_u_1913_2020": "CUUR0000SA0",
    "cpi_w_1913_2020": "CWUR0000SA0",
    "c_cpi_u_1999_2020": "SUUR0000SA0"
})


def main():
    for series_name, url in CSV_URLS.items():
        series_id = SERIES_IDS[series_name]

        # If the downloading fails, an exception will be thrown and the
        # script will crash.
        # See https://requests.readthedocs.io/en/latest/user/quickstart/#errors-and-exceptions.
        response = requests.get(url)
        response.raise_for_status()

        buffer = StringIO(response.text)

        # The raw csv has four columns: "series_id", "year", "period", "value",
        # and "footnote_codes".
        # "value" is the CPI values.
        # "year" is of the form "YYYY".
        # "period" is the months of the observations and is of the form "MM"
        # preceded by char 'M', e.g. "M05".
        in_df = pd.read_csv(buffer, sep="\s+", dtype="str")
        # "M13" is annual averages
        in_df = in_df[(in_df["series_id"] == series_id) &
            (in_df["period"] != "M13")]
        # Format "date" column as "YYYY-MM"
        in_df["date"] = in_df["year"] + "-" + in_df["period"].str[-2:]
        in_df = in_df[["date", "value"]]
        in_df.columns = ["date", "cpi"]

        in_df.to_csv(series_name + ".csv", index=False)


if __name__ == "__main__":
    main()
