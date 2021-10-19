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
import enum
import requests
import time
from os import path
from csv import writer

module_dir_ = os.path.dirname(__file__)

DATA_API_URL = "https://dashboard.udiseplus.gov.in/BackEnd-master/api/report/getTabularData"
MASTER_API_URL = "https://dashboard.udiseplus.gov.in/BackEnd-master/api/report/getMasterData"

DEFAULT_HEADERS = {
    'Accept':
        'application/json, text/plain, */*',
    'Accept-Language':
        'en-US,en;q=0.5',
    'Connection':
        'keep-alive',
    'Content-Type':
        'text/plain; charset=utf-8',
    'Origin':
        'https://dashboard.udiseplus.gov.in',
    'Referer':
        'https://dashboard.udiseplus.gov.in/',
    'Sec-Fetch-Dest':
        'empty',
    'Sec-Fetch-Mode':
        'cors',
    'Sec-Fetch-Site':
        'same-origin',
    'User-Agent':
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0',
}

DEFAULT_COOKIES = {
    'JSESSIONID': '6901720E4501A1DD1BF139B244DA75E0',
    'cookieWorked': 'yes',
}

DATA_FILE_NAME_FORMAT = "{udise_report_id}_{udise_map_id}_{geographic_level}_{udise_state_code}_{udise_dist_code}_{udise_block_code}_{year}.json"

SCHOOL_MANAGEMENT = {
    "Department of Education": "DepartmentOfEducation",
    "Tribal Welfare Department": "TribalWelfareDepartment",
    "Local body": "LocalBody",
    "Government Aided": "GovernmentAided",
    "Private Unaided (Recognized)": "PrivateUnaidedButRecognized",
    "Other Govt. managed schools": "OtherGovernmentManaged",
    "Unrecognized": "Unrecognized",
    "Social welfare Department": "SocialWelfareDepartment",
    "Ministry of Labor": "MinistryOfLabor",
    "Kendriya Vidyalaya / Central School": "KendriyaVidyalaya",
    "Jawahar Navodaya Vidyalaya": "JawaharNavodayaVidyalaya",
    "Sainik School": "SainikSchool",
    "Railway School": "RailwaySchool",
    "Central Tibetan School": "CentralTibetanSchool",
    "Madarsa recognized (by Wakf board/Madarsa Board)": "MadrasaRecognized",
    "Madarsa unrecognized": "MadrasaUnrecognized",
    "Other Central Govt. Schools": "OtherCentralGovernmentSchools",
    "Central Govt": "CentralGovernment",
    "No response": "UnknownSchoolManagement",
    "Total": "Total"
}

LATEST_YEAR = "2019-20"

TEMPLATE_STAT_VAR = """Node: dcid:{name}
typeOf: dcs:StatisticalVariable
populationType: dcs:{populationType}
statType: dcs:{statType}
measuredProperty: dcs:{measuredProperty}
{constraints}

"""
CSV_HEADERS = [
    "Period", "UDISECode", "LocationType", "StatisticalVariable", "Value"
]


class GeographicLevel(enum.Enum):
    STATE = "state"
    DISTRICT = "district"
    BLOCK = "block"


ATTRIBUTE_MAPPING = {
    "cat1": {
        "levelOfSchool": "PrimarySchool_Grade1To5"
    },
    "cat2": {
        "levelOfSchool": "UpperPrimarySchool_Grade1To8"
    },
    "cat3": {
        "levelOfSchool": "HigherSecondarySchool_Grade1To12"
    },
    "cat4": {
        "levelOfSchool": "UpperPrimarySchool_Grade6To8"
    },
    "cat5": {
        "levelOfSchool": "UpperPrimarySchool_Grade6To12"
    },
    "cat6": {
        "levelOfSchool": "SeniorSecondarySchool_Grade1To10"
    },
    "cat7": {
        "levelOfSchool": "SeniorSecondarySchool_Grade6To10"
    },
    "cat8": {
        "levelOfSchool": "SeniorSecondarySchool_Grade9To10"
    },
    "cat10": {
        "levelOfSchool": "HigherSecondarySchool_Grade9To12"
    },
    "cat11": {
        "levelOfSchool": "HigherSecondarySchool_Grade11To12"
    },
    "Total": {
        "levelOfSchool": "Total"
    }
}


