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
from india.formatters import CodeFormatter
from india.geo.districts import IndiaDistrictsMapper

PINCODE_TMCF = """Node: E:IndiaPost->E{index}
typeOf: dcs:PinCodeArea
name: C:IndiaPost->Pincode
pinCode: C:IndiaPost->Pincode
dcid: C:IndiaPost->PincodeDCID
{district_overlaps}
"""

# A PinCodeArea can overlap (they have some but not all points in common)
# one or more districts. We use geoOverlaps to map it.
# We do that by creating as many District template-nodes
# as the max number of overlapping districts currently possible

GEO_OVERLAPS_TMCF = """geoOverlaps: E:IndiaPost->E{district_index}
"""

DISTRICT_TMCF = """Node: E:IndiaPost->E{district_index}
typeOf: dcs:Place
lgdCode: C:IndiaPost->DistrictLGDCode{district_index}
"""


class IndiaPostPincodesDataLoader:

    def __init__(self, pincode_csv, clean_csv, tmcf_file):
        self.pincode_csv = pincode_csv
        self.raw_df = None
        self.clean_df = None
        self.clean_csv = clean_csv
        self.tmcf_file = tmcf_file
        self.mapper = IndiaDistrictsMapper()
        self.max_districts_per_pincode = 0

    def _setup_location(self, row):
        return self.mapper.get_district_name_to_lgd_code_mapping(
            row["StateName"], row["District"])

    def _pincode_dcid(self, pincode):
        return "pinCode/{pincode}".format(pincode=pincode)

    def process(self):
        self.raw_df = pd.read_csv(self.pincode_csv, dtype=str)
        self.raw_df.fillna('', inplace=True)
        self.raw_df.drop_duplicates(subset=["Pincode", "StateName", "District"],
                                    inplace=True)
        self.raw_df.drop([
            "CircleName", "RegionName", "DivisionName", "OfficeName",
            "OfficeType", "Delivery", "Latitude", "Longitude"
        ],
                         axis=1,
                         inplace=True,
                         errors="ignore")
        self.raw_df.sort_values(by=["Pincode", "StateName", "District"],
                                inplace=True)
        self.raw_df["DistrictLGDCode"] = self.raw_df.apply(
            lambda row: self._setup_location(row), axis=1)

        # Group by StateName and Pincode. Then for that combination, have the DistrictLGDCode column that
        # concatenates all the codes separated by comma
        self.raw_df = self.raw_df.groupby(
            by=["StateName", "Pincode"])["DistrictLGDCode"].apply(
                ','.join).reset_index()
        # Now split the single column DistrictLGDCode into multiple columns
        # with column name of format `DistrictLGDCode<N>`
        self.raw_df = self.raw_df.join(self.raw_df['DistrictLGDCode'].str.split(
            ',', expand=True).add_prefix('DistrictLGDCode'))
        # Drop the DistrictLGDCode Column
        self.raw_df.drop(["DistrictLGDCode"],
                         axis=1,
                         inplace=True,
                         errors="ignore")

        # Add column PincodeDCID derived from Pincode
        self.raw_df["PincodeDCID"] = self.raw_df["Pincode"].apply(
            self._pincode_dcid)

        # No of columns in DataFrame which starts with DistrictLGDCode
        self.max_districts_per_pincode = len([
            x for x in list(self.raw_df.columns)
            if x.startswith("DistrictLGDCode")
        ])
        self.clean_df = self.raw_df

    def save(self):
        district_index_range = range(self.max_districts_per_pincode)
        district_overlaps = ""
        districts_tmcf = ""
        for district_index in district_index_range:
            district_overlaps = district_overlaps + GEO_OVERLAPS_TMCF.format(
                district_index=district_index)
            districts_tmcf = districts_tmcf + DISTRICT_TMCF.format(
                district_index=district_index) + "\n"

        pincode_tmcf = PINCODE_TMCF.format(index=self.max_districts_per_pincode,
                                           district_overlaps=district_overlaps)

        with open(self.tmcf_file, 'w+', newline='') as f_out:
            f_out.write(districts_tmcf)
            f_out.write(pincode_tmcf)

        self.clean_df.to_csv(self.clean_csv, index=False, header=True)


def main():
    """Runs the program."""
    pincode_csv = os.path.join(os.path.dirname(__file__), "./data/pincode.csv")
    clean_csv = os.path.join(os.path.dirname(__file__),
                             "IndiaPost_Pincodes.csv")

    tmcf_file = os.path.join(os.path.dirname(__file__),
                             "IndiaPost_Pincodes.tmcf")

    loader = IndiaPostPincodesDataLoader(pincode_csv, clean_csv, tmcf_file)
    loader.process()
    loader.save()


if __name__ == '__main__':
    main()
