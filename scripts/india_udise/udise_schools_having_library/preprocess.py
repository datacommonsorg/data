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
"""Classes and methods to import Number of Schools having Library from Unified District Information System for Education (UDISE)"""

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
from india_udise.common.base_school_data import UDISEIndiaSchoolDataLoaderBase
from india_udise.common.base_school_data import BASE_DATA_FOLDER

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class UDISESchoolsHavingLibrary(UDISEIndiaSchoolDataLoaderBase):

    def _get_base_name(self, data_row):
        name = "Count_School_HasLibrary"
        return name

    def _get_base_constraints(self, data_row):
        constraints = []
        constraints.append("amenityFeature: dcs:Library")
        return constraints


if __name__ == "__main__":
    action = "download"
    if len(sys.argv) > 1:
        action = sys.argv[1]

    # Academic years or school years.
    # `2013-14` means - April 1st, 2013 to March 31st, 2014
    years = sorted([
        "2013-14", "2014-15", "2015-16", "2016-17", "2017-18", "2018-19",
        "2019-20"
    ],
                   reverse=True)

    api_report_code = "3031"
    api_map_id = "54"

    data_folder = BASE_DATA_FOLDER
    csv_file_path = os.path.join(
        module_dir_, "UDISEIndia_Schools_Having_Library.csv")
    mcf_file_path = os.path.join(
        module_dir_, "UDISEIndia_Schools_Having_Library.mcf")
    if path.exists(csv_file_path):
        os.remove(csv_file_path)

    if path.exists(mcf_file_path):
        os.remove(mcf_file_path)

    base = UDISESchoolsHavingLibrary(api_report_code, api_map_id,
                                               data_folder, csv_file_path,
                                               mcf_file_path, years)
    if action == "download":
        base.download()
    elif action == "process":
        base.process()
    else:
        print("Valid actions are download and process.")
