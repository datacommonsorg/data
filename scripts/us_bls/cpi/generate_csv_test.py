# Copyright 2025 Google LLC
# Author: Shamim Ansari
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
import unittest
import os
import frozendict
from absl import logging
from generate_csv import process
from generate_csv import retry_method
global buffer
import requests
import io
import pandas as pd


#@retry(tries=3, delay=5, backoff=5)
def retry_method(url, header):
    return requests.get(url, headers=header)


_MODULE_DIR = os.path.dirname(__file__)
TEST_DATA_DIR = os.path.join(_MODULE_DIR, 'test_data')
series_id = "CUSR0000SA0"
series_name = "cpi_u_1913_2024"
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
#print("MODULE_DIR: ",MODULE_DIR)
#print("TEST_DATA_DIR: ",TEST_DATA_DIR)

header = {
    'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Content-Type':
        'application/octet-stream',
}

url = "https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems"
#Retry method is calling
response = retry_method(url, header=header)
response.raise_for_status()
buffer = io.StringIO(response.text)


class TestGenerateCSV(unittest.TestCase):

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

    def test_GenerateCSV_data(self):

        in_df = pd.read_csv(buffer, sep=r"\s+", dtype="str")
        # "M13" is annual averages
        in_df = in_df[(in_df["series_id"] == series_id) &
                      (in_df["period"] != "M13")]
        # Format "date" column as "YYYY-MM"
        in_df["date"] = in_df["year"] + "-" + in_df["period"].str[-2:]
        in_df = in_df[["date", "value"]]
        in_df.columns = ["date", "cpi"]
        # Convert 'date' column to datetime format
        start_date = int(46)
        logging.info(f"start_date {start_date}")
        in_df['date'] = pd.to_datetime(in_df['date'], format='%Y-%m')
        in_df = in_df[in_df['date'].dt.year > start_date]
        in_df['date'] = in_df['date'].dt.strftime('%Y-%m')
        in_df["cpi"] = pd.to_numeric(in_df["cpi"], errors='coerce')
        # print("==================in_df ",in_df)
        df_from_csv = pd.read_csv(
            os.path.join(TEST_DATA_DIR, "cpi_u_1913_2024.csv"))
        #print("==================df_from_csv ",df_from_csv)
        pd.testing.assert_frame_equal(in_df, df_from_csv)


if __name__ == '__main__':
    unittest.main()
