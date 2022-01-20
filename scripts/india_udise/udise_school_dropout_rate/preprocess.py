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
"""Classes and methods to import School Dropout Rate data from Unified District Information System for Education (UDISE)"""

__author__ = ["Thejesh GN (i@thejeshgn.com)"]

import os
import sys
import json
import csv
import pandas as pd
import numpy as np
import requests
import time
from os import path
from india_udise.common.base import UDISEIndiaDataLoaderBase

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)

ATTRIBUTE_MAPPING = {
    "pri_girl_c1_c5_dropout_rate": {
        "Gender": "Female",
        "SchoolLevel": "PrimarySchool"
    },
    "pri_boy_c1_c5_dropout_rate": {
        "Gender": "Male",
        "SchoolLevel": "PrimarySchool"
    },
    "pri_c1_c5_dropout_rate": {
        "SchoolLevel": "PrimarySchool"
    },
    "upper_pri_girl_c6_c8_dropout_rate": {
        "Gender": "Female",
        "SchoolLevel": "MiddleSchool"
    },
    "upper_pri_boy_c6_c8_dropout_rate": {
        "Gender": "Male",
        "SchoolLevel": "MiddleSchool"
    },
    "upper_pri_c6_c8_dropout_rate": {
        "SchoolLevel": "MiddleSchool"
    },
    "secondary_girl_c9_c10_dropout_rate": {
        "Gender": "Female",
        "SchoolLevel": "SecondarySchool"
    },
    "secondary_boy_c9_c10_dropout_rate": {
        "Gender": "Male",
        "SchoolLevel": "SecondarySchool"
    },
    "secondary_c9_c10_dropout_rate": {
        "SchoolLevel": "SecondarySchool"
    },
}


class UDISESchoolDropoutRate(UDISEIndiaDataLoaderBase):

    def _get_base_name(self, data_row):
        name = "DropoutRate_Student"
        return name


if __name__ == "__main__":
    action = "download"
    if len(sys.argv) > 1:
        action = sys.argv[1]
    years = ["2014-15", "2015-16", "2016-17", "2017-18", "2018-19"]
    api_report_code = "117"
    data_folder = os.path.join(module_dir_, "data")
    csv_file_path = os.path.join(module_dir_,
                                 "UDISEIndia_School_Dropout_Rate.csv")
    mcf_file_path = os.path.join(module_dir_,
                                 "UDISEIndia_School_Dropout_Rate.mcf")
    if path.exists(csv_file_path):
        os.remove(csv_file_path)
    if path.exists(mcf_file_path):
        os.remove(mcf_file_path)
    base = UDISESchoolDropoutRate(api_report_code,
                                  data_folder,
                                  csv_file_path,
                                  mcf_file_path,
                                  years,
                                  attribute_mapping=ATTRIBUTE_MAPPING)
    if action == "download":
        base.download()
    elif action == "process":
        base.process()
    else:
        print("Valid actions are download and process.")
