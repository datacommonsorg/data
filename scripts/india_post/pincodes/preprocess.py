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
from pandasql import sqldf
import numpy as np
import urllib.request

from india.formatters import CodeFormatter

class IndiaPostPincodesDataLoader:

    def __init__(self, pincode_csv, clean_csv):
        self.pincode_csv = pincode_csv
        self.raw_df = None
        self.clean_df = None
        self.clean_csv = clean_csv


    def process(self):
        self.raw_df = pd.read_csv(self.pincode_csv, dtype=str)
        self.raw_df.fillna('', inplace=True)        
        self.raw_df.drop_duplicates(subset=["Pincode","StateName","District"], inplace=True)
        self.raw_df.drop(["CircleName","RegionName","DivisionName","OfficeName","OfficeType","Delivery","Latitude","Longitude"],axis=1,inplace=True,errors="ignore")
        self.raw_df.sort_values(by=["Pincode","StateName","District"], inplace=True)
        # Group by StateName and Pincode. Then for that combination have the Distict column that
        # concatenates all the districts seaparated by comma
        self.raw_df = self.raw_df.groupby(by=["StateName","Pincode"])["District"].apply(','.join).reset_index()
        # Now split the single column District into multiple with column name Distict<N>
        self.raw_df = self.raw_df.join(self.raw_df['District'].str.split(',', expand=True).add_prefix('District'))
        # Drop the District Column
        self.raw_df.drop(["District"],axis=1,inplace=True,errors="ignore")        
        self.clean_df = self.raw_df
    def save(self):
        self.clean_df.to_csv(self.clean_csv, index=False, header=True)


def main():
    """Runs the program."""
    wikidata_csv = os.path.join(
        os.path.dirname(__file__),
        "./data/pincode.csv")
    clean_csv = os.path.join(os.path.dirname(__file__),
                             "IndiaPost_Pincodes.csv")
    loader = IndiaPostPincodesDataLoader(wikidata_csv,
                                                     clean_csv)
    loader.process()
    loader.save()


if __name__ == '__main__':
    main()
