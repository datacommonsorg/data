# Copyright 2021 Google LLC
#
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

import os
import sys
import unittest
import csv

# Allows the following module imports to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from us_epa.ghgrp import download, gas, sources
from us_epa.util import crosswalk as cw

_FACILITY_ID = 'Facility Id'
_DCID = 'dcid'
_SV = 'sv'
_YEAR = 'year'
_VALUE = 'value'
_OUT_FIELDNAMES = [_DCID, _SV, _YEAR, _VALUE]


def process_data(data_filepaths, crosswalk, out_filepath):
    print(data_filepaths)
    with open(out_filepath, 'w') as out_fp:
        csv_writer = csv.DictWriter(out_fp, fieldnames=_OUT_FIELDNAMES)
        csv_writer.writeheader()
        for (year, filepath) in data_filepaths:
            with open(filepath, 'r') as fp:
                for row in csv.DictReader(fp):
                    dcid = crosswalk.get_dcid(row[_FACILITY_ID])
                    assert dcid
                    for key, value in row.items():
                        if not value:
                            continue
                        sv = gas.col_to_sv(key)
                        if not sv:
                            sv = sources.col_to_sv(key)
                            if not sv:
                                continue
                        csv_writer.writerow({
                            _DCID: f'dcid:{dcid}',
                            _SV: f'dcid:{sv}',
                            _YEAR: year,
                            _VALUE: value
                        })


if __name__ == '__main__':
    crosswalk = cw.Crosswalk('tmp_data/crosswalks.csv')
    downloader = download.Downloader()
    # downloader.download_data()
    # files = downloader.extract_all_years()
    # process_data(files, crosswalk, 'tmp_data/all_data.csv')
