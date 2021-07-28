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

__author__ = ["Thejesh GN (i@thejeshgn.com)"]

import os
import math
import json
import csv
import pandas as pd
import numpy as np
import urllib.request


class IndiaPostPincodesDataLoader:

    def __init__(self, pincode_csv, clean_csv):
        self.pincode_csv = pincode_csv
        self.raw_df = None
        self.clean_df = None
        self.clean_csv = clean_csv

    @staticmethod
    def format_title(s):
        # Converts to title case, except for the words like `of`, `and` etc
        name_list = s.split(' ')
        first_list = [name_list[0].capitalize()]
        for name in name_list[1:]:
            first_list.append(name if name in
                              ["of", "and"] else name.capitalize())
        return " ".join(first_list)

    @staticmethod
    def format_code(s):
        # Converts into two character length code
        # If the value is `0` then it makes it empty
        # If the length is single character then it prepends it
        # with `0` to make it two character length
        s = s.zfill(2)
        return "" if s == "00" else s


    def process(self):
        self.raw_df = pd.read_csv(self.pincode_csv, dtype=str)
        self.raw_df.fillna('', inplace=True)
        print(self.raw_df)


    def save(self):
        self.clean_df.to_csv(self.clean_csv, index=False, header=True)


def main():
    """Runs the program."""
    lgd_csv = os.path.join(os.path.dirname(__file__),
                           "./data/lgd_allStateofIndia_export.csv")
    wikidata_csv = os.path.join(
        os.path.dirname(__file__),
        "./data/wikidata_india_states_and_ut_export.csv")
    clean_csv = os.path.join(os.path.dirname(__file__),
                             "LocalGovernmentDirectory_States.csv")
    loader = IndiaPostPincodesDataLoader(lgd_csv, wikidata_csv,
                                                     clean_csv)
    loader.process()
    loader.save()


if __name__ == '__main__':
    main()