class UDISEIndiaSchoolDataLoaderBase:
    """Base Classes and methods to import any school level from Unified District Information System for Education (UDISE) report system.
    
    Attributes:
        udise_report_id (TYPE): This is the report code as per UDISE
        udise_map_id: This is the mapping code as per UDISE AP
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
                 udise_report_id,
                 udise_map_id,
                 data_folder,
                 csv_file_path,
                 mcf_file_path,
                 years,
                 attribute_mapping=ATTRIBUTE_MAPPING,
                 csv_headers=CSV_HEADERS):

        self.udise_report_id = udise_report_id
        self.udise_map_id = udise_map_id
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
        print("self.states_json_data_file_path",
              self.states_json_data_file_path)
        if path.exists(self.states_json_data_file_path):
            print("States JSON already exists.")
        else:
            condition = " where ac_year ='{LATEST_YEAR}' ".format(
                LATEST_YEAR=LATEST_YEAR)
            data = {"extensionCall": "GET_STATE", "condition": condition}
            self._pause()
            response = requests.post(MASTER_API_URL,
                                     headers=DEFAULT_HEADERS,
                                     data=json.dumps(data),
                                     cookies=DEFAULT_COOKIES,
                                     verify=False)
            print(response)
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
            condition = " where ac_year ='{LATEST_YEAR}' order by district_name ".format(
                LATEST_YEAR=LATEST_YEAR)
            data = {
                "extensionCall": "GET_DISTRICT",
                "condition": condition,
            }
            self._pause()
            response = requests.post(MASTER_API_URL,
                                     headers=DEFAULT_HEADERS,
                                     data=json.dumps(data),
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
            condition = " where ac_year ='{LATEST_YEAR}' order by block_name ".format(
                LATEST_YEAR=LATEST_YEAR)
            data = {"extensionCall": "GET_BLOCK", "condition": condition}
            self._pause()
            response = requests.post(MASTER_API_URL,
                                     headers=DEFAULT_HEADERS,
                                     data=json.dumps(data),
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
        if "LevelOfSchool" in data_row:
            school_level = data_row["LevelOfSchool"]
            if school_level == "Total":
                # If the level is total
                # then no need to add Constraint
                pass
            else:
                name_array.append(school_level)
                constraints_array.append(
                    "levelOfSchool: dcs:UDISE_{}".format(school_level))

        if "SchoolManagement" in data_row:
            school_management = data_row["SchoolManagement"]
            if school_management == "Total":
                # If the level is total
                # then no need to add Constraint
                pass
            else:
                name_array.append(school_management)
                constraints_array.append(
                    "schoolManagement: dcs:UDISE_{}".format(school_management))

        variable_name = "_".join(name_array)

        fileds = {}
        fileds["name"] = variable_name
        fileds["populationType"] = "School"
        fileds["statType"] = "measuredValue"
        fileds["measuredProperty"] = "count"
        fileds["constraints"] = "\n".join(constraints_array)
        stat_var = TEMPLATE_STAT_VAR.format(**dict(fileds))
        self.mcf[variable_name] = stat_var
        return stat_var, variable_name

    def _process_data(self,
                      year,
                      geographic_level,
                      udise_state_code,
                      udise_dist_code="NA",
                      udise_block_code="NA"):
        """This will process the data by loading the data file for a given
        year, udise_state_code, udise_dist_code and udise_block_code.
        
        Args:
            year (TYPE): Education year of the report
            geographic_level (str): geographic level for which we are processing data
            udise_state_code (TYPE): UDISE state code
            udise_dist_code (str, optional): UDISE district code
            udise_block_code (str, optional): UDISE block code
        
        Raises:
            Exception: Throws an exception if the data file doesn't exist
        """
        data_file = os.path.join(
            self.data_folder,
            DATA_FILE_NAME_FORMAT.format(year=year,
                                         geographic_level=geographic_level,
                                         udise_report_id=self.udise_report_id,
                                         udise_map_id=self.udise_map_id,
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
                        data_row["LocationType"] = geographic_level
                        if geographic_level == GeographicLevel.STATE.value:
                            data_row["UDISECode"] = udise_state_code
                        elif geographic_level == GeographicLevel.DISTRICT.value:
                            data_row["UDISECode"] = udise_dist_code

                        data_row["SchoolManagement"] = SCHOOL_MANAGEMENT[(
                            row["sch_mgmt_name"]).strip()]

                        attribute_map = self.attribute_mapping[column]

                        data_row["LevelOfSchool"] = attribute_map[
                            "levelOfSchool"]
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
                  geographic_level,
                  udise_state_code,
                  udise_dist_code="NA",
                  udise_block_code="NA"):
        """This will download the data for a given year, 
        udise_state_code, udise_dist_code and udise_block_code.
        
        Once downloaded it saves the data to the file system. If the
        file already exists then it doesn't download the data.

        Args:
            year (TYPE): Education year of the report
            geographic_level (str): For which level we are trying to download the data
            udise_state_code (TYPE): UDISE state code
            udise_dist_code (str, optional): UDISE district code
            udise_block_code (str, optional): UDISE block code
        
        Raises:
            Exception: Throws an exception if it can't download the data.
        """
        data_file = os.path.join(
            self.data_folder,
            DATA_FILE_NAME_FORMAT.format(year=year,
                                         geographic_level=geographic_level,
                                         udise_report_id=self.udise_report_id,
                                         udise_map_id=self.udise_map_id,
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
            if udise_state_code != "NA":
                query["state"] = udise_state_code
            if udise_dist_code != "NA":
                query["dist"] = udise_dist_code
            if udise_block_code != "NA":
                query["block"] = udise_block_code

            data = {
                "mapId": self.udise_map_id,
                "dependencyValue": json.dumps(query),
                "isDependency": "Y",
                "paramName": "civilian",
                "paramValue": "",
                "schemaName": "national",
                "reportType": "T"
            }

            self._pause()
            response = requests.post(DATA_API_URL,
                                     headers=DEFAULT_HEADERS,
                                     data=json.dumps(data),
                                     cookies=DEFAULT_COOKIES,
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
        #TODO: Add downloading blocks data

    def _load_geography(self):
        states_json_data_file = open(self.states_json_data_file_path, "r")
        states_json_data = json.loads(states_json_data_file.read())
        self.states = states_json_data["rowValue"]
        states_json_data_file.close()

        districts_json_data_file = open(self.districts_json_data_file_path, "r")
        districts_json_data = json.loads(districts_json_data_file.read())
        self.districts = districts_json_data["rowValue"]
        districts_json_data_file.close()

        #TODO: Load blocks data

    def _download_data(self):
        for year in self.years:
            for state in self.states:
                self._get_data(year,
                               geographic_level=GeographicLevel.STATE.value,
                               udise_state_code=state["udise_state_code"])

            for district in self.districts:
                self._get_data(year,
                               geographic_level=GeographicLevel.DISTRICT.value,
                               udise_state_code=district["udise_state_code"],
                               udise_dist_code=district["udise_district_code"])

            #TODO: Download blocks data

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
                                   geographic_level="state",
                                   udise_state_code=state["udise_state_code"])
            for district in self.districts:
                self._process_data(
                    year,
                    geographic_level="district",
                    udise_state_code=district["udise_state_code"],
                    udise_dist_code=district["udise_district_code"])

            #TODO: Process blocks data

        self._save_mcf()
