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
"""Classes and methods to import geography data from Unified District Information System for Education (UDISE)"""

__author__ = ["Thejesh GN (i@thejeshgn.com)"]

import os
import json
import csv
import pandas as pd
import numpy as np
import requests
import time
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
    "Ladhak": "IN-LA",
    "Lakshadweep": "IN-LD",
    "Lakshwadeep": "IN-LD",
    "Pondicherry": "IN-PY",
    "Puducherry": "IN-PY",
    "Puduchery": "IN-PY",
    "Dadra and Nagar Haveli and Daman and Diu": "IN-DN_DD",
    "all India": "IN",
    "all-India": "IN",
    "ALL INDIA": "IN",
}

API_URL = "http://pgi.seshagun.gov.in/BackEnd-master/api/report/getMasterData"
DEFAULT_HEADERS = {
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Content-Type": "application/json",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
}


class UDISEGeography:
    def __init__(
        self,
        states_json_data_file_path,
        states_json_csv_file_path,
        districts_json_data_file_path,
        districts_csv_data_file_path,
        blocks_json_data_file_path,
        blocks_csv_data_file_path,
    ):
        self.states_json_data_file_path = states_json_data_file_path
        self.states_json_csv_file_path = states_json_csv_file_path
        self.districts_json_data_file_path = districts_json_data_file_path
        self.districts_csv_data_file_path = districts_csv_data_file_path
        self.blocks_json_data_file_path = blocks_json_data_file_path
        self.blocks_csv_data_file_path = blocks_csv_data_file_path

    def download(self):
        self._get_states_json_data()
        time.sleep(1)
        self._get_districts_json_data()
        time.sleep(1)
        self._get_blocks_json_data()

    def process(self):
        self._process_states_data()
        self._process_districts_data()
        self._process_blocks_data()

    def _process_states_data(self):
        states_json_data_file = open(self.states_json_data_file_path, "r")
        states_json_data = json.loads(states_json_data_file.read())
        df = pd.DataFrame(states_json_data["rowValue"])
        df["isoCode"] = df["state_name"].apply(lambda x: INDIA_ISO_CODES[x])
        df["udise_state_code"] = df["udise_state_code"].apply(
            lambda x: "udiseCode/{}".format(x))
        df.to_csv(self.states_json_csv_file_path, index=False, header=True)

    def _process_districts_data(self):
        districts_json_data_file = open(self.districts_json_data_file_path,
                                        "r")
        districts_json_data = json.loads(districts_json_data_file.read())
        df = pd.DataFrame(districts_json_data["rowValue"])
        df = df.drop_duplicates()
        df["udise_district_code"] = df["udise_district_code"].apply(
            lambda x: "udiseCode/{}".format(x))
        df["district_name"] = df["district_name"].apply(lambda x: x.title())

        df.to_csv(self.districts_csv_data_file_path, index=False, header=True)

    def _process_blocks_data(self):
        blocks_json_data_file = open(self.blocks_json_data_file_path, "r")
        blocks_json_data = json.loads(blocks_json_data_file.read())
        df = pd.DataFrame(blocks_json_data["rowValue"])
        # udise_state_code is an empty column. So drop it
        df = df.drop(columns=['udise_state_code'])
        df = df.rename({"udise_dist_code": "udise_district_code"},
                       axis='columns',
                       errors="raise")

        df["udise_district_code"] = df["udise_district_code"].apply(
            lambda x: "dcid:udiseCode/{}".format(x))
        df["udise_block_code"] = df["udise_block_code"].apply(
            lambda x: "udiseCode/{}".format(x))
        df["block_name"] = df["block_name"].apply(lambda x: x.title()
                                                  if x else '')
        df = df.drop_duplicates()
        df.to_csv(self.blocks_csv_data_file_path, index=False, header=True)

    def _get_states_json_data(self):
        data = {"extensionCall": "GET_STATE", "condition": " "}
        response = requests.post(API_URL,
                                 headers=DEFAULT_HEADERS,
                                 json=data,
                                 verify=False)
        if response.status_code == 200:
            json_data_file = open(self.states_json_data_file_path, "w")
            json_data_file.write(json.dumps(response.json()))
            json_data_file.close()
        else:
            raise Exception("Couldn't download states JSON data")

    def _get_districts_json_data(self):
        data = {
            "extensionCall": "GET_DISTRICT",
            "condition": " order by district_name ",
        }
        response = requests.post(API_URL,
                                 headers=DEFAULT_HEADERS,
                                 json=data,
                                 verify=False)
        if response.status_code == 200:
            json_data_file = open(self.districts_json_data_file_path, "w")
            json_data_file.write(json.dumps(response.json()))
            json_data_file.close()
        else:
            raise Exception("Couldn't download districts JSON data")

    def _get_blocks_json_data(self):
        data = {
            "extensionCall": "GET_BLOCK",
            "condition": " order by block_name "
        }
        response = requests.post(API_URL,
                                 headers=DEFAULT_HEADERS,
                                 json=data,
                                 verify=False)
        if response.status_code == 200:
            json_data_file = open(self.blocks_json_data_file_path, "w")
            json_data_file.write(json.dumps(response.json()))
            json_data_file.close()
        else:
            raise Exception("Couldn't download blocks JSON data")


def main():
    """Runs the program."""
    states_json_data_file_path = os.path.join(os.path.dirname(__file__),
                                              "data/UDISE_States.json")
    states_json_csv_file_path = os.path.join(os.path.dirname(__file__),
                                             "UDISE_States.csv")

    districts_json_data_file_path = os.path.join(os.path.dirname(__file__),
                                                 "data/UDISE_Districts.json")
    districts_csv_data_file_path = os.path.join(os.path.dirname(__file__),
                                                "UDISE_Districts.csv")

    blocks_json_data_file_path = os.path.join(os.path.dirname(__file__),
                                              "data/UDISE_Blocks.json")
    blocks_csv_data_file_path = os.path.join(os.path.dirname(__file__),
                                             "UDISE_Blocks.csv")

    geography = UDISEGeography(
        states_json_data_file_path,
        states_json_csv_file_path,
        districts_json_data_file_path,
        districts_csv_data_file_path,
        blocks_json_data_file_path,
        blocks_csv_data_file_path,
    )
    geography.download()
    geography.process()


if __name__ == "__main__":
    main()
