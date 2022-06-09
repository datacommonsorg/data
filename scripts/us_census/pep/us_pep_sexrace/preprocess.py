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
three output csv, mcf and tmcf
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

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "config_files"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")


def _get_urls(json_file_path, key):
    """
    Extracting dataset urls from json_config_files
    Args:
        json_file_path: path to config json files
        key: provies the key for json file
    Returns:
        urls: dataset url
    """
    url_json = None
    with open(json_file_path, encoding="UTF-8") as file:
        url_json = json.load(file)
    urls = url_json[key]
    return urls


def process(config_files, output_files_names=None):
    """
    This method calls the required methods
    and generate final csv, mcf and tmcf
    Args:
        config_files: list of json files containing dataset url
        output_files_names: list of output file names
    """
    flag = None

    for config_file in config_files:
        files = _get_urls(config_file, "urls")
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

    if output_files_names is None:
        # list of output files which are processed as is
        as_is_output_files = [
            "nationals_result_1900_1959.csv", "nationals_result_1960_1979.csv",
            "nationals_result_2000_2010.csv", "state_result_2000_2010.csv",
            "state_result_2010_2020.csv", "county_result_2000_2009.csv",
            "county_result_2010_2020.csv"
        ]

        # list of output files which are having aggregation
        # E.g., Count_Person_Male and Count_Person_Female
        aggregate_output_files = [
            "state_result_1970_1979.csv", "state_result_1980_1990.csv",
            "state_result_1990_2000.csv", "county_result_1970_1979.csv",
            "county_result_1980_1989.csv", "county_result_1990_2000.csv"
        ]

        # list of files which are aggregated from state
        geo_aggregate_output_files = [
            "nationals_result_1980_1990.csv", "nationals_result_1990_2000.csv",
            "nationals_result_2010_2020.csv"
        ]
    else:
        as_is_output_files = output_files_names[0]
        aggregate_output_files = output_files_names[1]
        geo_aggregate_output_files = output_files_names[2]

    output_files_names = {
        1: as_is_output_files,
        2: aggregate_output_files,
        3: geo_aggregate_output_files
    }
    column_names = create_single_csv(output_files_names)

    for flag, columns in column_names.items():
        generate_mcf(columns, flag)
        generate_tmcf(columns, flag)


def main(_):
    """
    creating and processing input files
    """
    input_path = FLAGS.input_path

    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    process(ip_files)


if __name__ == "__main__":
    app.run(main)
