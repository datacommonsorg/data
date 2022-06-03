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
'''
This script runs
all the national state and
county python script and generate
three output csv, mcf and tmcf
'''

import os
import json
from absl import app
from absl import flags
from Nationals.national_1900_1970 import process_national_1900_1970
from Nationals.national_1980_1990 import process_national_1980_1990
from Nationals.national_1990_2000 import process_national_1990_2000
from Nationals.national_2000_2010 import process_national_2000_2010
from Nationals.national_2010_2020 import process_national_2010_2020
from State.state_1970_1979 import process_state_1970_1979
from State.state_1980_1990 import process_state_1980_1990
from State.state_1990_2000 import process_state_1990_2000
from State.state_2000_2010 import process_state_2000_2010
from State.state_2010_2020 import process_state_2010_2020
from County.county_1970_1979 import process_county_1970_1979
from County.county_1980_1989 import process_county_1980_1989
from County.county_1990_2000 import process_county_1990_2000
from County.county_2000_2009 import process_county_2000_2009
from County.county_2010_2020 import process_county_2010_2020
from postprocess import _create_single_csv, _generate_mcf, _generate_tmcf

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "config_files"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

def _get_urls(json_file_path, key):
    '''
    Extracting dataset urls from
    json_config_files
    '''
    _URLS_JSON = None
    with open(json_file_path, encoding="UTF-8") as file:
        _URLS_JSON = json.load(file)
    urls = _URLS_JSON[key]
    return urls

def process(config_files, sv_list=None):
    '''
    this method calls the required
    methods and generate final csv, mcf and tmcf
    '''
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

    if sv_list is None:
        # list of output files which are processed as is
        CSVLIST = ["nationals_result_1900_1959.csv",
            "nationals_result_1960_1979.csv",
            "nationals_result_2000_2010.csv",
            "state_result_2000_2010.csv","state_result_2010_2020.csv",
            "county_result_2000_2009.csv", "county_result_2010_2020.csv"]

        # list of output files which are having aggregation Count_Person_Male
        # and Count_Person_Female
        CSVLIST1 = ["state_result_1970_1979.csv","state_result_1980_1990.csv",
            "state_result_1990_2000.csv",
            "county_result_1970_1979.csv", "county_result_1980_1989.csv",
            "county_result_1990_2000.csv"]

        # list of files which are aggregated from state
        CSVLIST2 = ["nationals_result_1980_1990.csv",
            "nationals_result_1990_2000.csv",
            "nationals_result_2010_2020.csv"]
    else:
        CSVLIST = sv_list[0]
        CSVLIST1 = sv_list[1]
        CSVLIST2 = sv_list[2]

    flag_dict = {1:CSVLIST, 2:CSVLIST1, 3:CSVLIST2}
    sv_dict = _create_single_csv(flag_dict)

    for flag,sv_list in sv_dict.items():
        _generate_mcf(sv_list, flag)
        _generate_tmcf(sv_list, flag)

def main(_):
    '''
    creating and processing input files
    '''
    input_path = FLAGS.input_path

    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    process(ip_files)

if __name__ == "__main__":
    app.run(main)
