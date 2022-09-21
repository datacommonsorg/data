# Copyright 2022 Google LLC
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
"""
This script runs
all the national state and
county python script and generate
four output CSV, MCF and TMCF.
"""

import os
import json
from absl import app
from absl import flags
from national.national_1900_1970 import process_national_1900_1970
from national.national_1980_1990 import process_national_1980_1990
from national.national_1990_2000 import process_national_1990_2000
from national.national_2000_2010 import process_national_2000_2010
from national.national_2010_2020 import process_national_2010_2020
from state.state_1970_1979 import process_state_1970_1979
from state.state_1980_1990 import process_state_1980_1990
from state.state_1990_2000 import process_state_1990_2000
from state.state_2000_2010 import process_state_2000_2010
from state.state_2010_2020 import process_state_2010_2020
from county.county_1970_1979 import process_county_1970_1979
from county.county_1980_1989 import process_county_1980_1989
from county.county_1990_2000 import process_county_1990_2000
from county.county_2000_2009 import process_county_2000_2009
from county.county_2010_2020 import process_county_2010_2020
from postprocess import create_single_csv, generate_mcf, generate_tmcf
from common import Outputfiles, _OUTPUTFINAL, _OUTPUTINTERMEDIATE

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "config_files"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")
_MODULE_DIR = os.path.dirname(__file__)


def _get_urls(json_file_path, key, test):
    """
    Extracting dataset urls from json_config_files.

    Args:
        json_file_path: path to config json files.
        key: provies the key for json file.

    Returns:
        urls: dataset url.
    """
    url_json = None
    with open(json_file_path, encoding="UTF-8") as file:
        url_json = json.load(file)
    urls = url_json[key]

    if test:
        if (type(urls) == str):
            urls = os.path.join(_MODULE_DIR, urls)
        elif (type(urls) == list):
            urls = [os.path.join(_MODULE_DIR, url) for url in urls]

    return urls


def process(config_files: list, test=False):
    """
    This method calls the required methods
    and generate final csv, mcf and tmcf.

    Args:
        config_files (List) : list of json files containing dataset url.

    Returns:
        None.
    """
    flag = None

    os.system("mkdir -p " + os.path.join(_MODULE_DIR, _OUTPUTFINAL))
    os.system("mkdir -p " + os.path.join(_MODULE_DIR, _OUTPUTINTERMEDIATE))

    for config_file in config_files:
        files = _get_urls(config_file, "urls", test)
        if "national_1980_1990.json" in config_file:
            process_national_1980_1990(files)
        elif "national_1900_1970.json" in config_file:
            process_national_1900_1970(files)
        elif "national_1990_2000.json" in config_file:
            process_national_1990_2000(files)
        elif "national_2000_2010.json" in config_file:
            process_national_2000_2010(files)
        elif "national_2010_2020.json" in config_file:
            process_national_2010_2020(files)
        elif "state_1970_1979.json" in config_file:
            process_state_1970_1979(files)
        elif "state_1980_1990.json" in config_file:
            process_state_1980_1990(files)
        elif "state_1990_2000.json" in config_file:
            process_state_1990_2000(files)
        elif "state_2000_2010.json" in config_file:
            process_state_2000_2010(files)
        elif "state_2010_2020.json" in config_file:
            process_state_2010_2020(files)
        elif "county_1970_1979.json" in config_file:
            process_county_1970_1979(files)
        elif "county_1980_1989.json" in config_file:
            process_county_1980_1989(files)
        elif "county_1990_2000.json" in config_file:
            process_county_1990_2000(files)
        elif "county_2000_2009.json" in config_file:
            process_county_2000_2009(files)
        elif "county_2010_2020.json" in config_file:
            process_county_2010_2020(files)

    # list of national output files before year 2000
    national_before_2000 = [
        "nationals_result_1900_1959.csv", "nationals_result_1960_1979.csv",
        "nationals_result_1980_1990.csv", "nationals_result_1990_2000.csv"
    ]

    # list of state and county output files before year 2000
    state_county_before_2000 = [
        "state_result_1970_1979.csv", "state_result_1980_1990.csv",
        "state_result_1990_2000.csv", "county_result_1970_1979.csv",
        "county_result_1980_1989.csv", "county_result_1990_2000.csv"
    ]

    # list of state and county output files before after 2000
    state_county_after_2000 = [
        "state_result_2000_2010.csv", "state_result_2010_2020.csv",
        "county_result_2000_2009.csv", "county_result_2010_2020.csv"
    ]

    # list of national output files after year 2000
    national_after_2000 = [
        "nationals_result_2000_2010.csv", "nationals_result_2010_2020.csv"
    ]

    output_files_names = {
        Outputfiles.NationalBefore2000.value: national_before_2000,
        Outputfiles.StateCountyBefore2000.value: state_county_before_2000,
        Outputfiles.StateCountyAfter2000.value: state_county_after_2000,
        Outputfiles.NationalAfter2000.value: national_after_2000
    }
    column_names = create_single_csv(output_files_names)

    for flag, columns in column_names.items():
        generate_mcf(columns, flag)
        generate_tmcf(columns, flag)


def main(_):
    """
    Creating and processing input files
    """
    input_path = FLAGS.input_path

    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    process(ip_files)


if __name__ == "__main__":
    app.run(main)
