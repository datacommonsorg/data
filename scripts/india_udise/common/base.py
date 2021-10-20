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
"""Base Classes and methods to import any dataset from Unified District Information System for Education (UDISE) report system."""

__author__ = ["Thejesh GN (i@thejeshgn.com)"]

import os
import re
import json
import csv
import requests
import time
from os import path
from csv import writer

DATA_API_URL = "http://pgi.seshagun.gov.in/BackEnd-master/api/report/getTabularData"
MASTER_API_URL = "http://pgi.seshagun.gov.in/BackEnd-master/api/report/getMasterData"

DEFAULT_HEADERS = {
    "Connection":
        "keep-alive",
    "Accept":
        "application/json, text/plain, */*",
    "User-Agent":
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Content-Type":
        "application/json",
    "Accept-Language":
        "en-GB,en-US;q=0.9,en;q=0.8",
}

DATA_FILE_NAME_FORMAT = "{year}_{udise_state_code}_{udise_dist_code}_{udise_block_code}.json"

SOCIAL_CATEGORY_MAPPING = {
    "General": "GeneralCategory",
    "SC": "ScheduledCaste",
    "ST": "ScheduledTribe",
    "OBC": "OtherBackwardClass",
    "Overall": ""
}

TEMPLATE_STAT_VAR = """Node: dcid:{name}
typeOf: dcs:StatisticalVariable
populationType: dcs:{populationType}
statType: dcs:{statType}
measuredProperty: dcs:{measuredProperty}
{constraints}

"""
CSV_HEADERS = [
    "Period", "LocationCode", "LocationType", "SocialCategory", "Gender",
    "SchoolLevel", "StatisticalVariable", "Value"
]

module_dir_ = os.path.dirname(__file__)


