# Copyright 2020 Google LLC
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
import json
import csv
import copy
import pandas as pd
import numpy as np
import urllib.request

TEMPLATE_STAT_VAR = """
Node: dcid:{name}
description: "{description}"
typeOf: dcs:StatisticalVariable
populationType: dcs:{populationType}
statType: dcs:{statType}
measuredProperty: dcs:{measuredProperty}{constraints}
"""

TEMPLATE_TMCF = """Node: E:IndiaCensus{year}_{dataset_name}->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:IndiaCensus{year}_{dataset_name}->StatisticalVariable
observationDate: C:IndiaCensus{year}_{dataset_name}->Year
observationAbout: C:IndiaCensus{year}_{dataset_name}->E1
value: C:IndiaCensus{year}_{dataset_name}->value

Node: E:IndiaCensus{year}_{dataset_name}->E1
typeOf: schema:Place
indianCensusAreaCode{year}: C:IndiaCensus{year}_{dataset_name}->census_location_id"""

CENSUS_DATA_COLUMN_START = 9


class CensusPrimaryAbstractDataLoaderBase:
    """An object that represents Primary Abstract Data and its variables.
    
    Attributes:
        census_columns (list): It will have all the data column names of a dataset
        census_year : Census year
        csv_file_path : Path where cleaned csv file will be saved
        data_file_path : Input XLS file from Census of India. Can be url or local path.
        dataset_name : Census dataset name. Eg:Primary_Abstract_Data
        existing_stat_var (list): List of existing stat vars that we don't need to generate
        mcf (list): Description
        mcf_file_path : Description
        metadata_file_path : Description
        raw_df : Raw census data as dataframe
        stat_var_index (dict): local storage for census column name and corresponding statvar
        tmcf_file_path : Path where generated tmcf file will be saved
    """

    def __init__(self, data_file_path, metadata_file_path, mcf_file_path,
                 tmcf_file_path, csv_file_path, existing_stat_var, census_year,
                 dataset_name):
        """
        Constructor
        
        Args:
            data_file_path :  Input XLS file from Census of India. Can be url or local path
            metadata_file_path : Meta data csv file which has attribute details
            mcf_file_path : Path where generated mcf file will be saved
            tmcf_file_path : Path where generated tmcf file will be saved
            csv_file_path : Path where cleaned csv file will be saved
            existing_stat_var : List of existing stat vars that we don't need to generate
            census_year : Census Year
            dataset_name : Census dataset name. Eg:Primary_Abstract_Data
        """
        self.data_file_path = data_file_path
        self.metadata_file_path = metadata_file_path
        self.mcf_file_path = mcf_file_path
        self.csv_file_path = csv_file_path
        self.tmcf_file_path = tmcf_file_path
        self.existing_stat_var = existing_stat_var
        self.census_year = census_year
        self.dataset_name = dataset_name
        self.raw_df = None
        self.stat_var_index = {}
        self.census_columns = []

    def _download_and_standardize(self):
        dtype = {
            'State': str,
            'District': str,
            'Subdistt': str,
            "Town/Village": str,
            "Ward": str,
            "EB": str
        }
        self.raw_df = pd.read_excel(self.data_file_path, dtype=dtype)
        self.census_columns = self.raw_df.columns[CENSUS_DATA_COLUMN_START:]

    def _format_location(self, row):
        #In census of India. Location code for India is all zeros.
        if (row["Level"]).upper() == "INDIA":
            return "0"
        elif (row["Level"]).upper() == "STATE":
            return row["State"]
        elif (row["Level"]).upper() == "DISTRICT":
            return row["District"]
        elif (row["Level"]).upper() == "SUBDISTT":
            return row["Subdistt"]
        elif (row["Level"]).upper() == "TOWN":
            return row["Town/Village"]
        elif (row["Level"]).upper() == "VILLAGE":
            return row["Town/Village"]
        else:
            raise Exception("Location Level not supported")

    def _format_data(self):

        #Generate Census locationid
        self.raw_df["census_location_id"] = self.raw_df.apply(
            self._format_location, axis=1)

        #Remove the unwanted columns
        #They are census codes which we dont use
        #State,District,Subdistt,Town/Village,Ward,EB
        self.raw_df.drop([
            "State", "District", "Subdistt", "Town/Village", "Ward", "EB",
            "Level", "Name"
        ],
                         axis=1,
                         inplace=True)
        #first column is Name of the place
        #second column is Name of the TRU/placeOfResidence
        #3-N are the actual values
        value_columns = list(self.raw_df.columns[1:-1])

        #converting rows in to columns. So the final structure will be
        #Name,TRU,columnName,value
        self.raw_df = self.raw_df.melt(id_vars=["census_location_id", "TRU"],
                                       value_vars=value_columns,
                                       var_name='columnName',
                                       value_name='Value')

        #Add corresponding StatisticalVariable, based on columnName and TRU
        self.raw_df['StatisticalVariable'] = self.raw_df.apply(
            lambda row: self.stat_var_index["{0}_{1}".format(
                row["columnName"], row["TRU"])],
            axis=1)
        #add the census year
        self.raw_df['Year'] = self.census_year

        #Export it as CSV. It will have the following columns
        #Name,TRU,columnName,value,StatisticalVariable,Year
        self.raw_df.to_csv(self.csv_file_path, index=False, header=True)

    def _get_base_name(self, row):
        #This function is overridden in the child class
        name = "Count_" + row["populationType"]
        return name

    def _get_base_constraints(self, row):
        #This function is overridden in the child class
        constraints = ""
        return constraints

    def _create_variable(self, data_row, place_of_residence=None):
        row = copy.deepcopy(data_row)
        name_array = []
        constraints_array = []

        name_array.append(self._get_base_name(row))
        constraints_array.append(self._get_base_constraints(row))

        if row["age"] == "YearsUpto6":
            name_array.append("YearsUpto6")
            constraints_array.append("age: dcid:YearsUpto6")
        else:
            pass

        if row["workerStatus"] == "Worker":
            constraints_array.append("workerStatus: dcs:Worker")
            if row["workerClassification"] == "MainWorker":
                name_array.append("MainWorkers")
                constraints_array.append("workerClassification: dcs:MainWorker")
                if row["workCategory"] != "":
                    name_array.append(row["workCategory"])
                    constraints_array.append("workCategory: dcs:" +
                                             row["workCategory"])

            elif row["workerClassification"] == "MarginalWorker":
                name_array.append("MarginalWorker")
                constraints_array.append(
                    "workerClassification: dcs:MarginalWorker")

                if row["workCategory"] != "":
                    name_array.append("workCategory")
                    constraints_array.append("workCategory: dcs:" +
                                             row["workCategory"])

                if row["workPeriod"] == "[Month - 3]":
                    name_array.append("WorkedUpto3Months")
                    constraints_array.append("workPeriod:" + row["workPeriod"])

                if row["workPeriod"] == "[Month 3 6]":
                    name_array.append("Worked3To6Months")
                    constraints_array.append("workPeriod:" + row["workPeriod"])
            else:
                name_array.append("Workers")

        elif row["workerStatus"] == "NonWorker":
            name_array.append("NonWorker")
            constraints_array.append("workerStatus: dcs:NonWorker")

        if place_of_residence == "Urban":
            name_array.append("Urban")
            constraints_array.append("placeOfResidence: dcs:Urban")
            row["description"] = row["description"] + " - Urban"

        elif place_of_residence == "Rural":
            name_array.append("Rural")
            constraints_array.append("placeOfResidence: dcs:Rural")
            row["description"] = row["description"] + " - Rural"

        if row["gender"] == "Male":
            name_array.append("Male")
            constraints_array.append("gender: schema:Male")

        elif row["gender"] == "Female":
            name_array.append("Female")
            constraints_array.append("gender: schema:Female")

        name = "_".join(name_array)
        row["name"] = name
        row["constraints"] = "\n".join(constraints_array)

        key = "{0}_{1}".format(
            row["columnName"],
            place_of_residence if place_of_residence != None else "Total")
        self.stat_var_index[key] = name

        self.mcf.append(row)
        stat_var = TEMPLATE_STAT_VAR.format(**dict(row))
        return name, stat_var

    def _create_mcf(self):
        self.mcf = []
        with open(self.metadata_file_path) as csvfile:
            reader = csv.DictReader(csvfile)
            with open(self.mcf_file_path, 'w+', newline='') as f_out:
                for data_row in reader:
                    for place_of_residence in [None, "Urban", "Rural"]:
                        name, stat_var = self._create_variable(
                            data_row, place_of_residence)
                        #if the statvar already exists then we don't
                        #need to recreate it
                        if name in self.existing_stat_var:
                            pass
                        #we need to create statvars only for those columns that
                        #exist in the current data file
                        elif data_row["columnName"] not in self.census_columns:
                            pass
                        else:
                            f_out.write(stat_var)

    def _create_tmcf(self):
        with open(self.tmcf_file_path, 'w+', newline='') as f_out:
            f_out.write(
                TEMPLATE_TMCF.format(year=self.census_year,
                                     dataset_name=self.dataset_name))

    def process(self):
        self._download_and_standardize()
        self._create_mcf()
        self._create_tmcf()
        self._format_data()