class UDISEIndiaDataLoaderBase:
    """Base Classes and methods to import any dataset from Unified District Information System for Education (UDISE) report system.
    
    Attributes:
        api_report_code (TYPE): This is the report code as per UDISE
        attribute_mapping (TYPE): This is mapping of downloaded JSON data atributes to constraints
        blocks (list): List of UDISE blocks
        blocks_json_data_file_path (TYPE): Path to blocks geo data file
        csv_file_path (TYPE): Path to store generated CSV file
        csv_headers (TYPE): List of column names for the generated CSV file
        data_folder (TYPE):  Path to folder to store the downloaded data files
        districts (list): List of UDISE districts
        districts_json_data_file_path (TYPE): Path to districts geo data file
        mcf (dict): For storing the variables as they are generated
        mcf_file_path (TYPE): Path to store generated mcf file
        states (list): List of UDISE states
        states_json_data_file_path (TYPE):  Path to states geo data file
        years (TYPE): Years for which the download will run
    """

    def __init__(self,
                 api_report_code,
                 data_folder,
                 csv_file_path,
                 mcf_file_path,
                 years,
                 attribute_mapping,
                 csv_headers=CSV_HEADERS):

        self.api_report_code = api_report_code
        self.data_folder = data_folder
        self.states_json_data_file_path = os.path.join(data_folder,
                                                       "UDISE_States.json")
        self.districts_json_data_file_path = os.path.join(
            data_folder, "UDISE_Districts.json")
        self.blocks_json_data_file_path = os.path.join(data_folder,
                                                       "UDISE_Blocks.json")
        self.csv_file_path = csv_file_path
        self.mcf_file_path = mcf_file_path
        self.csv_headers = csv_headers
        self.years = years
        self.attribute_mapping = attribute_mapping
        self.states = []
        self.districts = []
        self.blocks = []
        self.mcf = {}

    def _year_to_period(self, year):
        assert re.match(r'^[0-9]{4}-[0-9]{2}$', year), year
        return year[:2] + year[-2:] + '-03'

    def _pause(self):
        time.sleep(1)

    def _get_states_json_data(self):
        if path.exists(self.states_json_data_file_path):
            print("States JSON already exists.")
        else:
            data = {"extensionCall": "GET_STATE", "condition": " "}
            self._pause()
            response = requests.post(MASTER_API_URL,
                                     headers=DEFAULT_HEADERS,
                                     json=data,
                                     verify=False)
            if response.status_code == 200:
                json_data_file = open(self.states_json_data_file_path, "w")
                json_data_file.write(json.dumps(response.json()))
                json_data_file.close()
            else:
                raise Exception("Couldn't download states JSON data.")

    def _get_districts_json_data(self):
        if path.exists(self.districts_json_data_file_path):
            print("Districts JSON already exists.")
        else:
            data = {
                "extensionCall": "GET_DISTRICT",
                "condition": " order by district_name ",
            }
            self._pause()
            response = requests.post(MASTER_API_URL,
                                     headers=DEFAULT_HEADERS,
                                     json=data,
                                     verify=False)
            if response.status_code == 200:
                json_data_file = open(self.districts_json_data_file_path, "w")
                json_data_file.write(json.dumps(response.json()))
                json_data_file.close()
            else:
                raise Exception("Couldn't download districts JSON data.")

    def _get_blocks_json_data(self):
        if path.exists(self.blocks_json_data_file_path):
            print("Blocks JSON already exists.")
        else:
            data = {
                "extensionCall": "GET_BLOCK",
                "condition": " order by block_name "
            }
            self._pause()
            response = requests.post(MASTER_API_URL,
                                     headers=DEFAULT_HEADERS,
                                     json=data,
                                     verify=False)
            if response.status_code == 200:
                json_data_file = open(self.blocks_json_data_file_path, "w")
                json_data_file.write(json.dumps(response.json()))
                json_data_file.close()
            else:
                raise Exception("Couldn't download blocks JSON data.")

    def _get_base_name(self, data_row):
        # This function is overridden in the child class
        name = ""
        return name

    def _get_base_constraints(self, data_row):
        # This function is overridden in the child class
        constraints = []
        return constraints

    def _create_variable(self, data_row):
        constraints_array = self._get_base_constraints(data_row)
        name_array = []
        name_array.append(self._get_base_name(data_row))

        if "Gender" in data_row:
            gender = data_row["Gender"]
            name_array.append(gender)
            if gender == "Male":
                constraints_array.append("gender: schema:Male")
            if gender == "Female":
                constraints_array.append("gender: schema:Female")
        
        if "SchoolLevel" in data_row:
            school_level = data_row["SchoolLevel"]
            name_array.append(school_level)
            if school_level == "PrimarySchool":
                constraints_array.append("levelOfSchool: dcs:PrimarySchool")
            if school_level == "MiddleSchool":
                constraints_array.append("levelOfSchool: dcs:MiddleSchool")
            if school_level == "SecondarySchool":
                constraints_array.append("levelOfSchool: dcs:SecondarySchool")

        if "SocialCategory" in data_row:
            social_category = data_row["SocialCategory"]
            if social_category == "GeneralCategory":
                constraints_array.append("socialCategory: dcs:GeneralCategory")
            if social_category == "ScheduledCaste":
                constraints_array.append("socialCategory: dcs:ScheduledCaste")
            if social_category == "ScheduledTribe":
                constraints_array.append("socialCategory: dcs:ScheduledTribe")
            if social_category == "OtherBackwardClass":
                constraints_array.append(
                    "socialCategory: dcs:OtherBackwardClass")

            if social_category != "":
                name_array.append(social_category)

        variable_name = "_".join(name_array)

        fileds = {}
        fileds["name"] = variable_name
        fileds["populationType"] = "Student"
        fileds["statType"] = "measuredValue"
        fileds["measuredProperty"] = "dropoutRate"
        fileds["constraints"] = "\n".join(constraints_array)
        stat_var = TEMPLATE_STAT_VAR.format(**dict(fileds))
        self.mcf[variable_name] = stat_var
        return stat_var, variable_name

    def _process_data(self,
                      year,
                      udise_state_code,
                      udise_dist_code="none",
                      udise_block_code="none"):
        """This will process the data by loading the data file for a given
        year, udise_state_code, udise_dist_code and udise_block_code.
        
        Args:
            year (TYPE): Education year of the report
            udise_state_code (TYPE): UDISE state code
            udise_dist_code (str, optional): UDISE district code
            udise_block_code (str, optional): UDISE block code
        
        Raises:
            Exception: Throws an exception if the data file doesn't exist
        """
        data_file = os.path.join(
            self.data_folder,
            DATA_FILE_NAME_FORMAT.format(year=year,
                                         udise_state_code=udise_state_code,
                                         udise_dist_code=udise_dist_code,
                                         udise_block_code=udise_block_code))
        data_rows = []
        valid_columns = self.attribute_mapping.keys()
        print("Processing {data_file}".format(data_file=data_file))
        if path.exists(data_file):
            json_data_file = open(data_file, "r")
            json_data = json.loads(json_data_file.read())
            json_data_file.close()

            rows = json_data["rowValue"]
            for row in rows:
                for column in valid_columns:
                    # Process only if the data exists for that column
                    if column in row:
                        data_row = {}
                        data_row["Value"] = row[column]
                        data_row["Period"] = self._year_to_period(year)
                        data_row["LocationCode"] = row["location_code"]
                        data_row["LocationType"] = row["rpt_type"]

                        data_row["SocialCategory"] = SOCIAL_CATEGORY_MAPPING[
                            row["item_name"]]

                        attribute_map = self.attribute_mapping[column]
                        if "Gender" in attribute_map:
                            data_row["Gender"] = attribute_map["Gender"]
                        data_row["SchoolLevel"] = attribute_map["SchoolLevel"]
                        stat_var, variable_name = self._create_variable(
                            data_row)
                        data_row["StatisticalVariable"] = variable_name
                        data_rows.append(data_row)

            # Write the final rows to CSV
            write_header = False
            if path.exists(self.csv_file_path) is False:
                write_header = True

            with open(self.csv_file_path, 'a') as file_object:
                writer = csv.DictWriter(file_object,
                                        extrasaction='ignore',
                                        fieldnames=self.csv_headers)
                if write_header:
                    writer.writeheader()
                writer.writerows(data_rows)
                file_object.close()
        else:
            raise Exception("Data file: {data_file} doesn't exist".format(
                data_file=data_file))

    def _get_data(self,
                  year,
                  udise_state_code,
                  udise_dist_code="none",
                  udise_block_code="none"):
        """This will download the data for a given year, 
        udise_state_code, udise_dist_code and udise_block_code.
        
        Once downloaded it saves the data to the file system. If the
        file already exists then it doesn't download the data.

        Args:
            year (TYPE): Education year of the report
            udise_state_code (TYPE): UDISE state code
            udise_dist_code (str, optional): UDISE district code
            udise_block_code (str, optional): UDISE block code
        
        Raises:
            Exception: Throws an exception if it can't download the data.
        """
        data_file = os.path.join(
            self.data_folder,
            DATA_FILE_NAME_FORMAT.format(year=year,
                                         udise_state_code=udise_state_code,
                                         udise_dist_code=udise_dist_code,
                                         udise_block_code=udise_block_code))

        if path.exists(data_file):
            print("Data file: {data_file} already exists".format(
                data_file=data_file))
        else:
            query = {
                "year": year,
                "state": "none",
                "dist": "none",
                "block": "none"
            }
            if udise_state_code:
                query["state"] = udise_state_code
            if udise_dist_code:
                query["dist"] = udise_dist_code
            if udise_block_code:
                query["block"] = udise_block_code

            data = {
                "mapId": self.api_report_code,
                "dependencyValue": json.dumps(query),
                "isDependency": "Y",
                "paramName": "civilian",
                "paramValue": "",
                "schemaName": "national",
                "reportType": "T"
            }
            print(data)
            self._pause()
            response = requests.post(DATA_API_URL,
                                     headers=DEFAULT_HEADERS,
                                     json=data,
                                     verify=False)
            if response.status_code == 200:
                json_data_file = open(data_file, "w")
                json_data_file.write(json.dumps(response.json()))
                json_data_file.close()
            else:
                raise Exception("Couldn't download data.")

    def _download_geography(self):
        self._get_states_json_data()
        self._get_districts_json_data()
        self._get_blocks_json_data()

    def _load_geography(self):
        states_json_data_file = open(self.states_json_data_file_path, "r")
        states_json_data = json.loads(states_json_data_file.read())
        self.states = states_json_data["rowValue"]
        states_json_data_file.close()

        districts_json_data_file = open(self.districts_json_data_file_path, "r")
        districts_json_data = json.loads(districts_json_data_file.read())
        self.districts = districts_json_data["rowValue"]
        districts_json_data_file.close()

        blocks_json_data_file = open(self.blocks_json_data_file_path, "r")
        blocks_json_data = json.loads(blocks_json_data_file.read())
        self.blocks = blocks_json_data["rowValue"]
        blocks_json_data_file.close()

    def _download_data(self):
        for year in self.years:
            for state in self.states:
                self._get_data(year, udise_state_code=state["udise_state_code"])
            for district in self.districts:
                self._get_data(year,
                               udise_state_code=district["udise_state_code"],
                               udise_dist_code=district["udise_district_code"])
            for block in self.blocks:
                self._get_data(year,
                               udise_state_code=block["udise_state_code"],
                               udise_dist_code=block["udise_dist_code"],
                               udise_block_code=block["udise_block_code"])

    def _save_mcf(self):
        if path.exists(self.mcf_file_path) is False:
            for stat_var in self.mcf.values():
                with open(self.mcf_file_path, 'a', newline='') as f_out:
                    f_out.write(stat_var)

    def download(self):
        self._download_geography()
        self._load_geography()
        # Geography needs to be downloaded and loaded first as
        # dowload_data depends on it to download the data
        # for each geography (state, district and block)
        self._download_data()

    def process(self):
        self._load_geography()

        for year in self.years:
            for state in self.states:
                self._process_data(year,
                                   udise_state_code=state["udise_state_code"])
            for district in self.districts:
                self._process_data(
                    year,
                    udise_state_code=district["udise_state_code"],
                    udise_dist_code=district["udise_district_code"])

            for block in self.blocks:
                self._process_data(year,
                                   udise_state_code=block["udise_state_code"],
                                   udise_dist_code=block["udise_dist_code"],
                                   udise_block_code=block["udise_block_code"])

        self._save_mcf()
